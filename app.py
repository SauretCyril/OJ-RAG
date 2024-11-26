import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from flask import Flask, render_template, jsonify, request, url_for
import os
import traceback
from werkzeug.utils import secure_filename
from qa_analyse import *
import torch
import torchvision
import numpy as np
import json
import logging

logging.basicConfig(level=logging.DEBUG)
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

# Configurer Flask pour utiliser le NumpyEncoder
app = Flask(__name__)
app.json_encoder = NumpyEncoder  # Ajouter cette ligne après la création de l'app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.static_folder = os.path.join(BASE_DIR, 'static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Assurer que les dossiers nécessaires existent
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.static_folder, exist_ok=True)

SAVED_TEXT_FOLDER = 'G:/OneDrive/Entreprendre/Actions-4'
ALLOWED_EXTENSIONS = {'pdf'}

#app.config['SAVED_TEXT_FOLDER'] = SAVED_TEXT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

""" @app.route('/upload', methods=['POST'])
def upload_file():
    if 'job' not in request.files:
        return jsonify(error='No file part'), 400
    
    job_file = request.files['job']
    
    if job_file.filename == '':
        return jsonify(error='No selected file'), 400
    
    # Save the file and return the path
    job_path = f"{job_file.filename}"
    job_file.save(job_path)
    
    return jsonify(num_job=123, job_path=job_path) """

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'job_file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        job_file1 = request.files['job_file']
        
        if job_file1.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(job_file1.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        job_file1_path=job_file1.filename[:4]
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        job_path = os.path.join(app.config['UPLOAD_FOLDER'], job_file1.filename)
        job_file1.save(job_path)

        #segments = job_file1.split('/')
        #print("file path",job_file1_path)
        #last_parent_directory = segments[-2]

        return jsonify({
            'job_path': job_path,
            'job_file_dir': job_file1_path
        })

    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/job-details')
def job_details():
    return render_template('job_details.html')

# get_answer
@app.route('/get_answer', methods=['POST'])
def extract_job_text():
    try:
        job_path = request.json.get('job_path')
        if not job_path:
            return jsonify({'error': 'Missing job file path'}), 400

        # Extraction rapide du texte
        job_text1 = extract_text_from_pdf(job_path)
        if not job_text1:
            return jsonify({'error': 'Job text extraction failed'}), 500

        # Formatage du texte avec la question prédéfinie
        q2_job = (
            "peux tu me faire un plan détaillé de l'offre avec les sections en précisant bien ce qui est obligatoire, optionnelle :"
            "- Titre poste proposé,"
            "- Duties (Description du poste décomposée en tache ou responsabilité),"
            "- requirements (expérience attendues, ),"
            "- skills (languages, outils obligatoires),"
            "- Savoir-être (soft skill),"
            "- autres (toutes informations autre utile à connaitre)"
        )

        formatted_job_text = get_answer(q2_job, job_text1)

        # Ensure consistent formatting of the response
        formatted_job_text = formatted_job_text.replace('\n', '<br>')
        #.replace(' - ', '<br>- ')
        return jsonify({
            'raw_text': job_text1,
            'formatted_text': formatted_job_text
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-job-text', methods=['POST'])
def save_job_text():
    try:
        job_text_data = request.json.get('job_text_data')
        job_number = request.json.get('job_number')
        if not job_text_data or not job_number:
            logger.error(f"Missing job text data or job number: job_text_data={job_text_data}, job_number={job_number}")
            return jsonify({'error': 'Missing job text data or job number'}), 400

        file_name = f"{job_number}_gpt_request.txt"
        file_path = os.path.join(SAVED_TEXT_FOLDER, job_number)
        file_path_full = os.path.join(file_path, file_name)
        
        with open(file_path_full, 'w', encoding='utf-8') as file:
            file.write(job_text_data)

        return jsonify({'message': 'Job text saved successfully', 'file_path': file_path_full})

    except Exception as e:
        logger.error(f"Error saving job text: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)