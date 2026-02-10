from flask import Blueprint, jsonify

file_picker = Blueprint('file_picker', __name__)


@file_picker.route('/pick_files', methods=['POST'])
def pick_files():
    """
    La sélection de fichiers se fait via l'agent local (localhost:5005/files/list).
    Cette route indique au frontend d'utiliser le sélecteur web.
    """
    return jsonify({
        "files": [],
        "use_agent": True,
        "message": "Utilisez l'agent local pour sélectionner des fichiers",
        "agent_route": "/files/list"
    }), 200
