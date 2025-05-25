import os
import json
from flask import request, jsonify
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer les paramètres de configuration depuis .env
AIXPLO_DIR = os.getenv("AIXPLO_DIR", "data/")
AIXPLO_FILE = os.getenv("AIXPLO_FILE", "AixPlo.json")

# Construire le chemin complet vers le fichier
AIXPLO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), AIXPLO_DIR, AIXPLO_FILE)

def ensure_directory_exists(file_path):
    """S'assurer que le répertoire existe pour le fichier spécifié."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_directories():
    """Récupérer la liste des répertoires depuis le fichier JSON."""
    if not os.path.exists(AIXPLO_PATH):
        # Créer un fichier vide avec une liste vide par défaut
        ensure_directory_exists(AIXPLO_PATH)
        with open(AIXPLO_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    
    try:
        with open(AIXPLO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier de répertoires: {e}")
        return []

def save_directories(directories):
    """Sauvegarder la liste des répertoires dans le fichier JSON."""
    try:
        ensure_directory_exists(AIXPLO_PATH)
        with open(AIXPLO_PATH, 'w', encoding='utf-8') as f:
            json.dump(directories, f, indent=2)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier de répertoires: {e}")
        return False

def register_directories_routes(app):
    """Enregistre les routes pour la gestion des répertoires."""
    
    @app.route('/get_directories', methods=['GET'])
    def api_get_directories():
        """Route pour récupérer la liste des répertoires."""
        directories = get_directories()
        return jsonify(directories)
    
    @app.route('/save_directories', methods=['POST'])
    def api_save_directories():
        """Route pour sauvegarder la liste des répertoires."""
        try:
            data = request.json
            if not isinstance(data, list):
                return jsonify({"message": "Format invalide. Une liste de répertoires est attendue."}), 400
            
            success = save_directories(data)
            if success:
                return jsonify({"message": "done"})
            else:
                return jsonify({"message": "Erreur lors de la sauvegarde des répertoires"}), 500
        except Exception as e:
            return jsonify({"message": f"Erreur: {str(e)}"}), 500