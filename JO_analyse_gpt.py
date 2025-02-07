import os

from PyPDF2 import PdfReader
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import json

DEFAULT_CONTEXT = """
Je peux analyser une offre d'emploi pour :
- Identifier les compétences clés requises, telles que les langages de programmation (Python, Java, C++, etc.), les frameworks (Django, React, etc.), et les outils (Git, Docker, etc.)
- Évaluer le niveau attendu pour chaque compétence (débutant, intermédiaire, avancé)
- Détecter les technologies principales utilisées dans le poste (cloud computing, bases de données, etc.)
- Comprendre le contexte du poste, y compris les responsabilités et les tâches principales
- Vérifier l'adéquation entre le profil du candidat et les exigences du poste
- Suggérer des points d'attention pour le candidat, tels que les certifications ou les expériences spécifiques

Exemple d'offre d'emploi :
- Titre du poste : Développeur Full Stack
- Compétences requises : 
  - Langages de programmation : Python, JavaScript
  - Frameworks : Django, React
  - Outils : Git, Docker, Kubernetes
- Responsabilités :
  - Développer et maintenir des applications web
  - Collaborer avec les équipes de conception et de produit
  - Participer aux revues de code et aux tests
- Qualifications :
  - Diplôme en informatique ou domaine connexe
  - Expérience de 3 ans en développement web
  - Connaissance des pratiques DevOps
"""


def extract_text_from_pdf(pdf_path):
    try:
        if os.path.exists(pdf_path):
            ##print(f"-> le {pdf_path} fichier existe")
            text= ""
            
            # Utiliser PyPDF2 pour extraire le texte
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                text +="Le PDF est vide ou ne contient pas de texte extractible"
                return text
            
            # Ensure the text is properly encoded and decoded
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            
            #print(f"-> Text extrait: {text[:200]}...")
            return text
            
        #print(". Le fichier PDF n'existe pas")
    except Exception as e:
        print(f"An error occurred while extracting text from PDF: {e}")
        return ""

def extract_text_from_url(url):
    try:
        #print(f"-> Tentative d'extraction de texte depuis l'URL: {url}")
        
        # Récupérer le contenu de l'URL
        response = requests.get(url)
        #print(f"-> Statut de la réponse HTTP: {response.status_code}")
        response.raise_for_status()  # Vérifie si la requête a réussi
        
        # Parser le HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        #print("-> HTML parsé avec succès")
        
        # Supprimer les scripts et styles
        for script in soup(["script", "style"]):
            script.decompose()
        #print("-> Scripts et styles supprimés")
            
        # Extraire le texte
        text = soup.get_text(separator='\n')
        #print("-> Texte extrait du HTML")
        
        # Nettoyer le texte (supprimer les lignes vides multiples)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        #print("-> Texte nettoyé")
        
        if not text.strip():
            print("-> L'URL ne contient pas de texte extractible")
            return "L'URL ne contient pas de texte extractible"
            
        #print(f"-> Texte extrait de l'URL: {text[:200]}...")
        return text
        
    except Exception as e:
        print(f"Erreur lors de l'extraction depuis l'URL: {str(e)}")
        return f"Une erreur s'est produite: {str(e)}"


def extract_text(source, is_url=False):
    """
    Extrait le texte soit d'un PDF soit d'une URL
    """
    if is_url:
        return extract_text_from_url(source)
    else:
        return extract_text_from_pdf(source)


def get_answer(question, role,context=""):
    try:
        
        client = OpenAI()  # Assurez-vous que OPENAI_API_KEY est défini dans vos variables d'environnement
        full_context = f"""{role}: {question}\n\nContexte:\n{context}"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": full_context}
            ],
            temperature=0.8,
            max_tokens=1100
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"Erreur lors de l'analyse: {str(e)}")
        return f"Une erreur s'est produite: {str(e)}"


def favicon():
    return ""



'''
get info of pdf file and return'''
def get_info(file_path,role, question):
    try:
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Assurez-vous que OPENAI_API_KEY est défini dans vos variables d'environnement
        context = extract_text_from_pdf(file_path)
        if (context == ""):
            return "{'url':'', 'entreprise':'inconnue', 'poste':'Annonce non lisible'}"
        
        #print(f"Contexte extrait: {context[:200]}...")
        full_context = f"{question}\n\nContexte:\n{context}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "analyse le texte suivant et réponds à cette question, peux tu renvoyer les informations sous forme de données json, les champs son définie dans la question entre [ et ]"},
                {"role": "user", "content": full_context}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"Erreur lors de l'analyse: {str(e)}")
        return f"Une erreur s'est produite: {str(e)}"




def response_me(question,url,role):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Assurez-vous que OPENAI_API_KEY est défini dans vos variables d'environnement
        context=extract_text_from_url(url)
        if (context == ""):
            return "{'url':'', 'entreprise':'inconnue', 'poste':'Annonce non lisible'}"
        
        
        full_context = f"{question}\n\nContexte:\n{context}"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": full_context}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"Erreur lors de l'analyse: {str(e)}")
        return f"Une erreur s'est produite: {str(e)}"
