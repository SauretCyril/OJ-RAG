import os
import json
import aiofiles
import shutil
import platform
import subprocess


async def read_json(path: str) -> dict:
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()
    return json.loads(content)


async def write_json(path: str, data: dict) -> None:
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))


async def read_text(path: str) -> str:
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()


async def write_text(path: str, content: str) -> None:
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)


def list_directory(path: str) -> dict:
    """
    Liste le contenu d'un répertoire.
    Retourne un dict avec 'dirs' et 'files'.
    """
    items = os.listdir(path)
    dirs = sorted([d for d in items if os.path.isdir(os.path.join(path, d))])
    files = sorted([f for f in items if os.path.isfile(os.path.join(path, f))])
    return {"dirs": dirs, "files": files}


def directory_tree(path: str, max_depth: int = 3, current_depth: int = 0) -> list:
    """
    Retourne l'arbre de dossiers (uniquement les répertoires) sous forme de liste.
    Utilisé par le sélecteur de répertoire web.
    """
    if current_depth >= max_depth:
        return []
    result = []
    try:
        items = sorted(os.listdir(path))
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path) and not item.startswith('.'):
                node = {
                    "name": item,
                    "path": full_path.replace("\\", "/"),
                    "children": directory_tree(full_path, max_depth, current_depth + 1)
                }
                result.append(node)
    except PermissionError:
        pass
    return result


def move_directory(source: str, target: str) -> None:
    """Déplace/renomme un répertoire."""
    if os.path.exists(target):
        raise FileExistsError(f"La cible existe déjà : {target}")
    if not os.path.exists(source):
        raise FileNotFoundError(f"La source est introuvable : {source}")
    shutil.move(source, target)


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """Conversion DOCX → PDF cross-platform via LibreOffice headless."""
    output_dir = os.path.dirname(pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    system = platform.system()

    if system == "Windows":
        libreoffice_candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        soffice = next((p for p in libreoffice_candidates if os.path.exists(p)), None)
        if soffice:
            cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path]
        else:
            # Fallback docx2pdf (MS Word requis)
            from docx2pdf import convert as _convert
            _convert(docx_path, pdf_path)
            return
    elif system == "Darwin":
        cmd = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path]
    else:
        cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

    # LibreOffice crée le PDF avec le même nom que le DOCX dans output_dir
    generated = os.path.join(output_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if generated != pdf_path and os.path.exists(generated):
        shutil.move(generated, pdf_path)
