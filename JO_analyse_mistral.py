from transformers import pipeline
from docx import Document
import os
import json
from flask import Flask, jsonify
import logging

def extract_text_from_word(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

  
def get_mistral_answer(question, role, context=""):
    try:
        #print("dbg A023c - Utilisation d'une approche par chunks avec formatage JSON")
        
        # Guard against empty context
        
            
        # Limiter le contexte pour éviter les problèmes
        # max_context_length = 2000
        # if len(context) > max_context_length:
        #     print(f"dbg A023d - Contexte tronqué de {len(context)} à {max_context_length} caractères")
        #     context = context[:max_context_length]
        #print ("debg 675a - contexte = ",context)
        #print ("debg 675b - role = ",role)
        #print ("debg 675c - question = ",question)
        try:
            # Utilisez une instruction explicite pour générer du JSON valide
            prompt = f"""
            {role}

            Question: {question}

            Contexte: {context}
"""
            
            
            # Utiliser l'API Hugging Face pour accéder à Mistral
            from huggingface_hub import InferenceClient
            client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2")
            
            # Générer la réponse
            response = client.text_generation(
                prompt,
                max_new_tokens=600,
                temperature=0.1,
                do_sample=True
            )
            #print (f"debg 675d - Réponse brute: {response}")
            
            # Essayer de parser la réponse comme JSON
            #import re
            
        
            return response
            
        except Exception as model_error:
            print(f"dbg A023e - Erreur avec le modèle: {str(model_error)}")
            # Fallback en cas d'erreur
           
            
    except Exception as e:
        print(f"dbg 2154 : Erreur lors de l'analyse: {str(e)}")
        # Même en cas d'erreur majeure, on renvoie un JSON valide
      
question = "peux tu annalyser la réalisation et extraire les informations suivantes :"
question+="-déterminer le context [contexte], "
question+="-trouver le titre [titre], "
question+="-le résultat obtenu [résultat], "
question+="-les savoir-faire [savoir-faire], "  
question+="-les savoir-être [savoir-être]."


def process_directory(directory, question, role, output_file):
    results = []
    
    print(f"dbg_658a start processing directory {directory}")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".docx"):
                print(f"dbg_658 : traiter le fichier {file}")
                file_path = os.path.join(root, file)
                text = extract_text_from_word(file_path)
                answer = get_mistral_answer(question, role, text)
               
                # Extract specific sections from the text
                """  context = extract_section(text, "Contexte de réalisation")
                main_steps = extract_section(text, "Les principales étapes")
                result = extract_section(text, "Le résultat obtenu") """
                
                """ # Get savoir-faire and savoir-être
                savoir_faire = get_mistral_answer("Quels sont les savoir-faire démontrés ?", role, text)
                savoir_etre = get_mistral_answer("Quels sont les savoir-être démontrés ?", role, text) """
                
                """  result_entry = {
                    "nom du doc": file,
                    "titre de la réalisation": answer,
                    "résumé du context": context,
                    "résultat obtenu": result,
                    "savoir-faire": savoir_faire,
                    "savoir-être": savoir_etre
                } """
                print (f"dbg_638a : answer = {answer}")
                results.append(answer)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def analyser_experiences():
    try:
        directory = "G:/OneDrive/Entreprendre/Actions-4/M488/RDV.6_Du_28-02-2025/Realisations"
        question = "Quelle est la réalisation professionnelle de ce document ?"
        role = "En tant qu'expert en recrutement, analysez le texte suivant et répondez à la question."
        output_file = "resultats.json"
        process_directory(directory, question, role, output_file)
        return jsonify({'status': 'success', 'message': 'Analysis completed successfully'}), 200
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500





