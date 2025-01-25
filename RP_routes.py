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
import logging
from logging import DEBUG
import aiofiles

routes = Blueprint('routes', __name__)
logging.basicConfig(level=DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define excluded directories
EXCLUDED_DIRECTORIES = ["suivi", "pile", "conf"]  # Add your excluded directories here

# Load shared constants
def load_constants():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'constants.json')
    with open(config_path, 'r') as f:
        return json.load(f)

CONSTANTS = load_constants()
#print('Loaded constants:', CONSTANTS)
@routes.route('/get_constants', methods=['GET'])
def get_constants():
    return jsonify(CONSTANTS)

def get_cookie_value(cookie_name):
    cookies = request.cookies
    return cookies.get(cookie_name, 'default')

@routes.route('/read_annonces_json', methods=['POST'])
async def read_annonces_json():
    try:
        data = request.get_json()
        excluedFile = data.get('excluded')
        directory_path = os.getenv("ANNONCES_FILE_DIR")
        if not os.path.exists(directory_path):
            return []

        annonces_list = []
        crit_annonces = load_crit_annonces(excluedFile)
        #print(f"RP-0 scan repertoire annonces for--------------------------------")
        #print(f"###-0 ")
        for root, _, files in os.walk(directory_path):
            parent_dir = os.path.basename(root)
            if parent_dir in EXCLUDED_DIRECTORIES:
                #print(f"RP-1 --Skipping directory: {parent_dir}")
                continue
                

            #print(f"RP-2 ------repertoire {root}")
            
            file_annonce = parent_dir + CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']
            file_annonce_steal=parent_dir + CONSTANTS['FILE_NAMES']['STEAL_ANNONCE_SUFFIX']
            file_annonce_path = os.path.join(root, file_annonce)
            
            # résumé gpt
            file_isGptResum = parent_dir + CONSTANTS['FILE_NAMES']['GPT_REQUEST_SUFFIX']
            file_isGptResum_Path1 = os.path.join(root, file_isGptResum)
            file_isGptResum_Path1 = file_isGptResum_Path1.replace('\\', '/')
            
           
            
            # CV 
            file_cv = parent_dir + CONSTANTS['FILE_NAMES']['CV_SUFFIX'] + ".docx"
            
            file_cv_pdf = parent_dir + CONSTANTS['FILE_NAMES']['CV_SUFFIX'] + ".pdf"
            
            file_cv_New = parent_dir + CONSTANTS['FILE_NAMES']['CV_SUFFIX_NEW'] + ".docx"
            file_cv_pdf_New = parent_dir + CONSTANTS['FILE_NAMES']['CV_SUFFIX_NEW'] + ".pdf"
            data_json_file = ".data.json" 
             
            #file_cv_Path = os.path.join(root, file_cv.replace('\\', '/'))
            record_added = False
            data = {}
            isCVin="N"
            isCVinpdf="N"
            isSteal="N"
            isJo="N"
            file_path_steal=""
            file_path_isJo=""
            isGptResum=""
           
            list_RQ = {}
            for filename in files:
                
               
                   #print ("dbg4625-------filename=file_annonce",data_json_file)
                if filename  == file_cv or filename == file_cv_New:
                    isCVin="O"
                    #print("###---->BINGO")
                if filename  == file_cv_pdf or filename == file_cv_pdf_New:
                    isCVinpdf="O"
                
                if (filename ==  file_annonce_steal):
                    isSteal="O"
                    file_path_steal = os.path.join(root, file_annonce_steal)
                  
                else :      
                    if (filename ==  file_annonce):
                        isJo="O"
                        file_path_isJo = os.path.join(root, file_annonce)
                   
                    else:
                        if (filename ==  file_isGptResum ):
                            isGptResum="O"
                            file_path_gpt = os.path.join(root, file_isGptResum)
                            
                            file_gpt_name= parent_dir+CONSTANTS['FILE_NAMES']['GPT_REQUEST_SUFFIX_NAME']
                            file_gpt_name_pdf=os.path.join(root,file_gpt_name+".pdf").replace('\\', '/') 
                            file_path_RQ=os.path.join(root,file_gpt_name+"RQ.txt").replace('\\', '/')
                            
                            index = 1
                            while os.path.exists(file_gpt_name_pdf):
                                list_RQ[index] = {"reponse":file_gpt_name_pdf,"question":file_path_RQ,"exist":os.path.exists(file_path_RQ)}
                                file_gpt_name_pdf = os.path.join(file_path, f"{file_gpt_name}({index}).pdf").replace('\\', '/')
                                file_path_RQ =os.path.join(file_path, f"{file_gpt_name}({index})_RQ.txt").replace('\\', '/')
                                index += 1
                            #print ("----file_path_gpt_name    ==", list_RQ)
                           
                            
                  
            for filename in files:
                file_path = os.path.join(root, filename)
                file_path = file_path.replace('\\', '/')  # Normalize path
                file_path_nodata=os.path.join(root, ".data.json")
                file_path_nodata =file_path_nodata.replace('\\', '/') 
                
                if filename == ".data.json":
                    record_added = True
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
                                # block ctrl document
                                data["isJo"] = isJo
                                data['isSteal'] = isSteal
                                data["GptSum"] = isGptResum
                                data["CV"] = isCVin
                                data["CVpdf"] = isCVinpdf
                                data["list_RQ"]=list_RQ
                                jData = {file_path: data}
                                annonces_list.append(jData)
                                """  with open(file_path, 'w', encoding='utf-8') as file:
                                    json.dump(jData, file, ensure_ascii=False, indent=4) """
                            

                    except json.JSONDecodeError:
                        errordata = {"id": parent_dir, "description": "?", "etat": "invalid JSON"}
                        print(f"Cyr_Error: The file {file_path} contains invalid JSON.")
            #print(f"RP-7 ------dossier {parent_dir}-----data json = {isData_json_file}")   
            Piece_exist=False
            
            if not record_added:
                #print ("RP-7234  fichier .data.json :", isData_json_file)
                thefile=""
                Piece_exist=False
                
                    
                if isSteal =="O":
                    thefile= file_path_steal
                    #print ("###-4 file_path_steal trouvé = ",file_path_steal)
                    Piece_exist=True
                else :
                        if isJo =="O":
                            thefile= file_path_isJo
                            #print ("###-5 file_path_isJo trouvé = ",file_path_isJo)
                            Piece_exist=True
                        else:
                            if isGptResum =="O":
                                thefile =file_path_gpt
                                Piece_exist=True
                
                if Piece_exist:
                    
                    try:
                        print ("RP-7245 le fichier annonce va être traité = ",thefile)
                        thefile = thefile.replace('\\', '/')

                        # Use the value of 'current_instruction' from cookies
                        current_instruction = get_cookie_value('current_instruction')
                        if not current_instruction:
                           current_instruction="default"
                            
                        the_request = load_CRQ_text(current_instruction)
                        
                        print("RP-2158", the_request)  
                         
                        infos = get_info(thefile,the_request)
                        print ("RP-9 infos = ",infos)    
                        if (infos):
                            infos = json.loads(infos)  # Parse the JSON response 
                            data["url"] = infos["url"]
                            data["dossier"] = parent_dir    
                            #print("DBG-234 -> url: %s" % infos["url"])
                            # block ctrl document
                            data["isJo"] = isJo
                            data['isSteal'] = isSteal
                            data["GptSum"] = isGptResum
                            data["Date"] = infos["Date"]
                            data["CV"] = isCVin
                            data["CVpdf"] = isCVinpdf
                            # block info piece         
                            data["entreprise"] = infos["entreprise"]
                            data["description"] = infos["poste"]
                            data["Lieu"] = infos["lieu"]  
                            data["etat"] = "New"
                            data["list_RQ"]=list_RQ
                            data["instructions"]=the_request
                            print("DBG-234 -> file_path_nodata: " + file_path_nodata)
                            print("DBG-5487 -> file_path: " + file_path) 
                            jData = {file_path_nodata:data}  
                            
                            annonces_list.append(jData)
                            record_added = True
                            #file_path_nodata = file_path_nodata.replace('\\', '/')  # Normalize path
                            with open(file_path_nodata, 'w', encoding='utf-8') as file:
                                json.dump(data, file, ensure_ascii=False, indent=4)
                    except Exception as e:   
                        print(f"Cyr_Error 14578: An error occurred while trying to retrieve information from {thefile}: {str(e)}")
                        return []
                 
                
               
                                
        return annonces_list 
    except Exception as e:
        print(f"Cyr_error_145 An unexpected error occurred while reading annonces: {e}")
        return []

def load_crit_annonces(excluedFile):
    try:
        #file="excluded_annonces.json"
        config_path = os.path.join(os.getenv("ANNONCES_DIR_STATE"), excluedFile)
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
        print(f"##-9998-saving filters to {file_path}")    
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
        
        filename = secure_filename(f"{dossier_number}_CV_CyrilSauret.docx")
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

@routes.route('/list-CRQ-files', methods=['GET'])
async def list_CRQ_files():
    list_CRQ = []
    try:
        directory_path = os.getenv("DIR_CRQ_FILE")
        defaultfile = os.path.join(directory_path, 'default.txt')
        if not os.path.exists(directory_path):
            logger.info("Directory does not exist, creating: %s", directory_path)
            os.makedirs(directory_path)
            the_request = (
                " -peux tu trouver : l'url référence de l'annonce ['url'], l'url peut aussi se trouver entre <- et ->, "
                "-l'entreprise [entreprise], "
                "-le titre ou l'intiltulé [poste] du poste à pourvoir (ce titre ne doit pas dépasser 20 caractères), "
                "-la localisation ou lieu dans lieux [lieu], "
                "-la date de publication ou d'actualisation [Date]"
            )
            defaultfile = defaultfile.replace('\\', '/')
            print("dbg1456-----", defaultfile)
            await save_CRQ_text(defaultfile,the_request)
        
        text_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
        #for each file in directory_path
        for file in text_files:
            file_path = os.path.join(directory_path, file)
            with open(file_path, 'r', encoding='utf-8') as thefile:
                list_CRQ.append({
                    'fichier': file_path,
                    'name': file,
                    
                })
        
        return jsonify(list_CRQ), 200
    except Exception as e:
        logger.error("Unable to scan directory: %s", str(e))
        return jsonify({"error": f"Unable to scan directory: {str(e)}"}), 500

# ...existing code...

#@routes.route('/save-CRQ-text', methods=['POST'])
async def save_CRQ_text(file_name,text_data):
    try:
        #file_name = request.json.get('file_name')
        #text_data = request.json.get('text_data')
        
        if not file_name or not text_data:
            return jsonify({'error': 'Missing file name or text data'}), 400

        async with aiofiles.open(file_name, 'w', encoding='utf-8') as file:
            await file.write(text_data)
        logger.debug(f"Text saved successfully as {file_name}")
        return jsonify({'message': 'Text saved successfully'}), 200

    except Exception as e:
        logger.error(f"Error saving text: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ...existing code...

#@routes.route('/load-CRQ-text', methods=['POST'])
def load_CRQ_text(file_name):
    try:
        text=""
        file_name_txt = file_name+".txt"
        filepath = os.path.join(os.getenv('DIR_CRQ_FILE'), file_name_txt)
        filepath = filepath.replace('\\', '/')
        
        print("dbg789 :fichier instructions",filepath)
        if os.path.exists(filepath):
            if not file_name:
                return jsonify({'error tre245': 'Missing file name'}), 400

            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        
        return text

    except Exception as e:
        logger.error(f"Error loading text: {str(e)}")
        return ""
