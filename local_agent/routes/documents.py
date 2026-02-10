import os
import sys
from flask import Blueprint, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as agent_config
from core.security import require_token, safe_absolute_path
from core.file_ops import convert_docx_to_pdf

documents_bp = Blueprint("documents", __name__)


def _resolve(path: str) -> str:
    root = agent_config.ROOT_DIR
    if root:
        return safe_absolute_path(path, root)
    return os.path.realpath(path)


@documents_bp.route("/documents/extract-pdf", methods=["POST"])
@require_token
def extract_pdf():
    """
    Extrait le texte d'un fichier PDF.
    Body : { "path": "<chemin du PDF>" }
    """
    data = request.get_json(force=True)
    path = data.get("path", "").strip()
    if not path:
        return jsonify({"error": "path manquant"}), 400
    try:
        full_path = _resolve(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    if not os.path.exists(full_path):
        return jsonify({"error": "Fichier PDF introuvable"}), 404
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(full_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        text = "\n".join(text_parts)
        return jsonify({
            "text": text,
            "pages": len(reader.pages),
            "path": full_path.replace("\\", "/"),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@documents_bp.route("/documents/convert-docx", methods=["POST"])
@require_token
def convert_docx():
    """
    Convertit un fichier DOCX en PDF via LibreOffice headless (cross-platform).
    Body : { "docx_path": "...", "pdf_path": "..." (optionnel) }
    """
    data = request.get_json(force=True)
    docx_path = data.get("docx_path", "").strip()
    if not docx_path:
        return jsonify({"error": "docx_path manquant"}), 400

    # pdf_path optionnel : si absent, même dossier que le DOCX
    pdf_path = data.get("pdf_path", "").strip()
    if not pdf_path:
        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

    try:
        full_docx = _resolve(docx_path)
        full_pdf = _resolve(pdf_path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403

    if not os.path.exists(full_docx):
        return jsonify({"error": "Fichier DOCX introuvable"}), 404

    try:
        convert_docx_to_pdf(full_docx, full_pdf)
        return jsonify({
            "success": True,
            "pdf_path": full_pdf.replace("\\", "/"),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@documents_bp.route("/documents/generate-pdf", methods=["POST"])
@require_token
def generate_pdf():
    """
    Génère un PDF depuis du texte brut avec reportlab.
    Body : {
        "output_path": "...",
        "title": "...",
        "content": "texte brut ou HTML simple"
    }
    """
    data = request.get_json(force=True)
    output_path = data.get("output_path", "").strip()
    title = data.get("title", "Document")
    content = data.get("content", "")
    if not output_path:
        return jsonify({"error": "output_path manquant"}), 400
    try:
        full_path = _resolve(output_path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm

        doc = SimpleDocTemplate(full_path, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(title, styles["Title"]),
            Spacer(1, 0.5*cm),
            Paragraph(content.replace("\n", "<br/>"), styles["BodyText"]),
        ]
        doc.build(story)
        return jsonify({
            "success": True,
            "path": full_path.replace("\\", "/"),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
