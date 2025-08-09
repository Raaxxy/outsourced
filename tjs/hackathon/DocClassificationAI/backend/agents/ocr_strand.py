import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from typing import Dict, Any
from .base_strand import Strand
import logging

class OCRStrand(Strand):
    """
    OCR Strand: Converts PDF and image files to text using Tesseract.
    """
    
    def __init__(self):
        super().__init__("ocr")
        # Configure Tesseract path for macOS (adjust if needed)
        if os.path.exists("/opt/homebrew/bin/tesseract"):
            pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
        elif os.path.exists("/usr/local/bin/tesseract"):
            pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate that file_path exists in input_data."""
        return "file_path" in input_data and os.path.exists(input_data["file_path"])
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text from PDF or image files.
        
        Args:
            input_data: Dictionary containing 'file_path'
            
        Returns:
            Dictionary with extracted text and metadata
        """
        file_path = input_data["file_path"]
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == ".pdf":
                text = await self._extract_text_from_pdf(file_path)
            elif file_extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                text = await self._extract_text_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Add OCR results to input_data
            input_data["extracted_text"] = text
            input_data["ocr_status"] = "success"
            input_data["text_length"] = len(text)
            
            self.logger.info(f"Extracted {len(text)} characters from {file_path}")
            
            return input_data
            
        except Exception as e:
            self.logger.error(f"OCR failed for {file_path}: {str(e)}")
            input_data["extracted_text"] = ""
            input_data["ocr_status"] = "failed"
            input_data["ocr_error"] = str(e)
            return input_data
    
    async def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdf2image and Tesseract."""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Extract text from each page
            all_text = []
            for i, image in enumerate(images):
                self.logger.info(f"Processing PDF page {i+1}/{len(images)}")
                text = pytesseract.image_to_string(image)
                all_text.append(text)
            
            return "\n".join(all_text)
            
        except Exception as e:
            self.logger.error(f"PDF processing failed: {str(e)}")
            raise
    
    async def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using Tesseract."""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            raise 