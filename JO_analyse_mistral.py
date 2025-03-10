from transformers import pipeline
from docx import Document
import os
import json
from flask import Flask, jsonify, Blueprint, request, render_template_string
from paths import GetRoot
import logging
import time
import textwrap
from functools import lru_cache
from mistralai import Mistral
import requests
from dotenv import load_dotenv

import re
from jinja2 import Template
# Charger les variables d'environnement
load_dotenv()

mistral = Blueprint('mistral', __name__)
# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def extract_text_from_word(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def get_mistral_answer(question, role, content):
    """
    Interroge l'API Mistral pour obtenir une réponse à une question basée sur un contenu.
    
    Args:
        question (str): La question à poser
        role (str): Le rôle que l'IA doit adopter
        content (str): Le contenu textuel sur lequel baser la réponse
        
    Returns:
        str: La réponse générée par le modèle Mistral
    """
    # Récupérer la clé API Mistral depuis les variables d'environnement
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        raise ValueError("La clé API Mistral n'est pas définie dans le fichier .env")
    
    # Construire les messages pour l'API
    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": f"Contenu: {content}\n\nQuestion: {question}"}
    ]
    
    # Configuration de la requête à l'API Mistral
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Données à envoyer à l'API Mistral
    data = {
        "model": "mistral-medium",  # Vous pouvez changer le modèle selon vos besoins
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        # Appel à l'API Mistral
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Lever une exception en cas d'erreur HTTP
        
        # Récupérer la réponse
        result = response.json()
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return answer
    
    except requests.exceptions.RequestException as e:
        # Gérer les erreurs de requête
        return f"Erreur lors de l'appel à l'API Mistral: {str(e)}"
    except json.JSONDecodeError:
        return f"Erreur de décodage de la réponse: {response.text}"

@mistral.route('/analyser_experiences', methods=['POST'])
def process_directory():
    try:
        results = []
        data = request.get_json()
        directory = data.get('directory')
        question = data.get('question')
        role = data.get('role')
        
        filname = os.getenv('REA_FILE');
        dir = os.getenv('DIR_REA_FILE');
        output_file = os.path.join(dir, filname)
        root=GetRoot()
        output_file_path = os.path.join(root,output_file)
        
        print(f"dbg_658a start processing directory {directory}")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".docx"):
                    print(f"dbg_658 : traiter le fichier {file}")
                    file_path = os.path.join(root, file)
                    text = extract_text_from_word(file_path)
                    answer = get_mistral_answer(question, role, text)
                    answer = answer.replace('\n', ' ').replace('\\', '').replace("\"", '"')
                    print(f"dbg_638a : answer = {answer}")
                    results.append({
                        "file": file,
                        "answer": answer
                    })
      # Sauvegarde des résultats dans un fichier
        for item in results:
            if 'answer' in item and isinstance(item['answer'], str):
                try:
                    # Parse the nested JSON string into an actual object
                    item['answer'] = json.loads(item['answer'])
                except json.JSONDecodeError:
                # If it's not valid JSON, leave it as is
                    pass
        if output_file:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        
        # Return success response with results and file info
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(results)} files successfully',
            'output_file': output_file_path,
            'results_count': len(results),
            'results': results  # You can remove this if you don't want to send all results in the response
        }), 200
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



