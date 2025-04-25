import os
import tkinter as tk
from tkinter import ttk, filedialog
from flask import Blueprint, request

exploreur = Blueprint('exploreur', __name__)

def populate_treeview(tree, parent, path):
    """
    Remplit le Treeview avec les fichiers et répertoires à partir d'un chemin donné.
    """
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        is_dir = os.path.isdir(item_path)
        node = tree.insert(parent, 'end', text=item, open=False, values=[item_path])
        if is_dir:
            # Ajouter un élément fictif pour permettre l'expansion
            tree.insert(node, 'end', text='...')

def on_tree_expand(event):
    """
    Gère l'expansion d'un élément dans le Treeview.
    """
    tree = event.widget
    node = tree.focus()
    path = tree.item(node, 'values')[0]

    # Supprimer les éléments fictifs
    tree.delete(*tree.get_children(node))

    # Ajouter les fichiers et répertoires enfants
    populate_treeview(tree, node, path)

def on_file_click(event):
    """
    Gère le clic sur un fichier dans le Treeview.
    Si le fichier est un .docx, il est ouvert avec Microsoft Word.
    """
    tree = event.widget
    node = tree.focus()
    path = tree.item(node, 'values')[0]

    if os.path.isfile(path) and path.endswith('.docx'):
        try:
            os.startfile(path)  # Ouvre le fichier avec l'application par défaut (Microsoft Word)
        except Exception as e:
            print(f"Erreur lors de l'ouverture du fichier : {e}")

def open_directory_explorer(tree, label_result, initial_dir):
    """
    Ouvre un explorateur de répertoires pour afficher un dossier initial et son contenu.
    """
    if initial_dir and os.path.exists(initial_dir):
        tree.delete(*tree.get_children())  # Réinitialiser l'arborescence
        populate_treeview(tree, '', initial_dir)
        label_result.config(text=f"Répertoire sélectionné : {initial_dir}")
    else:
        label_result.config(text="Le répertoire spécifié n'existe pas.")

@exploreur.route('/open_exploreur', methods=['POST'])
def open_exploreur():
    dir = request.json.get('dir')  # Récupérer le répertoire initial depuis la requête
    if not dir or not os.path.exists(dir):
        return {"error": "Le répertoire spécifié est invalide ou n'existe pas."}, 400

    # Créer la fenêtre principale
    root = tk.Tk()
    root.title("Explorateur Arborescent de Fichiers et Répertoires")
    root.geometry("600x400")

    # Ajouter un Treeview pour afficher les fichiers et répertoires
    tree = ttk.Treeview(root, columns=("fullpath",), displaycolumns=())
    tree.heading('#0', text='Nom')
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    # Ajouter un label pour afficher le résultat
    label_result = tk.Label(root, text="Aucun répertoire sélectionné.", wraplength=400, justify="left")
    label_result.pack(pady=10)

    # Remplir l'arborescence avec le répertoire initial
    open_directory_explorer(tree, label_result, dir)

    # Lier les événements
    tree.bind('<<TreeviewOpen>>', on_tree_expand)  # Expansion des répertoires
    tree.bind('<Double-1>', on_file_click)  # Double-clic sur un fichier

    # Lancer la boucle principale
    root.mainloop()

    return {"status": "Explorateur ouvert avec succès."}, 200

