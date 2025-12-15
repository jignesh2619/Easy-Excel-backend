"""
File Management Service

Handles file operations including:
- Saving uploaded files to /temp
- Cleaning old files
- Returning file paths safely
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


class FileManager:
    """Manages file storage and cleanup operations"""
    
    def __init__(self, temp_dir: str = "temp", output_dir: str = "output"):
        """
        Initialize FileManager with directories
        
        Args:
            temp_dir: Directory for temporary uploaded files
            output_dir: Directory for processed output files
        """
        self.base_path = Path(__file__).parent.parent
        self.temp_dir = self.base_path / temp_dir
        self.output_dir = self.base_path / output_dir
        self.charts_dir = self.output_dir / "charts"
        
        # Create directories if they don't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to temp directory
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Full path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Preserve original extension
        file_ext = Path(filename).suffix
        safe_filename = f"{timestamp}_{Path(filename).stem}{file_ext}"
        file_path = self.temp_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path)
    
    async def save_uploaded_file_streaming(self, file, filename: str) -> str:
        """
        Save uploaded file using streaming (more efficient for large files)
        
        Args:
            file: FastAPI UploadFile object
            filename: Original filename
            
        Returns:
            Full path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Preserve original extension
        file_ext = Path(filename).suffix
        safe_filename = f"{timestamp}_{Path(filename).stem}{file_ext}"
        file_path = self.temp_dir / safe_filename
        
        # Stream file directly to disk without loading into memory
        with open(file_path, "wb") as f:
            # Reset file pointer in case it was already read (seek is synchronous)
            file.file.seek(0)
            # Stream chunks of 64KB for efficient memory usage
            while True:
                chunk = await file.read(65536)  # 64KB chunks
                if not chunk:
                    break
                f.write(chunk)
        
        # Reset file pointer for potential reuse
        file.file.seek(0)
        
        # Check if file is empty
        if file_path.stat().st_size == 0:
            file_path.unlink()
            raise ValueError("Uploaded file is empty")
        
        return str(file_path)
    
    def save_processed_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save processed file to output directory
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename for naming
            
        Returns:
            Full path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(original_filename).suffix
        safe_filename = f"processed_{timestamp}_{Path(original_filename).stem}{file_ext}"
        file_path = self.output_dir / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path)
    
    def get_chart_path(self, chart_filename: str) -> str:
        """
        Get full path for chart file
        
        Args:
            chart_filename: Chart filename
            
        Returns:
            Full path to chart file
        """
        return str(self.charts_dir / chart_filename)
    
    def clean_old_files(self, days: int = 7) -> int:
        """
        Remove files older than specified days
        
        Args:
            days: Number of days to keep files
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clean temp directory
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        
        # Clean output directory (excluding charts)
        for file_path in self.output_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        
        # Clean old charts
        for file_path in self.charts_dir.iterdir():
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
        
        return deleted_count
    
    def delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        return Path(file_path).stat().st_size








