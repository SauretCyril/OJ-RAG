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
        Sanitize and validate file paths to prevent directory traversal.
        Uses os.path.realpath to resolve symlinks.
        """
        try:
            base = os.path.realpath(base_dir)
            target = os.path.realpath(os.path.join(base, path))

            if target != base and not target.startswith(base + os.sep):
                return None

            if len(target) > SecurityValidator.MAX_PATH_LENGTH:
                return None

            return target

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


# ---------------------------------------------------------------------------
# Fonctions standalone — importables directement dans les routes
# ---------------------------------------------------------------------------

def safe_path(user_input: str, base_dir: str) -> str:
    """
    Résout un chemin relatif dans base_dir et vérifie qu'il ne sort pas.
    Utilise os.path.realpath pour résoudre les symlinks.
    Lève ValueError si tentative de path traversal.
    Retourne le chemin absolu résolu.
    """
    if not base_dir:
        raise ValueError("Répertoire de base non configuré")
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, user_input))
    if target != base and not target.startswith(base + os.sep):
        raise ValueError(f"Chemin non autorisé : {user_input!r}")
    return target


def safe_absolute_path(absolute_path: str, base_dir: str) -> str:
    """
    Vérifie qu'un chemin absolu fourni par le client reste dans base_dir.
    Utilise os.path.realpath pour résoudre les symlinks.
    Lève ValueError si tentative de path traversal.
    Retourne le chemin absolu résolu.
    """
    if not base_dir:
        raise ValueError("Répertoire de base non configuré")
    base = os.path.realpath(base_dir)
    target = os.path.realpath(absolute_path)
    if target != base and not target.startswith(base + os.sep):
        raise ValueError(f"Chemin non autorisé : {absolute_path!r}")
    return target
