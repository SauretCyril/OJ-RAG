"""
IACAS Local Agent — v1.0.0
API REST locale pour la gestion des fichiers et dossiers de l'utilisateur.

Ce serveur tourne sur le PC local de l'utilisateur (127.0.0.1:5005).
Il ne doit JAMAIS être exposé sur une interface réseau publique.

Démarrage :
    python agent.py
    ou via le launcher :
    python launcher.py
"""
import os
import sys

# Ajouter le répertoire de l'agent au PYTHONPATH
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AGENT_DIR)

from flask import Flask
from flask_cors import CORS

import config as agent_config
from routes.system import system_bp
from routes.directories import directories_bp
from routes.files import files_bp
from routes.documents import documents_bp

app = Flask(__name__)

# CORS : autoriser uniquement les origines connues
# En production : remplacer par l'URL réelle du VPS
ALLOWED_ORIGINS = [
    "http://localhost:5000",
    "http://localhost:5001",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
]

# En production, ajouter l'URL du VPS depuis la variable d'environnement
vps_url = os.getenv("VPS_URL", "")
if vps_url:
    ALLOWED_ORIGINS.append(vps_url)

CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=False)

# Enregistrement des blueprints
app.register_blueprint(system_bp)
app.register_blueprint(directories_bp)
app.register_blueprint(files_bp)
app.register_blueprint(documents_bp)


@app.errorhandler(404)
def not_found(e):
    return {"error": "Route introuvable"}, 404


@app.errorhandler(405)
def method_not_allowed(e):
    return {"error": "Méthode non autorisée"}, 405


@app.errorhandler(500)
def internal_error(e):
    return {"error": "Erreur interne de l'agent"}, 500


if __name__ == "__main__":
    print(f"[IACAS Agent] Démarrage sur {agent_config.HOST}:{agent_config.PORT}")
    print(f"[IACAS Agent] ROOT_DIR = {agent_config.ROOT_DIR or '(non configuré)'}")
    print(f"[IACAS Agent] Token secret = {'configuré' if agent_config.TOKEN_SECRET != 'dev-token-change-in-production' else 'DEFAUT (à changer en production)'}")

    # SECURITE : L'agent ne doit écouter QUE sur 127.0.0.1
    app.run(
        host=agent_config.HOST,
        port=agent_config.PORT,
        debug=agent_config.DEBUG,
        use_reloader=False,
    )
