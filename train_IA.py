import json
import os
from PyPDF2 import PdfReader
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from flask import Flask, request, jsonify

# Charger le modèle et le tokenizer
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Fonction pour extraire le texte des fichiers PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Fonction pour vérifier les redondances
def is_redundant(response, responses):
    for existing_response in responses:
        if response['response'] == existing_response['response']:
            return True
    return False

# Fonction pour traiter les documents et répondre aux questions
def process_documents(directory, question):
    responses = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            elif file.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    text = json.dumps(data)
            else:
                continue

            response = get_answer(text, question)
            response_entry = {
                'file': file,
                'response': response
            }

            if not is_redundant(response_entry, responses):
                responses.append(response_entry)
    return responses

# Fonction pour obtenir la réponse à une question donnée
def get_answer(context, question):
    input_text = f"Context: {context}\nQuestion: {question}\nAnswer:"
    inputs = tokenizer.encode(input_text, return_tensors='pt')
    outputs = model.generate(inputs, max_length=512, num_return_sequences=1)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer

# Fonction pour agréger les fichiers JSON
def aggregate_json_files(directory):
    aggregated_data = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                parent_dir = os.path.basename(root)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['annonce_id'] = parent_dir  # Ajouter l'identifiant de l'annonce
                    aggregated_data.append(data)
    return aggregated_data

# Fonction pour sauvegarder les données agrégées dans un fichier JSON
def save_aggregated_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Créer une application Flask pour exposer l'API
app = Flask(__name__)

@app.route('/process_announcements', methods=['POST'])
def process_announcements():
    question = request.json.get('question')
    directory = os.getenv("ANNONCES_FILE_DIR")
    responses = process_documents(directory, question)
    return jsonify(responses)

if __name__ == '__main__':
    # Exemple d'appel avec une question
    example_question = "Quels sont les principaux langages de programmation mentionnés dans les annonces ?"
    example_directory = "path/to/your/announcements/directory"
    
    # Assurez-vous que la variable d'environnement est définie
    os.environ["ANNONCES_FILE_DIR"] = example_directory
    
    # Appeler la fonction process_documents directement
    example_responses = process_documents(example_directory, example_question)
    
    # Afficher les réponses
    for response in example_responses:
        print(f"File: {response['file']}")
        print(f"Response: {response['response']}")
        print("-----")
    
    # Lancer l'application Flask
    app.run(debug=True)