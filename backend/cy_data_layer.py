"""
Data access layer for JSON-based storage
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from cy_file_manager import AsyncFileManager, file_cache
from cy_error_handler import APIError
import logging

logger = logging.getLogger(__name__)

class JSONDataStore:
    """JSON-based data storage with caching and validation"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def _get_file_path(self, collection: str, document_id: str = None) -> str:
        """Get file path for collection or document"""
        if document_id:
            return os.path.join(self.base_dir, collection, f"{document_id}.json")
        return os.path.join(self.base_dir, f"{collection}.json")
    
    async def find_one(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        file_path = self._get_file_path(collection, document_id)
        cache_key = f"doc_{collection}_{document_id}"
        
        async def load_document():
            return await AsyncFileManager.read_json_file(file_path)
        
        try:
            from cy_file_manager import cached_file_operation
            return await cached_file_operation(cache_key, load_document, ttl=300)
        except Exception as e:
            logger.error(f"Error loading document {collection}/{document_id}: {e}")
            return None
    
    async def find_many(self, collection: str, filter_func=None) -> List[Dict[str, Any]]:
        """Find multiple documents in a collection"""
        collection_dir = os.path.join(self.base_dir, collection)
        if not os.path.exists(collection_dir):
            return []
        
        results = []
        try:
            for filename in os.listdir(collection_dir):
                if filename.endswith('.json'):
                    document_id = filename[:-5]  # Remove .json extension
                    document = await self.find_one(collection, document_id)
                    if document and (filter_func is None or filter_func(document)):
                        document['_id'] = document_id
                        results.append(document)
        except Exception as e:
            logger.error(f"Error finding documents in {collection}: {e}")
        
        return results
    
    async def save_one(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """Save a single document"""
        file_path = self._get_file_path(collection, document_id)
        
        # Add metadata
        data_with_meta = {
            **data,
            '_updated_at': datetime.now().isoformat(),
            '_created_at': data.get('_created_at', datetime.now().isoformat())
        }
        
        try:
            # Ensure collection directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            success = await AsyncFileManager.write_json_file(file_path, data_with_meta)
            if success:
                # Invalidate cache
                cache_key = f"doc_{collection}_{document_id}"
                await file_cache.set(cache_key, data_with_meta, ttl=300)
            
            return success
        except Exception as e:
            logger.error(f"Error saving document {collection}/{document_id}: {e}")
            return False
    
    async def delete_one(self, collection: str, document_id: str) -> bool:
        """Delete a single document"""
        file_path = self._get_file_path(collection, document_id)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Invalidate cache
                cache_key = f"doc_{collection}_{document_id}"
                file_cache.clear(cache_key)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document {collection}/{document_id}: {e}")
            return False
    
    async def get_collection_list(self, collection: str) -> List[str]:
        """Get list of document IDs in a collection"""
        collection_dir = os.path.join(self.base_dir, collection)
        if not os.path.exists(collection_dir):
            return []
        
        try:
            return [f[:-5] for f in os.listdir(collection_dir) if f.endswith('.json')]
        except Exception as e:
            logger.error(f"Error listing collection {collection}: {e}")
            return []

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_dir: str):
        self.data_store = JSONDataStore(config_dir)
        self.config_cache = {}
    
    async def get_config(self, config_name: str, default_value: Any = None) -> Any:
        """Get configuration value"""
        try:
            config_data = await self.data_store.find_one('configs', config_name)
            return config_data.get('value', default_value) if config_data else default_value
        except Exception as e:
            logger.error(f"Error getting config {config_name}: {e}")
            return default_value
    
    async def set_config(self, config_name: str, value: Any) -> bool:
        """Set configuration value"""
        config_data = {
            'value': value,
            'name': config_name
        }
        return await self.data_store.save_one('configs', config_name, config_data)
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        prefs = await self.data_store.find_one('user_preferences', user_id)
        return prefs or {}
    
    async def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save user preferences"""
        return await self.data_store.save_one('user_preferences', user_id, preferences)

class AnnonceManager:
    """Manages job announcements data"""
    
    def __init__(self, data_dir: str):
        self.data_store = JSONDataStore(data_dir)
    
    async def get_annonce(self, dossier_id: str) -> Optional[Dict[str, Any]]:
        """Get a single announcement"""
        return await self.data_store.find_one('annonces', dossier_id)
    
    async def save_annonce(self, dossier_id: str, annonce_data: Dict[str, Any]) -> bool:
        """Save announcement data"""
        return await self.data_store.save_one('annonces', dossier_id, annonce_data)
    
    async def get_annonces_list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get filtered list of announcements"""
        def filter_func(annonce):
            if not filters:
                return True
            
            # Apply filters
            for key, value in filters.items():
                if key in annonce and annonce[key] != value:
                    return False
            return True
        
        return await self.data_store.find_many('annonces', filter_func)
    
    async def update_annonce_status(self, dossier_id: str, new_status: str) -> bool:
        """Update announcement status"""
        annonce = await self.get_annonce(dossier_id)
        if not annonce:
            return False
        
        annonce['etat'] = new_status
        return await self.save_annonce(dossier_id, annonce)
    
    async def delete_annonce(self, dossier_id: str) -> bool:
        """Delete announcement"""
        return await self.data_store.delete_one('annonces', dossier_id)
