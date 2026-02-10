"""
cy_cookies.py — Préférences utilisateur
Les cookies sont maintenant stockés dans data/users/{username}/config.json.
Les routes anciennes (/save_cookie, /load_cookies, /get_cookie) sont conservées
pour la compatibilité avec le frontend existant.
"""
from flask import request, Blueprint, jsonify
from flask_login import current_user
import logging
import json
import os

logger = logging.getLogger(__name__)

cy_cookies = Blueprint('cy_cookies', __name__)

# Chemin fallback (utilisé uniquement si aucun utilisateur n'est connecté — dev)
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(_DATA_DIR, exist_ok=True)
_LEGACY_FILE = os.path.join(_DATA_DIR, 'cookies.json')


def _get_config_path() -> str:
    """Retourne le chemin du fichier config de l'utilisateur connecté."""
    if current_user and current_user.is_authenticated:
        from cy_users import get_profile_dir
        return os.path.join(get_profile_dir(current_user.username), "config.json")
    return _LEGACY_FILE


def _read_config() -> dict:
    path = _get_config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Erreur lecture config : {e}")
        return {}


def _write_config(data: dict) -> None:
    path = _get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Routes (compatibilité frontend existant)
# ---------------------------------------------------------------------------

@cy_cookies.route('/save_cookie', methods=['POST'])
def save_cookie():
    cookie_value = request.json.get('cookie_value')
    cookie_name = request.json.get('cookie_name')
    if cookie_value is None or cookie_name is None:
        return jsonify({"error": "cookie_name et cookie_value requis"}), 400
    config = _read_config()
    config[cookie_name] = cookie_value
    _write_config(config)
    return jsonify({"message": "done"})


@cy_cookies.route('/load_cookies', methods=['GET'])
def load_cookies():
    try:
        config = _read_config()
        return jsonify({"message": "Cookies loaded successfully", "cookies_data": config})
    except Exception as e:
        logger.error(f"Erreur chargement cookies : {e}")
        return jsonify({"error": "Failed to load cookies"}), 500


@cy_cookies.route('/get_cookie', methods=['POST'])
def get_cookie():
    try:
        cookie_name = request.json.get('cookie_name')
        if cookie_name is None:
            return jsonify({"error": "cookie_name requis"}), 400
        config = _read_config()
        return jsonify({cookie_name: config.get(cookie_name)})
    except Exception as e:
        logger.error(f"Erreur get_cookie : {e}")
        return jsonify({"error": "Failed to get cookie"}), 500


# ---------------------------------------------------------------------------
# Fonction utilitaire (appelée par cy_paths.py et d'autres modules)
# ---------------------------------------------------------------------------

def get_cookie_value(key_name: str):
    """Retourne la valeur d'une clé dans la config de l'utilisateur connecté."""
    try:
        return _read_config().get(key_name)
    except Exception as e:
        logger.error(f"get_cookie_value({key_name}) : {e}")
        return None
