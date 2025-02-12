from flask import Flask, request, jsonify, render_template,Blueprint
import os
import json
import logging
from paths import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

requests = Blueprint('requests', __name__)

@requests.route('/list-requests', methods=['GET'])
def list_requests(): 
    
    list_RQ = []
    try:
        directory_path = GetDirRQ()
        defaultfile = os.path.join(directory_path, 'default.txt')
        if not os.path.exists(directory_path):
            #logger.info("Directory does not exist, creating: %s", directory_path)
            os.makedirs(directory_path)
            the_request = (
                "peux tu faire un résumer détaillé"
            )
            defaultfile = defaultfile.replace('\\', '/')
            #print("dbg1456-----", defaultfile)
            save_request_text(defaultfile,the_request)
        
        text_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
        #for each file in directory_path
        for file in text_files:
            file_path = os.path.join(directory_path, file)
            with open(file_path, 'r', encoding='utf-8') as thefile:
                list_RQ.append({
                    'fichier': file_path,
                    'name': file,
                    
                })
        
        return jsonify(list_RQ), 200
    except Exception as e:
        logger.error("Unable to scan directory: %s", str(e))
        return jsonify({"error": f"Unable to scan directory: {str(e)}"}), 500
    
    
    
    
def save_request_text(file_name, text_data):
    try:
       
        if not file_name or not text_data:
            return jsonify({'error': 'Missing file name or text data'}), 400
        #print("dbg897b :sauvegarde en cours ")
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(text_data)
        
        #logger.debug(f"Text saved successfully as {file_name}")
        return jsonify({'message': 'Text saved successfully'}), 200

    except Exception as e:
        logger.error(f"Error saving text: {str(e)}")
        return jsonify({'error': str(e)}), 500