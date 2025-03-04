import requests

def query_mistral_ai(prompt, api_key):
    url = "https://api.mistral.ai/v1/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 150
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Exemple d'utilisation
api_key = "votre_cle_api"
prompt = "Quelle est la capitale de la France ?"
result = query_mistral_ai(prompt, api_key)
if 'generated_text' in result:
    print("Response:", result['generated_text'])
else:
    print("Error:", result)