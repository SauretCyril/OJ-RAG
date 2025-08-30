import os
from dotenv import load_dotenv
from fpdf import FPDF

def get_analysis_dir_from_env():
    load_dotenv()
    return os.getenv("ANALYSE_ANNONCES_DIR", os.getcwd())

def save_analysis_to_pdf(current_dossier,
    numdos, file, question, role, texte_annonce, resultat_question, cv_infos=None, resultat_correlation=None
):
    analysis_dir = f"{current_dossier}/_news"
    if not os.path.exists(analysis_dir):
        print(f"Le dossier d'analyse '{analysis_dir}' n'existe pas.")
        return None

    pdf = FPDF()
    font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
    if not os.path.exists(font_path):
        print("Police DejaVuSans.ttf manquante. Téléchargez-la et placez-la dans le dossier backend.")
        return None
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.add_font("DejaVu", "B", font_path, uni=True)
    pdf.set_font("DejaVu", "B", 16)
    pdf.add_page()
    pdf.cell(0, 10, f"Analyse Annonce - Dossier {numdos}", ln=1)

    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 8, "Résultat question :", ln=1)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 8, resultat_question)

    pdf.output(file)
    return

def save_correlation_to_pdf(current_dossier, numdos, file, resultat_correlation):
    analysis_dir = f"{current_dossier}/_news"
    if not os.path.exists(analysis_dir):
        print(f"Le dossier d'analyse '{analysis_dir}' n'existe pas.")
        return None

    pdf = FPDF()
    font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
    if not os.path.exists(font_path):
        print("Police DejaVuSans.ttf manquante. Téléchargez-la et placez-la dans le dossier backend.")
        return None
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.add_font("DejaVu", "B", font_path, uni=True)
    pdf.set_font("DejaVu", "B", 16)
    pdf.add_page()
    pdf.cell(0, 10, f"Corrélation Annonce / CV - Dossier {numdos}", ln=1)

    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 8, "Résultat corrélation :", ln=1)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 8, resultat_correlation)

    pdf.output(file)
    return file