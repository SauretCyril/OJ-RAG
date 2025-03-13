from docx import Document
import os
import json
from flask import Flask, jsonify, Blueprint

import logging


import requests
from dotenv import load_dotenv

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
        "model": "mistral-medium",  # Au lieu de mistral-large
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2500
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

def create_excel_report(results, output_file_name):
    try:
        # 1. Créer le répertoire analyse s'il n'existe pas
        #analyse_dir = os.path.join(root_dir, 'analyse')
        #os.makedirs(analyse_dir, exist_ok=True)
        
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
        excel_filename = f"{output_file_name}_{timestamp}.xlsx"
        #excel_path = os.path.join(analyse_dir, excel_filename)
        
        try:
            # 5. Sauvegarder en Excel avec formatage
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Résultats')
                # Ajuster la largeur des colonnes
                worksheet = writer.sheets['Résultats']
                for i, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(col)
                    ) + 2  # Ajouter un peu d'espace
                    worksheet.column_dimensions[chr(65 + i)].width = min(max_length, 50)  # Limiter à 50 pour éviter des colonnes trop larges
            print(f"Rapport Excel généré: {excel_filename}")
            return excel_filename
        except ImportError:
            # Si openpyxl n'est pas disponible, créer un CSV à la place
            csv_filename = f"{excel_filename}_{timestamp}.csv"
            #csv_path = os.path.join(analyse_dir, csv_filename)
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"Module openpyxl non disponible. Rapport CSV généré: {csv_filename}")
            return csv_filename
        
    except Exception as e:
        print(f"Erreur lors de la création du rapport: {str(e)}")
        return None

# Modifiez la fin de la fonction analyser_documents pour un usage standalone
def analyser_documents(directory,subject,type_doc_source,question,role):
    try:
        results = []
        #data = request.get_json()
        #directory = data.get('directory')
        #question = data.get('question')
        #role = data.get('role')
        #subject = data.get('subject')
        #type_doc=data.get('type_doc')
        
        
        print(f"dbg_658a start processing directory {directory}")
        
        '''repertoire de destination du fichier json et annalyse'''
        output_dir = os.path.join(directory, "mistral_analyse").replace('\\', '/') 
        os.makedirs(output_dir, exist_ok=True)
        print(f"dbg_659c data { output_dir}")
        
        '''fichier de data json'''
        output_file_name = os.path.join(output_dir, subject).replace('\\', '/') 
        
        output_file_path = f"{output_file_name}.json"
        print(f"dbg_659d data {output_file_path}")
        
        user_confirmation = input("Voulez-vous continuer avec l'analyse des documents ? (o/n): ")
        if user_confirmation.lower() != 'o':
            print("Analyse annulée par l'utilisateur.")
            exit(0)
        #return jsonify({'status': 'error', 'message': 'Interruption'}), 299
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".docx"):
                    print(f"dbg_658 : traiter le fichier {file}")
                    file_path = os.path.join(root, file)
                    if type_doc_source == "docx":
                       text = extract_text_from_word(file_path)
                    
                    else:
                        print(f"dbg_118 : type de document non pris en charge : {type_doc_source}")
                        exit(0)
                    if not text:
                       
                        print(f"dbg_119 : texte vide: {file_path}")
                        results.append({
                        "file": file,
                        "answer": "N/A : texte vide"
                        })
                        continue
                    answer = get_mistral_answer(question, role, text)
                    answer = answer.replace('\n', ' ').replace('\\', '').replace("\"", '"')
                    #print(f"dbg_638a : answer = {answer}")
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
        if output_file_path:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=4)
        
        # Créer le rapport Excel avec la fonction dédiée
        excel_path = create_excel_report(results, output_file_name)
        
        # Au lieu de jsonify, retournez simplement un dictionnaire
        if "__main__" == __name__:
            print(f"Traitement terminé avec succès! {len(results)} fichiers traités.")
            print(f"Fichier JSON: {output_file_path}")
            print(f"Rapport Excel: {excel_path}")
            return {
                'status': 'success',
                'message': f'Processed {len(results)} files successfully',
                'output_file': output_file_path,
                'excel_report': excel_path,
                'results_count': len(results)
            }
        else:
            # Cette partie est utilisée quand appelée depuis Flask
            return jsonify({
                'status': 'success',
                'message': f'Processed {len(results)} files successfully',
                'output_file': output_file_path,
                'excel_report': excel_path,
                'results_count': len(results),
                'results': results
            }), 200
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        if "__main__" == __name__:
            print(f"Erreur: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        else:
            return jsonify({'status': 'error', 'message': str(e)}), 500



if __name__ == '__main__':
    #Question à poser aux documents
    subject = "Realisations_analyses"
    type_doc_source="docx"
    question = "Analyse cette réalisation et extrait les informations suivantes sous format JSON structuré:"
    question+="{"
    question+='"contexte": "description du contexte de la mission",'
    question+='"titre": "intitulé du poste ou de la mission",'
    question+='"result": "résultats obtenus",'
    question+='"savoir_faire": ["compétence technique 1", "compétence technique 2"],'
    question+='"savoir_etre": ["qualité comportementale 1", "qualité comportementale 2"]'
    question+="}"
    question+="Respecte strictement ce format pour permettre le parsing JSON."

    directory = "G:/OneDrive/Entreprendre/Actions-4/M488/RDV.6_Du_28-02-2025/Realisations"
    role = "En tant qu'expert en recrutement, analyse ce document et réponds au format demandé."
    
    # Dans la partie __main__ de votre script
    if not os.path.exists(directory):
        print(f"ERREUR: Le répertoire {directory} n'existe pas!")
        exit(1)
        
    print(f"Analyse des documents dans: {directory}")
    print(f"Sujet: {subject}")
    print(f"Question: {question}")

    analyser_documents(directory,subject,type_doc_source,question,role)