import os
import aiofiles
from typing import List
from fastapi import UploadFile
import uuid
from datetime import datetime

class FileOperations:
    """
    Utility class for file operations.
    """
    
    def __init__(self, upload_dir: str = "backend/data/uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """
        Save an uploaded file to disk.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Path to saved file
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        
        filename = f"{timestamp}_{unique_id}{file_extension}"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    async def save_multiple_files(self, files: List[UploadFile]) -> List[str]:
        """
        Save multiple uploaded files to disk.
        
        Args:
            files: List of FastAPI UploadFile objects
            
        Returns:
            List of paths to saved files
        """
        saved_paths = []
        
        for file in files:
            file_path = await self.save_uploaded_file(file)
            saved_paths.append(file_path)
        
        return saved_paths
    
    def validate_file_type(self, filename: str) -> bool:
        """
        Validate if file type is supported.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file type is supported, False otherwise
        """
        supported_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        file_extension = os.path.splitext(filename.lower())[1]
        
        return file_extension in supported_extensions
    
    def get_file_size_mb(self, file_path: str) -> float:
        """
        Get file size in megabytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in MB
        """
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        return 0.0
    
    def cleanup_temp_file(self, file_path: str):
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {str(e)}") 