import os
import hmac
import hashlib
import time
from functools import wraps
from flask import request, jsonify
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as agent_config


def verify_token(token: str) -> bool:
    """
    Vérifie le token HMAC signé par le VPS.
    Format attendu : {user_id}:{timestamp}:{signature}
    Clé : AGENT_TOKEN (doit être identique à SECRET_KEY du VPS).
    Expiration : 8 h.
    """
    if not token:
        return False
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        user_id, timestamp_str, signature = parts
        # Vérifier expiration
        if int(time.time()) - int(timestamp_str) > 28800:
            return False
        # Vérifier signature
        message = f"{user_id}:{timestamp_str}"
        expected = hmac.new(
            agent_config.TOKEN_SECRET.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def require_token(f):
    """Décorateur : rejette les requêtes sans token HMAC valide."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
        else:
            token = request.headers.get("X-Agent-Token", "")
        if not verify_token(token):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def safe_path(user_input: str, base_dir: str) -> str:
    """
    Résout le chemin et vérifie qu'il reste dans base_dir.
    Lève ValueError si tentative de sortie (path traversal).
    Retourne le chemin absolu normalisé.
    """
    if not base_dir:
        raise ValueError("ROOT_DIR non configuré")
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, user_input))
    if target != base and not target.startswith(base + os.sep):
        raise ValueError(f"Chemin non autorisé : {user_input}")
    return target


def safe_absolute_path(absolute_path: str, base_dir: str) -> str:
    """
    Vérifie qu'un chemin absolu fourni par le client reste dans base_dir.
    Lève ValueError si tentative de sortie.
    """
    if not base_dir:
        raise ValueError("ROOT_DIR non configuré")
    base = os.path.realpath(base_dir)
    target = os.path.realpath(absolute_path)
    if target != base and not target.startswith(base + os.sep):
        raise ValueError(f"Chemin non autorisé : {absolute_path}")
    return target
