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
        """Initialiser l'interface graphique principale"""
        self.root = root
        self.title = config.get('title', 'Image Explorer')
        self.default_directory = config.get('default_directory', '')
        self.cible_directory = config.get('cible_directory', '')
        self.db_path = config.get('db_path', 'images.db')
        self.view_mode = "all"  # Mode d'affichage: "all" ou "new"
        
        # Initialiser les variables
        self.current_directory = self.default_directory
        self.image_files = []
        self.all_files = []
        self.image_widgets = []
        self.loading = False
        self.loading_lock = threading.Lock()
        self.page = 0
        self.page_size = 100
        
        # Initialiser la base de données
        self.init_database()
        
        # Configurer l'interface utilisateur
        self.setup_ui()
        
        # NE PAS charger les images automatiquement ici
        # self.load_images_async()  # Cette ligne est la source du problème
    
        # À la place, créer une méthode d'initialisation séparée
    
    def initialize(self):
        """Initialisation finale après la construction complète"""
        # Logs pour debug
        print(f"[DEBUG] Initializing with directory: {self.default_directory}")
        print(f"[DEBUG] Directory exists: {os.path.exists(self.default_directory)}")
    
        # Surveiller le répertoire pour les nouveaux fichiers
        if os.path.exists(self.default_directory):
            self.setup_directory_watcher()
        else:
            print(f"[WARNING] Directory does not exist: {self.default_directory}")
            messagebox.showwarning("Warning", f"Directory does not exist: {self.default_directory}")
    
        # Maintenant on peut charger les images en toute sécurité
        self.load_images_async()

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
       #Vérifier si une image a été vue, en utilisant un curseur spécifié ou celui par défaut
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
    """
    def mark_action_1(self, image_path):
        #Marquer une image comme vue (en attente de sauvegarde)
        if image_path not in [change[1] for change in self.pending_changes if change[0] == 'viewed']:
            self.pending_changes.append(('viewed', image_path))
            # Masquer visuellement l'image immédiatement
            self.hide_image_widget(image_path)
            # Activer le bouton de sauvegarde
            self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
    
    def mark_action_2(self, image_path):
        #Marquer une image pour suppression (en attente de sauvegarde)
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
    """
    def hide_image_widget(self, image_path):
        """Masquer visuellement une image sans la supprimer de l'interface"""
        for widget in self.image_widgets:
            if hasattr(widget, 'image_path') and widget.image_path == image_path:
                # Utiliser grid_remove() car les frames sont positionnées avec grid
                widget.grid_remove()  # Masquer mais ne pas détruire 
                print(f"[INFO] Image hidden from view: {os.path.basename(image_path)}")
                # S'assurer que le widget est retiré de la mise en page
                self.check_and_update_canvas()
                return True  # Indiquer que l'image a été masquée
    
        # Si on arrive ici, aucun widget correspondant n'a été trouvé
        print(f"[WARNING] No widget found for image: {os.path.basename(image_path)}")
        return False

    def save_changes(self):
        #Sauvegarder tous les changements en attente
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
        # self.save_btn = tk.Button(
        #     top_frame, 
        #     text="Save Changes", 
        #     command=self.save_changes,
        #     bg="orange",
        #     fg="white",
        #     font=("Arial", 10, "bold"),
        #     state="disabled"
        # )
        # self.save_btn.pack(side="right", padx=(5, 0))

        # Frame principal pour les images
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Canvas scrollable pour les images
        self.canvas = tk.Canvas(main_frame, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        # Label du dossier courant
        self.dir_label = ttk.Label(top_frame, text=f"Directory: {self.current_directory}")
        self.dir_label.pack(side="left", padx=(10, 0))
    
        # AJOUT: Label pour afficher les statistiques de filtrage
        self.filter_stats_label = ttk.Label(top_frame, text="")
        self.filter_stats_label.pack(side="left", padx=(20, 0))

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
        """Charge les images depuis le répertoire courant"""
        try:
            with self.loading_lock:  # Ajouter 4 espaces d'indentation ici
                # Créer une connexion spécifique à ce thread
                thread_conn, thread_cursor = self.get_db_connection()
                
                # Nettoyer les widgets existants
                self._prepare_image_loading()

                # Obtenir les fichiers images
                image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
                if not self.all_files:
                    self.all_files = [f for f in os.listdir(self.current_directory) if f.lower().endswith(image_extensions)]
                    self.all_files.sort()

                # Compteurs pour les statistiques
                total_images = len(self.all_files)
                filtered_images = 0
                
                # NOUVEAU: Filtrer d'abord toutes les images
                all_filtered_files = []
                
                # Premier passage pour trouver toutes les images qui correspondent au filtre
                for filename in self.all_files:
                    image_path = os.path.normpath(os.path.join(self.current_directory, filename))
                    if self._filter_image(image_path, thread_cursor):
                        all_filtered_files.append(filename)
                        filtered_images += 1
                
                # Mettre à jour les statistiques de filtrage
                self.root.after(0, lambda: self._update_filter_stats(filtered_images, total_images))
                
                # ENSUITE appliquer la pagination sur les images filtrées
                start = self.page * self.page_size
                end = start + self.page_size
                page_files = all_filtered_files[start:min(end, len(all_filtered_files))]
                
                self.image_files = []
                total = len(page_files)
                
                # Charger les images de la page actuelle
                for idx, filename in enumerate(page_files):
                    image_path = os.path.normpath(os.path.join(self.current_directory, filename))
                    self.image_files.append(image_path)
                    
                    # Mise à jour de la barre de progression
                    self._update_progress(idx, total)

                # Fermer la connexion et finaliser
                self._finish_image_loading(thread_conn)
        
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
            # Vérifier si les widgets existent encore
            if not self.check_widgets_exist():
                print("[WARNING] Widgets principaux détruits, impossible d'afficher les images")
                return
            
            # Vider le conteneur d'images existant
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            # Initialiser les variables de positionnement
            row, col = 0, 0
            max_cols = 3  # Nombre maximum de colonnes
            
            # Aucune image à afficher
            if not self.image_files:
                self._display_no_images_message()
                return
            
            # Afficher chaque image
            for i, image_path in enumerate(self.image_files):
                try:
                    # Créer le cadre pour l'image
                    image_frame = self._create_image_frame(row, col)
                    
                    # Charger et afficher l'image
                    self._load_and_display_image(image_frame, image_path, i)
                    
                    # Créer les boutons pour cette image
                    self._create_image_buttons(image_frame, image_path)
                    
                    # Méthode de hook pour les classes dérivées (status pour workflow)
                    self._add_custom_image_controls(image_frame, image_path)
                    
                    # Mettre à jour les coordonnées pour la prochaine image
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                
                except Exception as e:
                    print(f"[ERROR][display_image {i}] {type(e).__name__}: {e}")
            
            # Ajouter les boutons de navigation
            self._create_navigation_buttons(row + 1, max_cols)
            
            # Mettre à jour la région de défilement du canvas
            self.check_and_update_canvas()
    
        except Exception as e:
            print(f"[ERROR][display_images] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error displaying images: {str(e)}")

    # Méthodes "hook" à surcharger par les classes dérivées
    def _display_no_images_message(self):
        """Affiche un message quand aucune image n'est disponible"""
        no_image_label = ttk.Label(self.scrollable_frame, text="No images to display", font=("Arial", 14))
        no_image_label.grid(row=0, column=0, padx=20, pady=20)

    def _create_image_frame(self, row, col):
        """Crée le cadre pour une image"""
        image_frame = ttk.Frame(self.scrollable_frame, padding=5)
        image_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        return image_frame

    def _load_and_display_image(self, image_frame, image_path, index):
        """Charge et affiche une image dans le cadre donné"""
        # Code pour charger l'image depuis image_path
        # et l'afficher dans image_frame
        # ...

    def _create_image_buttons(self, image_frame, image_path):
        """Crée les boutons standard pour une image"""
        # Code pour créer les boutons (zoom, déplacer, supprimer)
        # ...

    def _add_custom_image_controls(self, image_frame, image_path):
        """Hook pour ajouter des contrôles personnalisés par les classes dérivées"""
        # Vide par défaut, à surcharger dans les classes dérivées
        pass

    def _create_navigation_buttons(self, row, max_cols):
        """Crée les boutons de navigation (page précédente/suivante)"""
        # Code pour créer les boutons de navigation
        # ...
    
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
    
    def _prepare_image_loading(self):
        """Prépare le chargement des images (peut être surchargé)"""
        for widget in self.image_widgets:
            widget.destroy()
        self.image_widgets.clear()

    def _filter_image(self, image_path, cursor):
        """Filtre les images selon les critères de base"""
        # Code de base pour la classe image_process (sans appel à super())
    
        # Vérification défensive
        if not hasattr(self, 'current_filter'):
            self.current_filter = "all"
        
        # Vérifier si on a accès à get_image_status
        if hasattr(self, 'get_image_status'):
            # Récupérer le statut de l'image
            status = self.get_image_status(image_path, cursor)
            
            # Si l'image a le statut "hidde", la masquer sauf si on filtre spécifiquement sur "hidde"
            if status["current"] == "hidde":
                # Retourner True uniquement si le filtre actuel est "hidde"
                return self.current_filter == "hidde"
        
        # Filtre de base: uniquement les images non vues en mode "new"
        if hasattr(self, 'view_mode') and self.view_mode == "new" and self.is_image_viewed(image_path, cursor):
            return False
        
        # Par défaut, inclure l'image
        return True
    
    def _update_progress(self, idx, total):
        """Met à jour la barre de progression"""
        if hasattr(self, 'progressbar') and self.progressbar:
            value = int((idx + 1) / total * 100)
            self.root.after(0, lambda v=value: self.progressbar.config(value=v))
            self.root.update_idletasks()

    def _finish_image_loading(self, conn):
        """Finalise le chargement des images"""
        conn.close()
        
        # Détruire la barre de progression
        if hasattr(self, 'progressbar') and self.progressbar:
            self.root.after(0, self.progressbar.destroy)
            self.progressbar = None

        # Afficher les images
        self.root.after(0, self.display_images)
        self.loading = False

    def setup_directory_watcher(self):
        """Configure le watcher pour le dossier courant"""
        try:
            self.watcher_thread = DirectoryWatcherThread(self)
            self.watcher_thread.start()
        except Exception as e:
            print(f"[ERROR][setup_directory_watcher] {type(e).__name__}: {e}")
    
    def status_function_factory(self, status_option):
        """
        Factory qui crée des fonctions spécifiques pour chaque type de statut
        Chaque statut peut avoir un comportement personnalisé
        """
        
        def standard_status_change(image_path, btn_frame=None):
            """Comportement standard pour les statuts génériques"""
            self.change_image_status(image_path, status_option, btn_frame)
        
        # def approved_status_change(image_path, btn_frame=None):
        #     """Action spéciale pour le statut 'approved'"""
        #     self.change_image_status(image_path, status_option, btn_frame)
        #     # Comportement supplémentaire pour les images approuvées
        #     # Par exemple: déplacer immédiatement l'image
        #     if os.path.exists(image_path) and self.cible_directory:
        #         basename = os.path.basename(image_path)
        #         target_path = os.path.join(self.cible_directory, basename)
        #         os.makedirs(self.cible_directory, exist_ok=True)
        #         shutil.copy(image_path, target_path)  # Copier plutôt que déplacer
        #         print(f"[INFO] Copied approved image to target directory: {target_path}")
        
        # def rejected_status_change(image_path, btn_frame=None):
        #     """Action spéciale pour le statut 'rejected'"""
        #     # Demander confirmation avant de rejeter
        #     result = messagebox.askyesno("Confirm Rejection", 
        #                                  f"Are you sure you want to reject {os.path.basename(image_path)}?")
        #     if result:
        #         self.change_image_status(image_path, status_option, btn_frame)
        
        def deleted_status_change(image_path, btn_frame=None):
            """Action spéciale pour le statut 'deleted'"""
            # Demander confirmation avant de supprimer
            result = messagebox.askyesno("Confirm Deletion", 
                                        f"Are you sure you want to mark {os.path.basename(image_path)} for deletion?")
            if result:
                self.change_image_status(image_path, status_option, btn_frame)
                # Ajouter à une liste pour suppression ultérieure
                self.pending_changes.append(('delete_file', image_path))
                self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
    
        def hidde_status_change(image_path, btn_frame=None):
            """Action spéciale pour le statut 'hidde'"""
            result = messagebox.askyesno("Confirm Hide", 
                                        f"Are you sure you want to hide {os.path.basename(image_path)}?\n\nHidden images will only be visible when the 'hidde' filter is selected.")
            if result:
                print(f"[DEBUG] Hiding image: {os.path.basename(image_path)}")
                
                # Changer le statut
                if hasattr(self, 'change_image_status'):
                    self.change_image_status(image_path, status_option, btn_frame)
                else:
                    print("[ERROR] Method change_image_status not found")
                
                # Masquer immédiatement l'image
                success = self.hide_image_widget(image_path)
                
                # Vérifier si l'image a été masquée
                if success:
                    print(f"[INFO] Successfully hidden image: {os.path.basename(image_path)}")
                else:
                    print(f"[WARNING] Failed to hide image: {os.path.basename(image_path)}")
                    
                # Forcer un rafraîchissement de l'interface
                self.root.update_idletasks()
    
            # Retourner la fonction appropriée selon le statut
            if status_option == "approved":
                return approved_status_change
            elif status_option == "rejected":
                return rejected_status_change
            elif status_option == "deleted":
                return deleted_status_change
            elif status_option == "hidde":
                return hidde_status_change
            else:
                return standard_status_change
    
    def create_status_buttons(self, image_path, status_options, current_status, btn_frame):
        """
        Crée des boutons pour chaque statut possible d'une image
        :param image_path: Chemin de l'image
        :param status_options: Liste des options de statut possibles
        :param current_status: Statut actuel de l'image
        :param btn_frame: Cadre dans lequel les boutons doivent être placés
        """
        status_buttons = {}
        
        # Créer un style compact pour tous les boutons
        style = ttk.Style()
        style.configure('Small.TButton', 
                        padding=(2, 0),         # Padding horizontal et vertical réduit
                        font=('Arial', 7))      # Police plus petite
        
        # Style pour le bouton actif
        style.configure('SmallActive.TButton',
                        padding=(2, 0),
                        background='#005500',
                        foreground='white',
                        font=('Arial', 7, 'bold'))
        
        for status_option in status_options:
            # Créer un style différent pour le statut actuel
            is_current = current_status == status_option
            
            # Obtenir la fonction spécifique pour ce statut via la factory
            status_function = self.status_function_factory(status_option)
            
            # Créer le bouton avec un style différent selon le statut
            status_btn = ttk.Button(
                btn_frame,
                text=status_option.capitalize(),
                style='SmallActive.TButton' if is_current else 'Small.TButton',
                command=lambda path=image_path, func=status_function, frame=btn_frame: 
                    func(path, frame)
            )
            
            status_btn.pack(side="left", padx=1)  # Réduit l'espace entre les boutons
            status_buttons[status_option] = status_btn
        
        return status_buttons

    def _update_filter_stats(self, filtered_count, total_count):
        """Met à jour l'affichage des statistiques de filtrage"""
        try:
            if hasattr(self, 'filter_stats_label') and self.filter_stats_label.winfo_exists():
                # Déterminer le texte du filtre actuel
                filter_text = "all"
                if hasattr(self, 'current_filter'):
                    filter_text = self.current_filter
                elif hasattr(self, 'view_mode') and self.view_mode == "new":
                    filter_text = "new"
                
                # Mettre à jour le label
                stats_text = f"Filter [{filter_text}]: {filtered_count}/{total_count} images"
                self.filter_stats_label.config(text=stats_text)
        except Exception as e:
            print(f"[ERROR][_update_filter_stats] {type(e).__name__}: {e}")
    
    def apply_filter(self):
        """Applique un filtre pour n'afficher que les images avec un statut spécifique"""
        try:
            filter_value = self.filter_var.get()
            self.current_filter = filter_value
            
            # Réinitialiser la pagination
            self.page = 0
            
            # On garde self.all_files pour conserver la liste complète des fichiers
            # self.all_files = [] - Cette ligne est supprimée pour conserver le comptage total
            
            # Mettre à jour le label de statistiques (avant le rechargement)
            if hasattr(self, 'all_files') and self.all_files:
                # Compter les images qui correspondent au nouveau filtre
                thread_conn, thread_cursor = self.get_db_connection()
                filtered_count = 0
                for filename in self.all_files:
                    image_path = os.path.normpath(os.path.join(self.current_directory, filename))
                    if self._filter_image(image_path, thread_cursor):
                        filtered_count += 1
                thread_conn.close()
                
                # Mettre à jour l'affichage
                self._update_filter_stats(filtered_count, len(self.all_files))
            
            # Recharger les images avec le filtre
            self.load_images_async()
        except Exception as e:
            print(f"[ERROR][apply_filter] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error applying filter: {str(e)}")
    
    def check_widgets_exist(self):
        """Vérifie si les widgets principaux existent encore"""
        if not hasattr(self, 'scrollable_frame') or not self.scrollable_frame.winfo_exists():
            return False
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return False
        return True



