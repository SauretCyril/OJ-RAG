import tkinter as tk
from tkinter import filedialog
from flask import Blueprint, jsonify, request

file_picker = Blueprint('file_picker', __name__)

@file_picker.route('/pick_files', methods=['POST'])
def pick_files():
    """
    Ouvre un explorateur natif pour sélectionner plusieurs fichiers.
    Retourne la liste complète des chemins sélectionnés au format JSON.
    """
    # Optionnel : récupérer un répertoire initial depuis la requête
    initial_dir = request.json.get('initial_dir', None) if request.is_json else None

    # Lancer Tkinter en mode caché
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # Met la fenêtre devant

    # Ouvre la boîte de dialogue de sélection multiple
    file_paths = filedialog.askopenfilenames(
        title="Sélectionnez un ou plusieurs fichiers",
        initialdir=initial_dir if initial_dir else None
    )

    # Fermer la fenêtre Tkinter
    root.destroy()

    # Convertir en liste Python standard
    files = list(file_paths)

    return jsonify({"files": files})