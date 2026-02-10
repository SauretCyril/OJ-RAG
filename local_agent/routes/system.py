import os
import sys
import platform
from flask import Blueprint, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as agent_config

system_bp = Blueprint("system", __name__)


@system_bp.route("/ping", methods=["GET"])
def ping():
    """Health check — pas d'authentification requise."""
    return jsonify({"status": "ok", "agent": "iacas-local-agent"}), 200


@system_bp.route("/status", methods=["GET"])
def status():
    """Statut détaillé de l'agent."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "platform": platform.system(),
        "python": sys.version,
        "root_dir": agent_config.ROOT_DIR or "(non configuré)",
        "root_dir_exists": os.path.exists(agent_config.ROOT_DIR) if agent_config.ROOT_DIR else False,
    }), 200
