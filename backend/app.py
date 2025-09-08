from flask import Flask, render_template, request, jsonify
import os
import json
import numpy as np
from werkzeug.serving import run_simple
import sys
import psutil
import subprocess
import requests  # Ajoutez cette ligne avec les autres imports
# Définir le chemin de PYTHONPATH pour inclure le dossier actuel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import de la configuration centralisée
from cy_app_config import app_config

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Configuration de l'application avec app_config
app.config['MAX_CONTENT_LENGTH'] = app_config.max_file_size
app.config['UPLOAD_FOLDER'] = str(app_config.uploads_dir)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32):
            return float(obj)
        return super(NumpyEncoder, self).default(obj)

app.json_encoder = NumpyEncoder  # Ajouter cette ligne après la création de l'app

from cy_paths import paths
app.register_blueprint(paths)  # Register the blueprint

from cy_routes import cy_routes 
app.register_blueprint(cy_routes)  # Register the blueprint

from cy_cookies import cy_cookies
app.register_blueprint(cy_cookies)  # Register the blueprint

from cy_requests import cy_requests
app.register_blueprint(cy_requests)  # Register the blueprint

from cy_columns import cy_columns
app.register_blueprint(cy_columns)  # Register the new columns blueprint

from cy_fbx_exploreur import cy_fbx
app.register_blueprint(cy_fbx)  
# Register the new FBX explorer blueprint
# Ajout du module de gestion des répertoires
from cy_directories import register_directories_routes
register_directories_routes(app)  # Enregistrer les routes de gestion des répertoires

from cy_file_picker import file_picker
app.register_blueprint(file_picker)  # Register the file picker blueprint

# from cy_analyse_prompt import cy_analyse_prompt
# app.register_blueprint(cy_analyse_prompt)  # Register the blueprint

# Ajoutez ce code dans votre app.py après avoir enregistré le Blueprint
""" print("Routes disponibles:")
for rule in app.url_map.iter_rules():
    print(f"{rule} - {rule.endpoint}") """

# Utilisation de app_config au lieu de BASE_DIR
BASE_DIR = str(app_config.base_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/columns_manager")
def columns_manager():
    return render_template("columns_manager.html")



# Route Flask pour ouvrir l'explorateur
@app.route('/get_local_FileExplorer', methods=['POST'])
def get_local_FileExplorer():
    data = request.get_json()
    dir_path = data.get('path')
    explorer_type = data.get('explorer_type', 'standard')
    
    if not dir_path or not os.path.exists(dir_path):
        return {"status": "error", "message": "Le répertoire spécifié est invalide ou n'existe pas."}, 400

    try:
        from cy_venv_utils import run_python_script
        
        print(f"dbg-explorer-03- Répertoire cible : {dir_path}")
        print(f"dbg-explorer-04- Type explorateur : {explorer_type}")
        
        # Lancer l'explorateur avec les utilitaires venv
        run_python_script('cy_file_explorer', [dir_path, explorer_type])
        print(f"dbg-explorer-07- Lancement de l'explorateur pour : {dir_path}")
        
        return jsonify({"status": "success", "message": f"Explorateur ouvert : {dir_path}"}), 200
        
    except Exception as e:
        print(f"dbg-explorer-08- Exception : {e}")
        return jsonify({"status": "error", "message": f"Erreur lors du lancement de l'explorateur : {e}"}), 500

@app.route('/get_local_PromptTable', methods=['POST'])
def prompt_table_open():
    print("dbg-667a : Received request to open prompt table")
    data = request.json
    
    try:
        # Note: La table de prompts nécessite un script dédié qui n'existe pas encore
        # Pour l'instant, on utilise directement la classe
        from cy_venv_utils import run_python_script
        
        # Préparer les arguments
        file_path = data.get('file_path', 'prompts.json')
        is_depend_on = str(data.get('isDependOn', False))
        num_dossier = data.get('num_dossier', '')
        nom_fichier = data.get('nom_fichier', '')
        descriptif = data.get('descriptif', '')
        
        print(f"dbg-prompt-03- Paramètres : {file_path}, {is_depend_on}, {num_dossier}")
        
        # Pour l'instant, créer directement l'instance (même processus)
        # TODO: Créer cy_prompt_table.py pour exécution séparée
        try:
            import threading
            from cls_local_analyse_prompt import cls_local_PromptTable
            
            def launch_prompt_table():
                app_prompt = cls_local_PromptTable(
                    file_path=file_path,
                    isDependOn=(is_depend_on.lower() == 'true'),
                    num_dossier=num_dossier,
                    nom_fichier=nom_fichier,
                    descriptif=descriptif
                )
                app_prompt.mainloop()
            
            threading.Thread(target=launch_prompt_table, daemon=True).start()
            print(f"dbg-prompt-04- Lancement de la table de prompts")
            
            return jsonify({"status": "success", "message": "Table de prompts ouverte"}), 200
            
        except ImportError:
            return jsonify({"status": "error", "message": "Module de table de prompts non disponible"}), 500
        
    except Exception as e:
        print(f"dbg-prompt-05- Exception : {e}")
        return jsonify({"status": "error", "message": f"Erreur lors du lancement de la table de prompts : {e}"}), 500


@app.route('/run_annonces_gui', methods=['POST'])
def run_annonces_gui():
    try:
        from cy_venv_utils import run_python_script
        run_python_script('cy3_annonces_gui')
        return jsonify({"message": "Lancement demandé."})
    except Exception as e:
        return jsonify({"message": f"Erreur: {e}"}), 500

@app.route('/run_analyse_prompt', methods=['POST'])
def run_analyse_prompt():
    try:
        from cy_venv_utils import run_python_script
        run_python_script('cy2_analyse_prompt')
        return jsonify({"message": "Lancement demandé."})
    except Exception as e:
        return jsonify({"message": f"Erreur: {e}"}), 500

@app.route('/run_images_production', methods=['POST'])
def run_images_production():
    try:
        from cy_venv_utils import run_python_script
        run_python_script('cy2_app_images', ['H:/Entreprendre/Actions-15-Images/I003/data/_fonctions_.db'])
        return jsonify({"message": "Lancement demandé."})
    except Exception as e:
        return jsonify({"message": f"Erreur: {e}"}), 500

@app.route('/run_general_analyse', methods=['POST'])
def run_general_analyse():
    try:
        data = request.get_json()
        numdos = data.get('numdos')
        content = data.get('content')
        
        print(f"dbg-app-E00- Numéro de dossier : {numdos}")
        # if not numdos:
        #     return jsonify({"message": "Le paramètre 'numdos' est requis."}), 400

        # Chemin absolu vers le python de l'environnement virtuel du workspace
        venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'))
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'cy4_general_analyse.py'))

        print(f"dbg-app-E01- Chemin python : {venv_python}")
        print(f"dbg-app-E02- Chemin script : {script_path}")

        if not os.path.isfile(venv_python):
            print(f"dbg-app-E03- Python introuvable : {venv_python}")
            return jsonify({"message": f"Python introuvable : {venv_python}"}), 500
        if not os.path.isfile(script_path):
            print(f"dbg-app-E04- Script introuvable : {script_path}")
            return jsonify({"message": f"Script introuvable : {script_path}"}), 500


        subprocess.Popen([venv_python, script_path, '--numdos', str(numdos), '--content', content])
        print(f"dbg-app-E05- Lancement de l'analyse générale pour le dossier : {numdos}")
        return jsonify({"message": "Lancement demandé."})
    except Exception as e:
        print(f"dbg-app-E06- Exception : {e}")
        return jsonify({"message": f"Erreur: {e}"}), 500

if __name__ == '__main__':
    # Initialiser le logging avec app_config
    app_config.setup_logging()
    
    # Utiliser les constantes de app_config si disponibles
    port = app_config.constants.get('port', 5000)
    debug = app_config.constants.get('debug', True)
    
    app.run(debug=debug, port=port)
