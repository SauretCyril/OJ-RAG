from mistralai import Mistral
import requests
import numpy as np
import faiss
import os
from getpass import getpass
from dotenv import load_dotenv
import time
from tqdm import tqdm  # Pour afficher une barre de progression
import pickle
import hashlib

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

# Ajoutez au début de votre script pour vérifier si votre clé API est correcte
print(f"API Key définie: {'Oui' if api_key else 'Non'}")
if api_key:
    # Teste la connexion avec une requête simple
    try:
        test_response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": "Dis bonjour"}]
        )
        print("✅ API Mistral connectée avec succès!")
    except Exception as e:
        print(f"❌ Erreur de connexion API: {str(e)}")
        # Si erreur d'authentification, demander la clé
        if "401" in str(e):
            new_api_key = getpass("Entrez votre clé API Mistral: ")
            os.environ["MISTRAL_API_KEY"] = new_api_key
            client = Mistral(api_key=new_api_key)

response = requests.get('https://raw.githubusercontent.com/run-llama/llama_index/main/docs/docs/examples/data/paul_graham/paul_graham_essay.txt')
text = response.text

f = open('essay.txt', 'w')
f.write(text)
f.close()

chunk_size = 2048
chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
len(chunks)

def get_text_embedding_with_retry(input, max_retries=5, initial_delay=1):
    """Obtenir l'embedding avec gestion des limites de débit"""
    for attempt in range(max_retries):
        try:
            embeddings_batch_response = client.embeddings.create(
                model="mistral-embed",
                inputs=input
            )
            return embeddings_batch_response.data[0].embedding
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                # Délai exponentiel entre les tentatives
                sleep_time = initial_delay * (2 ** attempt)
                print(f"Rate limit atteint. Attente de {sleep_time} secondes avant nouvel essai...")
                time.sleep(sleep_time)
            else:
                raise e

def get_cache_key(text):
    """Générer une clé de cache basée sur le contenu"""
    return hashlib.md5(text.encode()).hexdigest()

def get_embedding_cached(text, cache_file="embeddings_cache.pkl"):
    """Obtenir l'embedding avec cache"""
    # Charger le cache
    cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            cache = pickle.load(f)
    
    # Générer une clé pour ce texte
    key = get_cache_key(text)
    
    # Vérifier si dans le cache
    if key in cache:
        print("Utilisation du cache pour cet embedding")
        return cache[key]
    
    # Sinon générer et mettre en cache
    print("Génération d'un nouvel embedding...")
    time.sleep(1)  # Petit délai pour respecter le rate limit
    embedding = get_text_embedding_with_retry(text)
    
    # Sauvegarder dans le cache
    cache[key] = embedding
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)
    
    return embedding

# 1. Modifiez votre boucle pour ajouter des délais entre les requêtes
print("Génération des embeddings...")
text_embeddings = []

for i, chunk in enumerate(chunks):
    print(f"Traitement du chunk {i+1}/{len(chunks)}")
    # Délai plus long entre les requêtes
    time.sleep(3)  # Attendez au moins 3 secondes entre les requêtes
    
    try:
        embedding = get_embedding_cached(chunk)
        text_embeddings.append(embedding)
    except Exception as e:
        print(f"Erreur sur le chunk {i}: {str(e)}")
        # Attendez plus longtemps en cas d'erreur avant de continuer
        print("Pause prolongée suite à une erreur...")
        time.sleep(10)
        
        # Réessayez une dernière fois
        try:
            embedding = get_text_embedding_with_retry(chunk, max_retries=3, initial_delay=5)
            text_embeddings.append(embedding)
        except:
            print(f"Échec définitif pour le chunk {i}, utilisation d'un embedding vide")
            # Si nécessaire, utilisez un embedding vide (array de zéros) pour ne pas bloquer
            if text_embeddings:  # S'il y a au moins un embedding réussi
                embedding = np.zeros_like(text_embeddings[0])
                text_embeddings.append(embedding)

# Convertir en array numpy à la fin
text_embeddings = np.array(text_embeddings)

import faiss

d = text_embeddings.shape[1]
index = faiss.IndexFlatL2(d)
index.add(text_embeddings)

question = "What were the two main things the author worked on before college?"
question_embeddings = np.array([get_text_embedding_with_retry(question)])

D, I = index.search(question_embeddings, k=2) # distance, index
retrieved_chunk = [chunks[i] for i in I.tolist()[0]]


prompt = f"""
Context information is below.
---------------------
{retrieved_chunk}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {question}
Answer:
"""

# Modifiez votre fonction run_mistral pour ajouter plus de détails
def run_mistral(user_message, model="mistral-small-latest", max_retries=3):
    """Exécuter une requête au modèle Mistral avec retry en cas d'erreur"""
    
    # Debug: Afficher le début du prompt
    print(f"Début du prompt: {user_message[:100]}...")
    print(f"Longueur du prompt: {len(user_message)} caractères")
    
    for attempt in range(max_retries):
        try:
            print(f"Tentative {attempt+1}: Envoi de la requête à Mistral (modèle: {model})...")
            start_time = time.time()
            
            messages = [{"role": "user", "content": user_message}]
            
            chat_response = client.chat.complete(
                model=model,
                messages=messages,
                temperature=0.7  # Ajout d'un paramètre de température explicite
            )
            
            end_time = time.time()
            print(f"✅ Réponse reçue en {end_time - start_time:.2f} secondes")
            
            return chat_response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Tentative {attempt+1}/{max_retries} échouée: {str(e)}")
            # Afficher l'erreur complète pour le debug
            import traceback
            traceback.print_exc()
            
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"Nouvel essai dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                print("Échec définitif après plusieurs tentatives.")
                raise e

# Appel avec gestion d'erreur
try:
    response = run_mistral(prompt)
    print("\n----- RÉPONSE DE L'IA -----")
    print(response)
    print("---------------------------\n")
except Exception as e:
    print(f"ERREUR FINALE: {str(e)}")