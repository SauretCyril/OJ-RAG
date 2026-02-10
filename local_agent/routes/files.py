import os
import sys
import json
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as agent_config
from core.security import require_token, safe_absolute_path

files_bp = Blueprint("files", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".json", ".txt", ".csv", ".html"}


def _resolve(path: str) -> str:
    root = agent_config.ROOT_DIR
    if root:
        return safe_absolute_path(path, root)
    return os.path.realpath(path)


@files_bp.route("/files/read", methods=["GET"])
@require_token
def read_file():
    """
    Lit un fichier texte/JSON.
    Paramètre : ?path=<chemin absolu ou relatif à ROOT_DIR>
    """
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "path manquant"}), 400
    try:
        full_path = _resolve(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    if not os.path.exists(full_path):
        return jsonify({"error": "Fichier introuvable"}), 404
    if not os.path.isfile(full_path):
        return jsonify({"error": "Ce chemin est un dossier, pas un fichier"}), 400
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        ext = os.path.splitext(full_path)[1].lower()
        if ext == ".json":
            try:
                return jsonify({"content": json.loads(content), "type": "json"}), 200
            except json.JSONDecodeError:
                pass
        return jsonify({"content": content, "type": "text"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/write", methods=["POST"])
@require_token
def write_file():
    """
    Écrit dans un fichier (JSON ou texte).
    Body : { "path": "...", "content": "..." ou {} }
    """
    data = request.get_json(force=True)
    path = data.get("path", "").strip()
    content = data.get("content")
    if not path or content is None:
        return jsonify({"error": "path et content requis"}), 400
    try:
        full_path = _resolve(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    ext = os.path.splitext(full_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Extension non autorisée : {ext}"}), 400
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        if isinstance(content, (dict, list)):
            text = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            text = str(content)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(text)
        return jsonify({"success": True, "path": full_path.replace("\\", "/")}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/exists", methods=["GET"])
@require_token
def file_exists():
    """Vérifie si un fichier existe."""
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "path manquant"}), 400
    try:
        full_path = _resolve(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    return jsonify({
        "exists": os.path.exists(full_path),
        "is_file": os.path.isfile(full_path),
        "path": full_path.replace("\\", "/"),
    }), 200


@files_bp.route("/files/delete", methods=["DELETE"])
@require_token
def delete_file():
    """Supprime un fichier."""
    data = request.get_json(force=True)
    path = data.get("path", "").strip()
    if not path:
        return jsonify({"error": "path manquant"}), 400
    try:
        full_path = _resolve(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    if not os.path.exists(full_path):
        return jsonify({"error": "Fichier introuvable"}), 404
    try:
        os.remove(full_path)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/upload", methods=["POST"])
@require_token
def upload_file():
    """
    Reçoit un fichier uploadé et le sauvegarde dans ROOT_DIR/<dest_dir>/.
    Form field : file, dest_dir (optionnel)
    """
    root = agent_config.ROOT_DIR
    if not root:
        return jsonify({"error": "ROOT_DIR non configuré"}), 400
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    f = request.files["file"]
    dest_dir = request.form.get("dest_dir", "").strip()
    if not f.filename:
        return jsonify({"error": "Nom de fichier vide"}), 400
    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Extension non autorisée : {ext}"}), 400
    try:
        if dest_dir:
            target_dir = safe_absolute_path(os.path.join(root, dest_dir), root)
        else:
            target_dir = root
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    os.makedirs(target_dir, exist_ok=True)
    save_path = os.path.join(target_dir, filename)
    f.save(save_path)
    return jsonify({
        "success": True,
        "path": save_path.replace("\\", "/"),
        "filename": filename,
    }), 201


@files_bp.route("/files/list", methods=["GET"])
@require_token
def list_files():
    """
    Liste les fichiers d'un dossier.
    Paramètre : ?path=<chemin>
    Paramètre optionnel : ?ext=.pdf,.json (filtre par extensions)
    """
    path = request.args.get("path", "").strip()
    ext_filter = request.args.get("ext", "").strip()
    if not path:
        path = agent_config.ROOT_DIR
    if not path:
        return jsonify({"error": "path manquant et ROOT_DIR non configuré"}), 400
    try:
        full_path = _resolve(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    if not os.path.isdir(full_path):
        return jsonify({"error": "Ce chemin n'est pas un dossier"}), 400
    allowed_exts = set(e.strip() for e in ext_filter.split(",") if e.strip()) if ext_filter else None
    try:
        entries = []
        for name in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, name)
            if os.path.isfile(item_path):
                ext = os.path.splitext(name)[1].lower()
                if allowed_exts is None or ext in allowed_exts:
                    entries.append({
                        "name": name,
                        "path": item_path.replace("\\", "/"),
                        "size": os.path.getsize(item_path),
                        "ext": ext,
                    })
        return jsonify({"files": entries, "path": full_path.replace("\\", "/")}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
