from flask import request, Blueprint, jsonify
import logging
import json
import os

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cy_cookies = Blueprint('cy_cookies', __name__)
need_reload = True

# ⚠️ CORRECTION CRITIQUE: Initialiser la variable globale
cookies_data = {}

# Define the path to the JSON file
data_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(data_directory, exist_ok=True)
json_file_path = os.path.join(data_directory, 'cookies.json')

@cy_cookies.route('/save_cookie', methods=['POST'])
def save_cookie():
    global cookies_data
    
    try:
        logger.info("=== DEBUT save_cookie ===")
        
        # Vérifier que la requête contient du JSON
        if not request.is_json:
            logger.error("Erreur: La requête ne contient pas de JSON valide")
            return jsonify({"error": "Request must be JSON"}), 400
            
        # Récupérer les données JSON
        json_data = request.get_json()
        if not json_data:
            logger.error("Erreur: Données JSON vides")
            return jsonify({"error": "Empty JSON data"}), 400
            
        cookie_value = json_data.get('cookie_value')
        cookie_name = json_data.get('cookie_name')
        
        logger.info(f"Données reçues - Nom: '{cookie_name}', Valeur: '{cookie_value}'")
        
        if cookie_value is None or cookie_name is None:
            logger.error("Erreur: cookie_name ou cookie_value manquant")
            return jsonify({"error": "cookie_name and cookie_value are required"}), 400

        # Load existing cookies from the JSON file
        try:
            if os.path.exists(json_file_path):
                logger.info(f"Chargement du fichier existant: {json_file_path}")
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                    if content:
                        cookies_data = json.loads(content)
                        logger.info(f"Cookies chargés: {list(cookies_data.keys())}")
                    else:
                        cookies_data = {}
                        logger.info("Fichier vide, initialisation d'un dictionnaire vide")
            else:
                cookies_data = {}
                logger.info("Fichier n'existe pas, création d'un nouveau dictionnaire")
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erreur lors du chargement du fichier cookies: {e}")
            cookies_data = {}

        # Save the new cookie
        cookies_data[cookie_name] = cookie_value
        logger.info(f"Cookie ajouté: {cookie_name} = {cookie_value}")

        # Write the updated cookies back to the JSON file
        try:
            # Créer le répertoire s'il n'existe pas
            os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
            
            logger.info(f"Écriture dans le fichier: {json_file_path}")
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(cookies_data, file, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Cookie sauvegardé avec succès: {cookie_name} = {cookie_value}")
            
        except IOError as e:
            logger.error(f"❌ Erreur lors de l'écriture du fichier cookies: {e}")
            return jsonify({"error": f"Could not save cookie to file: {str(e)}"}), 500
   
        logger.info("=== FIN save_cookie - SUCCESS ===")
        return jsonify({"message": "done"})
        
    except Exception as e:
        logger.error(f"❌ Erreur 500 inattendue dans save_cookie: {str(e)}")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@cy_cookies.route('/load_cookies', methods=['GET'])
def load_cookies():
    global cookies_data
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                content = file.read().strip()
                if not content:
                    # Fichier vide, initialiser avec un objet JSON vide
                    cookies_data = {}
                    logger.info("Fichier cookies vide, initialisation avec un objet vide.")
                else:
                    cookies_data = json.loads(content)
                    logger.info("Cookies chargés avec succès depuis le fichier JSON.")
            return jsonify({"message": "Cookies loaded successfully", "cookies_data": cookies_data})
        else:
            # Fichier n'existe pas, créer un fichier vide avec un objet JSON
            cookies_data = {}
            with open(json_file_path, 'w') as file:
                json.dump(cookies_data, file, indent=2)
            logger.info("Fichier cookies créé avec un objet vide.")
            return jsonify({"message": "Cookies file created and initialized", "cookies_data": cookies_data})
    except json.JSONDecodeError as e:
        # Erreur de décodage JSON, réinitialiser le fichier
        logger.error(f"Erreur de décodage JSON dans le fichier cookies: {e}")
        cookies_data = {}
        try:
            with open(json_file_path, 'w') as file:
                json.dump(cookies_data, file, indent=2)
            logger.info("Fichier cookies réinitialisé après erreur de décodage.")
        except Exception as write_error:
            logger.error(f"Erreur lors de la réécriture du fichier cookies: {write_error}")
            return jsonify({"error": "Could not reset corrupted cookies file"}), 500
        return jsonify({"message": "Cookies file was corrupted and has been reset", "cookies_data": cookies_data})
    except Exception as e:
        logger.error(f"Erreur lors du chargement des cookies: {e}")
        return jsonify({"error": "Failed to load cookies"}), 500

@cy_cookies.route('/get_cookie', methods=['POST'])
def get_cookie():
    global cookies_data
    
    try:
        logger.info("=== DEBUT get_cookie ===")
        
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        json_data = request.get_json()
        cookie_name = json_data.get('cookie_name')
        
        if not cookie_name:
            return jsonify({"error": "cookie_name is required"}), 400
            
        # Load cookies from file
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    cookies_data = json.loads(content)
                else:
                    cookies_data = {}
        else:
            cookies_data = {}
            
        logger.info(f"Cookie demandé: {cookie_name}")
        cookie_value = cookies_data.get(cookie_name)
        
        result = {cookie_name: cookie_value}
        logger.info(f"Cookie retourné: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Erreur dans get_cookie: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Route de test pour diagnostiquer
@cy_cookies.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Server is running"})

