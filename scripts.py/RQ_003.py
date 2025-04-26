from RQ_002 import query_file,fix_and_generate_pdf
from json_to_pdf import json_to_pdf
def experience_professionnelles():
    """Fonction principale avec interface en ligne de commande"""
   
    file_path ="G:/OneDrive/Entreprendre/Actions-4/M547/M547_source_.pdf"
    
    question = """Ce document est un résumé de mes réalisations professionnelles probantes, l'expérience n°1 est la plus ancienne, la 10 la plus récente.
    J'ai 57 ans, j'ai du mal à réussir les entretiens techniques pour des postes de développeur full stack car je n'ai pas vraiment d'expériences dans les stack techniques actuelles.

    Peux-tu me proposer des postes qui pourraient correspondre à mes expériences probantes ?

    Réponds UNIQUEMENT au format JSON suivant:
    {
      "propositions": [
        {
          "titre_poste": "Nom du poste proposé",
          "correspondance": "Explication détaillée de pourquoi ce poste me correspondrait bien",
          "competences_cles": ["Compétence 1", "Compétence 2", "Compétence 3"]
        },
        {
          "titre_poste": "Autre poste proposé",
          "correspondance": "Explication pour ce deuxième poste",
          "competences_cles": ["Compétence A", "Compétence B", "Compétence C"]
        }
      ]
    }

    Important: Respecte strictement ce format JSON et n'ajoute aucun texte avant ou après la structure JSON.
    """
    
    role = "En tant qu' expert ressources humaines dans le domaine informatique (développeur, Analyste, Testeur logiciel), analyse le texte suivant et réponds à cette question"
    output = "G:/OneDrive/Entreprendre/Actions-4/M547/M547_response_.json"
    output_pdf = "G:/OneDrive/Entreprendre/Actions-4/M547/M547_reponse.pdf"
    model = "mistral-large"  # Nom exact du modèle actuel
    
    print(f"dbg 1102 : Sauvegarder dans un fichier si demandé {output}")
   
   
    result = query_file(file_path, question, role, output, model)
    if result["status"] == "success":
       pdf_path = fix_and_generate_pdf(output, output_pdf) 
       json_to_pdf(output, output_pdf)
       #print(f"PDF generated successfully: {pdf_path}")

if __name__ == "__main__":
    experience_professionnelles()