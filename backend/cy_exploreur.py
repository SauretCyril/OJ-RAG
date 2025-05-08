import os
import tkinter as tk
from tkinter import ttk, filedialog, Scale
from flask import Blueprint, request

exploreur = Blueprint('exploreur', __name__)

# Dictionnaire pour suivre l'état des filtres
active_filters = {}

# Définition des icônes et de leurs couleurs associées
FILE_TYPES = {
    'default': {'icon': '📄', 'color': '#e0e0e0'},    # Gris clair
    'folder': {'icon': '📁', 'color': '#f7df1e'},     # Bleu dossier
    'docx': {'icon': '📝', 'color': '#2b579a'},       # Bleu Word
    # 'doc': {'icon': '📝', 'color': '#2b579a'},        # Bleu Word
     'pdf': {'icon': '📕', 'color': '#c43e1c'},        # Rouge PDF
    # 'txt': {'icon': '📃', 'color': '#7c8ea9'},        # Gris bleuté
    # 'jpg': {'icon': '🖼️', 'color': '#9a329b'},       # Violet
    # 'jpeg': {'icon': '🖼️', 'color': '#9a329b'},      # Violet
    # 'png': {'icon': '🖼️', 'color': '#6a4c93'},       # Violet foncé
    # 'gif': {'icon': '🖼️', 'color': '#8b4fcb'},       # Violet moyen
    # 'mp3': {'icon': '🎵', 'color': '#1db954'},        # Vert Spotify
    # 'wav': {'icon': '🎵', 'color': '#66b3cc'},        # Bleu ciel
    # 'mp4': {'icon': '🎬', 'color': '#2793e6'},        # Bleu vidéo
    # 'avi': {'icon': '🎬', 'color': '#3d85c6'},        # Bleu vidéo foncé
    # 'zip': {'icon': '🗜️', 'color': '#7e6551'},       # Marron clair
    # 'rar': {'icon': '🗜️', 'color': '#6a5043'},       # Marron foncé
    # 'py': {'icon': '🐍', 'color': '#3775a9'},         # Bleu Python
    # 'js': {'icon': '📜', 'color': '#f7df1e'},         # Jaune JavaScript
    # 'html': {'icon': '🌐', 'color': '#e34c26'},       # Orange HTML
    # 'css': {'icon': '🎨', 'color': '#264de4'},        # Bleu CSS
    # 'json': {'icon': '{ }', 'color': '#5ba478'},      # Vert JSON
    'col': {'icon': '🔨', 'color': '#5ba478'},        # Orange-marron
    'ask': {'icon': '💬', 'color': '#5ba478'},        # Violet
    'role': {'icon': '👷', 'color': '#5ba478'},       # Orange
    'data.json': {'icon': '📊', 'color': '#5ba478'},# Vert JSON
    'clas': {'icon': '⚙️', 'color': '#5ba478'},
     'conf': {'icon': '🛠️', 'color': '#5ba478'},
     'exclued': {'icon': '👁️', 'color': '#5ba478'}
}

# Définition des groupes de fichiers pour le filtrage
FILE_GROUPS = {
    'Documents': {
        'icon': '📚',
        'types': ['pdf', 'docx', 'default'],
        'color': '#2b579a'
    },
    'Configuration': {
        'icon': '⚙️',
        'types': ['conf', 'clas', 'data.json'],
        'color': '#5ba478'
    },
    'Données': {
        'icon': '🗂️',
        'types': ['col', 'ask', 'role', 'exclued'],
        'color': '#9a329b'
    }
}

# Définition des filtres par motif de nom de fichier
NAME_FILTERS = {
    'CV': {
        'icon': '📋',
        'pattern': '_CV_',
        'color': '#ff6b6b'  # Rouge vif
    }
    # Vous pouvez ajouter d'autres filtres par nom ici
}

def initialize_filters():
    """
    Initialise tous les filtres à actif (True)
    """
    global active_filters
    # Initialiser les filtres par groupe
    for group_name in FILE_GROUPS:
        active_filters[group_name] = True
    
    # Initialiser les filtres par motif de nom
    for filter_name in NAME_FILTERS:
        active_filters[filter_name] = True
    
    # Assurer que le filtre folder est toujours actif (les dossiers sont toujours affichés)
    active_filters['folder'] = True

def get_file_type(path):
    """
    Détermine le type de fichier et renvoie ses informations (icône et couleur).
    """
    if os.path.isdir(path):
        return FILE_TYPES['folder']
    
    # Extraction du nom du fichier et de l'extension
    filename = os.path.basename(path)
    
    # Cas spécial : si le nom du fichier commence par un point (fichier caché ou juste une extension)
    if filename.startswith('.'):
        extension = filename[1:].lower()  # On prend tout après le point
        if extension in FILE_TYPES:
            return FILE_TYPES[extension]
    
    # Cas normal : extraction de l'extension
    _, extension = os.path.splitext(path)
    extension = extension[1:].lower() if extension else ""  # Enlever le point et convertir en minuscules
    
    # Vérifier l'extension dans FILE_TYPES
    if extension in FILE_TYPES:
        return FILE_TYPES[extension]
    else:
        return FILE_TYPES['default']

def setup_file_tags(tree):
    """
    Configure les tags de couleur pour les différents types de fichiers.
    """
    for file_type, info in FILE_TYPES.items():
        color = info['color']
        # Créer un tag pour chaque couleur unique
        tag_name = f"color_{color.replace('#', '')}"
        tree.tag_configure(tag_name, foreground=color)  # Appliquer la couleur au texte

def populate_treeview(tree, parent, path):
    """
    Remplit le Treeview avec les fichiers et répertoires à partir d'un chemin donné.
    Prend en compte les filtres actifs pour afficher uniquement les types de fichiers sélectionnés.
    """
    try:
        items = os.listdir(path)
        # Trier les items : d'abord les dossiers, puis les fichiers
        dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
        files = [item for item in items if not os.path.isdir(os.path.join(path, item))]
        
        # Trier alphabétiquement
        dirs.sort()
        files.sort()
        
        # Ajouter les dossiers (toujours affichés)
        for item in dirs:
            item_path = os.path.join(path, item)
            file_info = get_file_type(item_path)
            icon = file_info['icon']
            color = file_info['color']
            
            # Ajouter avec tag de couleur personnalisé pour l'icône
            node = tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path], tags=(f"color_{color.replace('#', '')}",))
            
            # Ajouter un élément fictif pour permettre l'expansion
            tree.insert(node, 'end', text='...', values=["dummy"])
        
        # Vérifier s'il y a des filtres par nom actifs
        active_name_filters = {name: info['pattern'] for name, info in NAME_FILTERS.items() 
                               if active_filters.get(name, False)}
        
        # Ajouter les fichiers en tenant compte des filtres
        for item in files:
            item_path = os.path.join(path, item)
            
            # Si des filtres par nom sont actifs, vérifier si le fichier correspond à au moins un des motifs
            if active_name_filters:
                # Par défaut, on exclut le fichier s'il ne correspond à aucun filtre actif
                should_display = False
                
                # Vérifier si le fichier correspond à au moins un des motifs de filtres actifs
                for filter_name, pattern in active_name_filters.items():
                    if pattern in item:
                        should_display = True
                        break
                
                # Si le fichier ne correspond à aucun filtre actif, passer au suivant
                if not should_display:
                    continue
            
            file_type = get_file_extension(item_path)
            file_info = get_file_type(item_path)
            icon = file_info['icon']
            color = file_info['color']
            
            # Ajouter avec tag de couleur personnalisé
            tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path], tags=(f"color_{color.replace('#', '')}",))
    except Exception as e:
        print(f"Erreur lors du peuplement de l'arborescence : {e}")
        import traceback
        traceback.print_exc()

def get_file_extension(path):
    """
    Retourne le type de fichier pour le filtrage.
    Pour les groupes de filtres, identifie à quel groupe appartient le fichier.
    Pour les filtres par nom, vérifie si le nom du fichier contient le motif spécifié.
    """
    if os.path.isdir(path):
        return 'folder'
    
    filename = os.path.basename(path)
    
    # Vérifier si le nom du fichier correspond à un filtre par motif
    for filter_name, filter_info in NAME_FILTERS.items():
        if filter_info['pattern'] in filename:
            return filter_name
    
    # Extraction de l'extension
    _, extension = os.path.splitext(path)
    extension = extension[1:].lower() if extension else ""
    
    # Vérification des types de fichiers spéciaux
    file_type = None
    
    # Vérifier les fichiers spéciaux par leur nom complet
    for special_type in ['data.json', 'col', 'ask', 'role', 'clas', 'conf', 'exclued']:
        if filename.endswith(special_type):
            file_type = special_type
            break
    
    # Si pas de type spécial, utiliser l'extension
    if file_type is None:
        file_type = extension if extension in FILE_TYPES else 'default'
    
    # Déterminer à quel groupe appartient ce type de fichier
    for group_name, group_info in FILE_GROUPS.items():
        if file_type in group_info['types']:
            return group_name
    
    # Si le fichier n'appartient à aucun groupe défini, le considérer comme 'default'
    return 'Documents'  # Par défaut, dans le groupe Documents

def on_tree_expand(event):
    """
    Gère l'expansion d'un élément dans le Treeview.
    """
    tree = event.widget
    node = tree.focus()
    
    # Vérifier si c'est un élément qui peut être développé
    children = tree.get_children(node)
    if len(children) == 1 and tree.item(children[0], "text") == "...":
        # C'est un dossier non développé
        path = tree.item(node, "values")[0]
        
        # Supprimer l'élément fictif
        tree.delete(children[0])
        
        # Remplir avec le contenu du dossier
        try:
            populate_treeview(tree, node, path)
        except Exception as e:
            print(f"Erreur lors de l'expansion du dossier {path}: {e}")
            import traceback
            traceback.print_exc()

def on_file_click(event):
    """
    Gère le clic sur un fichier dans le Treeview.
    Si le fichier est un .docx, il est ouvert avec Microsoft Word.
    """
    tree = event.widget
    node = tree.focus()
    path = tree.item(node, 'values')[0]

    #if os.path.isfile(path) and path.endswith('.docx'):
    try:
        os.startfile(path)  # Ouvre le fichier avec l'application par défaut
    except Exception as e:
        print(f"Erreur lors de l'ouverture du fichier : {e}")
        if os.path.isfile(path):
            if path.endswith('.docx'):
                try:
                    os.startfile(path)  # Ouvre le fichier avec Microsoft Word
                except Exception as e:
                    print(f"Erreur lors de l'ouverture du fichier Word : {e}")
            elif path.endswith('.pdf'):
                try:
                    os.system(f'start {path}')  # Ouvre le fichier PDF avec l'application par défaut
                except Exception as e:
                    print(f"Erreur lors de l'ouverture du fichier PDF : {e}")
            elif path.endswith('.xlsx'):
                try:
                    os.system(f'start excel "{path}"')  # Ouvre le fichier Excel avec Microsoft Excel
                except Exception as e:
                    print(f"Erreur lors de l'ouverture du fichier Excel : {e}")

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

def toggle_filter(filter_name, button, tree, current_path, label_result):
    """
    Active ou désactive un filtre et rafraîchit l'affichage du Treeview
    """
    global active_filters
    
    # Inverser l'état du filtre
    active_filters[filter_name] = not active_filters[filter_name]
    
    # Mettre à jour l'apparence du bouton
    if active_filters[filter_name]:
        button.config(relief=tk.SUNKEN, bg="#d3d3d3")  # Bouton désactivé
    else:   
        button.config(relief=tk.RAISED, bg="#a0d2eb")  # Bouton activé
   
        
    
    # Rafraîchir l'affichage
    refresh_treeview(tree, current_path, label_result)

def refresh_treeview(tree, current_path, label_result):
    """
    Rafraîchit l'affichage du Treeview en fonction des filtres actifs
    """
    # Sauvegarder les éléments développés
    expanded_items = []
    for item in get_all_items(tree):
        if tree.item(item, "open"):
            item_path = tree.item(item, "values")[0]
            expanded_items.append(item_path)
    
    # Réinitialiser et repeupler l'arborescence
    tree.delete(*tree.get_children())
    populate_treeview(tree, '', current_path)
    
    # Redévelopper les éléments qui étaient développés
    expand_saved_items(tree, '', expanded_items)
    
    # Mettre à jour le label d'information
    label_result.config(text=f"Répertoire: {current_path} | Filtres actifs: {count_active_filters()}/{len(active_filters)}")

def get_all_items(tree, parent=''):
    """
    Récupère tous les éléments du Treeview de façon récursive
    """
    items = []
    for item in tree.get_children(parent):
        items.append(item)
        items.extend(get_all_items(tree, item))
    return items

def expand_saved_items(tree, parent, expanded_paths):
    """
    Redéveloppe les éléments qui étaient développés avant le rafraîchissement
    """
    for item in tree.get_children(parent):
        item_path = tree.item(item, "values")[0]
        if item_path in expanded_paths and os.path.isdir(item_path):
            tree.item(item, open=True)
            # Vérifier si l'élément a un élément fictif
            children = tree.get_children(item)
            if len(children) == 1 and tree.item(children[0], "text") == "...":
                tree.delete(children[0])  # Supprimer l'élément fictif
                populate_treeview(tree, item, item_path)  # Remplir avec le contenu du dossier
            expand_saved_items(tree, item, expanded_paths)

def count_active_filters():
    """
    Compte le nombre de filtres actuellement actifs
    """
    return sum(1 for value in active_filters.values() if value)

def create_filter_buttons(parent, tree, current_path, label_result):
    """
    Crée le cadre contenant les boutons de filtre pour les différents groupes de fichiers
    """
    # Initialiser les filtres
    initialize_filters()
    
    # Créer un cadre pour les boutons de filtres
    filter_frame = tk.Frame(parent)
    filter_frame.pack(fill='x', padx=10, pady=5)
    
    # Ajouter une étiquette pour les filtres
    filter_label = tk.Label(filter_frame, text="Filtres :")
    filter_label.pack(side='left', padx=(0, 10))
    
    # Créer un bouton pour chaque groupe de fichiers
    buttons = {}
    # for group_name, group_info in FILE_GROUPS.items():
    #     button = tk.Button(
    #         filter_frame, 
    #         text=f"{group_info['icon']} {group_name}", 
    #         relief=tk.RAISED, 
    #         bg="#a0d2eb",
    #         fg=group_info['color'],
    #         padx=5,
    #         pady=2,
    #         command=lambda grp=group_name, btn=None: toggle_filter(grp, btn, tree, current_path, label_result)
    #     )
    #     button.pack(side='left', padx=2)
        
    #     # Stocker la référence au bouton et mettre à jour la commande
    #     buttons[group_name] = button
    #     button.config(command=lambda grp=group_name, btn=button: toggle_filter(grp, btn, tree, current_path, label_result))
    
    # # Ajouter un séparateur visuel
    # separator = tk.Frame(filter_frame, width=1, height=20, bg='#cccccc')
    # separator.pack(side='left', padx=5, pady=0)
    
    # Ajouter des boutons pour les filtres par motif de nom de fichier
    for filter_name, filter_info in NAME_FILTERS.items():
        pattern_button = tk.Button(
            filter_frame, 
            text=f"{filter_info['icon']} {filter_name}", 
            relief=tk.RAISED, 
            bg="#a0d2eb",
            fg=filter_info['color'],
            padx=5,
            pady=2,
            command=lambda f=filter_name, btn=None: toggle_filter(f, btn, tree, current_path, label_result)
        )
        pattern_button.pack(side='left', padx=2)
        
        # Stocker la référence au bouton et mettre à jour la commande
        buttons[filter_name] = pattern_button
        pattern_button.config(command=lambda f=filter_name, btn=pattern_button: toggle_filter(f, btn, tree, current_path, label_result))
    
    # Ajouter un bouton pour tout sélectionner/désélectionner
    select_all_button = tk.Button(
        filter_frame,
        text="🔍 Tous",
        relief=tk.RAISED,
        bg="#a0d2eb",
        padx=5,
        pady=2,
        command=lambda: toggle_all_filters(buttons, tree, current_path, label_result)
    )
    select_all_button.pack(side='left', padx=(10, 2))
    
    return filter_frame, buttons

def toggle_all_filters(buttons, tree, current_path, label_result):
    """
    Active ou désactive tous les filtres à la fois
    """
    global active_filters
    
    # Déterminer si la majorité des filtres sont activés
    active_count = sum(1 for value in active_filters.values() if value and value != 'folder')
    total_count = len(active_filters) - 1  # -1 pour ignorer 'folder'
    
    # Si la majorité est active, désactiver tous, sinon activer tous
    new_state = active_count <= total_count / 2
    
    # Mettre à jour tous les filtres sauf 'folder'
    for file_type, button in buttons.items():
        active_filters[file_type] = new_state
        
        # Mettre à jour l'apparence du bouton
        if new_state:
            button.config(relief=tk.RAISED, bg="#a0d2eb")  # Bouton activé
        else:
            button.config(relief=tk.SUNKEN, bg="#d3d3d3")  # Bouton désactivé
    
    # Assurer que le filtre 'folder' est toujours actif
    active_filters['folder'] = True
    
    # Rafraîchir l'affichage
    refresh_treeview(tree, current_path, label_result)

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
    style.configure("Treeview", font=('Arial', 12))  # Police par défaut
    
    # Configurer les tags de couleur pour les différents types de fichiers
    setup_file_tags(tree)
    
    # Lier le changement de taille de police au Treeview
    font_size_slider.bind("<ButtonRelease-1>", lambda e: on_font_size_change(e, tree, style))
    
    # Créer les boutons de filtre
    create_filter_buttons(control_frame, tree, dir, label_result)
    
    # Remplir l'arborescence avec le répertoire initial
    open_directory_explorer(tree, label_result, dir)

    # Lier les événements
    tree.bind('<<TreeviewOpen>>', on_tree_expand)  # Expansion des répertoires
    tree.bind('<Double-1>', on_file_click)  # Double-clic sur un fichier

    # Lancer la boucle principale
    root.mainloop()

    return {"status": "Explorateur ouvert avec succès."}, 200


