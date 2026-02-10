"""
Blueprint d'authentification — IACAS OTA
Routes : /login, /logout, /api/me, /api/me/*, /admin/users
"""
import os
import hmac
import hashlib
import time
import logging

from flask import (
    Blueprint, request, jsonify, session,
    redirect, url_for, render_template, g
)
from flask_login import login_user, logout_user, login_required, current_user

from cy_users import (
    verify_password, find_by_id, find_by_username,
    load_all_users, create_user, update_user, delete_user, change_password,
    load_profile_file, save_profile_file
)
from cy_limiter import limiter

logger = logging.getLogger(__name__)

cy_auth = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Génération / validation du TOKEN agent
# ---------------------------------------------------------------------------

def _secret_key() -> str:
    return os.getenv("SECRET_KEY", "dev-secret-change-me")


def generate_agent_token(user_id: str) -> str:
    """Génère un TOKEN signé HMAC pour l'agent local."""
    timestamp = str(int(time.time()))
    message = f"{user_id}:{timestamp}"
    signature = hmac.new(
        _secret_key().encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{message}:{signature}"


def validate_agent_token(token: str, max_age_seconds: int = 28800) -> bool:
    """Vérifie signature + expiration (8h par défaut)."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        user_id, timestamp, signature = parts
        if int(time.time()) - int(timestamp) > max_age_seconds:
            return False
        expected = hmac.new(
            _secret_key().encode("utf-8"),
            f"{user_id}:{timestamp}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------

@cy_auth.route("/login", methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("login.html")


@cy_auth.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login_post():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Identifiant et mot de passe requis"}), 400

    user = verify_password(username, password)
    if not user:
        logger.warning(f"Tentative de connexion échouée pour '{username}' depuis {request.remote_addr}")
        return jsonify({"error": "Identifiant ou mot de passe incorrect"}), 401

    login_user(user, remember=False)

    # Générer le TOKEN pour l'agent local
    agent_token = generate_agent_token(user.id)
    session["agent_token"] = agent_token

    logger.info(f"Connexion réussie : '{username}' depuis {request.remote_addr}")
    return jsonify({
        "success": True,
        "token": agent_token,
        "user": user.to_public(),
        "redirect": "/"
    }), 200


@cy_auth.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logger.info(f"Déconnexion : '{current_user.username}'")
    session.pop("agent_token", None)
    logout_user()
    return redirect(url_for("auth.login_page"))


# ---------------------------------------------------------------------------
# Profil utilisateur courant
# ---------------------------------------------------------------------------

@cy_auth.route("/api/me", methods=["GET"])
@login_required
def get_me():
    """Retourne le profil complet de l'utilisateur connecté."""
    username = current_user.username
    return jsonify({
        "user": current_user.to_public(),
        "token": session.get("agent_token", ""),
        "config": load_profile_file(username, "config.json"),
        "prompts": load_profile_file(username, "prompts.json"),
        "filters": load_profile_file(username, "filters.json"),
        "directories": load_profile_file(username, "directories.json"),
    }), 200


@cy_auth.route("/api/me/config", methods=["GET"])
@login_required
def get_config():
    config = load_profile_file(current_user.username, "config.json")
    return jsonify(config), 200


@cy_auth.route("/api/me/config", methods=["POST"])
@login_required
def save_config():
    data = request.get_json(force=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Données invalides"}), 400
    # Lire la config existante et merger (ne pas écraser les clés non envoyées)
    existing = load_profile_file(current_user.username, "config.json")
    if isinstance(existing, dict):
        existing.update(data)
        data = existing
    save_profile_file(current_user.username, "config.json", data)
    return jsonify({"success": True}), 200


@cy_auth.route("/api/me/prompts", methods=["GET"])
@login_required
def get_prompts():
    return jsonify(load_profile_file(current_user.username, "prompts.json")), 200


@cy_auth.route("/api/me/prompts", methods=["POST"])
@login_required
def save_prompts():
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({"error": "Un tableau de prompts est attendu"}), 400
    save_profile_file(current_user.username, "prompts.json", data)
    return jsonify({"success": True}), 200


@cy_auth.route("/api/me/filters", methods=["GET"])
@login_required
def get_filters():
    return jsonify(load_profile_file(current_user.username, "filters.json")), 200


@cy_auth.route("/api/me/filters", methods=["POST"])
@login_required
def save_filters():
    data = request.get_json(force=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Un objet de filtres est attendu"}), 400
    save_profile_file(current_user.username, "filters.json", data)
    return jsonify({"success": True}), 200


@cy_auth.route("/api/me/directories", methods=["GET"])
@login_required
def get_directories():
    return jsonify(load_profile_file(current_user.username, "directories.json")), 200


@cy_auth.route("/api/me/directories", methods=["POST"])
@login_required
def save_directories():
    data = request.get_json(force=True)
    if not isinstance(data, list):
        return jsonify({"error": "Un tableau de chemins est attendu"}), 400
    save_profile_file(current_user.username, "directories.json", data)
    return jsonify({"success": True}), 200


@cy_auth.route("/api/me/token", methods=["GET"])
@login_required
def get_token():
    """Retourne le TOKEN agent courant (pour le frontend JS)."""
    return jsonify({"token": session.get("agent_token", "")}), 200


# ---------------------------------------------------------------------------
# Admin — Gestion des utilisateurs
# ---------------------------------------------------------------------------

def _admin_required(f):
    """Décorateur : réserve la route aux admins."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({"error": "Accès réservé aux administrateurs"}), 403
        return f(*args, **kwargs)
    return decorated


@cy_auth.route("/admin/users", methods=["GET"])
@login_required
@_admin_required
def admin_list_users():
    users = [u.to_public() for u in load_all_users()]
    return jsonify(users), 200


@cy_auth.route("/admin/users", methods=["POST"])
@login_required
@_admin_required
def admin_create_user():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"error": "username et password requis"}), 400
    if role not in ("user", "admin"):
        return jsonify({"error": "role invalide (user ou admin)"}), 400
    try:
        user = create_user(username, password, email, role)
        logger.info(f"Admin '{current_user.username}' a créé l'utilisateur '{username}'")
        return jsonify(user.to_public()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@cy_auth.route("/admin/users/<user_id>", methods=["PUT"])
@login_required
@_admin_required
def admin_update_user(user_id):
    data = request.get_json(force=True)
    allowed = {k: v for k, v in data.items() if k in ("active", "email", "role")}
    if not allowed:
        return jsonify({"error": "Aucun champ modifiable fourni (active, email, role)"}), 400
    if update_user(user_id, **allowed):
        return jsonify({"success": True}), 200
    return jsonify({"error": "Utilisateur introuvable"}), 404


@cy_auth.route("/admin/users/<user_id>", methods=["DELETE"])
@login_required
@_admin_required
def admin_delete_user(user_id):
    # Empêcher la suppression de son propre compte
    if user_id == current_user.id:
        return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte"}), 400
    if delete_user(user_id):
        return jsonify({"success": True}), 200
    return jsonify({"error": "Utilisateur introuvable"}), 404
