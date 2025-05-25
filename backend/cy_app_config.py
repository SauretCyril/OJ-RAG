"""
Application configuration and initialization
"""
import os
import logging
from pathlib import Path
from cy_data_layer import ConfigManager, AnnonceManager
from cy_file_manager import FileCache
from cy_security import SecurityValidator

class AppConfig:
    """Application configuration manager"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.config_dir = self.base_dir / "backend" / "config"
        self.cache_dir = self.base_dir / "cache"
        self.uploads_dir = self.base_dir / "uploads"
        
        # Ensure directories exist
        for dir_path in [self.data_dir, self.cache_dir, self.uploads_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Initialize managers
        self.config_manager = ConfigManager(str(self.config_dir))
        self.annonce_manager = AnnonceManager(str(self.data_dir))
        self.file_cache = FileCache(str(self.cache_dir))
        
        # Load constants
        self.constants = self._load_constants()
        
        # Security settings
        self.max_file_size = 16 * 1024 * 1024  # 16MB
        self.allowed_extensions = {'.pdf', '.docx', '.json', '.txt', '.csv'}
        
    def _load_constants(self):
        """Load constants from configuration file"""
        constants_file = self.config_dir / "constants.json"
        try:
            import json
            with open(constants_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading constants: {e}")
            return {}
    
    def get_excluded_directories(self):
        """Get list of excluded directories"""
        return ["suivi", "pile", "conf", "__pycache__", ".git", "node_modules"]
    
    def get_upload_path(self, filename: str) -> str:
        """Get safe upload path for file"""
        if not SecurityValidator.validate_filename(filename):
            raise ValueError("Invalid filename")
        
        return str(self.uploads_dir / filename)
    
    def setup_logging(self, log_level=logging.INFO):
        """Setup application logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(str(self.base_dir / 'app.log')),
                logging.StreamHandler()
            ]
        )

# Global configuration instance
app_config = AppConfig()
