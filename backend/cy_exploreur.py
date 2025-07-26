import os
import requests
import tkinter as tk
from tkinter import ttk, filedialog, Scale
from flask import Blueprint, request
from cy_fbx_exploreur import launch_fbxreview
import threading

exploreur = Blueprint('exploreur', __name__)

class FileExplorer:
    """Classe générique pour l'explorateur de fichiers"""
    
    # Dictionnaire pour suivre l'état des filtres (statique par défaut)
    active_filters = {}
    
    # Définition des icônes et de leurs couleurs associées (par défaut)
    FILE_TYPES = {
        'default': {'icon': '📄', 'color': '#e0e0e0'},    # Gris clair
        'folder': {'icon': '📁', 'color': '#4800FF'},     # Bleu dossier
        'docx': {'icon': '📝', 'color': '#2b579a'},       # Bleu Word
        'pdf': {'icon': '📕', 'color': '#c43e1c'},        # Rouge PDF
        'col': {'icon': '🔨', 'color': '#5ba478'},        # Orange-marron
        'ask': {'icon': '💬', 'color': '#5ba478'},        # Violet
        'role': {'icon': '👷', 'color': '#5ba478'},       # Orange
        'data.json': {'icon': '📊', 'color': '#5ba478'},  # Vert JSON
        'clas': {'icon': '⚙️', 'color': '#5ba478'},
        'conf': {'icon': '🛠️', 'color': '#5ba478'},
        'exclued': {'icon': '👁️', 'color': '#5ba478'},
        # Images
        'png': {'icon': '🖼️', 'color': '#ff6b35'},        # Orange pour PNG
        'jpg': {'icon': '🖼️', 'color': '#ff6b35'},        # Orange pour JPG
        'jpeg': {'icon': '🖼️', 'color': '#ff6b35'},       # Orange pour JPEG
        'gif': {'icon': '🎞️', 'color': '#ff6b35'},        # Orange pour GIF (animé)
        'bmp': {'icon': '🖼️', 'color': '#ff6b35'},        # Orange pour BMP
        'ico': {'icon': '🖼️', 'color': '#ff6b35'},        # Orange pour ICO
        'svg': {'icon': '🎨', 'color': '#ff6b35'},         # Orange pour SVG
        'webp': {'icon': '🖼️', 'color': '#ff6b35'},       # Orange pour WebP
        'tiff': {'icon': '🖼️', 'color': '#ff6b35'},       # Orange pour TIFF
        'tif': {'icon': '🖼️', 'color': '#ff6b35'}         # Orange pour TIF
    }
    
    # Définition des groupes de fichiers pour le filtrage
    FILE_GROUPS = {
        'Documents': {
            'icon': '📚',
            'types': ['pdf', 'docx', 'default'],
            'color': '#2b579a'
        },
        'Images': {
            'icon': '🖼️',
            'types': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico', 'svg', 'webp', 'tiff', 'tif'],
            'color': '#ff6b35'
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
        #print (f"DBG-1234 = group ={self.active_filters}")   

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

                #print (f"<FILE > fichier inserting {item}: => {file_type}")
                #print (f"<FILEa> >self.FILE_GROUPS = {self.FILE_GROUPS}")

                is_in_active_group = False
                #print (f"<FILEa> >self.FILE_GROUPS = {self.FILE_GROUPS}")
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
        Ouvre le fichier avec l'application appropriée selon son type.
        """
        node = self.tree.focus()
        path = self.tree.item(node, 'values')[0]

        try:
            # Si c'est un fichier FBX, appeler la route Flask dans un thread séparé
            if path.lower().endswith('.fbx'):
                normalized_path = os.path.normpath(path)
                print(f"[DEBUG-14] Envoi du chemin FBX normalisé : {normalized_path}")
                def call_fbxreview():
                    try:
                        launch_fbxreview(normalized_path)
                    except Exception as e:
                        print(f"Erreur lors de l'appel à /launch_fbxreview : {e}")
                threading.Thread(target=call_fbxreview, daemon=True).start()
            elif path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.show_image_viewer(path)
            else:
                os.startfile(path)
        except Exception as e:
            print(f"Erreur lors de l'ouverture du fichier : {e}")
            # Méthodes alternatives pour différents types de fichiers
            if os.path.isfile(path):
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    self.show_image_viewer(path)
                elif path.endswith('.docx'):
                    try:
                        os.startfile(path)
                    except Exception as e:
                        print(f"Erreur lors de l'ouverture du fichier Word : {e}")
                elif path.endswith('.pdf'):
                    try:
                        os.system(f'start {path}')
                    except Exception as e:
                        print(f"Erreur lors de l'ouverture du fichier PDF : {e}")
                elif path.endswith('.xlsx'):
                    try:
                        os.system(f'start excel \"{path}\"')
                    except Exception as e:
                        print(f"Erreur lors de l'ouverture du fichier Excel : {e}")
    
    def show_image_viewer(self, image_path):
        """
        Affiche une image dans une fenêtre dédiée avec possibilité de zoom et de redimensionnement.
        """
        try:
            from PIL import Image, ImageTk
            import tkinter as tk
            from tkinter import ttk
            
            # Stocker les références PIL au niveau de l'instance pour les autres méthodes
            self.PIL_Image = Image
            self.PIL_ImageTk = ImageTk
            
            # Créer une nouvelle fenêtre pour l'affichage de l'image
            image_window = tk.Toplevel(self.root)
            image_window.title(f"Visualiseur d'image - {os.path.basename(image_path)}")
            image_window.geometry("800x600")
            
            # Variables pour le zoom et la position
            self.zoom_factor = 1.0
            self.image_x = 0
            self.image_y = 0
            self.original_image = None
            self.display_image = None
            self.photo_image = None
            
            # Charger l'image originale
            self.original_image = self.PIL_Image.open(image_path)
            
            # Créer un frame pour les contrôles
            control_frame = tk.Frame(image_window)
            control_frame.pack(fill='x', padx=5, pady=5)
            
            # Boutons de contrôle
            zoom_in_btn = tk.Button(control_frame, text="Zoom +", command=lambda: self.zoom_image(1.2, canvas))
            zoom_in_btn.pack(side='left', padx=2)
            
            zoom_out_btn = tk.Button(control_frame, text="Zoom -", command=lambda: self.zoom_image(0.8, canvas))
            zoom_out_btn.pack(side='left', padx=2)
            
            reset_btn = tk.Button(control_frame, text="Réinitialiser", command=lambda: self.reset_image(canvas))
            reset_btn.pack(side='left', padx=2)
            
            fit_btn = tk.Button(control_frame, text="Ajuster à la fenêtre", command=lambda: self.fit_to_window(canvas))
            fit_btn.pack(side='left', padx=2)
            
            # Informations sur l'image
            image_info = f"Taille: {self.original_image.size[0]}x{self.original_image.size[1]} pixels"
            info_label = tk.Label(control_frame, text=image_info)
            info_label.pack(side='right', padx=10)
            
            # Créer un canvas avec barres de défilement
            canvas_frame = tk.Frame(image_window)
            canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            canvas = tk.Canvas(canvas_frame, bg='white')
            v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
            
            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Placer le canvas et les barres de défilement
            canvas.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            canvas_frame.grid_rowconfigure(0, weight=1)
            canvas_frame.grid_columnconfigure(0, weight=1)
            
            # Afficher l'image initialement
            self.display_image_on_canvas(canvas)
            
            # Lier les événements de la souris pour le zoom avec la molette
            canvas.bind("<MouseWheel>", lambda e: self.on_mouse_wheel(e, canvas))
            canvas.bind("<Button-4>", lambda e: self.on_mouse_wheel(e, canvas))  # Linux
            canvas.bind("<Button-5>", lambda e: self.on_mouse_wheel(e, canvas))  # Linux
            
            # Lier les événements pour le déplacement avec la souris
            canvas.bind("<ButtonPress-1>", lambda e: self.start_drag(e, canvas))
            canvas.bind("<B1-Motion>", lambda e: self.on_drag(e, canvas))
            
            # Ajuster l'image à la fenêtre au démarrage
            image_window.after(100, lambda: self.fit_to_window(canvas))
            
        except ImportError:
            # Si PIL n'est pas disponible, utiliser l'application par défaut
            print("PIL (Pillow) n'est pas installé. Utilisation de l'application par défaut.")
            try:
                os.startfile(image_path)
            except Exception as e:
                print(f"Erreur lors de l'ouverture de l'image : {e}")
        except Exception as e:
            print(f"Erreur lors de l'affichage de l'image : {e}")
            # Fallback vers l'application par défaut
            try:
                os.startfile(image_path)
            except Exception as e:
                print(f"Erreur lors de l'ouverture de l'image : {e}")

    def display_image_on_canvas(self, canvas):
        """Affiche l'image sur le canvas avec le zoom actuel."""
        try:
            # Vérifier que PIL est disponible
            if not hasattr(self, 'PIL_Image') or not hasattr(self, 'PIL_ImageTk'):
                print("PIL n'est pas disponible pour l'affichage de l'image")
                return
                
            # Calculer la nouvelle taille
            new_width = int(self.original_image.size[0] * self.zoom_factor)
            new_height = int(self.original_image.size[1] * self.zoom_factor)
            
            # Redimensionner l'image
            self.display_image = self.original_image.resize((new_width, new_height), self.PIL_Image.Resampling.LANCZOS)
            
            # Convertir pour Tkinter
            self.photo_image = self.PIL_ImageTk.PhotoImage(self.display_image)
            
            # Effacer le canvas
            canvas.delete("all")
            
            # Afficher l'image
            canvas.create_image(self.image_x, self.image_y, anchor="nw", image=self.photo_image)
            
            # Configurer la région de défilement
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        except Exception as e:
            print(f"Erreur lors de l'affichage de l'image : {e}")

    def zoom_image(self, factor, canvas):
        """Applique un zoom à l'image."""
        try:
            self.zoom_factor *= factor
            self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))  # Limiter le zoom
            self.display_image_on_canvas(canvas)
        except Exception as e:
            print(f"Erreur lors du zoom : {e}")

    def reset_image(self, canvas):
        """Remet l'image à sa taille originale."""
        try:
            self.zoom_factor = 1.0
            self.image_x = 0
            self.image_y = 0
            self.display_image_on_canvas(canvas)
        except Exception as e:
            print(f"Erreur lors de la réinitialisation : {e}")

    def fit_to_window(self, canvas):
        """Ajuste l'image pour qu'elle s'adapte à la fenêtre."""
        try:
            if not hasattr(self, 'original_image') or self.original_image is None:
                return
                
            # Obtenir les dimensions du canvas
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            # Calculer le facteur de zoom pour ajuster à la fenêtre
            zoom_x = canvas_width / self.original_image.size[0]
            zoom_y = canvas_height / self.original_image.size[1]
            
            # Utiliser le plus petit facteur pour que l'image tienne entièrement
            self.zoom_factor = min(zoom_x, zoom_y, 1.0)  # Ne pas agrandir au-delà de la taille originale
            
            # Centrer l'image
            self.image_x = max(0, (canvas_width - self.original_image.size[0] * self.zoom_factor) // 2)
            self.image_y = max(0, (canvas_height - self.original_image.size[1] * self.zoom_factor) // 2)
            
            self.display_image_on_canvas(canvas)
            
        except Exception as e:
            print(f"Erreur lors de l'ajustement à la fenêtre : {e}")

    def on_mouse_wheel(self, event, canvas):
        """Gère le zoom avec la molette de la souris."""
        try:
            # Déterminer la direction du zoom
            if event.delta > 0 or event.num == 4:  # Zoom in
                factor = 1.1
            else:  # Zoom out
                factor = 0.9
            
            # Obtenir la position de la souris
            mouse_x = canvas.canvasx(event.x)
            mouse_y = canvas.canvasy(event.y)
            
            # Calculer le nouveau zoom
            old_zoom = self.zoom_factor
            self.zoom_factor *= factor
            self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))
            
            # Ajuster la position pour zoomer sur la position de la souris
            zoom_ratio = self.zoom_factor / old_zoom
            self.image_x = mouse_x - (mouse_x - self.image_x) * zoom_ratio
            self.image_y = mouse_y - (mouse_y - self.image_y) * zoom_ratio
            
            self.display_image_on_canvas(canvas)
            
        except Exception as e:
            print(f"Erreur lors du zoom à la souris : {e}")

    def start_drag(self, event, canvas):
        """Démarre le glissement de l'image."""
        try:
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        except Exception as e:
            print(f"Erreur lors du démarrage du glissement : {e}")

    def on_drag(self, event, canvas):
        """Gère le déplacement de l'image par glissement."""
        try:
            if hasattr(self, 'drag_start_x') and hasattr(self, 'drag_start_y'):
                dx = event.x - self.drag_start_x
                dy = event.y - self.drag_start_y
                
                self.image_x += dx
                self.image_y += dy
                
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                
                self.display_image_on_canvas(canvas)
        
        except Exception as e:
            print(f"Erreur lors du déplacement : {e}")
    
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

