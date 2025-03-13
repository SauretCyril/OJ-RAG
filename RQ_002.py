import os

import json
from mistralai.client import MistralClient  # Correct

from dotenv import load_dotenv
import time
import logging
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import re
from RQ_001 import  get_mistral_answer
# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement

  


def query_file(file_path, question, role, output_file=None, model="mistral-small"):
        """Analyse un fichier local avec Mistral au lieu d'une URL"""
        try:
            # Déterminer le type de fichier
            file_extension = os.path.splitext(file_path)[1].lower()
            
            # Extraire le contenu selon le type de fichier
            if file_extension == '.pdf':
                # Pour les fichiers PDF
                content = extract_text_from_pdf(file_path)
                #print (f"dbg 1101a.content: {content}")
            
            
                answer = get_mistral_answer(question, role, content)
                answer = answer.replace('\n', ' ').replace('\\', '').replace("\"", '"')
                print (f"dbg 1101b.answer: {answer}")
            

                # Préparer le résultat
                result = {
                    "status": "success",
                    "file": file_path,
                    "question": question,
                    "role": role,
                    "model": model,
                    "answer": answer
                }
          
              
            # Sauvegarder dans un fichier si demandé
            if output_file:
    # Si la réponse est une chaîne JSON
                try:
                    # Essayer de parser la réponse comme JSON
                    answer_obj = json.loads(answer)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(answer_obj, f, ensure_ascii=False, indent=4)
                   
                except:
                    # Sinon écrire telle quelle
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(answer, f, ensure_ascii=False, indent=4)
                
                #fix_json_file(output_file)
                return result
            else:
                return {"status": "error", "message": "dbg_234 : Format de fichier non pris en charge"}
        
        except Exception as e:
            logger.error(f"dbg_235 Erreur lors de l'analyse du fichier: {str(e)}")
            return {"status": "error", "message": "dbg_235 : "+ str(e)}

def extract_text_from_pdf( pdf_path):
    """Extraire le texte d'un fichier PDF"""
    try:
        import PyPDF2
            
        logger.info(f"Extraction du texte depuis le PDF: {pdf_path}")
        text = ""
            
        # Ouvrir le PDF en mode binaire
        with open(pdf_path, 'rb') as pdf_file:
                # Créer un lecteur PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extraire le texte de chaque page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
            
        logger.info(f"Extraction réussie: {len(text)} caractères extraits")
        return text
    except ImportError:
            # Si PyPDF2 n'est pas installé, suggérer l'installation
            logger.error("PyPDF2 n'est pas installé. Installez-le avec 'pip install PyPDF2'")
            raise ImportError("PyPDF2 n'est pas installé. Installez-le avec 'pip install PyPDF2'")
    except Exception as e:
            logger.error(f"dbg_236-Erreur lors de l'extraction du texte du PDF: {str(e)}")
            return f"dbg_236-Erreur lors de l'extraction du texte: {str(e)}"



def generate_pdf_from_json(json_file_path, pdf_output=None):
    """
    Génère un fichier PDF structuré à partir d'un fichier JSON contenant une analyse.
    Utilise directement les objets ReportLab pour les expériences professionnelles.
    """
    try:
        # Déterminer le nom du fichier PDF de sortie
        if pdf_output is None:
            pdf_output = os.path.splitext(json_file_path)[0] + ".pdf"
        
        # Lire le fichier JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            pdf_output,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Utiliser vos styles existants
        styles = getSampleStyleSheet()
        
        # Vérifier que les styles personnalisés sont définis
        if 'Title' not in styles:
            styles.add(ParagraphStyle(
                name='Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.darkblue
             ))

        if 'Heading2Custom' not in styles:
            styles.add(ParagraphStyle(
                name='Heading2Custom',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.darkblue
            ))
        
        if 'NormalCustom' not in styles:
            styles.add(ParagraphStyle(
                name='NormalCustom',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            ))
        
        if 'List' not in styles:
            styles.add(ParagraphStyle(
                name='List',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=20,
                spaceAfter=3
            ))
        
        if 'Info' not in styles:
            styles.add(ParagraphStyle(
                name='Info',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.darkgrey,
                spaceAfter=10
            ))
        
        # Contenu du PDF
        story = []
        
        # Titre
        title_text = "Analyse de profil professionnel"
        story.append(Paragraph(title_text, styles['Title']))
        story.append(Spacer(1, 0.5*cm))
        
        # Section d'informations sur la requête
        info_table_data = [
            ["Question", data.get('question', 'N/A')],
            ["Rôle", data.get('role', 'N/A')],
            ["Modèle utilisé", data.get('model', 'N/A')]
        ]
        
        info_table = Table(info_table_data, colWidths=[doc.width*0.3, doc.width*0.7])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 1*cm))
        
        # Extraire la réponse comme avant
        if isinstance(data, dict) and "answer" in data:
            answer = data.get("answer", "")
        else:
            answer = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Pour le cas des expériences professionnelles structurées
        if isinstance(answer, str) and "experiences" in answer:
            try:
                # Essayer de parser comme JSON
                answer_obj = json.loads(answer)
                # Ajouter l'accroche si elle existe
                if "accroche" in answer_obj:
                    accroche = answer_obj["accroche"]
                    story.append(Paragraph("Accroche", styles['Heading2Custom']))
                    story.append(Paragraph(accroche, styles['NormalCustom']))
                    story.append(Spacer(1, 0.5*cm))
                # Ajouter un titre pour la section des expériences
                story.append(Paragraph("Expériences Professionnelles", styles['Heading2Custom']))
                story.append(Spacer(1, 0.5*cm))
                
                # Pour chaque expérience, créer les objets PDF directement
                for i, exp in enumerate(answer_obj.get("experiences", [])):
                    # Titre de l'expérience
                    story.append(Paragraph(exp.get('titre', 'Sans titre'), styles['Heading2Custom']))
                    
                    # Tableau d'informations sur l'expérience
                    exp_info = [
                        ["Entreprise", exp.get('entreprise', 'N/A')],
                        ["Période", exp.get('dates', 'N/A')],
                        ["Contexte", exp.get('context', 'N/A')],
                        ["Savoir faire", ', '.join(exp.get('savoir_faire', [])) if isinstance(exp.get('savoir_faire', []), list) else exp.get('savoir_faire', 'N/A')]
                        # ["Savoir être", get_skill_value(exp, ['savoir_etre', 'savoirEtre', 'savoir être', 'savoir-être'])]
                    ]
                    
                    exp_table = Table(exp_info, colWidths=[doc.width*0.2, doc.width*0.7])
                    exp_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    
                    story.append(exp_table)
                    story.append(Spacer(1, 0.3*cm))
                    
                    # Description avec traitement spécifique
                    desc = exp.get('description', 'N/A')
                    story.append(Paragraph("Taches:", styles['Heading2Custom']))
                    
                    # Traitement différent selon le type de description
                    if isinstance(desc, dict) and "taches" in desc:
                        # Liste à puces directe
                        list_items = []
                        for tache in desc.get("taches", []):
                            list_items.append(ListItem(Paragraph(tache, styles['List'])))
                        
                        if list_items:
                            story.append(ListFlowable(list_items, bulletType='bullet', start=None))
                    elif isinstance(desc, str):
                        # Pour une description texte simple
                        story.append(Paragraph(desc, styles['NormalCustom']))
                    
                    # Espace entre les expériences
                    story.append(Spacer(1, 0.8*cm))
            
            except Exception as e:
                logger.error(f"Erreur lors du formatage direct des expériences: {str(e)}")
                # En cas d'échec, utiliser la fonction structure_answer existante
                structured_items = structure_answer(answer)
                story.extend(structured_items)
        else:
            # Pour le contenu non structuré, utiliser structure_answer comme avant
            structured_items = structure_answer(answer)
            story.extend(structured_items)
        
        # Pied de page
        story.append(Spacer(1, 1*cm))
        footer = Paragraph("Document généré automatiquement par Mistral AI", styles['Info'])
        story.append(footer)
        
        # Générer le PDF
        doc.build(story)
        
        logger.info(f"PDF généré avec succès: {pdf_output}")
        return pdf_output
        
    except Exception as e:
        logger.error(f"dbg_238- Erreur lors de la génération du PDF: {str(e)}")
        return None



def fix_json_file(input_file, output_file=None):
    """Corrige et reformat un fichier JSON tout en préservant l'indentation."""
    if output_file is None:
        output_file = input_file
    
    try:
        # Lire le contenu
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Traitement du contenu
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        content = content.replace('\\"', '"')
        
        # Corrections supplémentaires pour les erreurs courantes
        # 1. Problème des noms de propriété sans guillemets
        content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
        
        # SUPPRIMÉ: Ne pas remplacer les apostrophes par des guillemets doubles
        # content = re.sub(r"'([^']*)'", r'"\1"', content)
        
        try:
            # Essayer de charger comme JSON
            data = json.loads(content)
            
            # Écrire le contenu formaté avec l'indentation
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except json.JSONDecodeError as e:
            # En cas d'erreur, sauvegarder une version pour débogage
            debug_file = output_file + ".debug"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.error(f"Erreur JSON à la position {e.pos}, voir fichier {debug_file}")
            
            # Écrire le contenu tel quel, avec les corrections déjà appliquées
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Vérifier la validité
        with open(output_file, 'r', encoding='utf-8') as f:
            json.load(f)
        
        logger.info(f"JSON corrigé, validé et formaté: {output_file}")
        return True
    except Exception as e:
        logger.error(f"dbg_239-Erreur: {str(e)}")
        return False


def fix_and_generate_pdf(json_file_path, pdf_output=None, metadata=None):
    """Version combinée qui corrige le JSON puis génère le PDF"""
    try:
        # D'abord corriger le JSON
        fixed = fix_json_file(json_file_path)
        
        # Puis générer le PDF avec les métadonnées
        return generate_pdf_from_json(json_file_path, pdf_output)
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        return None

def get_skill_value(exp, keys):
    """Récupère une valeur en essayant plusieurs variantes de clés possibles"""
    for key in keys:
        if key in exp:
            return exp[key]
    return 'N/A'

def structure_answer(text):
    """
    Analyse un texte structuré et le convertit en objets PDF ReportLab.
    Détecte les titres, les paragraphes et les listes à puces.
    """
    if not text or not isinstance(text, str):
        logger.warning(f"Texte invalide pour structure_answer: {type(text)}")
        return [Paragraph("Aucun contenu à afficher", getSampleStyleSheet()['Normal'])]
    
    # Initialiser la liste d'objets pour le PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Définir les styles personnalisés s'ils n'existent pas
    if 'Heading2Custom' not in styles:
        styles.add(ParagraphStyle(
            name='Heading2Custom',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.darkblue
        ))
    
    if 'NormalCustom' not in styles:
        styles.add(ParagraphStyle(
            name='NormalCustom',
            parent=styles['Normal'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6
        ))
    
    if 'List' not in styles:
        styles.add(ParagraphStyle(
            name='List',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=3
        ))
    
    # Diviser le texte en sections basées sur les titres et sous-titres
    sections = []
    
    # Rechercher les titres de type # Titre
    heading_pattern = r'(?m)^(#+)\s+(.+)$'
    
    # Trouver tous les titres dans le texte
    matches = re.findall(heading_pattern, text)
    
    if matches:
        # Position de départ pour la recherche
        start_pos = 0
        
        # Pour chaque titre trouvé
        for i, match in enumerate(matches):
            # Extraire le niveau du titre (nombre de #) et le texte
            level = len(match[0])
            heading_text = match[1].strip()
            
            # Trouver la position du titre dans le texte
            heading_full = f"{match[0]} {heading_text}"
            pos = text.find(heading_full, start_pos)
            
            # Si ce n'est pas le premier titre, ajouter le contenu précédent
            if i > 0:
                section_content = text[start_pos:pos].strip()
                if section_content:
                    sections.append((matches[i-1][1], section_content))
            elif pos > 0:
                # Texte avant le premier titre
                intro = text[0:pos].strip()
                if intro:
                    sections.append(("Introduction", intro))
            
            # Mettre à jour la position de départ pour la prochaine recherche
            start_pos = pos + len(heading_full)
        
        # Ajouter la dernière section
        if start_pos < len(text):
            last_section = text[start_pos:].strip()
            if last_section:
                sections.append((matches[-1][1], last_section))
    else:
        # Pas de titres, traiter tout comme un seul bloc
        sections.append(("Contenu", text))
    
    # Traiter chaque section
    for title, content in sections:
        # Ajouter le titre de section
        elements.append(Paragraph(title, styles['Heading2Custom']))
        elements.append(Spacer(1, 0.2*cm))
        
        # Traiter les paragraphes de la section
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Vérifier si c'est une liste à puces
            if re.search(r'(?m)^(\s*[-*•])\s', para):
                bullet_items = re.split(r'(?m)^(\s*[-*•])\s', para)
                items = []
                
                # Ignorer le premier élément vide
                i = 1
                while i < len(bullet_items):
                    # Ignorer le marqueur de puce lui-même
                    i += 1
                    if i < len(bullet_items):
                        bullet_text = bullet_items[i].strip()
                        if bullet_text:
                            items.append(ListItem(Paragraph(bullet_text, styles['List'])))
                    i += 1
                
                if items:
                    elements.append(ListFlowable(items, bulletType='bullet', start=None))
                    elements.append(Spacer(1, 0.2*cm))
            else:
                # Paragraphe normal
                elements.append(Paragraph(para, styles['NormalCustom']))
                elements.append(Spacer(1, 0.2*cm))
    
    return elements

def main():
    """Fonction principale avec interface en ligne de commande"""
    #parser = argparse.ArgumentParser(description='Interrogez une URL avec Mistral AI')
    #parser.add_argument('--url', required=True, help='URL à interroger')
    #parser.add_argument('--question', required=True, help='Question à poser')
    #parser.add_argument('--role', default="un assistant IA expert", help='Rôle de l\'IA (par défaut: un assistant IA expert)')
    #parser.add_argument('--output', help='Fichier de sortie pour la réponse (JSON)')
    #parser.add_argument('--model', default='mistral-small-latest', help='Modèle Mistral à utiliser')
    
    #args = parser.parse_args()
    file_path ="G:/OneDrive/Entreprendre/Actions-4/M544/M544_profile_.pdf"
    
    question = "Peux tu me donner son profil professionnel ? "
    question += "Réponds UNIQUEMENT au format JSON suivant: "
    question += """
{
  "accroche": "résumé de présentation du profil (une seule accroche globale)",
  "experiences": [
    {
      "titre": "titre de l'expérience professionnelle",
      "description": {
        "taches": [
          "tâche 1 réalisée pendant cette expérience",
          "tâche 2 réalisée pendant cette expérience"
        ]
      },
      "dates": "période de l'expérience", 
      "entreprise": "nom de l'entreprise",
      "context": "contexte de l'expérience",
      "savoir_faire": "compétences techniques démontrées",
      "savoir_etre": "compétences comportementales démontrées"
    }
  ]
}"""
    
    question += "\n\nAttention: respecte STRICTEMENT ce format JSON. Fournis UNIQUEMENT le JSON sans commentaire."
    
    role = "En tant qu' expert ressources humaines dans le domaine informatique (développeur, Analyste, Testeur logiciel), analyse le texte suivant et réponds à cette question"
    output = "G:/OneDrive/Entreprendre/Actions-4/M544/M544_annonce_.json"
    output_pdf = "G:/OneDrive/Entreprendre/Actions-4/M544/M544_annonce_.pdf"
    model = "mistral-large"  # Nom exact du modèle actuel
    
   
   
    result = query_file(file_path, question, role, output, model)
    if result["status"] == "success":
        pdf_path = fix_and_generate_pdf(output, output_pdf)
        print(f"PDF generated successfully: {pdf_path}")

if __name__ == "__main__":
    main()