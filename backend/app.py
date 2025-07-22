from flask import Flask, render_template, request, jsonify
import os
import json
import numpy as np
from werkzeug.serving import run_simple
import sys

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

from cy_exploreur import exploreur
app.register_blueprint(exploreur)  # Register the blueprint      

from cy_cookies import cy_cookies
app.register_blueprint(cy_cookies)  # Register the blueprint

from cy_requests import cy_requests
app.register_blueprint(cy_requests)  # Register the blueprint

from cy_columns import cy_columns
app.register_blueprint(cy_columns)  # Register the new columns blueprint

#from cy_fbx import cy_fbx_exploreur
#app.register_blueprint(cy_fbx)  # Register the new FBX explorer blueprint

# Ajout du module de gestion des répertoires
from cy_directories import register_directories_routes
register_directories_routes(app)  # Enregistrer les routes de gestion des répertoires

from cy_file_picker import file_picker
app.register_blueprint(file_picker)  # Register the file picker blueprint

# Ajoutez ce code dans votre app.py après avoir enregistré le Blueprint
""" print("Routes disponibles:")
for rule in app.url_map.iter_rules():
    print(f"{rule} - {rule.endpoint}") """

# Utilisation de app_config au lieu de BASE_DIR
BASE_DIR = str(app_config.base_dir)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Initialiser le logging avec app_config
    app_config.setup_logging()
    
    # Utiliser les constantes de app_config si disponibles
    port = app_config.constants.get('port', 5001)
    debug = app_config.constants.get('debug', True)
    
    app.run(debug=debug, port=port)
