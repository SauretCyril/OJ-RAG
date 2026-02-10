import os
import sys
from flask import Blueprint, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as agent_config
from core.security import require_token, safe_absolute_path
from core.file_ops import list_directory, directory_tree, move_directory

directories_bp = Blueprint("directories", __name__)


@directories_bp.route("/directories/root", methods=["GET"])
@require_token
def get_root():
    """Retourne le ROOT_DIR actuel."""
    root = agent_config.ROOT_DIR
    return jsonify({
        "root_dir": root.replace("\\", "/") if root else "",
        "exists": os.path.exists(root) if root else False,
    }), 200


@directories_bp.route("/directories/root", methods=["POST"])
@require_token
def set_root():
    """Définit un nouveau ROOT_DIR (persisté dans la session, pas dans le .env)."""
    data = request.get_json(force=True)
    new_root = data.get("root_dir", "").strip()
    if not new_root:
        return jsonify({"error": "root_dir manquant"}), 400
    if not os.path.exists(new_root):
        return jsonify({"error": f"Répertoire introuvable : {new_root}"}), 404
    agent_config.ROOT_DIR = new_root
    return jsonify({"success": True, "root_dir": new_root.replace("\\", "/")}), 200


@directories_bp.route("/directories/list", methods=["GET"])
@require_token
def list_root():
    """Liste les sous-dossiers du ROOT_DIR."""
    root = agent_config.ROOT_DIR
    if not root or not os.path.exists(root):
        return jsonify({"error": "ROOT_DIR non configuré ou introuvable"}), 400
    try:
        content = list_directory(root)
        return jsonify(content), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@directories_bp.route("/directories/tree", methods=["GET"])
@require_token
def get_tree():
    """
    Retourne l'arbre de dossiers pour le sélecteur web.
    Paramètre optionnel : ?path=<chemin> (doit être dans ROOT_DIR ou libre si ROOT_DIR vide)
    Paramètre optionnel : ?depth=<int> (profondeur max, défaut 3)
    """
    root = agent_config.ROOT_DIR
    requested_path = request.args.get("path", "").strip()
    depth = int(request.args.get("depth", 3))
    depth = min(depth, 5)  # Limite à 5 niveaux max

    if requested_path:
        try:
            if root:
                base_path = safe_absolute_path(requested_path, root)
            else:
                base_path = os.path.realpath(requested_path)
        except ValueError as e:
            return jsonify({"error": str(e)}), 403
    elif root:
        base_path = os.path.realpath(root)
    else:
        # Sans ROOT_DIR, retourner les lecteurs/racines disponibles
        base_path = None

    if base_path is None:
        import platform
        if platform.system() == "Windows":
            import string
            drives = [f"{d}:/" for d in string.ascii_uppercase if os.path.exists(f"{d}:/")]
            tree = [{"name": d, "path": d, "children": []} for d in drives]
        else:
            tree = directory_tree("/", max_depth=1)
        return jsonify({"path": "/", "tree": tree}), 200

    if not os.path.exists(base_path):
        return jsonify({"error": f"Chemin introuvable : {base_path}"}), 404

    tree = directory_tree(base_path, max_depth=depth)
    return jsonify({
        "path": base_path.replace("\\", "/"),
        "tree": tree
    }), 200


@directories_bp.route("/directories/exists", methods=["GET"])
@require_token
def dir_exists():
    """Vérifie si un dossier existe."""
    root = agent_config.ROOT_DIR
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "path manquant"}), 400
    try:
        if root:
            full_path = safe_absolute_path(path, root)
        else:
            full_path = os.path.realpath(path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    return jsonify({
        "exists": os.path.exists(full_path),
        "is_dir": os.path.isdir(full_path),
        "path": full_path.replace("\\", "/"),
    }), 200


@directories_bp.route("/directories/create", methods=["POST"])
@require_token
def create_directory():
    """Crée un dossier dans ROOT_DIR."""
    root = agent_config.ROOT_DIR
    if not root:
        return jsonify({"error": "ROOT_DIR non configuré"}), 400
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name manquant"}), 400
    try:
        full_path = safe_absolute_path(os.path.join(root, name), root)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    if os.path.exists(full_path):
        return jsonify({"error": "Le dossier existe déjà"}), 409
    try:
        os.makedirs(full_path)
        return jsonify({"success": True, "path": full_path.replace("\\", "/")}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@directories_bp.route("/directories/move", methods=["POST"])
@require_token
def move_dir():
    """Déplace ou renomme un dossier."""
    root = agent_config.ROOT_DIR
    if not root:
        return jsonify({"error": "ROOT_DIR non configuré"}), 400
    data = request.get_json(force=True)
    source = data.get("source", "").strip()
    target = data.get("target", "").strip()
    if not source or not target:
        return jsonify({"error": "source et target requis"}), 400
    try:
        safe_source = safe_absolute_path(source, root)
        safe_target = safe_absolute_path(target, root)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    try:
        move_directory(safe_source, safe_target)
        return jsonify({
            "success": True,
            "source": safe_source.replace("\\", "/"),
            "target": safe_target.replace("\\", "/"),
        }), 200
    except FileExistsError as e:
        return jsonify({"error": str(e)}), 409
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@directories_bp.route("/directories/delete", methods=["DELETE"])
@require_token
def delete_directory():
    """Supprime un dossier (récursif)."""
    root = agent_config.ROOT_DIR
    if not root:
        return jsonify({"error": "ROOT_DIR non configuré"}), 400
    data = request.get_json(force=True)
    path = data.get("path", "").strip()
    if not path:
        return jsonify({"error": "path manquant"}), 400
    try:
        full_path = safe_absolute_path(path, root)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    if not os.path.exists(full_path):
        return jsonify({"error": "Dossier introuvable"}), 404
    try:
        import shutil
        shutil.rmtree(full_path)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
