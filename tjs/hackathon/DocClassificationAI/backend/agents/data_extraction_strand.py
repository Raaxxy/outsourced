import re
import json
import os
from typing import Dict, Any, List
from .base_strand import Strand
from utils.ocr_helpers import OCRHelpers

class DataExtractionStrand(Strand):
    """
    Data Extraction Strand: Extracts structured data from VA documents.
    """
    
    def __init__(self):
        super().__init__("data_extraction")
        self.ocr_helpers = OCRHelpers()
        
        # VA Form patterns and field mappings
        self.form_patterns = {
            "21-526EZ": {
                "name": [
                    r"VETERAN'S FULL NAME[:\s]*([A-Za-z\s]+)",
                    r"NAME OF VETERAN[:\s]*([A-Za-z\s]+)",
                    r"VETERAN NAME[:\s]*([A-Za-z\s]+)"
                ],
                "ssn": [
                    r"SSN[:\s]*(\d{3}-\d{2}-\d{4})",
                    r"SOCIAL SECURITY NUMBER[:\s]*(\d{3}-\d{2}-\d{4})",
                    r"(\d{3}-\d{2}-\d{4})"
                ],
                "email": [
                    r"EMAIL[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
                    r"E-MAIL[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})"
                ],
                "phone": [
                    r"PHONE[:\s]*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})",
                    r"TELEPHONE[:\s]*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})",
                    r"(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})"
                ],
                "address": [
                    r"ADDRESS[:\s]*([A-Za-z0-9\s,.-]+)",
                    r"STREET ADDRESS[:\s]*([A-Za-z0-9\s,.-]+)"
                ],
                "disability_percentage": [
                    r"(\d{1,3})\s*%\s*DISABILITY",
                    r"DISABILITY RATING[:\s]*(\d{1,3})\s*%"
                ]
            },
            "10-10EZ": {
                "name": [
                    r"VETERAN'S NAME[:\s]*([A-Za-z\s]+)",
                    r"FULL NAME[:\s]*([A-Za-z\s]+)"
                ],
                "ssn": [
                    r"SSN[:\s]*(\d{3}-\d{2}-\d{4})",
                    r"SOCIAL SECURITY[:\s]*(\d{3}-\d{2}-\d{4})"
                ],
                "email": [
                    r"EMAIL[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})"
                ],
                "phone": [
                    r"PHONE[:\s]*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})"
                ]
            },
            "RDS": {
                "diagnostic_codes": [
                    r"DIAGNOSTIC CODE[:\s]*(\d{4})",
                    r"DC[:\s]*(\d{4})",
                    r"CODE[:\s]*(\d{4})",
                    r"(\d{4})\s*-\s*[A-Za-z]",  # Pattern like "5010 - Lumbar"
                    r"DC\s+(\d{4})"
                ],
                "medical_conditions": [
                    r"CONDITION[:\s]*([A-Za-z\s,]+)",
                    r"DISABILITY[:\s]*([A-Za-z\s,]+)",
                    r"(\d{4})\s*-?\s*([A-Za-z\s,]+?)(?:\s*-?\s*\d{1,3}%)",  # Extract condition from code-condition-% pattern
                    r"LUMBAR[:\s]*([A-Za-z\s,]+)",
                    r"CERVICAL[:\s]*([A-Za-z\s,]+)",
                    r"PTSD|POST TRAUMATIC STRESS|ANXIETY|DEPRESSION"
                ],
                "individual_ratings": [
                    r"(\d{1,3})\s*%(?:\s*DISABILITY)?",
                    r"RATING[:\s]*(\d{1,3})\s*%",
                    r"SCHEDULAR[:\s]*(\d{1,3})\s*%",
                    r"(\d{4})\s*-\s*[A-Za-z\s,]+-?\s*(\d{1,3})%"  # Extract rating from DC-condition-rating
                ],
                "combined_rating": [
                    r"COMBINED RATING[:\s]*(\d{1,3})\s*%",
                    r"TOTAL RATING[:\s]*(\d{1,3})\s*%",
                    r"OVERALL RATING[:\s]*(\d{1,3})\s*%",
                    r"FINAL RATING[:\s]*(\d{1,3})\s*%"
                ],
                "cfr_references": [
                    r"38 CFR[:\s]*([0-9.]+)",
                    r"CFR[:\s]*([0-9.]+)",
                    r"38\s*CFR\s*§?\s*([0-9.]+)",
                    r"SECTION\s*([0-9.]+)"
                ],
                "schedular_rating": [
                    r"SCHEDULAR RATING[:\s]*(\d{1,3})\s*%",
                    r"SCHEDULE RATING[:\s]*(\d{1,3})\s*%",
                    r"SCHEDULAR[:\s]*(\d{1,3})%"
                ],
                "extra_schedular": [
                    r"EXTRA-SCHEDULAR[:\s]*(YES|NO)",
                    r"EXTRASCHEDULAR[:\s]*(YES|NO)",
                    r"EXTRA SCHEDULAR[:\s]*(YES|NO)"
                ],
                "effective_dates": [
                    r"EFFECTIVE DATE[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
                    r"EFFECTIVE[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
                    r"FROM[:\s]*(\d{1,2}/\d{1,2}/\d{4})"
                ],
                "bilateral_factor": [
                    r"BILATERAL FACTOR[:\s]*(\d{1,3})\s*%",
                    r"BILATERAL[:\s]*(\d{1,3})\s*%"
                ],
                "tdiu_info": [
                    r"TDIU[:\s]*(YES|NO|GRANTED|DENIED)",
                    r"TOTAL DISABILITY.*?UNEMPLOYABLE[:\s]*(YES|NO|GRANTED|DENIED)",
                    r"INDIVIDUAL UNEMPLOYABILITY[:\s]*(YES|NO|GRANTED|DENIED)"
                ],
                "dbq_references": [
                    r"DBQ[:\s]*([A-Za-z\s,]+)",
                    r"DISABILITY BENEFITS QUESTIONNAIRE[:\s]*([A-Za-z\s,]+)",
                    r"C&P EXAM[:\s]*([A-Za-z\s,]+)",
                    r"COMPENSATION.*?EXAMINATION[:\s]*([A-Za-z\s,]+)"
                ],
                "pyramiding": [
                    r"PYRAMIDING[:\s]*(YES|NO|APPLICABLE|NOT APPLICABLE)",
                    r"PYRAMID[:\s]*(YES|NO|APPLICABLE|NOT APPLICABLE)"
                ]
            },
            "DD-214": {
                "name": [
                    r"NAME[:\s]*([A-Za-z\s]+)",
                    r"VETERAN NAME[:\s]*([A-Za-z\s]+)"
                ],
                "ssn": [
                    r"SSN[:\s]*(\d{3}-\d{2}-\d{4})",
                    r"SOCIAL SECURITY[:\s]*(\d{3}-\d{2}-\d{4})"
                ],
                "discharge_date": [
                    r"DATE OF SEPARATION[:\s]*(\d{1,2}/\d{1,2}/\d{4})",
                    r"DISCHARGE DATE[:\s]*(\d{1,2}/\d{1,2}/\d{4})"
                ],
                "service_branch": [
                    r"BRANCH OF SERVICE[:\s]*([A-Za-z\s]+)",
                    r"SERVICE BRANCH[:\s]*([A-Za-z\s]+)"
                ]
            }
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that extracted_text exists in input_data."""
        return "extracted_text" in input_data and input_data["extracted_text"].strip()
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from document text.
        
        Args:
            input_data: Dictionary containing 'extracted_text' and 'document_type'
            
        Returns:
            Dictionary with extracted data
        """
        extracted_text = input_data["extracted_text"]
        document_type = input_data.get("document_type", "unknown")
        
        try:
            # Extract general data (emails, phones, etc.)
            general_data = self._extract_general_data(extracted_text)
            
            # Extract form-specific data
            form_data = self._extract_form_data(extracted_text, document_type)
            
            # Combine all extracted data
            extracted_data = {
                **general_data,
                **form_data,
                "extraction_timestamp": self._get_timestamp(),
                "document_type": document_type
            }
            
            # Add to input_data
            input_data["extracted_data"] = extracted_data
            input_data["data_extraction_status"] = "success"
            
            # Save to local storage
            self._save_extracted_data(extracted_data, input_data.get("original_filename", "unknown"))
            
            self.logger.info(f"Extracted {len(extracted_data)} data fields from {document_type}")
            
            return input_data
            
        except Exception as e:
            self.logger.error(f"Data extraction failed: {str(e)}")
            input_data["extracted_data"] = {}
            input_data["data_extraction_status"] = "failed"
            input_data["data_extraction_error"] = str(e)
            return input_data
    
    def _extract_general_data(self, text: str) -> Dict[str, Any]:
        """Extract general data like emails, phones, names."""
        data = {}
        
        # Extract emails
        emails = self.ocr_helpers.extract_emails(text)
        if emails:
            data["emails"] = emails
            data["primary_email"] = emails[0]
        
        # Extract phone numbers
        phones = self.ocr_helpers.extract_phone_numbers(text)
        if phones:
            data["phone_numbers"] = phones
            data["primary_phone"] = phones[0]
        
        # Extract names using enhanced patterns
        names = self.ocr_helpers.extract_names(text)
        
        # Additional name extraction patterns specific to VA documents by type
        additional_name_patterns = [
            # RDL (Rating Decision Letter) specific patterns
            r'Dear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'This\s+letter\s+is\s+to\s+inform\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'We\s+have\s+(?:granted|denied).*?([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # RCS (Rating Claim Statement) specific patterns
            r'Claimant[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Service\s+Member[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Your\s+claim.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # Medical Evidence specific patterns  
            r'Patient[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Patient\s+Name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Examination\s+of[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # Lay Statement specific patterns
            r'I,\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+),\s+(?:am|was|served)',
            r'My\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Statement\s+(?:of|by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # General patterns
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,?\s*SSN',
            r'File\s+of[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'RE[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)\s*,?\s*DOB'
        ]
        
        for pattern in additional_name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clean_name = match.strip()
                if len(clean_name.split()) >= 2 and clean_name not in names:
                    names.append(clean_name)
        
        if names:
            data["names"] = names
            data["primary_name"] = names[0]
        
        # Extract SSN (general pattern)
        ssn_pattern = r"(\d{3}-\d{2}-\d{4})"
        ssn_matches = re.findall(ssn_pattern, text)
        if ssn_matches:
            data["ssn"] = ssn_matches[0]
        
        # Extract disability info
        disability_info = self.ocr_helpers.extract_disability_info(text)
        data["disability_info"] = disability_info
        
        # Extract VA forms
        va_forms = self.ocr_helpers.extract_va_forms(text)
        if va_forms:
            data["va_forms"] = va_forms
            data["primary_form"] = va_forms[0]
        
        return data
    
    def _extract_form_data(self, text: str, document_type: str) -> Dict[str, Any]:
        """Extract form-specific data based on document type."""
        data = {}
        
        # Determine which form patterns to use
        form_key = self._identify_form(text, document_type)
        
        if form_key and form_key in self.form_patterns:
            patterns = self.form_patterns[form_key]
            
            for field_name, field_patterns in patterns.items():
                for pattern in field_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Clean up the extracted value
                        value = matches[0].strip()
                        if value and len(value) > 1:  # Avoid single characters
                            data[field_name] = value
                            break  # Use first match for this field
        
        return data
    
    def _identify_form(self, text: str, document_type: str) -> str:
        """Identify which VA form this document is."""
        text_upper = text.upper()
        
        if "21-526EZ" in text_upper or "526EZ" in text_upper:
            return "21-526EZ"
        elif "10-10EZ" in text_upper or "10EZ" in text_upper:
            return "10-10EZ"
        elif "DD-214" in text_upper or "DD214" in text_upper:
            return "DD-214"
        elif "RATING DECISION SHEET" in text_upper or ("DIAGNOSTIC CODE" in text_upper and "38 CFR" in text_upper):
            return "RDS"
        
        # Fallback based on document type
        if document_type == "disability_claim":
            return "21-526EZ"
        elif document_type == "discharge_papers":
            return "DD-214"
        elif document_type == "rds":
            return "RDS"
        
        return None
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for data extraction."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _save_extracted_data(self, data: Dict[str, Any], filename: str):
        """Save extracted data to local storage."""
        try:
            # Create data directory if it doesn't exist
            data_dir = "data/extracted_data"
            os.makedirs(data_dir, exist_ok=True)
            
            # Create filename for the data file
            safe_filename = re.sub(r'[^a-zA-Z0-9.-]', '_', filename)
            data_filename = f"{safe_filename}_data.json"
            data_path = os.path.join(data_dir, data_filename)
            
            # Save data as JSON
            with open(data_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved extracted data to {data_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save extracted data: {str(e)}") 