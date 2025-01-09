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

routes = Blueprint('routes', __name__)

@routes.route('/read_annonces_json', methods=['POST'])
def read_annonces_json():
    try:
        directory_path = os.getenv("ANNONCES_FILE_DIR")
        if not os.path.exists(directory_path):
            return []

        annonces_list = []
        crit_annonces = load_crit_annonces()
        print(f"###1 ------Excluded annonces: {crit_annonces}")
        for root, _, files in os.walk(directory_path):
            parent_dir = os.path.basename(root)
            file_annonce = parent_dir + "_annonce_.pdf"
            file_isGptResum = parent_dir + "_gpt_request.pdf"
            file_cv = parent_dir + "_CyrilSauret.docx"
            file_cv_pdf = parent_dir + "_CyrilSauret.pdf"
            file_isGptResum_Path1 = os.path.join(root, file_isGptResum)
            file_isGptResum_Path1 = file_isGptResum_Path1.replace('\\', '/') 
            file_cv_Path = os.path.join(root, file_cv.replace('\\', '/'))
            record_added = False
            data = {}
            isCVin="N"
            isCVinpdf="N"
            for filename in files:
                if filename  == file_cv:
                    isCVin="O"
                    print("###---->BINGO")
                if filename  == file_cv_pdf:
                    isCVinpdf="O"
                    
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
                                    isGptResum = "True"
                                else:
                                    isGptResum = "False"
                            
                                data["GptSum"] = isGptResum
                                data["CV"] = isCVin
                                data["CVpdf"] = isCVinpdf
                                jData = {file_path: data}
                                annonces_list.append(jData)
                            
                            record_added = True

                    except json.JSONDecodeError:
                        errordata = {"id": parent_dir, "description": "?", "etat": "invalid JSON"}
                        print(f"Error: The file {file_path} contains invalid JSON.")
                
              
            if not record_added:
                for filename in files:
                    file_path = os.path.join(root, filename)
                    file_path = file_path.replace('\\', '/')  # Normalize path
                    #file_annonce = parent_dir + "_annonce_.pdf"
                    file_annonce_path = os.path.join(root, ".data.json")
                    if filename == file_annonce:
                        Data = define_default_data()     
                        Data["dossier"] = parent_dir
                        Data["etat"] = "gpt"
                        Data["CV"] = isCVin
                        data["CVpdf"] = isCVinpdf
                       
                        
                        try: 
                            infos = get_info(file_path, "peux tu me trouver : l'url [url] de l'annoncese trouve entre <- et ->, "+
                                             "-l'entreprise [entreprise],"+
                                             "-le titre ou l'intiltulé [poste] du poste à pourvoir (ce titre ne doit pas dépasser 20 caractère)"+
                                             "-la localisation ou lieu dans lieux [lieu]")
                        
                            infos = json.loads(infos)  # Parse the JSON response
                            if infos:
                                Data["url"] = infos["url"]
                                
                                print("DBG-234 -> url: %s" % infos["url"])
                                
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
                            print(f"An unexpected error occurred get infos with gpt: {e}")
                            record_added = True  
                            Data["etat"] = "Error"
                            jData = {file_annonce_path: Data}   
                            annonces_list.append(jData)
                    if record_added: break
                                
        return annonces_list 
    except Exception as e:
        print(f"An unexpected error occurred while reading annonces: {e}")
        return []

def load_crit_annonces():
    try:
        config_path = os.path.join(os.getenv("ANNONCES_DIR_STATE"), "excluded_annonces.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as file:
                return json.load(file)
     
    except Exception as e:
        print(f"An error occurred while loading excluded annonces: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"An error occurred while saving excluded annonces: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"An error occurred while saving config columns: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ...existing code...

@routes.route('/open_url', methods=['POST'])
def open_url():
    try:
        data = request.get_json()
        url = data.get('url')
        print ("##3-------------------------------",url)
        if url:
            # Logic to open the URL
            os.system(f'start {url}')
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "URL not provided"}), 400
    except Exception as e:
        print(f"An error occurred while opening URL: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"An error occurred while checking file existence: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@routes.route('/read_filters_json', methods=['POST'])
def read_filters_json():
    try:
        
        data = request.get_json()
        tab_active = data.get('tabActive')
        
        file_path = os.path.join(os.getenv("ANNONCES_DIR_FILTER"), tab_active + "_filter") + ".json"
        file_path = file_path.replace('\\', '/')  # Normalize path
        print(f"##01-loading filters from {file_path}")
        if not os.path.exists(file_path):
            return jsonify({})
        with open(file_path, 'r', encoding='utf-8') as file:
            filters = json.load(file)
            print("##02#",filters)
            return jsonify(filters)  # Return dictionary directly
    except Exception as e:
        print(f"An unexpected error occurred while reading filter values: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"An unexpected error occurred while saving data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"An unexpected error occurred while saving filter values: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"An unexpected error occurred while reading columns config: {e}")
        return jsonify([])

# ...existing code...

@routes.route('/read_csv_file', methods=['POST'])
def read_csv_file():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        file_path = os.path.join(os.getenv("SUIVI_DIR"), file_path)
        file_path = file_path.replace('\\', '/')  # Normalize path
        print(f"file path: {file_path}")
        if not os.path.exists(file_path):
            return jsonify([])

        with open(file_path, 'r', encoding='ISO-8859-1') as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=';')
            data = [row for row in csvreader]
            return jsonify(data)
    except Exception as e:
        print(f"An unexpected error occurred while reading CSV file: {e}")
        return jsonify([])


@routes.route('/save_csv_file', methods=['POST'])
def save_csv_file():
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        csv_data = data.get('data')
        file_path = os.path.join(os.getenv("SUIVI_DIR"), file_path)
        file_path = file_path.replace('\\', '/')  # Normalize path
        print(f"Saving CSV to {file_path}")
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File path does not exist"}), 400

        with open(file_path, 'w', newline='', encoding='ISO-8859-1') as csvfile:
            fieldnames = csv_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(csv_data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"An unexpected error occurred while saving CSV file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
        print(f"Error opening parent directory: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ...existing code...


@routes.route('/convert_cv', methods=['POST'])
def convert_cv():
    print ("convertir le cv docx en cv pdf")
    data = request.get_json()
    file_path= data.get('repertoire_annonces')
    num_dossier = data.get('num_dossier')
    filename = secure_filename(f"{num_dossier}_CyrilSauret.docx")
    target_path = os.path.join(file_path, filename)
    target_path_pdf= os.path.join(file_path, filename.replace('.docx', '.pdf'))
    if os.path.exists(target_path_pdf):
        os.remove(target_path_pdf)
        print("-->04 pdf removed", target_path_pdf)
    

@routes.route('/share_cv', methods=['POST'])
def select_cv():
    try:
        print("##0---")
        file = request.files.get('file_path')
        dossier_number = request.form.get('num_dossier')
        target_directory = request.form.get('repertoire_annonce')
        print("##2-------------------------------", dossier_number, target_directory)
        
        if not dossier_number or not target_directory or not file:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400 
        
        filename = secure_filename(f"{dossier_number}_CyrilSauret.docx")
        target_path = os.path.join(target_directory, filename)
        target_path = target_path.replace('\\', '/') 
        print("##3-------------------------------", target_path)
        pdf_file_path = target_path.replace('.docx', '.pdf')
        pdf_file_path = pdf_file_path.replace('\\', '/') 
        
        if not os.path.exists(target_path):
            file.save(target_path)
            print("-->01 docx saved : ", target_path)
        else:
            os.remove(target_path)
            print("-->02 docx removed", target_path)
            file.save(target_path)
            print("-->03 docx saved", target_path)
        convert_to_pdf(target_path,pdf_file_path)
        print("##3a-----------------------",pdf_file_path)
        
        return jsonify({"status": "success", "message": f"File saved as {filename} in {target_directory}"}), 200
    except Exception as e:
        print(f"An error occurred when duplicate file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500 

# ...existing code...


def convert_to_pdf(target_path,pdf_file_path):
    
    if os.path.exists(pdf_file_path):# Delete the existing file
        os.remove(pdf_file_path)
        print("-->04 pdf removed", pdf_file_path)
    pythoncom.CoInitialize()
    
    try:
        convert(target_path, pdf_file_path)
        print("-->05 docx converted to pdf", pdf_file_path)
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
        "title":""
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
        print(f"An error occurred while saving the announcement: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
                file.write("")  # Write an empty string to create the file
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return jsonify({"status": "success", "content": content}), 200
    except Exception as e:
        print(f"An error occurred while reading notes: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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
            file.write(content)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"An error occurred while saving notes: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ...existing code...
