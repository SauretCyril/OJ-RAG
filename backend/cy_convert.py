"""
Conversion DOCX → PDF cross-platform.
Remplace l'usage direct de docx2pdf + pythoncom (Windows uniquement).
"""
import os
import platform
import shutil
import subprocess


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """
    Convertit un fichier DOCX en PDF.
    - Windows (avec LibreOffice installé) : LibreOffice headless
    - Windows (sans LibreOffice) : fallback docx2pdf (nécessite MS Word)
    - Linux / macOS : LibreOffice headless
    """
    output_dir = os.path.dirname(os.path.abspath(pdf_path))
    os.makedirs(output_dir, exist_ok=True)

    system = platform.system()

    if system == "Windows":
        libreoffice_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        soffice = next((p for p in libreoffice_paths if os.path.exists(p)), None)
        if soffice:
            _run_libreoffice(soffice, docx_path, output_dir, pdf_path)
        else:
            # Fallback : docx2pdf (requiert MS Word)
            from docx2pdf import convert as _docx2pdf_convert
            _docx2pdf_convert(docx_path, pdf_path)
    elif system == "Darwin":
        _run_libreoffice("soffice", docx_path, output_dir, pdf_path)
    else:
        _run_libreoffice("libreoffice", docx_path, output_dir, pdf_path)


def _run_libreoffice(executable: str, docx_path: str, output_dir: str, expected_pdf: str) -> None:
    cmd = [executable, "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice échec (code {result.returncode}) : {result.stderr}")

    # LibreOffice génère le PDF avec le nom du DOCX dans output_dir
    generated = os.path.join(
        output_dir,
        os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    )
    if generated != expected_pdf and os.path.exists(generated):
        shutil.move(generated, expected_pdf)
