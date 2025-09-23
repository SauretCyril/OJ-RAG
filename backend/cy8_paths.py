"""
Module de gestion des chemins - Version cy8
Utilitaires pour la gestion cross-platform des chemins de fichiers
"""

import os
import tempfile
from pathlib import Path

class cy8_paths_manager:
    """Gestionnaire des chemins de fichiers cross-platform"""
    
    @staticmethod
    def get_default_db_path():
        """Obtenir le chemin par défaut de la base de données"""
        # Utiliser un répertoire temporaire système ou un dossier dans le profil utilisateur
        if os.name == 'nt':  # Windows
            # Préférer un dossier dans TEMP ou créer dans le profil utilisateur
            base_dir = os.environ.get('TEMP') or tempfile.gettempdir()
        else:  # Unix/Linux/Mac
            base_dir = tempfile.gettempdir()
        
        return os.path.join(base_dir, "prompts_manager.db")
    
    @staticmethod
    def get_data_directory():
        """Obtenir le répertoire de données par défaut"""
        if os.name == 'nt':  # Windows
            base_dir = os.environ.get('TEMP') or tempfile.gettempdir()
        else:  # Unix/Linux/Mac
            base_dir = tempfile.gettempdir()
        
        data_dir = os.path.join(base_dir, "cy8_data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    @staticmethod
    def normalize_path(path):
        """Normaliser un chemin pour la plateforme actuelle"""
        if not path:
            return path
        
        # Convertir les séparateurs et normaliser
        normalized = os.path.normpath(path)
        # Résoudre le chemin absolu
        return os.path.abspath(normalized)
    
    @staticmethod
    def ensure_directory_exists(file_path):
        """S'assurer que le répertoire parent d'un fichier existe"""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return file_path
    
    @staticmethod
    def join_path(*parts):
        """Joindre des parties de chemin de manière cross-platform"""
        return os.path.join(*parts)
    
    @staticmethod
    def is_absolute_path(path):
        """Vérifier si un chemin est absolu"""
        return os.path.isabs(path)
    
    @staticmethod
    def get_relative_path(path, start=None):
        """Obtenir un chemin relatif"""
        try:
            return os.path.relpath(path, start)
        except ValueError:
            # Retourner le chemin original si la conversion échoue
            return path
    
    @staticmethod
    def path_exists(path):
        """Vérifier si un chemin existe"""
        return os.path.exists(path) if path else False
    
    @staticmethod
    def compare_paths(path1, path2):
        """Comparer deux chemins de manière normalisée"""
        if not path1 or not path2:
            return path1 == path2
        
        norm1 = cy8_paths_manager.normalize_path(path1)
        norm2 = cy8_paths_manager.normalize_path(path2)
        
        # Comparaison insensible à la casse sur Windows
        if os.name == 'nt':
            return norm1.lower() == norm2.lower()
        else:
            return norm1 == norm2
    
    @staticmethod
    def get_directory_from_path(file_path):
        """Obtenir le répertoire parent d'un fichier"""
        return os.path.dirname(file_path) if file_path else ""
    
    @staticmethod
    def get_filename_from_path(file_path):
        """Obtenir le nom de fichier depuis un chemin"""
        return os.path.basename(file_path) if file_path else ""
    
    @staticmethod
    def change_file_extension(file_path, new_extension):
        """Changer l'extension d'un fichier"""
        if not file_path:
            return file_path
        
        root, _ = os.path.splitext(file_path)
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension
        
        return root + new_extension
    
    @staticmethod
    def get_file_extension(file_path):
        """Obtenir l'extension d'un fichier"""
        if not file_path:
            return ""
        
        _, ext = os.path.splitext(file_path)
        return ext
    
    @staticmethod
    def sanitize_filename(filename):
        """Nettoyer un nom de fichier pour le rendre valide"""
        if not filename:
            return filename
        
        # Caractères interdits sur Windows
        invalid_chars = '<>:"/\\|?*'
        
        # Remplacer les caractères interdits
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Supprimer les espaces en début/fin
        sanitized = sanitized.strip()
        
        # Éviter les noms réservés sur Windows
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + \
                        [f'COM{i}' for i in range(1, 10)] + \
                        [f'LPT{i}' for i in range(1, 10)]
        
        # Vérifier le nom sans extension
        name_without_ext, ext = os.path.splitext(sanitized)
        if name_without_ext.upper() in reserved_names:
            sanitized = name_without_ext + '_file' + ext
        
        return sanitized

# Fonctions de commodité globales
def get_default_db_path():
    """Raccourci pour obtenir le chemin par défaut de la DB"""
    return cy8_paths_manager.get_default_db_path()

def normalize_path(path):
    """Raccourci pour normaliser un chemin"""
    return cy8_paths_manager.normalize_path(path)

def ensure_dir(file_path):
    """Raccourci pour s'assurer qu'un répertoire existe"""
    return cy8_paths_manager.ensure_directory_exists(file_path)