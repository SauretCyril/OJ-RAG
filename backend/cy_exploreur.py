import os
import tkinter as tk
from tkinter import ttk, filedialog, Scale
from flask import Blueprint, request

exploreur = Blueprint('exploreur', __name__)

# Icônes Unicode pour différents types de fichiers
FILE_ICONS = {
    'default': '📄',  # Document générique
    'folder': '📁',   # Dossier
    'docx': '📘',     # Document Word
    'pdf': '📕',      # Document PDF
    'col':'🔨',# configuration columns
    'ask':'💬',# ask question to Doc
    'role':'👷'# Role
}


def get_file_icon(path):
    """
    Détermine l'icône à utiliser en fonction de l'extension du fichier.
    """
    if os.path.isdir(path):
        return FILE_ICONS['folder']
    
    _, extension = os.path.splitext(path)
    extension = extension[1:].lower()  # Enlever le point et convertir en minuscules
    
    return FILE_ICONS.get(extension, FILE_ICONS['default'])

def populate_treeview(tree, parent, path):
    """
    Remplit le Treeview avec les fichiers et répertoires à partir d'un chemin donné.
    """
    try:
        items = os.listdir(path)
        # Trier les items : d'abord les dossiers, puis les fichiers
        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if not os.path.isdir(os.path.join(path, item))]
        
        # Trier alphabétiquement
        dirs.sort()
        files.sort()
        
        # Ajouter les dossiers
        for item in dirs:
            item_path = os.path.join(path, item)
            icon = get_file_icon(item_path)
            node = tree.insert(parent, 'end', text=f"{icon} {item}", open=False, values=[item_path])
            # Ajouter un élément fictif pour permettre l'expansion
            tree.insert(node, 'end', text='...')
        
        # Ajouter les fichiers
        for item in files:
            item_path = os.path.join(path, item)
            icon = get_file_icon(item_path)
            tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path])
    except Exception as e:
        print(f"Erreur lors du listage du répertoire {path}: {e}")

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

def on_font_size_change(event, tree, style):
    """
    Gère le changement de taille de police.
    """
    font_size = event.widget.get()
    style.configure("Treeview", font=('Arial', font_size))
    # Mettre à jour l'info-bulle du slider
    event.widget.config(label=f"Taille de la police : {font_size}")

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
    dir = request.json.get('path')  # Récupérer le répertoire initial depuis la requête
    if not dir or not os.path.exists(dir):
        return {"error": "Le répertoire spécifié est invalide ou n'existe pas."}, 400

    # Créer la fenêtre principale
    root = tk.Tk()
    root.title("Explorateur Arborescent de Fichiers et Répertoires")
    root.geometry("700x500")  # Augmenter légèrement la taille de la fenêtre

    # Créer un cadre pour les contrôles
    control_frame = tk.Frame(root)
    control_frame.pack(fill='x', padx=10, pady=5)

    # Ajouter un slider pour ajuster la taille de la police
    font_size_label = tk.Label(control_frame, text="Taille de la police :")
    font_size_label.pack(side='left', padx=(0, 10))
    
    font_size_slider = Scale(control_frame, from_=8, to=20, orient='horizontal', 
                             length=200, resolution=1)
    font_size_slider.set(10)  # Valeur par défaut
    font_size_slider.pack(side='left')

    # Ajouter un Treeview pour afficher les fichiers et répertoires
    tree = ttk.Treeview(root, columns=("fullpath",), displaycolumns=())
    tree.heading('#0', text='Nom')
    tree.pack(fill='both', expand=True, padx=10, pady=10)

    # Ajouter une barre de défilement
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    scrollbar.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar.set)

    # Ajouter un label pour afficher le résultat
    label_result = tk.Label(root, text="Aucun répertoire sélectionné.", wraplength=600, justify="left")
    label_result.pack(pady=10)

    # Configurer le style des éléments du Treeview pour une meilleure lisibilité
    style = ttk.Style()
    style.configure("Treeview", font=('Arial', 10))  # Police par défaut
    
    # Lier le changement de taille de police au Treeview
    font_size_slider.bind("<ButtonRelease-1>", lambda e: on_font_size_change(e, tree, style))
    
    # Remplir l'arborescence avec le répertoire initial
    open_directory_explorer(tree, label_result, dir)

    # Lier les événements
    tree.bind('<<TreeviewOpen>>', on_tree_expand)  # Expansion des répertoires
    tree.bind('<Double-1>', on_file_click)  # Double-clic sur un fichier

    # Lancer la boucle principale
    root.mainloop()

    return {"status": "Explorateur ouvert avec succès."}, 200

