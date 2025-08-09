import os
import shutil
import re
from datetime import datetime
from typing import Dict, Any, Set
from .base_strand import Strand

class RoutingStrand(Strand):
    """
    Routing Strand: Organizes files by veteran name at root level with category subfolders.
    
    NEW STRUCTURE: {veteran_name}_docs/{category}/{veteran_name}_{category}_{timestamp}.{ext}
    
    All documents for a veteran go under the same veteran folder regardless of confidence level.
    Categories: RDL, RCS, RDS, Medical_Evidence, VA_Forms, Lay_Statements, Legal_Documents, Other
    """

    def __init__(self, base_data_path: str = "data"):
        super().__init__("routing")
        # Use relative path from the backend directory
        if not os.path.isabs(base_data_path):
            backend_dir = os.path.dirname(os.path.dirname(__file__))  # Get backend/ directory
            self.base_data_path = os.path.join(backend_dir, base_data_path)
        else:
            self.base_data_path = base_data_path
        
        # Define the 8 document categories
        self.categories = [
            "RDL", "RCS", "RDS", "Medical_Evidence", 
            "VA_Forms", "Lay_Statements", "Legal_Documents", "Other"
        ]
        
        # Track veteran names for grouping
        self.known_veterans: Set[str] = set()
        self._load_existing_veterans()

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that required fields exist in input_data."""
        required_fields = ["file_path", "processing_route", "document_type", "confidence"]
        return all(field in input_data for field in required_fields)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route file to veteran-specific directory structure at root level.
        """
        original_file_path = input_data["file_path"]
        processing_route = input_data["processing_route"]
        document_type = input_data["document_type"]
        confidence = input_data["confidence"]
        extracted_data = input_data.get("extracted_data", {})
        
        # Get veteran name from extracted data
        veteran_name = self._get_veteran_name(extracted_data, input_data.get("original_filename", ""))
        
        # Check if we should group with existing veteran
        grouped_veteran = self._find_matching_veteran(veteran_name)
        if grouped_veteran:
            veteran_name = grouped_veteran
            self.logger.info(f"Grouping with existing veteran: {veteran_name}")
        
        try:
            # New structure: Root-level veteran folders with category subfolders
            destination_dir, new_filename = self._handle_veteran_document(
                original_file_path, document_type, veteran_name, confidence
            )
            
            # Create destination directory
            os.makedirs(destination_dir, exist_ok=True)
            
            # Move file to destination
            destination_path = os.path.join(destination_dir, new_filename)
            
            # Handle file conflicts by adding counter
            counter = 1
            base_name, ext = os.path.splitext(new_filename)
            while os.path.exists(destination_path):
                new_filename = f"{base_name}_{counter}{ext}"
                destination_path = os.path.join(destination_dir, new_filename)
                counter += 1
            
            shutil.move(original_file_path, destination_path)

            # Track this veteran
            self.known_veterans.add(veteran_name)

            # Update input_data with results
            input_data["final_path"] = destination_path
            input_data["final_directory"] = destination_dir
            input_data["new_filename"] = new_filename
            input_data["veteran_name_used"] = veteran_name
            input_data["routing_status"] = "success"
            input_data["confidence_category"] = self._get_confidence_category(confidence)
            input_data["document_category"] = document_type

            self.logger.info(f"File routed to: {destination_path} (veteran: {veteran_name}, confidence: {confidence:.1%})")

            return input_data

        except Exception as e:
            self.logger.error(f"Routing failed: {str(e)}")
            input_data["routing_status"] = "failed"
            input_data["routing_error"] = str(e)
            return input_data

    def _get_veteran_name(self, extracted_data: Dict[str, Any], filename: str) -> str:
        """
        Extract and validate veteran name from data, ensuring it's a human-like name.
        
        Args:
            extracted_data: Extracted data dictionary
            filename: Original filename as fallback
            
        Returns:
            Clean veteran name for folder/file naming
        """
        # Try multiple sources for veteran name
        veteran_name = None
        
        # Priority order for name extraction
        name_sources = [
            extracted_data.get("primary_name"),
            extracted_data.get("names", [None])[0] if extracted_data.get("names") else None,
            extracted_data.get("name"),  # From form-specific extraction
        ]
        
        for name in name_sources:
            if self._is_valid_human_name(name):
                veteran_name = name.strip()
                break
        
        # If no valid name found, try filename extraction
        if not veteran_name:
            filename_name = self._extract_name_from_filename(filename)
            if self._is_valid_human_name(filename_name):
                veteran_name = filename_name
        
        # Final fallback - but only if we really can't find anything
        if not veteran_name:
            veteran_name = "Unknown_Veteran"
            self.logger.warning(f"No valid human name found in {filename}, using fallback")
        
        # Clean name for file system use
        return self._sanitize_name(veteran_name)

    def _is_valid_human_name(self, name: str) -> bool:
        """
        Validate that a name looks like a human name, not form fields or artifacts.
        
        Args:
            name: Candidate name string
            
        Returns:
            True if name appears to be a valid human name
        """
        if not name or not isinstance(name, str):
            return False
        
        name = name.strip()
        
        # Basic length checks
        if len(name) < 3 or len(name) > 50:
            return False
        
        # Must have at least first and last name (2 words minimum after cleaning titles)
        clean_name = name
        
        # Remove common titles first
        titles = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Lt.', 'Col.', 'Maj.', 'Sgt.', 'Cpl.']
        for title in titles:
            if clean_name.startswith(title):
                clean_name = clean_name[len(title):].strip()
        
        # Handle LAST, FIRST format
        if ',' in clean_name:
            parts = clean_name.split(',', 1)
            if len(parts) == 2:
                clean_name = f"{parts[1].strip()} {parts[0].strip()}"
        
        words = clean_name.split()
        if len(words) < 2:
            return False
        
        # Reject common form field artifacts
        reject_patterns = [
            r'^(VETERAN|NAME|FULL|FIRST|LAST|MIDDLE)$',
            r'^(CLAIMANT|PATIENT|SERVICE|MEMBER)$', 
            r'^(FILE|CLAIM|CASE|DOC|DOCUMENT)$',
            r'^(TEMP|UPLOAD|TEST|EXAMPLE|SAMPLE)$',
            r'^\d+$',  # All numbers
            r'[0-9]{3,}',  # Contains 3+ consecutive numbers
            r'[@#$%^&*()]',  # Special characters
            r'(\.pdf|\.doc|\.txt)$',  # File extensions
        ]
        
        name_upper = name.upper()
        for pattern in reject_patterns:
            if re.search(pattern, name_upper):
                return False
        
        # Check that each word looks like a name part
        for word in words:
            # Skip empty words
            if not word:
                continue
                
            # Allow common name patterns:
            # - Standard names (John, Smith)
            # - Names with apostrophes (O'Connor)
            # - Names with hyphens (Jean-Luc)
            # - Names with periods (Jr.)
            if not re.match(r'^[A-Za-z][A-Za-z\'\.\-]*[A-Za-z\.]?$', word):
                return False
        
        # Additional validation - should contain mostly letters
        letter_count = sum(1 for c in clean_name if c.isalpha())
        total_chars = len(re.sub(r'\s', '', clean_name))
        
        if total_chars > 0 and letter_count / total_chars < 0.8:  # At least 80% letters
            return False
        
        return True

    def _extract_name_from_filename(self, filename: str) -> str:
        """Extract potential name from filename."""
        if not filename:
            return ""
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Skip obvious non-name files
        skip_patterns = [
            r'^(temp|upload|file|document|doc|pdf)',
            r'^\d+',
            r'^(rdl|rcs|rds|medical|va|form)',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, base_name.lower()):
                return ""
        
        # Try to extract name patterns from filename
        # Look for patterns like "John_Smith" or "Smith_John"  
        name_patterns = [
            r'([A-Z][a-z]+_[A-Z][a-z]+)',  # First_Last
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, base_name)
            if matches:
                return matches[0].replace('_', ' ')
        
        return ""

    def _find_matching_veteran(self, current_name: str) -> str:
        """
        Find if current name matches an existing veteran (for grouping documents).
        
        Args:
            current_name: Current extracted veteran name
            
        Returns:
            Existing veteran name if match found, None otherwise
        """
        if not current_name or current_name == "Unknown_Veteran":
            return None
        
        current_clean = current_name.lower().replace('_', ' ')
        current_words = set(current_clean.split())
        
        # Look for existing veterans with similar names
        for existing_veteran in self.known_veterans:
            if existing_veteran == "Unknown_Veteran":
                continue
                
            existing_clean = existing_veteran.lower().replace('_', ' ')
            existing_words = set(existing_clean.split())
            
            # Check for exact match
            if current_clean == existing_clean:
                return existing_veteran
            
            # Check for partial match (same first + last name)
            if len(current_words.intersection(existing_words)) >= 2:
                # If we have at least 2 matching words (likely first + last)
                return existing_veteran
        
        return None

    def _load_existing_veterans(self):
        """Load existing veteran folders to enable document grouping."""
        try:
            if os.path.exists(self.base_data_path):
                for item in os.listdir(self.base_data_path):
                    if item.endswith('_docs') and os.path.isdir(os.path.join(self.base_data_path, item)):
                        veteran_name = item[:-5]  # Remove '_docs' suffix
                        self.known_veterans.add(veteran_name)
                        
            self.logger.info(f"Loaded {len(self.known_veterans)} existing veterans for grouping")
        except Exception as e:
            self.logger.error(f"Error loading existing veterans: {e}")
            self.known_veterans = set()

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize name for file system use following FOLDER_STRUCTURE.md specifications.
        
        Args:
            name: Raw name string
            
        Returns:
            Sanitized name suitable for file/folder names
        """
        if not name:
            return "Unknown_Veteran"
        
        # Remove titles and clean up
        name = name.strip()
        
        # Remove common titles (enhanced list)
        titles = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Lt.', 'Col.', 'Maj.', 'Sgt.', 'Cpl.']
        for title in titles:
            if name.startswith(title):
                name = name[len(title):].strip()
        
        # Handle LAST, FIRST format conversion (enhanced)
        if ',' in name:
            parts = name.split(',', 1)
            if len(parts) == 2:
                last_name = parts[0].strip().title()  # Convert to title case
                first_name = parts[1].strip().title() # Convert to title case
                # Convert to FIRST LAST format
                name = f"{first_name} {last_name}"
        
        # Replace spaces with underscores and handle special characters
        # Keep apostrophes for names like O'Connor
        sanitized = ""
        for c in name:
            if c.isalnum():
                sanitized += c
            elif c in " -.'":
                if c == "'":
                    sanitized += "_"  # Convert apostrophe to underscore
                elif c == " ":
                    sanitized += "_"
                elif c == "-":
                    sanitized += "_"
                elif c == ".":
                    pass  # Remove dots
            # Skip other special characters
        
        # Remove multiple underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        
        # Ensure minimum length requirements
        if len(sanitized) < 2:
            sanitized = "Unknown_Veteran"
            
        # Ensure it's not empty and doesn't start with numbers
        if not sanitized or sanitized[0].isdigit():
            sanitized = "Unknown_Veteran"
            
        return sanitized
    def _handle_veteran_document(self, file_path: str, document_type: str, veteran_name: str, confidence: float) -> tuple:
        """
        Handle document routing to veteran-specific root-level directory structure.
        
        NEW STRUCTURE: {veteran_name}_docs/{category}/
        
        Args:
            file_path: Original file path
            document_type: Document category (RDL, RCS, RDS, etc.)
            veteran_name: Sanitized veteran name
            confidence: Classification confidence
            
        Returns:
            Tuple of (destination_directory, new_filename)
        """
        # Create veteran-specific folder at root level: {veteran_name}_docs
        veteran_folder = f"{veteran_name}_docs"
        
        # Map document types to proper category names
        category_mapping = {
            "RDL": "RDL",
            "RCS": "RCS", 
            "RDS": "RDS",
            "Medical Evidence": "Medical_Evidence",
            "VA Forms": "VA_Forms",
            "Lay Statements": "Lay_Statements",
            "Legal Documents": "Legal_Documents",
            "Other": "Other"
        }
        
        category = category_mapping.get(document_type, "Other")
        
        # Create full path: root/{veteran_name}_docs/{category}/
        destination_dir = os.path.join(self.base_data_path, veteran_folder, category)
        
        # Generate new filename with confidence indicator
        confidence_suffix = ""
        if confidence < 0.6:
            confidence_suffix = "_low_confidence"
        elif confidence < 0.8:
            confidence_suffix = "_needs_review"
        
        new_filename = self._generate_filename(file_path, document_type + confidence_suffix, veteran_name)
        
        return destination_dir, new_filename

    def _get_confidence_category(self, confidence: float) -> str:
        """
        Get confidence category for metadata tracking.
        
        Args:
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            Confidence category string
        """
        if confidence >= 0.8:
            return "high_confidence"
        elif confidence >= 0.6:
            return "medium_confidence"  
        else:
            return "low_confidence"

    def _generate_filename(self, original_path: str, category: str, veteran_name: str) -> str:
        """
        Generate a new filename based on veteran name, category, and timestamp.
        
        Args:
            original_path: Path to original file
            category: Document category (with potential confidence suffix)
            veteran_name: Sanitized veteran name
            
        Returns:
            New filename in format: {veteran_name}_{category}_{timestamp}.{ext}
        """
        _, ext = os.path.splitext(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean category name (remove spaces, special chars)
        clean_category = category.replace(" ", "_").replace("-", "_").lower()
        
        new_filename = f"{veteran_name}_{clean_category}_{timestamp}{ext}"
        
        return new_filename
 