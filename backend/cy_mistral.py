from docx import Document
import os
import json
from flask import Flask, jsonify, Blueprint

import logging
import httpx

import requests
from dotenv import load_dotenv

import pandas as pd
from datetime import datetime
import os
import base64
import time
import sys

from typing import List, Dict, Optional

# Charger les variables d'environnement
load_dotenv()

mistral = Blueprint('mistral', __name__)
# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def get_trez_score(texte):
    # Implémentez la logique pour obtenir le score Trez ici
    pass

def extract_text_from_word(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def _strip_code_fences(content: str) -> str:
    """Supprime les balises de code Markdown pour faciliter le parsing JSON."""
    cleaned = content.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return cleaned

def call_mistral_chat(
    messages: List[Dict[str, str]],
    model: str = "mistral-medium",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    max_retries: int = 3,
    backoff_seconds: float = 5.0,
) -> str:
    """Wrapper pour appeler l'API chat Mistral avec gestion du rate limiting."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("La cle API Mistral n'est pas definie dans le fichier .env")

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    last_exception: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            response_json = response.json()
            if "choices" in response_json and response_json["choices"]:
                return response_json["choices"][0]["message"]["content"]
            error_msg = response_json.get("error", "Reponse inattendue de l'API Mistral")
            raise ValueError(str(error_msg))
        except requests.exceptions.HTTPError as exc:
            last_exception = exc
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 429 and attempt < max_retries:
                retry_after = exc.response.headers.get("Retry-After") if exc.response is not None else None
                try:
                    wait_delay = float(retry_after) if retry_after else backoff_seconds * attempt
                except (TypeError, ValueError):
                    wait_delay = backoff_seconds * attempt
                wait_delay = max(1.0, min(wait_delay, 60.0))
                logger.warning(
                    "Mistral rate limit atteint (tentative %s/%s). Nouvelle tentative dans %.1f s.",
                    attempt,
                    max_retries,
                    wait_delay,
                )
                time.sleep(wait_delay)
                continue
            logger.error(f"Erreur HTTP lors de l'appel a l'API Mistral (statut {status_code}): {exc}")
            raise
        except requests.exceptions.RequestException as exc:
            last_exception = exc
            logger.error(f"Erreur reseau lors de l'appel a l'API Mistral: {exc}")
            raise
        except Exception as exc:
            last_exception = exc
            logger.error(f"Erreur lors de l'appel a l'API Mistral: {exc}")
            raise

    if last_exception is not None:
        if isinstance(last_exception, requests.exceptions.HTTPError):
            response = last_exception.response
            status_code = response.status_code if response is not None else None
            if status_code == 429:
                retry_after = response.headers.get('Retry-After') if response is not None else None
                hint = ''
                if retry_after:
                    hint = f" Veuillez patienter environ {retry_after} seconde(s) avant de reessayer."
                raise ValueError(
                    "Mistral a limite le nombre de requetes. Reessayez dans un instant." + hint
                ) from last_exception
        raise last_exception
    raise RuntimeError("Appel Mistral interrompu sans reponse ni exception.")


def analyze_comfyui_log_with_mistral(log_text: str) -> List[Dict[str, Optional[str]]]:
    """Analyse un log ComfyUI et renvoie une liste structurée d'erreurs."""
    if not log_text or not log_text.strip():
        return []

    role = "Expert Python, comfyuil et génération d'image via IA"
    instruction = (
        "Analyse les extraits de log ComfyUI fournis et renvoie un JSON conforme au schéma suivant :\n\n"
        "[\n"
        "  {\n"
        "    \"id\": \"identifiant court\",\n"
        "    \"timestamp\": \"horodatage ou null\",\n"
        "    \"resume\": \"description courte du problème\",\n"
        "    \"gravite\": \"critique\"/\"majeur\"/\"mineur\"/\"info\",\n"
        "    \"categorie\": \"type d'erreur ou module concerné\",\n"
        "    \"details\": \"explication concise\",\n"
        "    \"recommandation\": \"proposition d'action concrète\",\n"
        "    \"extrait\": \"portion significative du log\"\n"
        "  }\n"
        "]\n\n"
        "Ne renvoie que les anomalies pertinentes. Si aucune erreur n'est détectée, renvoie []."
    )
    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": f"{instruction}\n\nLOG:\n{log_text}"}
    ]

    raw_response = call_mistral_chat(messages, temperature=0.2, max_tokens=3000)
    cleaned = _strip_code_fences(raw_response)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(f"Analyse ComfyUI: JSON invalide renvoyé par Mistral: {exc}")
        raise ValueError("Impossible d'analyser la réponse de Mistral") from exc

    if isinstance(parsed, dict) and "errors" in parsed:
        parsed = parsed.get("errors", [])

    if not isinstance(parsed, list):
        raise ValueError("La réponse de Mistral n'est pas une liste d'erreurs.")

    sanitized = []
    for idx, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            continue
        sanitized.append({
            "id": item.get("id") or f"ERR-{idx:03d}",
            "timestamp": item.get("timestamp"),
            "resume": item.get("resume") or item.get("error") or "",
            "gravite": item.get("gravite") or item.get("severity"),
            "categorie": item.get("categorie") or item.get("category"),
            "details": item.get("details") or item.get("description"),
            "recommandation": item.get("recommandation") or item.get("recommendation"),
            "extrait": item.get("extrait") or item.get("snippet")
        })
    return sanitized

def chat_with_mistral(messages: List[Dict[str, str]], role: str = "Expert Python, comfyuil et génération d'image via IA", temperature: float = 0.4, max_tokens: int = 2000) -> str:
    """Délègue une conversation à Mistral avec un rôle spécifique."""
    convo = [{"role": "system", "content": role}] + messages
    return call_mistral_chat(convo, temperature=temperature, max_tokens=max_tokens)

def get_mistral_answer(question, role, texte):
    try:
        # Récupérer la clé API Mistral depuis les variables d'environnement
        print(f"Python utilisé dans cy_mistral.py : {sys.executable}")
        api_key = os.getenv("MISTRAL_API_KEY")
        
        if not api_key:
            raise ValueError("La clé API Mistral n'est pas définie dans le fichier .env")
        
        # Construire les messages pour l'API
        messages = [
            {"role": "system", "content": role},
            {"role": "user", "content": f"Contenu: {texte}\n\nQuestion: {question}"}
        ]
        
        # Configuration de la requête à l'API Mistral
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Données à envoyer à l'API Mistral
        data = {
            "model": "mistral-medium",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 9000  # Augmenter cette valeur (était 5000)
        }
        
        # Appel à l'API Mistral
        time.sleep(10)
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Ajoute cette ligne
        response_json = response.json()
        if "choices" in response_json and response_json["choices"]:
            content = response_json["choices"][0]["message"]["content"]
            print(f"dbg-678 : Réponse de l'API Mistral: {content}")
            return content
        else:
            # Retourner le message d'erreur de l'API si présent
            error_msg = response_json.get("error", "Réponse inattendue de l'API Mistral")
            return f'{{"error": "{error_msg}"}}'
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            print(f"dbg-678 : Trop de requêtes envoyées à l'API Mistral: {e}")
            return '{"error": "Trop de requêtes envoyées à l\'API Mistral. Merci de patienter avant de réessayer."}'
            print(f"dbg-678 : Erreur de l'API Mistral: {e}")
        return f'{{"error": "Erreur lors de l\'appel à l\'API Mistral: {str(e)}"}}'
    except Exception as e:
        print(f"dbg-678 : Erreur inattendue: {e}")
        return f'{{"error": "Erreur lors de l\'appel à l\'API Mistral: {str(e)}"}}'

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
                    answer =  get_mistral_answer(question, role, text)
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

def get_mistral_translate(text, src_lang="fr", tgt_lang="en"):
    """
    Utilise get_mistral_answer pour traduire du texte via un prompt.
    """
    question = f"Traduis le texte suivant du {src_lang} vers le {tgt_lang} :"
    role = "Tu es un traducteur professionnel. Réponds uniquement par la traduction, sans explication."
    content = text
    return  get_mistral_answer(question, role, content)



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
    