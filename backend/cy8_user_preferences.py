"""
Module de gestion des préférences utilisateur - Version cy8
Gestion des cookies et paramètres utilisateur stockés localement
"""

import os
import json
import tempfile
from pathlib import Path

class cy8_user_preferences:
    """Gestionnaire des préférences utilisateur"""
    
    def __init__(self, app_name="cy8_prompts_manager"):
        self.app_name = app_name
        self.preferences_dir = self._get_preferences_directory()
        self.preferences_file = os.path.join(self.preferences_dir, "user_preferences.json")
        self.cookies_file = os.path.join(self.preferences_dir, "cookies.json")
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(self.preferences_dir, exist_ok=True)
        
        # Charger les préférences existantes
        self.preferences = self._load_preferences()
        self.cookies = self._load_cookies()
    
    def _get_preferences_directory(self):
        """Obtenir le répertoire des préférences utilisateur selon l'OS"""
        if os.name == 'nt':  # Windows
            # Utiliser APPDATA ou USERPROFILE
            base_dir = os.environ.get('APPDATA') or os.environ.get('USERPROFILE')
            if base_dir:
                return os.path.join(base_dir, self.app_name)
        
        # Unix/Linux/Mac
        home_dir = os.path.expanduser('~')
        if home_dir:
            return os.path.join(home_dir, f'.{self.app_name}')
        
        # Fallback vers temp
        return os.path.join(tempfile.gettempdir(), self.app_name)
    
    def _load_preferences(self):
        """Charger les préférences depuis le fichier"""
        try:
            if os.path.exists(self.preferences_file):
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des préférences: {e}")
        
        # Préférences par défaut
        return {
            "version": "1.0",
            "created_at": "",
            "last_updated": ""
        }
    
    def _load_cookies(self):
        """Charger les cookies depuis le fichier"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des cookies: {e}")
        
        # Cookies par défaut
        return {
            "last_database_path": "",
            "window_geometry": "",
            "recent_databases": []
        }
    
    def _save_preferences(self):
        """Sauvegarder les préférences"""
        try:
            import datetime
            self.preferences["last_updated"] = datetime.datetime.now().isoformat()
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des préférences: {e}")
    
    def _save_cookies(self):
        """Sauvegarder les cookies"""
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des cookies: {e}")
    
    def get_last_database_path(self):
        """Obtenir le chemin de la dernière base de données utilisée"""
        return self.cookies.get("last_database_path", "")
    
    def set_last_database_path(self, db_path):
        """Définir le chemin de la dernière base de données utilisée"""
        if db_path and os.path.exists(db_path):
            # Normaliser le chemin pour cohérence cross-platform
            normalized_path = os.path.normpath(os.path.abspath(db_path))
            self.cookies["last_database_path"] = normalized_path
            self._update_recent_databases(normalized_path)
            self._save_cookies()
    
    def _update_recent_databases(self, db_path):
        """Mettre à jour la liste des bases récentes"""
        # Normaliser le chemin
        normalized_path = os.path.normpath(os.path.abspath(db_path))
        recent = self.cookies.get("recent_databases", [])
        
        # Retirer le chemin s'il existe déjà (comparaison normalisée)
        recent_normalized = [os.path.normpath(p) for p in recent]
        if normalized_path in recent_normalized:
            # Trouver et supprimer l'ancien chemin
            for i, p in enumerate(recent):
                if os.path.normpath(p) == normalized_path:
                    recent.pop(i)
                    break
        
        # Ajouter en tête
        recent.insert(0, normalized_path)
        
        # Limiter à 10 entrées
        self.cookies["recent_databases"] = recent[:10]
    
    def get_recent_databases(self):
        """Obtenir la liste des bases de données récentes"""
        recent = self.cookies.get("recent_databases", [])
        # Filtrer les chemins qui n'existent plus
        existing = [path for path in recent if os.path.exists(path)]
        
        # Mettre à jour si des chemins ont été supprimés
        if len(existing) != len(recent):
            self.cookies["recent_databases"] = existing
            self._save_cookies()
        
        return existing
    
    def get_window_geometry(self):
        """Obtenir la géométrie de la fenêtre"""
        return self.cookies.get("window_geometry", "")
    
    def set_window_geometry(self, geometry):
        """Définir la géométrie de la fenêtre"""
        self.cookies["window_geometry"] = geometry
        self._save_cookies()
    
    def get_preference(self, key, default_value=None):
        """Obtenir une préférence"""
        return self.preferences.get(key, default_value)
    
    def set_preference(self, key, value):
        """Définir une préférence"""
        self.preferences[key] = value
        self._save_preferences()
    
    def get_cookie(self, key, default_value=None):
        """Obtenir un cookie"""
        return self.cookies.get(key, default_value)
    
    def set_cookie(self, key, value):
        """Définir un cookie"""
        self.cookies[key] = value
        self._save_cookies()
    
    def clear_recent_databases(self):
        """Effacer la liste des bases récentes"""
        self.cookies["recent_databases"] = []
        self._save_cookies()
    
    def remove_recent_database(self, db_path):
        """Retirer une base de la liste des récentes"""
        normalized_path = os.path.normpath(os.path.abspath(db_path))
        recent = self.cookies.get("recent_databases", [])
        
        # Chercher et supprimer avec comparaison normalisée
        for i, p in enumerate(recent[:]):  # Copie pour modification pendant itération
            if os.path.normpath(p) == normalized_path:
                recent.remove(p)
        
        self.cookies["recent_databases"] = recent
        self._save_cookies()
    
    def get_preferences_info(self):
        """Obtenir des informations sur les préférences"""
        return {
            "preferences_dir": self.preferences_dir,
            "preferences_file": self.preferences_file,
            "cookies_file": self.cookies_file,
            "preferences_exists": os.path.exists(self.preferences_file),
            "cookies_exists": os.path.exists(self.cookies_file),
            "recent_databases_count": len(self.get_recent_databases())
        }