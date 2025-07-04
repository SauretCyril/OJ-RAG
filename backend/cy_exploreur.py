import os
import tkinter as tk
from tkinter import ttk, filedialog, Scale
from flask import Blueprint, request

exploreur = Blueprint('exploreur', __name__)

class FileExplorer:
    """Classe générique pour l'explorateur de fichiers"""
    
    # Dictionnaire pour suivre l'état des filtres (statique par défaut)
    active_filters = {}
    
    # Définition des icônes et de leurs couleurs associées (par défaut)
    FILE_TYPES = {
        'default': {'icon': '📄', 'color': '#e0e0e0'},    # Gris clair
        'folder': {'icon': '📁', 'color': '#f7df1e'},     # Bleu dossier
        'docx': {'icon': '📝', 'color': '#2b579a'},       # Bleu Word
        'pdf': {'icon': '📕', 'color': '#c43e1c'},        # Rouge PDF
        'col': {'icon': '🔨', 'color': '#5ba478'},        # Orange-marron
        'ask': {'icon': '💬', 'color': '#5ba478'},        # Violet
        'role': {'icon': '👷', 'color': '#5ba478'},       # Orange
        'data.json': {'icon': '📊', 'color': '#5ba478'},  # Vert JSON
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
            'types': ['conf','col','exclued' ],
            'color': '#5ba478'
        },
        'Données': {
            'icon': '🗂️',
            'types': ['data.json'],
            'color': '#9a329b'
        },
         'IA': {
            'icon': '🗂️',
            'types': ['ask', 'role','clas'],
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
    }
    
    def __init__(self, title="Explorateur de Fichiers", initial_dir=None, explorer_type="standard"):
        """
        Initialisation de l'explorateur
        
        Args:
            title (str): Titre de la fenêtre
            initial_dir (str): Répertoire initial à afficher
            explorer_type (str): Type d'explorateur (standard, document, config, etc.)
        """
        self.title = title
        self.initial_dir = initial_dir
        self.explorer_type = explorer_type
        self.root = None
        self.tree = None
        self.label_result = None
        self.buttons = {}
        self.current_path = initial_dir if initial_dir and os.path.exists(initial_dir) else os.getcwd()
        
        # Initialiser les filtres selon le type d'explorateur
        self.initialize_filters()
        
        # Personnaliser l'explorateur selon son type
        self.customize_by_type()
    
    def customize_by_type(self):
        """Personnalise l'explorateur selon son type"""
        if self.explorer_type == "document":
            # Explorateur spécialisé pour les documents
            self.title = "Explorateur de Documents"
            # Filtrer uniquement les types de documents
            for group in list(self.FILE_GROUPS.keys()):
                if group != "Documents":  # CORRECTION: garder seulement "Documents"
                    self.FILE_GROUPS.pop(group)
            # Activer uniquement le filtre de documents
            for group in self.active_filters:
                self.active_filters[group] = (group == "Documents")
    
        elif self.explorer_type == "config":
            # Explorateur spécialisé pour les fichiers de configuration
            self.title = "Explorateur de Configuration"
            # Désactiver l'affichage des dossiers pour ce type d'explorateur
            self.active_filters['folder'] = False
            # Filtrer uniquement les types de configuration
            for group in list(self.FILE_GROUPS.keys()):
                if group != "Configuration":  # CORRECTION: garder seulement "Configuration"
                    self.FILE_GROUPS.pop(group)
            # Activer uniquement le filtre de configuration
            for group in self.active_filters:
                self.active_filters[group] = (group == "Configuration")
    
        elif self.explorer_type == "data":
            # Explorateur spécialisé pour les données
            self.title = "Explorateur de Données"
            # Filtrer uniquement les types de données
            for group in list(self.FILE_GROUPS.keys()):
                if group != "Données":  # CORRECTION: garder seulement "Données"
                    self.FILE_GROUPS.pop(group)
            # Activer uniquement le filtre de données
            for group in self.active_filters:
                self.active_filters[group] = (group == "Données")
      
        elif self.explorer_type == "IA":
            # Explorateur spécialisé pour les données IA
            self.title = "Explorateur paramétrage IA"
            # Filtrer uniquement les types IA
            for group in list(self.FILE_GROUPS.keys()):
                if group != "IA":  # CORRECTION: garder seulement "IA"
                    self.FILE_GROUPS.pop(group)
            # Activer uniquement le filtre IA
            for group in self.active_filters:
                self.active_filters[group] = (group == "IA")
        print (f"DBG-1234 = group ={self.active_filters}")   

    def initialize_filters(self):
        """Initialise tous les filtres à actif (True)"""
        self.active_filters = {}
      
        # Initialiser les filtres par groupe
        for group_name in self.FILE_GROUPS:
            self.active_filters[group_name] = False
        
        # Initialiser les filtres par motif de nom
        for filter_name in self.NAME_FILTERS:
            self.active_filters[filter_name] = False

        # Assurer que le filtre folder est toujours actif (les dossiers sont toujours affichés)
        self.active_filters['folder'] = True
    
    def get_file_type(self, path):
        """
        Détermine le type de fichier et renvoie ses informations (icône et couleur).
        """
        if os.path.isdir(path):
            return self.FILE_TYPES['folder']
        
        # Extraction du nom du fichier et de l'extension
        filename = os.path.basename(path)
        
        # Cas spécial : si le nom du fichier commence par un point (fichier caché ou juste une extension)
        if filename.startswith('.'):
            extension = filename[1:].lower()  # On prend tout après le point
            if extension in self.FILE_TYPES:
                return self.FILE_TYPES[extension]
        
        # Cas normal : extraction de l'extension
        _, extension = os.path.splitext(path)
        extension = extension[1:].lower() if extension else ""  # Enlever le point et convertir en minuscules
        
        # Vérifier l'extension dans FILE_TYPES
        if extension in self.FILE_TYPES:
            return self.FILE_TYPES[extension]
        else:
            return self.FILE_TYPES['default']
    
    def setup_file_tags(self):
        """Configure les tags de couleur pour les différents types de fichiers."""
        for file_type, info in self.FILE_TYPES.items():
            color = info['color']
            # Créer un tag pour chaque couleur unique
            tag_name = f"color_{color.replace('#', '')}"
            self.tree.tag_configure(tag_name, foreground=color)  # Appliquer la couleur au texte
    
    def populate_treeview(self, parent, path):
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
            
            # Ajouter les dossiers SEULEMENT si le filtre 'folder' est actif
            if self.active_filters.get('folder', True):  # Par défaut True si non défini
                for item in dirs:
                    item_path = os.path.join(path, item)
                    file_info = self.get_file_type(item_path)
                    icon = file_info['icon']
                    color = file_info['color']
                    
                    # Ajouter avec tag de couleur personnalisé pour l'icône
                    node = self.tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path], tags=(f"color_{color.replace('#', '')}",))
                    
                    # Ajouter un élément fictif pour permettre l'expansion
                    self.tree.insert(node, 'end', text='...', values=["dummy"])
        
          
       
            # Ajouter les fichiers en tenant compte des filtres
            for item in files:
                item_path = os.path.join(path, item)
                
       
                # Déterminer le type de fichier et son groupe
                file_type = self.get_file_extension(item_path)
                file_info = self.get_file_type(item_path)
                icon = file_info['icon']
                color = file_info['color']

                print (f"<FILE > fichier inserting {item}: => {file_type}")
                print (f"<FILEa> >self.FILE_GROUPS = {self.FILE_GROUPS}")

                is_in_active_group = False
                print (f"<FILEa> >self.FILE_GROUPS = {self.FILE_GROUPS}")
                if self.active_filters.get(file_type) or self.explorer_type == "standard":
                    self.tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path], 
                    tags=(f"color_{color.replace('#', '')}",))
        except Exception as e:
            print(f"Erreur lors du peuplement de l'arborescence : {e}")
            import traceback
            traceback.print_exc()
    
    def get_file_extension(self, path):
        """
        Retourne le type de fichier pour le filtrage.
        Pour les groupes de filtres, identifie à quel groupe appartient le fichier.
        Pour les filtres par nom, vérifie si le nom du fichier contient le motif spécifié.
        """
        if os.path.isdir(path):
            return 'folder'
        
        filename = os.path.basename(path)
        
        # Vérifier si le nom du fichier correspond à un filtre par motif
        for filter_name, filter_info in self.NAME_FILTERS.items():
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
            file_type = extension if extension in self.FILE_TYPES else 'default'
        
        # Déterminer à quel groupe appartient ce type de fichier
        for group_name, group_info in self.FILE_GROUPS.items():
            if file_type in group_info['types']:
                return group_name
        
        # Si le fichier n'appartient à aucun groupe défini, le considérer comme 'default'
        return 'Documents'  # Par défaut, dans le groupe Documents
    
    def on_tree_expand(self, event):
        """Gère l'expansion d'un élément dans le Treeview."""
        node = self.tree.focus()
        
        # Vérifier si c'est un élément qui peut être développé
        children = self.tree.get_children(node)
        if len(children) == 1 and self.tree.item(children[0], "text") == "...":
            # C'est un dossier non développé
            path = self.tree.item(node, "values")[0]
            
            # Supprimer l'élément fictif
            self.tree.delete(children[0])
            
            # Remplir avec le contenu du dossier
            try:
                self.populate_treeview(node, path)
            except Exception as e:
                print(f"Erreur lors de l'expansion du dossier {path}: {e}")
                import traceback
                traceback.print_exc()
    
    def on_file_click(self, event):
        """
        Gère le clic sur un fichier dans le Treeview.
        Si le fichier est un .docx, il est ouvert avec Microsoft Word.
        """
        node = self.tree.focus()
        path = self.tree.item(node, 'values')[0]

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
    
    def on_font_size_change(self, event, style):
        """Gère le changement de taille de police."""
        font_size = event.widget.get()
        style.configure("Treeview", font=('Arial', font_size))
        # Mettre à jour l'info-bulle du slider
        event.widget.config(label=f"Taille de la police : {font_size}")
    
    def open_directory_explorer(self):
        """Ouvre un explorateur de répertoires pour afficher un dossier initial et son contenu."""
        if self.initial_dir and os.path.exists(self.initial_dir):
            self.tree.delete(*self.tree.get_children())  # Réinitialiser l'arborescence
            self.populate_treeview('', self.initial_dir)
            self.label_result.config(text=f"Répertoire sélectionné : {self.initial_dir}")
            self.current_path = self.initial_dir
        else:
            self.label_result.config(text="Le répertoire spécifié n'existe pas.")
    
    def toggle_filter(self, filter_name, button):
        """Active ou désactive un filtre et rafraîchit l'affichage du Treeview"""
        # Inverser l'état du filtre
        self.active_filters[filter_name] = not self.active_filters[filter_name]
        
        # Mettre à jour l'apparence du bouton
        if self.active_filters[filter_name]:
            button.config(relief=tk.SUNKEN, bg="#d3d3d3")  # Bouton désactivé
        else:   
            button.config(relief=tk.RAISED, bg="#a0d2eb")  # Bouton activé
        
        # Rafraîchir l'affichage
        self.refresh_treeview()
    
    def refresh_treeview(self):
        """Rafraîchit l'affichage du Treeview en fonction des filtres actifs"""
        # Sauvegarder les éléments développés
        expanded_items = []
        for item in self.get_all_items():
            if self.tree.item(item, "open"):
                item_path = self.tree.item(item, "values")[0]
                expanded_items.append(item_path)
        
        # Réinitialiser et repeupler l'arborescence
        self.tree.delete(*self.tree.get_children())
        self.populate_treeview('', self.current_path)
        
        # Redévelopper les éléments qui étaient développés
        self.expand_saved_items('', expanded_items)
        
        # Mettre à jour le label d'information
        self.label_result.config(text=f"Répertoire: {self.current_path} | Filtres actifs: {self.count_active_filters()}/{len(self.active_filters)}")
    
    def get_all_items(self, parent=''):
        """Récupère tous les éléments du Treeview de façon récursive"""
        items = []
        for item in self.tree.get_children(parent):
            items.append(item)
            items.extend(self.get_all_items(item))
        return items
    
    def expand_saved_items(self, parent, expanded_paths):
        """Redéveloppe les éléments qui étaient développés avant le rafraîchissement"""
        for item in self.tree.get_children(parent):
            item_path = self.tree.item(item, "values")[0]
            if item_path in expanded_paths and os.path.isdir(item_path):
                self.tree.item(item, open=True)
                # Vérifier si l'élément a un élément fictif
                children = self.tree.get_children(item)
                if len(children) == 1 and self.tree.item(children[0], "text") == "...":
                    self.tree.delete(children[0])  # Supprimer l'élément fictif
                    self.populate_treeview(item, item_path)  # Remplir avec le contenu du dossier
                self.expand_saved_items(item, expanded_paths)
    
    def count_active_filters(self):
        """Compte le nombre de filtres actuellement actifs"""
        return sum(1 for value in self.active_filters.values() if value)
    
    def create_filter_buttons(self, parent):
        """Crée le cadre contenant les boutons de filtre pour les différents groupes de fichiers"""
        # Créer un cadre pour les boutons de filtres
        filter_frame = tk.Frame(parent)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        # Ajouter une étiquette pour les filtres
        filter_label = tk.Label(filter_frame, text="Filtres :")
        filter_label.pack(side='left', padx=(0, 10))
        
        # Créer un bouton pour chaque groupe de fichiers
        buttons = {}
        for group_name, group_info in self.FILE_GROUPS.items():
            button = tk.Button(
                filter_frame, 
                text=f"{group_info['icon']} {group_name}", 
                relief=tk.RAISED, 
                bg="#a0d2eb",
                fg=group_info['color'],
                padx=5,
                pady=2
            )
            button.pack(side='left', padx=2)
            
            # Stocker la référence au bouton et mettre à jour la commande
            buttons[group_name] = button
            button.config(command=lambda grp=group_name, btn=button: self.toggle_filter(grp, btn))
        
        # Ajouter un séparateur visuel
        separator = tk.Frame(filter_frame, width=1, height=20, bg='#cccccc')
        separator.pack(side='left', padx=5, pady=0)
        
        # Ajouter des boutons pour les filtres par motif de nom de fichier
        for filter_name, filter_info in self.NAME_FILTERS.items():
            pattern_button = tk.Button(
                filter_frame, 
                text=f"{filter_info['icon']} {filter_name}", 
                relief=tk.RAISED, 
                bg="#a0d2eb",
                fg=filter_info['color'],
                padx=5,
                pady=2
            )
            pattern_button.pack(side='left', padx=2)
            
            # Stocker la référence au bouton et mettre à jour la commande
            buttons[filter_name] = pattern_button
            pattern_button.config(command=lambda f=filter_name, btn=pattern_button: self.toggle_filter(f, btn))
        
        # Ajouter un bouton pour tout sélectionner/désélectionner
        select_all_button = tk.Button(
            filter_frame,
            text="🔍 Tous",
            relief=tk.RAISED,
            bg="#a0d2eb",
            padx=5,
            pady=2,
            command=lambda: self.toggle_all_filters(buttons)
        )
        select_all_button.pack(side='left', padx=(10, 2))
        
        self.buttons = buttons
        return filter_frame
    
    def toggle_all_filters(self, buttons):
        """Active ou désactive tous les filtres à la fois"""
        # Déterminer si la majorité des filtres sont activés
        active_count = sum(1 for value in self.active_filters.values() if value and value != 'folder')
        total_count = len(self.active_filters) - 1  # -1 pour ignorer 'folder'
        
        # Si la majorité est active, désactiver tous, sinon activer tous
        new_state = active_count <= total_count / 2
        
        # Mettre à jour tous les filtres sauf 'folder'
        for file_type, button in buttons.items():
            self.active_filters[file_type] = new_state
            
            # Mettre à jour l'apparence du bouton
            if new_state:
                button.config(relief=tk.RAISED, bg="#a0d2eb")  # Bouton activé
            else:
                button.config(relief=tk.SUNKEN, bg="#d3d3d3")  # Bouton désactivé
        
        # Assurer que le filtre 'folder' est toujours actif
        #self.active_filters['folder'] = True
        
        # Rafraîchir l'affichage
        self.refresh_treeview()
    
    def run(self):
        """Lance l'interface graphique de l'explorateur"""
        # Créer la fenêtre principale
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("800x600")  # Taille de la fenêtre
        
        # Créer un cadre pour les contrôles
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Ajouter un slider pour ajuster la taille de la police
        #font_size_label = tk.Label(control_frame, text="Taille de la police :")
        #font_size_label.pack(side='left', padx=(0, 10))
        
        #font_size_slider = Scale(control_frame, from_=8, to=20, orient='horizontal', 
        #                        length=200, resolution=1)
        #font_size_slider.set(10)  # Valeur par défaut
        #font_size_slider.pack(side='left')
        
        # Ajouter un Treeview pour afficher les fichiers et répertoires
        self.tree = ttk.Treeview(self.root, columns=("fullpath",), displaycolumns=())
        self.tree.heading('#0', text='Nom')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Ajouter une barre de défilement
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Ajouter un label pour afficher le résultat
        self.label_result = tk.Label(self.root, text="Aucun répertoire sélectionné.", wraplength=600, justify="left")
        self.label_result.pack(pady=10)
        
        # Configurer le style des éléments du Treeview pour une meilleure lisibilité
        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 10))  # Police par défaut
        
        # Configurer les tags de couleur pour les différents types de fichiers
        self.setup_file_tags()
        
        # Lier le changement de taille de police au Treeview
        #font_size_slider.bind("<ButtonRelease-1>", lambda e: self.on_font_size_change(e, style))
        
        # Créer les boutons de filtre
        #self.create_filter_buttons(control_frame)
        
        # Remplir l'arborescence avec le répertoire initial
        self.open_directory_explorer()
        
        # Lier les événements
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_expand)  # Expansion des répertoires
        self.tree.bind('<Double-1>', self.on_file_click)  # Double-clic sur un fichier
        
        # Lancer la boucle principale
        self.root.mainloop()
        
        return True  # Indiquer que l'explorateur s'est terminé avec succès


# Créer des classes d'explorateurs spécialisés
class DocumentExplorer(FileExplorer):
    """Explorateur spécialisé pour les documents"""
    
    def __init__(self, title="Explorateur de Documents", initial_dir=None):
        super().__init__(title, initial_dir, explorer_type="document")


class DataExplorer(FileExplorer):
    """Explorateur spécialisé pour les données"""
    
    def __init__(self, title="Explorateur de Données", initial_dir=None):
        super().__init__(title, initial_dir, explorer_type="data")


class ConfigExplorer(FileExplorer):
    """Explorateur spécialisé pour les fichiers de configuration"""
    
    def __init__(self, title="Explorateur de Configuration", initial_dir=None):
        super().__init__(title, initial_dir, explorer_type="config")


    # def populate_treeview(self, parent, path):
    #     """
    #     Remplit le Treeview avec UNIQUEMENT les fichiers du répertoire courant.
    #     Ne montre pas les sous-répertoires et n'ajoute pas d'éléments fictifs pour l'expansion.
    #     """
    #     try:
    #         items = os.listdir(path)
            
    #         # Ne garder que les fichiers (ignorer les répertoires)
    #         files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            
    #         # Trier alphabétiquement
    #         files.sort()
            
    #         # Vérifier s'il y a des filtres par nom actifs
    #         active_name_filters = {name: info['pattern'] for name, info in self.NAME_FILTERS.items() 
    #                             if self.active_filters.get(name, False)}
            
    #         # Ajouter les fichiers en tenant compte des filtres
    #         for item in files:
    #             item_path = os.path.join(path, item)
                
    #             # Si des filtres par nom sont actifs, vérifier si le fichier correspond à au moins un des motifs
    #             if active_name_filters:
    #                 # Par défaut, on exclut le fichier s'il ne correspond à aucun filtre actif
    #                 should_display = False
                    
    #                 # Vérifier si le fichier correspond à au moins un des motifs de filtres actifs
    #                 for filter_name, pattern in active_name_filters.items():
    #                     if pattern in item:
    #                         should_display = True
    #                         break
                    
    #                 # Si le fichier ne correspond à aucun filtre actif, passer au suivant
    #                 if not should_display:
    #                     continue
                
    #             file_type = self.get_file_extension(item_path)
    #             file_info = self.get_file_type(item_path)
    #             icon = file_info['icon']
    #             color = file_info['color']
                
    #             # Vérifier si le type de fichier est dans un groupe actif
    #             is_in_active_group = False
    #             for group_name, group_info in self.FILE_GROUPS.items():
    #                 if file_type in group_info['types'] and self.active_filters.get(group_name, False):
    #                     is_in_active_group = True
    #                     break
                
    #             # Si le fichier appartient à un groupe actif, l'afficher
    #             if is_in_active_group or file_type in self.active_filters:
    #                 # Ajouter avec tag de couleur personnalisé
    #                 self.tree.insert(parent, 'end', text=f"{icon} {item}", values=[item_path], 
    #                                 tags=(f"color_{color.replace('#', '')}",))
                
    #     except Exception as e:
    #         print(f"Erreur lors du peuplement de l'arborescence : {e}")
    #         import traceback
    #         traceback.print_exc()
    
    # def refresh_treeview(self):
    #     """
    #     Rafraîchit l'affichage du Treeview en fonction des filtres actifs.
    #     Version simplifiée car nous n'avons pas d'éléments développés à conserver.
    #     """
    #     # Réinitialiser et repeupler l'arborescence
    #     self.tree.delete(*self.tree.get_children())
    #     self.populate_treeview('', self.current_path)
        
    #     # Mettre à jour le label d'information
    #     self.label_result.config(text=f"Répertoire: {self.current_path} | Filtres actifs: {self.count_active_filters()}/{len(self.active_filters)}")
    
    # def on_tree_expand(self, event):
    #     """
    #     Ne fait rien car nous n'avons pas d'éléments à développer.
    #     Cette méthode est surchargée pour désactiver l'expansion.
    #     """
    #     pass


# Route Flask pour ouvrir l'explorateur
@exploreur.route('/open_exploreur', methods=['POST'])
def open_exploreur():
    dir_path = request.json.get('path')  # Récupérer le répertoire initial depuis la requête
    explorer_type = request.json.get('type', 'standard')  # Type d'explorateur, par défaut 'standard'
    
    if not dir_path or not os.path.exists(dir_path):
        return {"error": "Le répertoire spécifié est invalide ou n'existe pas."}, 400

    # Créer l'explorateur selon le type demandé
    if explorer_type == 'document':
        explorer = DocumentExplorer(initial_dir=dir_path)
    elif explorer_type == 'config':
        explorer = ConfigExplorer(initial_dir=dir_path)
    elif explorer_type == 'data':
        explorer = DataExplorer(initial_dir=dir_path)
   
    else:
        # Explorer standard par défaut
        explorer = FileExplorer(initial_dir=dir_path)
    
    # Lancer l'explorateur
    explorer.run()

    return {"status": "Explorateur ouvert avec succès."}, 200

