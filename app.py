import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from flask import Flask, render_template, jsonify, request, url_for
import os

from werkzeug.utils import secure_filename
from JO_analyse import *
import torch
#import torchvision
import numpy as np
import json
import logging
from docx import Document
from docx2pdf import convert
import pythoncom
from fpdf import FPDF

# ...existing code...

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

# Configurer Flask pour utiliser le NumpyEncoder
app = Flask(__name__)
from RP_routes import routes 
app.register_blueprint(routes)  # Register the blueprint

app.json_encoder = NumpyEncoder  # Ajouter cette ligne après la création de l'app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.static_folder = os.path.join(BASE_DIR, 'static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Assurer que les dossiers nécessaires existent
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SAVED_TEXT_FOLDER = 'G:/OneDrive/Entreprendre/Actions-4'
ALLOWED_EXTENSIONS = {'pdf'}

#app.config['SAVED_TEXT_FOLDER'] = SAVED_TEXT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.route('/alive')
def alive():
    return jsonify({'message': ' Im alive'}), 200


@app.route('/')
def index():
    return render_template('RP_index.html')

@app.route('/save-path')
def getSavePath():
    return SAVED_TEXT_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.debug("dbg001.Upload file request received")
        if 'file' not in request.files:
            logger.error("Er001.No file part in the request")
            return jsonify({'Er001': 'No file part'}), 400

        file1 = request.files['file']
        
        if file1.filename == '':
            logger.error("Er002.No selected file")
            return jsonify({'Er002': 'No selected file'}), 400

        if not allowed_file(file1.filename):
            logger.error(f"Er003.File type not allowed: {file1.filename}")
            return jsonify({'Er003': 'File type not allowed'}), 400
        
        file1_path = file1.filename[:4]
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file = os.path.join(app.config['UPLOAD_FOLDER'],file1.filename)
        file1.save(file)
        logger.debug(f"dbg002.File saved to {file}")

        return jsonify({
            'path': file,
            'file_dir': file1_path
        })

    except Exception as e:
        logger.error(f"Er004.Upload error: {str(e)}")
        return jsonify({'Er004': str(e)}), 500

@app.route('/job-details')
def job_details():
    return render_template('job_details.html')

# get_answer
@app.route('/get_job_answer', methods=['POST'])
def extract_job_text():
    try:
        logger.debug(f"dbg003.Request method: {request.method}")
        file = request.json.get('path')
        RQ = request.json.get('RQ')
        logger.debug(f"dbg004.Received file path: {file}")
        logger.debug(f"dbg004.Received RQ: {RQ}")
      
        if not file or not RQ:
            logger.error("Er005.Missing job file path or question")
            return jsonify({'Er005': 'Missing job file path or question'}), 400

        # Extraction rapide du texte
        text1 = extract_text_from_pdf(file)
        
        if not text1:
            logger.error("Er006.Job text extraction failed")
            return jsonify({'Er006': 'Job text extraction failed'}), 500
       
        # formated pour affichage text
        """  return jsonify({
            'raw_text':'raw_text',
            'formatted_text':text1
        }) """
        
        answer = get_answer(RQ, text1)
        logger.debug(f"dbg005.Generated answer: {answer}")
       
        return jsonify({
            'raw_text': text1,
            'formatted_text': answer
        })

    except Exception as e:
        logger.error(f"Er007.Error: {str(e)}")
        return jsonify({'Er007': str(e)}), 500

@app.route('/save-answer', methods=['POST'])
def save_job_text():
    try:
        logger.debug("dbg006.Save job text request received")
        pythoncom.CoInitialize()  # Initialize COM library
        job_text_data = request.json.get('text_data')
        job_number = request.json.get('number')
        the_path = request.json.get('the_path')
        logger.debug("dbg007.Received path: %s", the_path)

        if not job_text_data or not job_number:
            logger.error(f"Er008.error.Missing job text data or job number: job_text_data={job_text_data}, job_number={job_number}")
            return jsonify({'Er008': 'Missing job text data or job number'}), 400

        if not the_path:
            logger.error("Er009.Received path is None")
            return jsonify({'Er009': 'Missing path'}), 400

        file_name = f"{job_number}_gpt_request"
        file_path = os.path.join(the_path, job_number)
        file_path_txt = os.path.join(file_path, file_name + ".txt")
        file_path_docx = os.path.join(file_path, file_name + ".docx")
        logger.debug(f"dbg008.Saving job to : {file_path_txt} and {file_path_docx}")

        """ Save txt file"""
        with open(file_path_txt, 'w', encoding='utf-8') as file:
            file.write(job_text_data)
        
        """ Save pdf file"""
        doc = format_text_as_word_style(job_text_data, job_number)
        doc.save(file_path_docx)

        pdf_file_path = file_path_docx.replace('.docx', '.pdf')
        convert(file_path_docx, pdf_file_path)
        logger.debug(f"dbg009.Job text saved successfully as {pdf_file_path}")

        return jsonify({'dbg009': 'Job text saved successfully', 'file_path': file_path_txt, 'pdf_file_path': pdf_file_path})

    except Exception as e:
        logger.error(f"Er009.Error saving job text: {str(e)}")
        return jsonify({'Er009': str(e)}), 500

    finally:
        pythoncom.CoUninitialize()  # Uninitialize COM library
        

def format_text_as_word_style(job_text, job_number):
    doc = Document()
    doc.add_heading(f"Job Number: {job_number}", level=1)
    
    for line in job_text.split('\n'):
        if line.startswith('- '):
            doc.add_paragraph(line, style='ListBullet')
        else:
            doc.add_paragraph(line)
    
    return doc

    """--------------------------- Analyse_
    
    """
@app.route('/extract_features', methods=['POST'])
def extract_features(text):
    logger.debug("dbg010.2. Extracting features...")
    cv_features = extract_features(cv_text)
    job_features = extract_features(job_text)
    logger.debug("dbg011.3. Computing similarity...")
    raw_similarity = cosine_similarity(cv_features, job_features)
    adjusted_similarity = calculate_similarity_score(cv_features, job_features)
        
    logger.debug("dbg012.4.Results:")
    raw_similarity_s=f"{raw_similarity:.4f}"
    adjusted_similarity_s=f"{adjusted_similarity:.4f}"
    logger.debug("dbg013.Raw similarity score: {raw_similarity_s}")
    logger.debug("dbg014.Adjusted similarity score: {adjusted_similarity_s}")
    return jsonify({'Raw_similarity_score': raw_similarity_s, 'Adjusted_similarity_score':adjusted_similarity_s})

 
    
if __name__ == '__main__':
    app.run(debug=True)