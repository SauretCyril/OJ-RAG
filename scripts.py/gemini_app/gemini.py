import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types


load_dotenv()
def generate_content(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    api_key = os.getenv("GEMINI_API_KEY")
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data, params={"key": api_key})

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def generate_image():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_image(
    model='imagen-3.0-generate-002',
    prompt='Fuzzy bunnies in my kitchen',
    config=types.GenerateImageConfig(
        negative_prompt= 'people',
        number_of_images= 1,
        include_rai_reason= True,
        output_mime_type= 'image/jpeg'
        )
    )
    response.generated_images[0].image.show()
   


def test_gemini():
    genai.configure(api_key="YOUR_API_KEY")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Explain how AI works in french")
    print(response.text)
    

def list_models():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    models = client.models.list_models()
    for model in models:
        print(model)


if __name__ == "__main__":
    """  prompt = "Explain how AI works, peux tu répondre en francais ?"
    result = generate_content(prompt)
    if result:
        print(result) """
    #generate_image()    
    list_models()
        

   
    

