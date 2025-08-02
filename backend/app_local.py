from flask import Flask, request, jsonify
import requests  # Ajoutez cette ligne avec les autres imports
from cls_local_FileExplorer import cls_local_FileExplorer
from cls_local_analyse_prompt import cls_local_PromptTable
import threading
import time
import os
import json

applocal = Flask(__name__)


@applocal.route('/local_FileExplorer', methods=['POST'])
def launch_explorer():
    data = request.json
    path = data.get("path")
    explorer_type = data.get("explorer_type", "")
    if path and os.path.exists(path):
        def run_explorer():
            print(f"LOCAL :Launching explorer for path: {path} with type: {explorer_type}")
            explorer = cls_local_FileExplorer(initial_dir=path, explorer_type=explorer_type)
            explorer.run()
        threading.Thread(target=run_explorer).start()
        return jsonify({"status": "explorer launched"}), 200
    return jsonify({"error": "Invalid path"}), 400

@applocal.route('/local_PromptTable', methods=['POST'])
def launch_prompt():
    data = request.json
    def run_prompt():
        app_prompt = cls_local_PromptTable(
            file_path=data.get("file_path", "prompts.json"),
            isDependOn=data.get("isDependOn", False),
            num_dossier=data.get("num_dossier", ""),
            nom_fichier=data.get("nom_fichier", ""),
            descriptif=data.get("descriptif", "")
        )
        app_prompt.mainloop()  # <-- Déplacé ici
    threading.Thread(target=run_prompt).start()
    return jsonify({"status": "prompt launched"}), 200



if __name__ == "__main__":
    applocal.run(port=5005, debug=True)
    # main()  # <-- SUPPRIMER ou COMMENTER cette ligne