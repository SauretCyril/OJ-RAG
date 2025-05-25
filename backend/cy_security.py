"""
Security utilities for file operations and input validation
"""
import os
import re
import subprocess
import platform
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional

class SecurityValidator:
    """Handles secure file operations and input validation"""
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.json', '.txt', '.csv'}
    MAX_PATH_LENGTH = 260  # Windows path limit
    
    @staticmethod
    def sanitize_path(path: str, base_dir: str) -> Optional[str]:
        """
        Sanitize and validate file paths to prevent directory traversal
        """
        try:
            # Normalize the path
            clean_path = os.path.normpath(path)
            base_path = os.path.normpath(base_dir)
            
            # Convert to absolute paths
            abs_clean_path = os.path.abspath(os.path.join(base_path, clean_path))
            abs_base_path = os.path.abspath(base_path)
            
            # Check if the path is within the allowed base directory
            if not abs_clean_path.startswith(abs_base_path + os.sep):
                return None
                
            # Check path length
            if len(abs_clean_path) > SecurityValidator.MAX_PATH_LENGTH:
                return None
                
            return abs_clean_path
            
        except (ValueError, OSError):
            return None
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename for security"""
        if not filename or len(filename) > 255:
            return False
            
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        if re.search(invalid_chars, filename):
            return False
            
        # Check file extension
        ext = Path(filename).suffix.lower()
        return ext in SecurityValidator.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format and scheme"""
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except:
            return False
    
    @staticmethod
    def safe_open_url(url: str) -> bool:
        """Safely open URL in browser"""
        if not SecurityValidator.validate_url(url):
            return False
            
        try:
            if platform.system() == 'Windows':
                subprocess.run(['start', url], shell=True, check=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', url], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', url], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def safe_open_directory(directory_path: str, base_dir: str) -> bool:
        """Safely open directory in file explorer"""
        safe_path = SecurityValidator.sanitize_path(directory_path, base_dir)
        if not safe_path or not os.path.isdir(safe_path):
            return False
            
        try:
            if platform.system() == 'Windows':
                subprocess.run(['explorer', safe_path], check=True)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', safe_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', safe_path], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
