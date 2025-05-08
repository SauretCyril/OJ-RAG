from flask import Flask, render_template, request, jsonify
import os
import json
import numpy as np
from werkzeug.serving import run_simple
import sys

# Définir le chemin de PYTHONPATH pour inclure le dossier actuel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, template_folder='../templates', static_folder='../static')

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

# Ajout du module de gestion des répertoires
from cy_directories import register_directories_routes
register_directories_routes(app)  # Enregistrer les routes de gestion des répertoires

# Ajoutez ce code dans votre app.py après avoir enregistré le Blueprint
""" print("Routes disponibles:")
for rule in app.url_map.iter_rules():
    print(f"{rule} - {rule.endpoint}") """

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
