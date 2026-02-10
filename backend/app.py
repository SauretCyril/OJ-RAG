from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta

import numpy as np
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cy_app_config import app_config

# ---------------------------------------------------------------------------
# Création de l'app
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Configuration de sécurité
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-me-in-production"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_NAME="iacas_session",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=app_config.max_file_size,
    UPLOAD_FOLDER=str(app_config.uploads_dir),
)

# Validation config production
_secret = app.config["SECRET_KEY"]
if _secret == "dev-secret-change-me-in-production":
    logging.warning("[SECURITE] SECRET_KEY non définie — utilisez une clé forte en production !")
if os.getenv("FLASK_ENV") == "production" and _secret in ("dev-secret-change-me-in-production", ""):
    logging.critical("[SECURITE] SECRET_KEY invalide en production — arrêt.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Logs rotatifs
# ---------------------------------------------------------------------------
_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_handler = RotatingFileHandler(
    os.path.join(_log_dir, "iacas.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
_log_handler.setLevel(logging.INFO)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
app.logger.addHandler(_log_handler)
logging.getLogger().addHandler(_log_handler)


# ---------------------------------------------------------------------------
# NumpyEncoder
# ---------------------------------------------------------------------------
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.float32):
            return float(obj)
        return super().default(obj)

app.json_encoder = NumpyEncoder


# ---------------------------------------------------------------------------
# Flask-Limiter (rate limiting)
# ---------------------------------------------------------------------------
from cy_limiter import limiter
limiter.init_app(app)


# ---------------------------------------------------------------------------
# Headers de sécurité HTTP
# ---------------------------------------------------------------------------
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if os.getenv("FLASK_ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net https://use.fontawesome.com; "
        "img-src 'self' data:; "
        "connect-src 'self' http://127.0.0.1:5005; "
        "frame-src 'none'; "
        "object-src 'none';"
    )
    return response


# ---------------------------------------------------------------------------
# Flask-Login
# ---------------------------------------------------------------------------
from flask_login import LoginManager, current_user
from cy_users import find_by_id, ensure_admin_exists

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login_page"
login_manager.login_message = ""

@login_manager.user_loader
def load_user(user_id):
    return find_by_id(user_id)

# Crée le compte admin au premier démarrage si nécessaire
ensure_admin_exists()


# ---------------------------------------------------------------------------
# Protection globale : toutes les routes nécessitent d'être connecté
# sauf /login et /static
# ---------------------------------------------------------------------------
PUBLIC_ENDPOINTS = {"auth.login_page", "auth.login_post", "static"}

@app.before_request
def require_login():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return
    if current_user.is_authenticated:
        return
    # Requête API → JSON 401
    if request.is_json or (request.path.startswith("/api/") or request.path.startswith("/admin/")):
        return jsonify({"error": "Non authentifié", "redirect": "/login"}), 401
    # Requête page → redirect login
    return redirect(url_for("auth.login_page"))


# ---------------------------------------------------------------------------
# Enregistrement des blueprints
# ---------------------------------------------------------------------------
from cy_auth import cy_auth
app.register_blueprint(cy_auth)

from cy_paths import paths
app.register_blueprint(paths)

from cy_routes import cy_routes
app.register_blueprint(cy_routes)

from cy_cookies import cy_cookies
app.register_blueprint(cy_cookies)

from cy_requests import cy_requests
app.register_blueprint(cy_requests)

from cy_columns import cy_columns
app.register_blueprint(cy_columns)

from cy_fbx_exploreur import cy_fbx
app.register_blueprint(cy_fbx)

from cy_directories import register_directories_routes
register_directories_routes(app)

from cy_file_picker import file_picker
app.register_blueprint(file_picker)


# ---------------------------------------------------------------------------
# Routes principales
# ---------------------------------------------------------------------------
BASE_DIR = str(app_config.base_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/columns_manager")
def columns_manager():
    return render_template("column_manager.html")


# Ces fonctionnalités sont gérées par l'agent local (localhost:5005).
@app.route('/get_local_FileExplorer', methods=['POST'])
def get_local_FileExplorer():
    return jsonify({"status": "use_agent", "message": "Utilisez l'agent local via localhost:5005/directories/tree"}), 200

@app.route('/get_local_PromptTable', methods=['POST'])
def prompt_table_open():
    return jsonify({"status": "use_agent", "message": "Fonctionnalité disponible dans l'interface web"}), 200


# ---------------------------------------------------------------------------
# Démarrage
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app_config.setup_logging()
    port = app_config.constants.get('port', 5001)
    debug = app_config.constants.get('debug', True)
    app.run(debug=debug, port=port)
