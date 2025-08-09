import re
from typing import Dict, Any, List, Optional

class OCRHelpers:
    """
    Utility class for OCR and text processing operations.
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text.strip()
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text.
        
        Args:
            text: Text to search for emails
            
        Returns:
            List of found email addresses
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """
        Extract phone numbers from text.
        
        Args:
            text: Text to search for phone numbers
            
        Returns:
            List of found phone numbers
        """
        # Various phone number patterns
        patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 123-456-7890
            r'\b\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
            r'\b\d{10}\b',  # 1234567890
        ]
        
        phone_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phone_numbers.extend(matches)
        
        return list(set(phone_numbers))  # Remove duplicates
    
    @staticmethod
    def extract_names(text: str) -> List[str]:
        """
        Extract potential veteran names from text using multiple patterns.
        
        Args:
            text: Text to search for names
            
        Returns:
            List of potential names
        """
        names = []
        
        # VA-specific name patterns (enhanced for folder structure)
        va_patterns = [
            # RDL (Rating Decision Letter) patterns
            r'VETERAN[\'S]*\s+(?:FULL\s+)*NAME[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Dear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Veteran:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # RCS (Rating Claim Statement) patterns
            r'Claimant[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'File\s+(?:of|for)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'VA\s+File\s+Number.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # Medical Evidence patterns
            r'Patient[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Patient\s+Name[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Medical\s+Record\s+for[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # General VA Forms patterns
            r'VETERAN[\'S]*\s+(?:FULL\s+)*NAME[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'FULL\s+NAME[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Service\s+Member[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # Enhanced LAST, FIRST format patterns  
            r"VETERAN['\s]*(?:FULL\s+)?NAME[:\s]*([A-Z]+),\s*([A-Z][a-z]+(?:\s+[A-Z]?[a-z]*)*)",  # VETERAN'S FULL NAME: LAST, FIRST
            r'([A-Z][A-Z\s]+),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',  # LAST, FIRST format
            r'NAME[:\s]*([A-Z][A-Z\s]+),\s*([A-Z][a-z]+)',  # NAME: LAST, FIRST
            
            # Lay Statement patterns
            r'I,\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+),',
            r'My\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'Statement\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            
            # Additional VA patterns
            r'([A-Z][A-Z]+),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)',  # LAST, FIRST format
            r'RE[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)\s*,?\s*SSN',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)\s*,?\s*DOB'
        ]
        
        # Title patterns
        title_patterns = [
            r'\b(Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+),\s*(Jr\.|Sr\.|III|IV)\b'
        ]
        
        # Extract VA-specific names
        for pattern in va_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle LAST, FIRST format
                    if len(match) == 2:
                        if match[0].isupper():  # LAST, FIRST format like "DAVIS, SARAH"
                            name = f"{match[1]} {match[0].title()}"
                        else:
                            name = ' '.join(match)
                    else:
                        name = ' '.join(match)
                else:
                    name = match
                
                # Clean and validate name
                name = name.strip()
                if len(name.split()) >= 2 and len(name) > 3:
                    names.append(name)
        
        # Extract names with titles
        for pattern in title_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    if match[2] in ['Jr.', 'Sr.', 'III', 'IV']:
                        name = f"{match[0]} {match[1]} {match[2]}"
                    else:
                        name = f"{match[0]} {match[1]} {match[2]}"
                else:
                    name = f"{match[0]} {match[1]} {match[2]}" if len(match) > 2 else f"{match[0]} {match[1]}"
                names.append(name)
        
        # Remove duplicates and clean names
        cleaned_names = []
        for name in names:
            # Remove extra spaces and common non-name words
            clean_name = ' '.join(name.split())
            # Remove common suffixes that got captured 
            clean_name = re.sub(r'\s+(Medical|Record|Number|SSN|DOB|File|Patient).*$', '', clean_name, flags=re.IGNORECASE)
            if (clean_name not in cleaned_names and len(clean_name.split()) >= 2 and
                not any(word.lower() in clean_name.lower() for word in ['veteran', 'name', 'dear', 'patient', 'record', 'medical'])):
                cleaned_names.append(clean_name)
        
        return cleaned_names
    
    @staticmethod
    def extract_disability_info(text: str) -> Dict[str, Any]:
        """
        Extract disability-related information from text.
        
        Args:
            text: Text to search for disability information
            
        Returns:
            Dictionary with disability information
        """
        text_lower = text.lower()
        
        disability_info = {
            "has_disability_mention": False,
            "disability_types": [],
            "service_connected": False,
            "disability_percentage": None
        }
        
        # Check for disability mentions
        disability_keywords = [
            "disability", "disabled", "impairment", "condition",
            "service connected", "service-connected", "veteran"
        ]
        
        for keyword in disability_keywords:
            if keyword in text_lower:
                disability_info["has_disability_mention"] = True
                break
        
        # Check for service connection
        service_connected_patterns = [
            r'service\s*connected',
            r'service-connected',
            r'sc\s*disability'
        ]
        
        for pattern in service_connected_patterns:
            if re.search(pattern, text_lower):
                disability_info["service_connected"] = True
                break
        
        # Extract disability percentage
        percentage_pattern = r'(\d{1,3})\s*%\s*disability'
        percentage_match = re.search(percentage_pattern, text_lower)
        if percentage_match:
            disability_info["disability_percentage"] = int(percentage_match.group(1))
        
        return disability_info
    
    @staticmethod
    def extract_va_forms(text: str) -> List[str]:
        """
        Extract VA form numbers from text.
        
        Args:
            text: Text to search for VA forms
            
        Returns:
            List of found VA form numbers
        """
        # VA form patterns
        form_patterns = [
            r'\bVA\s*Form\s*(\d{2,4}[A-Z]?)\b',
            r'\bForm\s*(\d{2,4}[A-Z]?)\b',
            r'\b(\d{2,4}[A-Z]?)\s*form\b'
        ]
        
        forms = []
        for pattern in form_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            forms.extend(matches)
        
        return list(set(forms))  # Remove duplicates
    
    @staticmethod
    def get_text_statistics(text: str) -> Dict[str, Any]:
        """
        Get statistics about the extracted text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with text statistics
        """
        if not text:
            return {
                "word_count": 0,
                "character_count": 0,
                "line_count": 0,
                "average_word_length": 0
            }
        
        words = text.split()
        lines = text.split('\n')
        
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        return {
            "word_count": len(words),
            "character_count": len(text),
            "line_count": len(lines),
            "average_word_length": round(avg_word_length, 2)
        } 