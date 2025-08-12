import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import shutil
import sqlite3
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time  # Ajoute cet import en haut du fichier





class DirectoryWatcher(FileSystemEventHandler):
    def __init__(self, image_explorer):
        super().__init__()
        self.image_explorer = image_explorer
   
    def on_created(self, event):
        """Appelé lorsqu'un fichier est créé dans le répertoire surveillé"""
        if not event.is_directory:
            # Vérifier si le fichier est une image
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            if event.src_path.lower().endswith(image_extensions):
                print(f"[INFO] New image detected: {event.src_path}")
                self.image_explorer.add_new_image(event.src_path)

class DirectoryWatcherThread:
    def __init__(self, image_explorer):
        self.image_explorer = image_explorer
        self.observer = Observer()

    def start(self):
        event_handler = DirectoryWatcher(self.image_explorer)
        self.observer.schedule(event_handler, self.image_explorer.current_directory, recursive=False)
        self.observer.start()
        print(f"[INFO] Started watching directory: {self.image_explorer.current_directory}")

    def stop(self):
        self.observer.stop()
        self.observer.join()

class image_process:
    def __init__(self, root, config):
        self.root = root
        self.root.title(config.get('title', 'Image Explorer'))
        self.root.geometry("1200x800")
        
        # Extract configuration parameters with defaults
        self.default_directory = os.path.normpath(config.get('default_directory', ''))
        self.cible_directory = os.path.normpath(config.get('cible_directory', ''))
        self.current_directory = self.default_directory  # Répertoire actif
        self.changed_value = config.get('changed_value', 'none')
        self.title = config.get('title', 'Image Explorer')
        self.processor_type = config.get('processor_type', 'standard')

        # Database path
        self.db_path = os.path.normpath(config.get('db_path', ''))
        
        # Initialize collections
        self.image_files = []
        self.image_widgets = []
        self.pending_changes = []
        self.view_mode = "new"
        self.zoomed_images = {}
        self.page = 0
        self.page_size = 100
        self.all_files = []
        self.show_more_btn = None
        
        # Threading attributes
        self.loading_lock = threading.Lock()
        self.loading = False
        
        # Initialize database
        self.init_database()
        
        # Set up UI
        self.setup_ui()
        
        # Load images
        if os.path.exists(self.current_directory):
            self.dir_label.config(text=f"Directory: {self.current_directory}")
            self.load_images_async()
        else:
            self.dir_label.config(text="No directory selected")
            messagebox.showwarning(
                "Invalid Directory",
                f"The default directory does not exist:\n{self.current_directory}\n\nPlease select a valid directory."
            )
            self.select_directory()
        
        # Start directory watcher
        self.watcher_thread = DirectoryWatcherThread(self)
        self.watcher_thread.start()

    def __del__(self):
        """Nettoyage des ressources lors de la destruction de l'objet"""
        try:
            # SQLite ne peut pas être fermé depuis un autre thread
            import threading
            if hasattr(self, 'conn') and self.conn:
                try:
                    # Tester si la connexion peut être fermée (même thread)
                    self.cursor.execute("SELECT 1")
                    # Si pas d'erreur, on peut fermer
                    self.conn.close()
                    print("[INFO] Database connection closed successfully")
                except sqlite3.ProgrammingError as e:
                    # Erreur de thread, on ignore la fermeture
                    print("[INFO] Cannot close DB connection from different thread")
                except Exception as e:
                    print(f"[WARNING] Error closing database: {e}")
        except Exception as e:
            print(f"[ERROR] Error in __del__: {e}")
    
    def init_database(self):
        """Initialise la base de données SQLite pour stocker les images vues"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Créer la table si elle n'existe pas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS viewed_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE,
                viewed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ne pas essayer de modifier la table functions ici
        # La table functions est dans une autre base de données gérée par FunctionDatabase
        
        self.conn.commit()
    
    def get_db_connection(self):
        """Créer une nouvelle connexion à la base de données pour le thread actuel"""
        conn = sqlite3.connect(self.db_path)
        return conn, conn.cursor()

    def is_image_viewed(self, image_path, cursor=None):
        """Vérifier si une image a été vue, en utilisant un curseur spécifié ou celui par défaut"""
        try:
            image_path = os.path.normpath(image_path)
            use_local_connection = cursor is None
            
            if use_local_connection:
                # Si dans un thread différent, créer une connexion locale
                thread_conn, cursor = self.get_db_connection()
                
            cursor.execute(
                "SELECT COUNT(*) FROM viewed_images WHERE image_path = ?",
                (image_path,)
            )
            result = cursor.fetchone()[0] > 0
            
            if use_local_connection:
                thread_conn.close()
                
            return result
        except Exception as e:
            print(f"[ERROR][is_image_viewed] {type(e).__name__}: {e}")
            return False
    
    def mark_action_1(self, image_path):
        """Marquer une image comme vue (en attente de sauvegarde)"""
        if image_path not in [change[1] for change in self.pending_changes if change[0] == 'viewed']:
            self.pending_changes.append(('viewed', image_path))
            # Masquer visuellement l'image immédiatement
            self.hide_image_widget(image_path)
            # Activer le bouton de sauvegarde
            self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
    
    def mark_action_2(self, image_path):
        """Marquer une image pour suppression (en attente de sauvegarde)"""
        result = messagebox.askyesno(
            "Confirm Delete", 
            f"Mark for deletion:\n{os.path.basename(image_path)}?\n\nClick 'Save Changes' to apply."
        )
        print("dbg 1457 mark_action_2 : ",self.changed_value)
        if result:
            if image_path not in [change[1] for change in self.pending_changes]:
                self.pending_changes.append((self.changed_value, image_path))
                # Masquer visuellement l'image immédiatement
                self.hide_image_widget(image_path)
                # Activer le bouton de sauvegarde
                self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
    
    def hide_image_widget(self, image_path):
        """Masquer visuellement une image sans la supprimer de l'interface"""
        for widget in self.image_widgets:
            if hasattr(widget, 'image_path') and widget.image_path == image_path:
                widget.grid_remove()  # Masquer mais ne pas détruire
    
    def save_changes(self):
        """Sauvegarder tous les changements en attente"""
        if not self.pending_changes:
            return
            
        import threading
        import time  # Ajoute cet import en haut du fichier


       
    
    def setup_ui(self):
        """Initialise l'interface graphique principale"""
        # Frame du haut pour la sélection du dossier
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Bouton pour sélectionner le dossier
        select_btn = ttk.Button(top_frame, text="Select Directory", command=self.select_directory)
        select_btn.pack(side="left")

        # Label du dossier courant
        self.dir_label = ttk.Label(top_frame, text=f"Directory: {self.current_directory}")
        self.dir_label.pack(side="left", padx=(10, 0))

        # Bouton pour sauvegarder les changements
        self.save_btn = tk.Button(
            top_frame, 
            text="Save Changes", 
            command=self.save_changes,
            bg="orange",
            fg="white",
            font=("Arial", 10, "bold"),
            state="disabled"
        )
        self.save_btn.pack(side="right", padx=(5, 0))

        # Frame principal pour les images
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Canvas scrollable pour les images
        self.canvas = tk.Canvas(main_frame, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Frame interne pour placer les widgets d'image
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Lier les événements à tous les widgets (y compris les enfants)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)

        # Pour le resize horizontal
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
    
    def load_images_async(self):
        """Lance le chargement des images dans un thread pour ne pas bloquer l'UI"""
        import threading
        if hasattr(self, 'loading') and self.loading:
            return  # Un chargement est déjà en cours
        self.loading = True
        threading.Thread(target=self.load_images, daemon=True).start()

    def load_images(self):
        """Charge les images du dossier courant avec pagination"""
        try:
            with self.loading_lock:
                # Créer une connexion spécifique à ce thread
                thread_conn, thread_cursor = self.get_db_connection()
                
                # Nettoyer les widgets existants
                for widget in self.image_widgets:
                    widget.destroy()
                self.image_widgets.clear()

                # Obtenir les fichiers images
                image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
                if not self.all_files:
                    self.all_files = [f for f in os.listdir(self.current_directory) if f.lower().endswith(image_extensions)]
                    self.all_files.sort()

                # Pagination
                start = self.page * self.page_size
                end = start + self.page_size
                files = self.all_files[start:end]

                self.image_files = []
                total = len(files)
                for idx, filename in enumerate(files):
                    image_path = os.path.normpath(os.path.join(self.current_directory, filename))
                    if self.view_mode == "new":
                        if not self.is_image_viewed(image_path, thread_cursor):
                            self.image_files.append(image_path)
                    else:
                        self.image_files.append(image_path)
                    # Mise à jour de la barre de progression
                    if hasattr(self, 'progressbar') and self.progressbar:
                        value = int((idx + 1) / total * 100)
                        self.root.after(0, lambda v=value: self.progressbar.config(value=v))
                        self.root.update_idletasks()

                # Fermer la connexion du thread
                thread_conn.close()
                
                # Détruire la barre de progression
                if hasattr(self, 'progressbar') and self.progressbar:
                    self.root.after(0, self.progressbar.destroy)
                    self.progressbar = None

                # Afficher les images
                self.root.after(0, self.display_images)
                self.loading = False
        except Exception as e:
            print(f"[ERROR][load_images] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error loading images: {str(e)}")
            self.loading = False

    def select_directory(self):
        """Ouvrir un dialogue pour sélectionner un nouveau dossier d'images"""
        try:
            directory = filedialog.askdirectory()
            if directory:
                self.current_directory = os.path.normpath(directory)
                self.dir_label.config(text=f"Directory: {self.current_directory}")
                
                # Réinitialiser la pagination
                self.page = 0
                self.all_files = []
                
                # Arrêter et redémarrer le watcher pour le nouveau dossier
                if hasattr(self, 'watcher_thread'):
                    self.watcher_thread.stop()
                self.watcher_thread = DirectoryWatcherThread(self)
                self.watcher_thread.start()
                
                # Charger les images du nouveau dossier
                self.load_images_async()
        except Exception as e:
            print(f"[ERROR][select_directory] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error selecting directory: {str(e)}")
    
    def display_images(self):
        """Affiche les images chargées dans l'interface graphique"""
        try:
            # Vider le conteneur d'images existant
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            # Initialiser les variables de positionnement
            row, col = 0, 0
            max_cols = 3  # Nombre maximum de colonnes
            
            # Aucune image à afficher
            if not self.image_files:
                no_image_label = ttk.Label(self.scrollable_frame, text="No images to display", font=("Arial", 14))
                no_image_label.grid(row=0, column=0, padx=20, pady=20)
                return
            
            # Afficher chaque image
            for i, image_path in enumerate(self.image_files):
                try:
                    # Vérifier si le fichier existe toujours
                    if not os.path.exists(image_path):
                        continue
                        
                    # Créer un cadre pour chaque image
                    image_frame = ttk.Frame(self.scrollable_frame)
                    image_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    image_frame.image_path = image_path  # Référence pour masquage
                    
                    # Charger l'image avec PIL
                    with Image.open(image_path) as img:
                        # Redimensionner pour l'affichage
                        img.thumbnail((300, 300), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                    
                    # Créer un label pour l'image
                    image_label = ttk.Label(image_frame, image=photo)
                    image_label.image = photo  # Garder une référence
                    image_label.pack(padx=5, pady=5)
                    
                    # Ajouter un événement de clic pour zoomer
                    image_label.bind("<Button-1>", lambda e, path=image_path, label=image_label: self.toggle_image_zoom(label, path))
                    
                    # Créer un label pour le nom du fichier
                    file_label = ttk.Label(image_frame, text=os.path.basename(image_path))
                    file_label.pack(pady=2)
                    
                    # Ajouter des boutons d'action
                    btn_frame = ttk.Frame(image_frame)
                    btn_frame.pack(pady=5)
                    
                    # Bouton "Mark as Viewed"
                    view_btn = ttk.Button(
                        btn_frame, 
                        text="Mark as Viewed", 
                        command=lambda path=image_path: self.mark_action_1(path)
                    )
                    view_btn.pack(side="left", padx=2)
                    
                    # Bouton "Mark for Deletion"
                    delete_btn = ttk.Button(
                        btn_frame, 
                        text="Mark for Deletion", 
                        command=lambda path=image_path: self.mark_action_2(path)
                    )
                    delete_btn.pack(side="left", padx=2)
                    
                    # Stocker le widget pour référence future
                    self.image_widgets.append(image_frame)
                    
                    # Passer à la prochaine position
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                        
                except Exception as e:
                    print(f"Error loading image {image_path}: {str(e)}")
            
            # Ajouter le bouton "Afficher plus" si besoin
            if (self.page + 1) * self.page_size < len(self.all_files):
                if hasattr(self, 'show_more_btn') and self.show_more_btn:
                    self.show_more_btn.destroy()
                
                self.show_more_btn = tk.Button(
                    self.scrollable_frame,
                    text="Afficher plus",
                    command=self.show_more_images,
                    bg="purple",
                    fg="white",
                    font=("Arial", 10, "bold")
                )
                self.show_more_btn.grid(row=row+1, column=0, columnspan=max_cols, pady=20)
            
            # Mettre à jour la région de défilement du canvas
            self.check_and_update_canvas()
        
        except Exception as e:
            print(f"[ERROR][display_images] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error displaying images: {str(e)}")
    
    def check_and_update_canvas(self):
        """Mettre à jour en toute sécurité la région de défilement du canvas s'il existe encore"""
        try:
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            print(f"[INFO] Erreur de mise à jour du canvas: {str(e)}")
    
    def show_more_images(self):
        """Affiche une page supplémentaire d'images"""
        try:
            self.page += 1
            self.load_images_async()
        except Exception as e:
            print(f"[ERROR][show_more_images] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error loading more images: {str(e)}")
    
    def toggle_image_zoom(self, image_label, image_path):
        """Basculer entre la taille normale et la taille agrandie d'une image"""
        try:
            # Vérifier si l'image est déjà zoomée
            if image_path in self.zoomed_images:
                # Restaurer l'image normale
                image_label.config(image=self.zoomed_images[image_path]['normal'])
                del self.zoomed_images[image_path]
            else:
                # Sauvegarder l'image normale
                normal_image = image_label.image
                
                # Charger l'image agrandie
                with Image.open(image_path) as img:
                    # Agrandir l'image pour une meilleure vue
                    img.thumbnail((800, 800), Image.LANCZOS)
                    zoomed_photo = ImageTk.PhotoImage(img)
                
                # Mettre à jour l'affichage
                image_label.config(image=zoomed_photo)
                
                # Stocker les références
                self.zoomed_images[image_path] = {
                    'normal': normal_image,
                    'zoomed': zoomed_photo
                }
            
            # Mettre à jour la région de défilement
            self.check_and_update_canvas()
        except Exception as e:
            print(f"[ERROR][toggle_image_zoom] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error zooming image: {str(e)}")
    
    def add_new_image(self, image_path):
        """Ajoute une nouvelle image détectée au dossier à l'affichage"""
        try:
            image_path = os.path.normpath(image_path)
            if image_path not in self.image_files:
                self.image_files.append(image_path)
                print(f"[INFO] Adding new image to display: {image_path}")
                # Uniquement recharger si en mode "all" ou si l'image est nouvelle
                if self.view_mode == "all" or not self.is_image_viewed(image_path):
                    self.load_images_async()
        except Exception as e:
            print(f"[ERROR][add_new_image] {type(e).__name__}: {e}")
    
    def _on_mousewheel(self, event):
        """Gère le défilement avec la molette de souris"""
        try:
            # Ajouter un log pour voir si l'événement est détecté
            print(f"[DEBUG] Mousewheel event detected: {event}")
            
            # Détection adaptée à Windows
            if hasattr(event, "delta"):  # Windows
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            # Détection pour Linux/Unix
            elif hasattr(event, "num"):  # Linux
                if event.num == 4:
                    self.canvas.yview_scroll(-3, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(3, "units")
        except Exception as e:
            print(f"[ERROR][_on_mousewheel] {type(e).__name__}: {e}")



