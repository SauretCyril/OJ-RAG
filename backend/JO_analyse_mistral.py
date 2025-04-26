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
#from mistralai import Mistral
import requests
from dotenv import load_dotenv

import re
from jinja2 import Template
import pandas as pd
from datetime import datetime
import os

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

def create_excel_report(results, root_dir, subject):
    try:
        # 1. Créer le répertoire analyse s'il n'existe pas
        analyse_dir = os.path.join(root_dir, 'analyse')
        os.makedirs(analyse_dir, exist_ok=True)
        
        # 2. Préparer les données pour Excel
        excel_data = []
        for item in results:
            row = {'Fichier': item['file']}
            
            # Traitement différent selon que answer est un dict ou une string
            answer = item['answer']
            if isinstance(answer, dict):
                # Si c'est un dictionnaire, ajouter chaque clé comme colonne
                for key, value in answer.items():
                    # Gérer les listes en les joignant
                    if isinstance(value, list):
                        row[key] = ", ".join(value)
                    else:
                        row[key] = value
            else:
                # Si c'est une chaîne, mettre dans une colonne "Réponse"
                row['Réponse'] = answer
                
            excel_data.append(row)
            
        # 3. Créer un DataFrame pandas
        df = pd.DataFrame(excel_data)
        
        # 4. Générer un nom de fichier avec horodatage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"{subject}_{timestamp}.xlsx"
        excel_path = os.path.join(analyse_dir, excel_filename)
        
        try:
            # 5. Sauvegarder en Excel avec formatage
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Résultats')
                # Ajuster la largeur des colonnes
                worksheet = writer.sheets['Résultats']
                for i, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    ) + 2  # Ajouter un peu d'espace
                    worksheet.column_dimensions[chr(65 + i)].width = min(max_length, 50)  # Limiter à 50 pour éviter des colonnes trop larges
            print(f"Rapport Excel généré: {excel_path}")
            return excel_path
        except ImportError:
            # Si openpyxl n'est pas disponible, créer un CSV à la place
            csv_filename = f"analyse_{timestamp}.csv"
            csv_path = os.path.join(analyse_dir, csv_filename)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"Module openpyxl non disponible. Rapport CSV généré: {csv_path}")
            return csv_path
        
    except Exception as e:
        print(f"Erreur lors de la création du rapport: {str(e)}")
        return None

@mistral.route('/analyser_documents', methods=['POST'])
def analyser_documents():
    try:
        results = []
        data = request.get_json()
        directory = data.get('directory')
        question = data.get('question')
        role = data.get('role')
        subject = data.get('subject')
        type_doc=data.get('type_doc')
        
        filname = os.getenv('REA_FILE');
        dir = os.getenv('DIR_REA_FILE');
        output_file = os.path.join(dir, filname)
        root=GetRoot()
        #output_file_path = os.path.join(root,output_file)
        output_dir= os.path.join(directory,subject)
        output_file_name = os.path.join(output_dir, subject).replace('\\', '/')
        output_file_path = output_file_name+".json".replace('\\', '/')
        output_file_name=output_file_name.replace('\\', '/')
        output_file_path=output_file_path.replace('\\', '/')
        os.makedirs(output_dir, exist_ok=True)
        print(f"dbg_658a start processing directory {directory}")
        print(f"dbg_659b output {output_dir}")
        print(f"dbg_659c data {output_file_path}")
        
       
        #return jsonify({'status': 'error', 'message': 'Interruption'}), 299
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".docx"):
                    print(f"dbg_658 : traiter le fichier {file}")
                    file_path = os.path.join(root, file)
                    if type_doc == "docx":
                        text = extract_text_from_word(file_path)
                    
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
        
        # Créer le rapport Excel avec la fonction dédiée
        excel_path = create_excel_report(results, root,subject)
        
        # Return success response with results and file info
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(results)} files successfully',
            'output_file': output_file_path,
            'excel_report': excel_path,  # Ajout du chemin du fichier Excel
            'results_count': len(results),
            'results': results  # You can remove this if you don't want to send all results in the response
        }), 200
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



