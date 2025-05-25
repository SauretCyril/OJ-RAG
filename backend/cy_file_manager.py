"""
Async file operations and caching utilities
"""
import aiofiles
import asyncio
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class AsyncFileManager:
    """Handles asynchronous file operations"""
    
    @staticmethod
    async def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
        """Asynchronously read JSON file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
                return json.loads(content)
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    @staticmethod
    async def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
        """Asynchronously write JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                json_str = json.dumps(data, ensure_ascii=False, indent=4)
                await file.write(json_str)
                return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    @staticmethod
    async def read_text_file(file_path: str) -> Optional[str]:
        """Asynchronously read text file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                return await file.read()
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    @staticmethod
    async def write_text_file(file_path: str, content: str) -> bool:
        """Asynchronously write text file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                await file.write(content)
                return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False

class FileCache:
    """Simple file-based cache with TTL"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache file path from key"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache_file = self._get_cache_key(key)
        
        try:
            data = await AsyncFileManager.read_json_file(cache_file)
            if not data:
                return None
            
            # Check if cache has expired
            expires_at = datetime.fromisoformat(data.get('expires_at'))
            if datetime.now() > expires_at:
                # Cache expired, remove file
                try:
                    os.remove(cache_file)
                except:
                    pass
                return None
            
            return data.get('value')
        except Exception as e:
            logger.debug(f"Cache miss for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        cache_file = self._get_cache_key(key)
        expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        
        cache_data = {
            'value': value,
            'expires_at': expires_at.isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        return await AsyncFileManager.write_json_file(cache_file, cache_data)
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache files"""
        cleared = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    if pattern is None or pattern in filename:
                        os.remove(os.path.join(self.cache_dir, filename))
                        cleared += 1
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
        
        return cleared

# Global cache instance
file_cache = FileCache()

async def cached_file_operation(key: str, operation_func, ttl: int = 3600):
    """Decorator for caching file operation results"""
    # Try to get from cache first
    cached_result = await file_cache.get(key)
    if cached_result is not None:
        logger.debug(f"Cache hit for {key}")
        return cached_result
    
    # Execute operation and cache result
    try:
        result = await operation_func()
        await file_cache.set(key, result, ttl)
        logger.debug(f"Cached result for {key}")
        return result
    except Exception as e:
        logger.error(f"Error in cached operation {key}: {e}")
        raise
