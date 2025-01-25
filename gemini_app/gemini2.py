import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


instruction = (
    "You are a coding expert that specializes in front end interfaces. When I describe a component "
    "of a website I want to build, please return the HTML with any CSS inline. Do not give an "
    "explanation for this code."
)

model = genai.GenerativeModel(
    "models/gemini-1.5-flash", system_instruction=instruction
)

prompt = (
    "A flexbox with a large text logo aligned left and a list of links aligned right."
)
response = model.generate_content(prompt)
print(response.text)