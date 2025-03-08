from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download

# Authentification (si nécessaire)
# huggingface-cli login

# Télécharger le modèle et le tokenizer depuis Hugging Face
model_name = "mistralai/Mistral-7B-Instruct-v0.3"
local_model_path = snapshot_download(repo_id=model_name)

tokenizer = AutoTokenizer.from_pretrained(local_model_path)
model = AutoModelForCausalLM.from_pretrained(local_model_path)

# Préparez une requête
prompt = "Analyse cette offre d'emploi et extraits-en les compétences principales : ..."
inputs = tokenizer(prompt, return_tensors="pt")

# Générez une réponse
outputs = model.generate(**inputs, max_new_tokens=200)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)