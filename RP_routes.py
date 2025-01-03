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
            
            file_isGptResum_Path1 = os.path.join(root, file_isGptResum)
            file_isGptResum_Path1 = file_isGptResum_Path1.replace('\\', '/') 
            file_cv_Path = os.path.join(root, file_cv.replace('\\', '/'))
            record_added = False
            data = {}
            isCVin="N"
            for filename in files:
                file_path = os.path.join(root, filename)
                file_path = file_path.replace('\\', '/')  # Normalize path
                if (filename  == "_CyrilSauret.docx"):
                    isCVin="O"
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
                       
                        
                        try: 
                            infos = get_info(file_path, "peux tu me trouver l'url de l'annonce ( elle se trouve entre <- et ->)  [url], l'entreprise [entreprise], le titre du poste [poste] (ce titre ne doit pas dépasser 20 caractère)")
                            infos = json.loads(infos)  # Parse the JSON response
                            if infos:
                                Data["url"] = infos["url"]
                                Data["entreprise"] = infos["entreprise"]
                                Data["description"] = infos["poste"]
                                record_added = True  
                                Data["etat"] = "New"
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

@routes.route('/select_cv', methods=['POST'])
def select_cv():
    try:
        data = request.get_json()
        dossier_number = data.get('num_dossier')
        target_directory = data.get('repertoire_annonce')
        print ("##2-------------------------------",dossier_number,target_directory)
        """ if not dossier_number or not target_directory:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        """ 
        # Open file dialog to select .docx file
        def open_file_dialog():
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            file_path = filedialog.askopenfilename(filetypes=[("DOCX files", "*.docx")])
            root.destroy()  # Destroy the root window after file selection
            return file_path
        print ("##3------")
        file_path = open_file_dialog()
        
        if not file_path:
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        filename = secure_filename(f"{dossier_number}_CyrilSauret.docx")
        target_path = os.path.join(target_directory, filename)
        os.rename(file_path, target_path)
        
        return jsonify({"status": "success", "message": f"File saved as {filename} in {target_directory}"}), 200
    except Exception as e:
        print(f"an error occur when select file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500 

# ...existing code...

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
