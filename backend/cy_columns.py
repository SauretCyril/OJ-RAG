from flask import Blueprint, request, jsonify, render_template
import os
import json
import logging
from logging import DEBUG

from cy_paths import GetRoot

# Configuration du logging
logging.basicConfig(level=DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Création du Blueprint pour les colonnes
cy_columns = Blueprint('cy_columns', __name__)

@cy_columns.route('/columns_manager')
def columns_manager_page():
    """
    Route pour afficher la page de gestion des colonnes
    """
    return render_template('column_manager.html')

@cy_columns.route('/get_current_dir', methods=['GET'])
def get_current_dir():
    """
    Route pour récupérer le répertoire courant
    """
    try:
        directory = GetRoot()
        # Récupérer le nom du répertoire parent
        parent_dir = os.path.basename(directory)
        parent_path = os.path.dirname(directory)
        grand_parent_dir = os.path.basename(parent_path)
        
        # Construire un chemin plus lisible
        readable_path = f"{grand_parent_dir}/{parent_dir}"
        
        return jsonify({"directory": readable_path, "full_path": directory})
    except Exception as e:
        error_msg = f"Erreur lors de la récupération du répertoire courant: {str(e)}"
        logger.error(error_msg)
        print(f"DEBUG ERROR: {error_msg}")
        return jsonify({"error": error_msg}), 500

@cy_columns.route('/load_conf_cols', methods=['GET'])
def load_conf_cols():
    """
    Route pour charger les colonnes depuis le fichier .cols
    """
    try:
        dir = GetRoot()
        filepath = os.path.join(dir, ".cols")
        filepath = filepath.replace('\\', '/')
        
        print(f"DEBUG: Chargement des colonnes depuis {filepath}")
        
        # Si le fichier existe, le charger
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as file:
                content = json.load(file)
            
            print(f"DEBUG: {len(content)} colonnes chargées avec succès")
            return jsonify(content)
        else:
            # Si le fichier n'existe pas, renvoyer un tableau vide
            # Le script JS utilisera window.columns comme valeur par défaut
            print(f"DEBUG: Fichier .cols non trouvé, renvoi d'un tableau vide")
            return jsonify([])
    except Exception as e:
        error_msg = f"Erreur lors du chargement des colonnes: {str(e)}"
        logger.error(error_msg)
        print(f"DEBUG ERROR: {error_msg}")
        return jsonify({"error": error_msg}), 500

@cy_columns.route('/save_conf_cols', methods=['POST'])
def save_conf_cols():
    """
    Route pour sauvegarder les colonnes dans le fichier .cols
    """
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({"status": "error", "message": "Aucune donnée reçue"}), 400
            
        if not isinstance(data, list):
            return jsonify({"status": "error", "message": "Les données doivent être un tableau de colonnes"}), 400
        
        dir = GetRoot()
        filepath = os.path.join(dir, ".cols")
        filepath = filepath.replace('\\', '/')
        
        print(f"DEBUG: Sauvegarde de {len(data)} colonnes dans {filepath}")
        
        # Créer le répertoire parent si nécessaire
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Écrire les données dans le fichier
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        return jsonify({"status": "success", "message": f"{len(data)} colonnes sauvegardées"}), 200
    except Exception as e:
        error_msg = f"Erreur lors de la sauvegarde des colonnes: {str(e)}"
        logger.error(error_msg)
        print(f"DEBUG ERROR: {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 500