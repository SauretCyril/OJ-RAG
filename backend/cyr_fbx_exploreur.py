#blender --background --python ton_script.py
from flask import Blueprint, request, jsonify
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
cy_fbx = Blueprint('cy_fbx', __name__)
FBX_ICON = "🗂️"

def launch_fbxreview(fbx_path):
    exe_path = os.getenv("FBXREVIEW_EXE_PATH", "G:/G_WCS/OJ-RAG/exe/fbxreview.exe")
    subprocess.Popen([exe_path, fbx_path])

class FBXExplorer:
    def __init__(self, initial_dir=None):
        self.initial_dir = initial_dir if initial_dir and os.path.exists(initial_dir) else os.getcwd()
        self.root = None
        self.tree = None

    def populate_treeview(self, parent, path):
        try:
            for root, dirs, files in os.walk(path):
                files = [f for f in files if f.lower().endswith('.fbx')]
                files.sort()
                for item in files:
                    item_path = os.path.join(root, item)
                    self.tree.insert(
                        parent,
                        'end',
                        text=f"{item_path} {FBX_ICON} {item}",
                        values=[item_path]
                    )
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des fichiers : {e}")

    def on_file_double_click(self, event):
        node = self.tree.focus()
        path = self.tree.item(node, 'values')[0]
        try:
            launch_fbxreview(path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier : {e}")

    def run(self):
        self.root = tk.Tk()
        self.root.title("Explorateur FBX")
        self.root.geometry("600x400")

        # Bouton pour changer de dossier
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill='x', padx=10, pady=5)
        change_btn = tk.Button(btn_frame, text="Changer de dossier", command=self.change_directory)
        change_btn.pack(side='left')

        # Treeview pour les fichiers FBX
        self.tree = ttk.Treeview(self.root, columns=("fullpath",), displaycolumns=())
        self.tree.heading('#0', text='Nom du fichier FBX')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

        self.populate_treeview('', self.initial_dir)

        self.tree.bind('<Double-1>', self.on_file_double_click)

        self.root.mainloop()

    def change_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.initial_dir, title="Sélectionner un dossier")
        if new_dir:
            self.initial_dir = new_dir
            self.tree.delete(*self.tree.get_children())
            self.populate_treeview('', self.initial_dir)

@cy_fbx.route('/launch_fbxreview', methods=['POST'])
def api_launch_fbxreview():
    data = request.get_json()
    fbx_path = data.get('fbx_path')
    if not fbx_path or not os.path.exists(fbx_path):
        return jsonify({'error': 'Chemin FBX invalide'}), 400
    try:
        launch_fbxreview(fbx_path)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    explorer = FBXExplorer(initial_dir="H:/Entreprendre/Actions-11-Projects")  # Mets ton dossier par défaut ici
    explorer.run()