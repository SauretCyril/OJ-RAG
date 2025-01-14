from flask import Blueprint, request, jsonify, send_from_directory, render_template_string
import os
import json
import platform
import csv
import subprocess
from werkzeug.utils import secure_filename
from JO_analyse_gpt import get_info
import tkinter as tk
from tkinter import filedialog
import threading
from docx2pdf import convert
import pythoncom
from fpdf import FPDF
from docx import Document
import requests
import json
from tqdm import tqdm
from PyPDF2 import PdfFileReader, PdfFileWriter
from io import BytesIO

routes = Blueprint('routes', __name__)

# Load shared constants
def load_constants():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'constants.json')
    with open(config_path, 'r') as f:
        return json.load(f)

CONSTANTS = load_constants()
print('Loaded constants:', CONSTANTS)
@routes.route('/get_constants', methods=['GET'])
def get_constants():
    return jsonify(CONSTANTS)

@routes.route('/read_annonces_json', methods=['POST'])
def read_annonces_json():
    try:
        directory_path = os.getenv("ANNONCES_FILE_DIR")
        if not os.path.exists(directory_path):
            return []

        annonces_list = []
        crit_annonces = load_crit_annonces()
        #print(f"###1 ------Excluded annonces: {crit_annonces}")
        for root, _, files in os.walk(directory_path):
            parent_dir = os.path.basename(root)
            file_annonce = parent_dir + CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']
            file_annonce_steal=parent_dir + CONSTANTS['FILE_NAMES']['STEAL_ANNONCE_SUFFIX']
            file_isGptResum = parent_dir + CONSTANTS['FILE_NAMES']['GPT_REQUEST_SUFFIX']
            file_cv = parent_dir + CONSTANTS['FILE_NAMES']['CV_SUFFIX'] + ".docx"
            file_cv_pdf = parent_dir + CONSTANTS['FILE_NAMES']['CV_SUFFIX'] + ".pdf"
            file_isGptResum_Path1 = os.path.join(root, file_isGptResum)
            file_isGptResum_Path1 = file_isGptResum_Path1.replace('\\', '/') 
            file_cv_Path = os.path.join(root, file_cv.replace('\\', '/'))
            record_added = False
            data = {}
            isCVin="N"
            isCVinpdf="N"
            isSteal="N"
            isJo="N"
            for filename in files:
                if filename  == file_cv:
                    isCVin="O"
                    #print("###---->BINGO")
                if filename  == file_cv_pdf:
                    isCVinpdf="O"
                if (filename ==  file_annonce_steal):
                    isSteal="O"
                    file_path_isJo = os.path.join(root, file_annonce)
                    file_path_isJo = file_path.replace('\\', '/') 
                if (filename ==  file_annonce):
                    isJo="O"
                    file_path_isJo = os.path.join(root, file_annonce)
                    file_path_isJo = file_path.replace('\\', '/') 
                if (filename ==  file_isGptResum):
                    isGptResum="O"
                    
                  
            for filename in files:
                file_path = os.path.join(root, filename)
                file_path = file_path.replace('\\', '/')  # Normalize path
               
                 
                if filename == ".data.json":
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            data = json.load(file)
                            # Check exclusion criteria
                            isExclued = False
                            if crit_annonces:
                                excl = crit_annonces["exclude"]
                                for crit in excl:
                                    for key, values in crit.items():
                                        if data.get(key) in values:
                                            isExclued = True
                                            break
                                    if isExclued:
                                        break
                            else:
                                if not data['etat'] in ["DELETED"]:
                                    isExclued = True
                            if not isExclued:
                                data["dossier"] = parent_dir  # Add parent directory name to data
                                if os.path.exists(file_isGptResum_Path1):
                                    isGptResum = "O"
                                else:
                                    isGptResum = "N"
                                data["isJo"] = isJo
                                data['isSteal'] = isSteal
                                data["GptSum"] = isGptResum
                                data["CV"] = isCVin
                                data["CVpdf"] = isCVinpdf
                                
                                jData = {file_path: data}
                                annonces_list.append(jData)
                                
                            
                            record_added = True

                    except json.JSONDecodeError:
                        errordata = {"id": parent_dir, "description": "?", "etat": "invalid JSON"}
                        print(f"Cyr_Error: The file {file_path} contains invalid JSON.")
                
              
            """ if not record_added:
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_path = file_path.replace('\\', '/')  # Normalize path
                    #file_annonce = parent_dir + "_annonce_.pdf"
                    file_annonce_path = os.path.join(root, ".data.json")
                    if filename == file_annonce:
                        Data = define_default_data()     
                        Data["dossier"] = parent_dir
                        data["isJo"] = isJo
                        data['isSteal'] = isSteal
                        data["GptSum"] = isGptResum
                        Data["CV"] = isCVin
                        data["CVpdf"] = isCVinpdf
                        
                        # Save the data to JSON file
                        #save_annonces_json(data=[{file_annonce_path: Data}])
                        
                        try: 
                            infos = get_info(file_path, "peux tu me trouver : l'url [url] de l'annoncese trouve entre <- et ->, "+
                                             "-l'entreprise [entreprise],"+
                                             "-le titre ou l'intiltulé [poste] du poste à pourvoir (ce titre ne doit pas dépasser 20 caractère)"+
                                             "-la localisation ou lieu dans lieux [lieu]")
                        
                            infos = json.loads(infos)  # Parse the JSON response
                            if infos:
                                Data["url"] = infos["url"]
                                
                                #print("DBG-234 -> url: %s" % infos["url"])
                                
                                Data["entreprise"] = infos["entreprise"]
                                Data["description"] = infos["poste"]
                                record_added = True  
                                Data["etat"] = "New"
                                Data["CV"] = isCVin
                                data["CVpdf"] = isCVinpdf
                                data["Lieu"] = infos["lieu"]
                                jData = {file_annonce_path: Data}   
                                annonces_list.append(jData)
                            else:
                                record_added = True  
                                Data["etat"] = "Vide"
                                jData = {file_annonce_path: Data}   
                                annonces_list.append(jData)
                               
                        except Exception as e:
                            #print(f"An unexpected error occurred get infos with gpt: {e}")
                            record_added = True  
                            Data["etat"] = "Error"
                            jData = {file_annonce_path: Data}   
                            annonces_list.append(jData)
                    if record_added: break """
                                
        return annonces_list 
    except Exception as e:
        print(f"Cyr_error_145 An unexpected error occurred while reading annonces: {e}")
        return []

def load_crit_annonces():
    try:
        config_path = os.path.join(os.getenv("ANNONCES_DIR_STATE"), "excluded_annonces.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as file:
                return json.load(file)
     
    except Exception as e:
        print(f"Cyr_error_156 An error occurred while loading excluded annonces: {e}")
        return jsonify({"status": "error", "message": "156>"+str(e)}), 500

@routes.route('/save_excluded_annonces', methods=['POST'])
def save_excluded_annonces():
    try:
        data = request.get_json()
        excluded_annonces = data.get('excluded_annonces', [])
        
        config_path = os.path.join(os.getenv("ANNONCES_DIR_FILTER"), "excluded_annonces.json")
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(excluded_annonces, config_file, ensure_ascii=False, indent=4)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_171 An error occurred while saving excluded annonces: {e}")
        return jsonify({"status": "error", "message": "171>"+str(e)}), 500

'''save config columns'''
@routes.route('/save_config_col', methods=['POST'])
def save_config_col():
    try:
        data = request.get_json()
        serialized_columns = data.get('columns')
        tab_active = data.get('tabActive')
        
        # Save the serialized columns to a file or database
        config_path = os.path.join(os.getenv("ANNONCES_DIR_FILTER"), f"{tab_active}__colums")+ ".json"
        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(serialized_columns, config_file, ensure_ascii=False, indent=4)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_189 An error occurred while saving config columns: {e}")
        return jsonify({"status": "error", "message": "189>"+str(e)}), 500

# ...existing code...

@routes.route('/open_url', methods=['POST'])
def open_url():
    try:
        data = request.get_json()
        url = data.get('url')
        #print ("##3-------------------------------",url)
        if url:
            # Logic to open the URL
            os.system(f'start {url}')
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "URL not provided"}), 400
    except Exception as e:
        print(f"Cyr_error_207 An error occurred while opening URL: {e}")
        return jsonify({"status": "error", "message": "207>"+str(e)}), 500

# ...existing code...

@routes.route('/file_exists', methods=['POST'])
def file_exists():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if file_path and os.path.exists(file_path):
            return jsonify({"exists": True}), 200
        else:
            return jsonify({"exists": False}), 200
    except Exception as e:
        print(f"Cyr_error_223 An error occurred while checking file existence: {e}")
        return jsonify({"status": "error", "message": "223>"+str(e)}), 500


@routes.route('/read_filters_json', methods=['POST'])
def read_filters_json():
    try:
        
        data = request.get_json()
        tab_active = data.get('tabActive')
        
        file_path = os.path.join(os.getenv("ANNONCES_DIR_FILTER"), tab_active + "_filter") + ".json"
        file_path = file_path.replace('\\', '/')  # Normalize path
        #print(f"##01-loading filters from {file_path}")
        if not os.path.exists(file_path):
            return jsonify({})
        with open(file_path, 'r', encoding='utf-8') as file:
            filters = json.load(file)
            #print("##02#",filters)
            return jsonify(filters)  # Return dictionary directly
    except Exception as e:
        print(f"Cyr_error_244 An unexpected error occurred while reading filter values: {e}")
        return jsonify({"status": "error", "message": "244>"+str(e)}), 500

# ...existing code...

@routes.route('/save_annonces_json', methods=['POST'])
def save_annonces_json():
    try:
        data = request.get_json()
        for item in data:
            for file_path, content in item.items():
                file_path = file_path.replace('\\', '/')  # Normalize path
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(content, file, ensure_ascii=False, indent=4)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_260 An unexpected error occurred while saving data: {e}")
        return jsonify({"status": "error", "message": "260>"+str(e)}), 500

# ...existing code...

@routes.route('/save_filters_json', methods=['POST'])
def save_filters_json():
    try:
        data = request.get_json()
        filters = data.get('filters')
        tab_active = data.get('tabActive')
        file_path = os.path.join(os.getenv("ANNONCES_DIR_FILTER"), tab_active + "_filter") + ".json"
        file_path = file_path.replace('\\', '/')  # Normalize path
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(filters, file, ensure_ascii=False, indent=4)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_277 An unexpected error occurred while saving filter values: {e}")
        return jsonify({"status": "error", "message": "277>"+str(e)}), 500

# ...existing code...

@routes.route('/load_config_col', methods=['POST'])
def load_config_col():
    try:
        data = request.get_json()
        tab_active = data.get('tabActive')
        file_path = os.path.join(os.getenv("ANNONCES_DIR_FILTER"), tab_active + "_colums") + ".json"
        file_path = file_path.replace('\\', '/')  # Normalize path
        if not os.path.exists(file_path):
            return jsonify([])  # Return empty list if file does not exist
        with open(file_path, 'r', encoding='utf-8') as file:
            conf = json.load(file)
            return jsonify(conf)  # Return JSON response
    except Exception as e:
        print(f"Cyr_error_295 An unexpected error occurred while reading columns config: {e}")
        return jsonify([])

# ...existing code...

@routes.route('/read_csv_file', methods=['POST'])
def read_csv_file():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        file_path = os.path.join(os.getenv("SUIVI_DIR"), file_path)
        file_path = file_path.replace('\\', '/')  # Normalize path
        #print(f"file path: {file_path}")
        if not os.path.exists(file_path):
            return jsonify([])

        with open(file_path, 'r', encoding='ISO-8859-1') as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=';')
            data = [row for row in csvreader]
            return jsonify(data)
    except Exception as e:
        print(f"Cyr_error_316 An unexpected error occurred while reading CSV file: {e}")
        return jsonify([])


@routes.route('/save_csv_file', methods=['POST'])
def save_csv_file():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        csv_data = data.get('data')
        file_path = os.path.join(os.getenv("SUIVI_DIR"), file_path)
        file_path = file_path.replace('\\', '/')  # Normalize path
        #print(f"Saving CSV to {file_path}")
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File path does not exist"}), 400

        with open(file_path, 'w', newline='', encoding='ISO-8859-1') as csvfile:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(csv_data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_339 An unexpected error occurred while saving CSV file: {e}")
        return jsonify({"status": "error", "message": "339>"+str(e)}), 500

# ...existing code...

@routes.route('/open_parent_directory', methods=['POST'])
def open_parent_directory():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        parent_directory = os.path.dirname(file_path)
        parent_directory = parent_directory.replace('\\', '/')  # Normalize path
        if platform.system() == 'Windows':
            os.startfile(parent_directory)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', parent_directory])
        else:  # Linux
            subprocess.run(['xdg-open', parent_directory])
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_359 opening parent directory: {e}")
        return jsonify({"status": "error", "message": "359>"+str(e)}), 500

# ...existing code...


@routes.route('/convert_cv', methods=['POST'])
def convert_cv():
    #print ("convertir le cv docx en cv pdf")
    data = request.get_json()
    file_path= data.get('repertoire_annonces')
    num_dossier = data.get('num_dossier')
    filename = secure_filename(f"{num_dossier}_CyrilSauret.docx")
    target_path = os.path.join(file_path, filename)
    target_path_pdf= os.path.join(file_path, filename.replace('.docx', '.pdf'))
    if os.path.exists(target_path_pdf):
        os.remove(target_path_pdf)
        #print("-->04 pdf removed", target_path_pdf)
    

@routes.route('/share_cv', methods=['POST'])
def select_cv():
    try:
        #print("##0---")
        file = request.files.get('file_path')
        dossier_number = request.form.get('num_dossier')
        target_directory = request.form.get('repertoire_annonce')
        #print("##2-------------------------------", dossier_number, target_directory)
        
        if not dossier_number or not target_directory or not file:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400 
        
        filename = secure_filename(f"{dossier_number}_CyrilSauret.docx")
        target_path = os.path.join(target_directory, filename)
        target_path = target_path.replace('\\', '/') 
        #print("##3-------------------------------", target_path)
        pdf_file_path = target_path.replace('.docx', '.pdf')
        pdf_file_path = pdf_file_path.replace('\\', '/') 
        
        if not os.path.exists(target_path):
            file.save(target_path)
            #print("-->01 docx saved : ", target_path)
        else:
            os.remove(target_path)
            #print("-->02 docx removed", target_path)
            file.save(target_path)
            #print("-->03 docx saved", target_path)
        convert_to_pdf(target_path,pdf_file_path)
        #print("##3a-----------------------",pdf_file_path)
        
        return jsonify({"status": "success", "message": f"File saved as {filename} in {target_directory}"}), 200
    except Exception as e:
        print(f"Cyr_error_411 An error occurred when duplicate file: {e}")
        return jsonify({"status": "error", "message": "441>"+str(e)}), 500 

# ...existing code...


def convert_to_pdf(target_path,pdf_file_path):
    
    if os.path.exists(pdf_file_path):# Delete the existing file
        os.remove(pdf_file_path)
        #print("-->04 pdf removed", pdf_file_path)
    pythoncom.CoInitialize()
    
    try:
        convert(target_path, pdf_file_path)
        #print("-->05 docx converted to pdf", pdf_file_path)
    finally:
        # Uninitialize COM library
        pythoncom.CoUninitialize()
            

def define_default_data():
    return {
        "id": "",
        "description": "?",
        "etat": "Auto",
        "entreprise": "?",
        "categorie": "",
        "Date": "",
        "todo": "?",
        "todoList": "",
        "action": "",
        "tel": "",
        "contact": "",
        "url": "",
        "Commentaire": "",
        "type": "AN",
        "type_question": "pdf",
        "title":"",
        "isSteal": "N",
    }

@routes.route('/save_announcement', methods=['POST'])
def save_announcement():
    try:
        data = request.get_json()
        num_dossier = data.get('contentNum')
        content = data.get('content')
        url = data.get('url')

        if not num_dossier or not content or not url:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400

        directory_path = os.path.join(os.getenv("ANNONCES_FILE_DIR"), num_dossier)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
       
        docx_file_path = os.path.join(directory_path, f"{num_dossier}_annonce_.docx")
        pdf_file_path = os.path.join(directory_path, f"{num_dossier}_annonce_.pdf")
        
        """ if os.path.exists(pdf_file_path):
            return jsonify({"status": "error", "message": f"Fichier {pdf_file_path} existe déjà"}), 400 """
        
        pythoncom.CoInitialize()
        # Create DOCX file
        try:
            doc = Document()
            # Ensure URL is properly formatted
            doc.add_paragraph("<-")
            doc.add_paragraph(url)
            doc.add_paragraph("->")
            doc.add_paragraph(content)
            
            doc.save(docx_file_path)
            # Convert DOCX to PDF
            convert(docx_file_path, pdf_file_path)
        finally:
            # Uninitialize COM library
            pythoncom.CoUninitialize() 

        return jsonify({"status": "success", "message": f"Announcement saved as {pdf_file_path}"}), 200
    except Exception as e:
        print(f"Cyr_error_492 An error occurred while saving the announcement: {e}")
        return jsonify({"status": "error", "message": "492>"+str(e)}), 500

# ...existing code...

@routes.route('/read_notes', methods=['POST'])
def read_notes():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({"status": "error", "message": "File path not provided"}), 400
        
        if not os.path.exists(file_path):
            # Create the file if it does not exist
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump([], file)  # Write an empty JSON array to create the file
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = json.load(file)
        
        return jsonify({"status": "success", "content": content}), 200
    except Exception as e:
        print(f"Cyr_error_516 An error occurred while reading notes: {e}")
        return jsonify({"status": "error", "message": "516>"+str(e)}), 500

# ...existing code...

@routes.route('/save_notes', methods=['POST'])
def save_notes():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        content = data.get('content')
        
        if not file_path or content is None:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(content, file, ensure_ascii=False, indent=4)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_536 An error occurred while saving notes: {e}")
        return jsonify({"status": "error", "message": "536>"+str(e)}), 500

# ...existing code...

@routes.route('/load_reseaux_link', methods=['GET'])
def load_reseaux_link():
    try:
       file_path = os.path.join(os.getenv("RESEAUX_FILE"))
       file_path = file_path.replace('\\', '/')  # Normalize path
       if not os.path.exists(file_path):
           return jsonify([])  # Return empty list if file does not exist
       with open(file_path, 'r', encoding='utf-8') as file:
           file = json.load(file)
           return jsonify(file)  # Return JSON response
    except Exception as e:
        print(f"Cyr_error_552 An unexpected error occurred while reading reseaux: {e}")
        return jsonify([])

@routes.route('/save_reseaux_link_update', methods=['POST'])
def save_reseaux_link_update():
    try:
        link_data = request.get_json()
        file_path = os.getenv("RESEAUX_FILE")
        file_path = file_path.replace('\\', '/')  # Normalize path
        #print(f"Cyr_error_561---",file_path)
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File path does not exist"}), 400

        with open(file_path, 'r', encoding='utf-8') as file:
            links = json.load(file)

        # Update the link in the list
        for link in links:
            if link['name'] == link_data['name']:
                link.update(link_data)
                break

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(links, file, ensure_ascii=False, indent=4)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Cyr_error_579 An error occurred while saving reseaux link update: {e}")
        return jsonify({"status": "error", "message": "579>"+str(e)}), 500

# ...existing code...


from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import tempfile

@routes.route('/scrape_url', methods=['POST'])
def scrape_url():
    try:
        data = request.get_json()
        
        num_job = data.get('num_job') 
        url_to_scrape = data.get('item_url')
        
        if not url_to_scrape or not num_job:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400

        api_url = "http://localhost:3000/v1/pdf"
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            "url": url_to_scrape,
            "waitFor": 1000
        }
        print(f"DBG01------payload : {payload}")
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            try:
                directory_path = os.path.join(os.getenv("ANNONCES_FILE_DIR"), num_job)
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)
                    
                pdf_file_path = os.path.join(directory_path, f"{num_job}_annonce_steal.pdf")
                
                # Create temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as url_temp_file:
                    # Create URL page
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, f"<-\n{url_to_scrape}\n->")
                    pdf.output(url_temp_file.name)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as content_temp_file:
                    # Save content to temp file
                    content_temp_file.write(response.content)
                    content_temp_file.flush()
                
                # Merge PDFs
                output_pdf = PdfWriter()
                
                # Add URL page
                url_pdf = PdfReader(url_temp_file.name)
                output_pdf.add_page(url_pdf.pages[0])
                
                # Add content pages
                content_pdf = PdfReader(content_temp_file.name)
                for page in content_pdf.pages:
                    output_pdf.add_page(page)
                
                # Write final PDF
                with open(pdf_file_path, 'wb') as output_file:
                    output_pdf.write(output_file)
                
                # Clean up temp files
                os.unlink(url_temp_file.name)
                os.unlink(content_temp_file.name)
                
                return jsonify({"status": "success", "data": "Success"}), 200
              
            except Exception as e:
                print(f"Error details: {str(e)}")
                return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
        else:
            return jsonify({"status": "error", "message": response.text}), response.status_code
    except Exception as e:
        print(f"Cyr_error_616 An error occurred in scrape_url: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500 

# ...existing code...
