import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from flask import Flask, render_template, request, jsonify
import os

# Set correct paths for templates and static files
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
static_folder_path = os.path.join(parent_dir, 'static')
templates_folder_path = os.path.join(parent_dir, 'templates')

app = Flask(__name__, 
           static_folder=static_folder_path, 
           template_folder=templates_folder_path)

from werkzeug.utils import secure_filename
#from JO_analyse import *

''' Procédures'''

# ...existing code...
import torch
import numpy as np
import json
import logging
from docx import Document
from docx2pdf import convert
import pythoncom
from fpdf import FPDF
#from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity
from dotenv import load_dotenv
from backend.cy_paths import *

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Définir NumpyEncoder avant de l'utiliser
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32):
            return float(obj)
        if isinstance(obj, torch.Tensor):
            return obj.detach().cpu().numpy().tolist()
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

# Ajoutez ce code dans votre app.py après avoir enregistré le Blueprint
""" print("Routes disponibles:")
for rule in app.url_map.iter_rules():
    print(f"{rule} - {rule.endpoint}") """

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Assurer que les dossiers nécessaires existent
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SAVED_TEXT_FOLDER = 'path/to/save/folder'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['SAVED_TEXT_FOLDER'] = SAVED_TEXT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/alive')
def alive():
    return jsonify({'message': 'Im alive'}), 200

@app.route('/')
def index():
    return render_template('index.html')



if __name__ == '__main__':
    from multiprocessing import freeze_support
    #from JO_analyse import *
    import webbrowser
    import threading
    import time
    
    def open_browser():
        """Ouvre le navigateur après un court délai"""
        time.sleep(1.5)  # Attendre que le serveur démarre
        webbrowser.open('http://127.0.0.1:5000')
    
    # Lancer l'ouverture du navigateur dans un thread séparé
    threading.Thread(target=open_browser).start()
    
    # Initialiser multiprocessing
    freeze_support()
    
    # Démarrer le serveur Flask (cette ligne est bloquante)
    app.run(debug=True)
