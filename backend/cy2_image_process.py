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
import time
import hashlib
from PIL.ExifTags import TAGS

# class DirectoryWatcher(FileSystemEventHandler):
#     def __init__(self, image_explorer):
#         super().__init__()
#         self.image_explorer = image_explorer
   
#     def on_created(self, event):
#         """Appelé lorsqu'un fichier est créé dans le répertoire surveillé"""
#         if not event.is_directory:
#             # Vérifier si le fichier est une image
#             image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
#             if event.src_path.lower().endswith(image_extensions):
#                 print(f"[INFO] New image detected: {event.src_path}")
#                 self.image_explorer.add_new_image(event.src_path)

# class DirectoryWatcherThread:
#     def __init__(self, image_explorer):
#         self.image_explorer = image_explorer
#         self.observer = Observer()

#     def start(self):
#         event_handler = DirectoryWatcher(self.image_explorer)
#         self.observer.schedule(event_handler, self.image_explorer.current_directory, recursive=False)
#         self.observer.start()
#         print(f"[INFO] Started watching directory: {self.image_explorer.current_directory}")

#     def stop(self):
#         self.observer.stop()
#         self.observer.join()

class image_process:
    def __init__(self, root, config):
        """Initialiser l'interface graphique principale"""
        self.root = root
        self.title = config.get('title', 'Image Explorer')
        self.default_directory = config.get('default_directory', '')
        self.cible_directory = config.get('cible_directory', '')
        self.db_path = config.get('db_path', 'image_explorer.db')
        self.processor_type = config.get('processor_type', 'standard')
        # Variables d'état
        self.current_directory = self.default_directory
        self.image_files = []
        self.all_files = []
        self.image_widgets = []
        self.loading = False
        self.loading_lock = threading.Lock()
        self.page = 0
        self.page_size = 50
        self.watcher_thread = None
        
        # Variables pour la gestion des actions
        self.pending_changes = []
        
        # Mode de filtrage : "all" pour tout voir, "new" pour masquer les vues
        self.view_mode = "new"  # Par défaut, masquer les images vues
        
        # Configuration de la fenêtre
        self.root.title(self.title)
        self.root.geometry("1200x800")
        
        # Initialiser la base de données
        self.init_database()
        
        # Configurer l'interface utilisateur
        self.setup_ui()
        
    def initialize(self):
        """Initialisation finale après la construction complète"""
        print(f"[DEBUG] Initializing with directory: {self.default_directory}")
        print(f"[DEBUG] Directory exists: {os.path.exists(self.default_directory)}")
        
        if os.path.exists(self.default_directory):
            self.setup_directory_watcher()
            self.load_images_async()
        else:
            print(f"[WARNING] Directory does not exist: {self.default_directory}")
            messagebox.showwarning("Warning", f"Directory does not exist: {self.default_directory}")

    def init_database(self):
        """Initialise la base de données SQLite pour stocker les images vues par fonction"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Créer la table des images vues
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS viewed_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    function_name TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    viewed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(function_name, image_path)
                )
            ''')
            
            # Supprimer et recréer la table des métadonnées avec tous les champs ComfyUI
            self.cursor.execute("DROP TABLE IF EXISTS image_metadata")
            
            self.cursor.execute('''
                CREATE TABLE image_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    function_name TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    format TEXT,
                    mode TEXT,
                    file_hash TEXT,
                    creation_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    exif_data TEXT,
                    positive_prompt TEXT,
                    negative_prompt TEXT,
                    workflow_data TEXT,
                    model_checkpoint TEXT,
                    model_vae TEXT,
                    generation_steps INTEGER,
                    cfg_scale REAL,
                    sampler_name TEXT,
                    scheduler TEXT,
                    seed INTEGER,
                    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(function_name, image_path)
                )
            ''')
            
            self.conn.commit()
            print(f"[INFO] Database initialized with complete ComfyUI support: {self.db_path}")
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")

    def get_db_connection(self):
        """Créer une nouvelle connexion à la base de données pour le thread actuel"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return conn, conn.cursor()

    def is_image_viewed(self, image_path):
        """Vérifier si une image a été vue pour cette fonction spécifique"""
        try:
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            cursor.execute(
                "SELECT COUNT(*) FROM viewed_images WHERE function_name = ? AND image_path = ?",
                (self.title, image_path)
            )
            result = cursor.fetchone()[0] > 0
            conn.close()
            
            # Debug pour voir ce qui se passe
            #print(f"[DEBUG] Image {os.path.basename(image_path)} viewed for '{self.title}': {result}")
            
            return result
        except Exception as e:
            print(f"[ERROR] Error checking if image viewed: {e}")
            return False

    def mark_image_viewed(self, image_path):
        """Marquer une image comme vue pour cette fonction spécifique"""
        try:
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            cursor.execute(
                "INSERT OR IGNORE INTO viewed_images (function_name, image_path) VALUES (?, ?)",
                (self.title, image_path)
            )
            conn.commit()
            conn.close()
            print(f"[INFO] Image marked as viewed for '{self.title}': {os.path.basename(image_path)}")
            
            return True
        except Exception as e:
            print(f"[ERROR] Error marking image as viewed: {e}")
            return False

    def setup_ui(self):
        """Initialise l'interface graphique principale"""
        # Frame du haut pour les contrôles
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Première ligne - Info fonction
        info_frame = ttk.Frame(top_frame)
        info_frame.pack(fill="x", pady=(0, 5))
        
        function_label = ttk.Label(info_frame, text=f"Function: {self.title}", font=("Arial", 10, "bold"))
        function_label.pack(side="left")
        
        stats_btn = ttk.Button(info_frame, text="Stats", command=self.show_function_stats)
        stats_btn.pack(side="right", padx=(0, 5))
        
        clear_btn = ttk.Button(info_frame, text="Clear Viewed", command=self.clear_function_viewed_images)
        clear_btn.pack(side="right", padx=(0, 5))

        # Bouton metadata
        metadata_btn = ttk.Button(info_frame, text="Extract ComfyUI Data", 
                         command=self.extract_all_metadata_with_progress)
        metadata_btn.pack(side="right", padx=(0, 5))

        # Deuxième ligne - Contrôles principaux
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(fill="x", pady=(0, 5))

        # Bouton pour sélectionner le dossier
        select_btn = ttk.Button(control_frame, text="Select Directory", command=self.select_directory)
        select_btn.pack(side="left")

        # Label du dossier courant
        self.dir_label = ttk.Label(control_frame, text=f"Directory: {self.current_directory}")
        self.dir_label.pack(side="left", padx=(10, 0))

        # Troisième ligne - Actions
        action_frame = ttk.Frame(top_frame)
        action_frame.pack(fill="x", pady=(0, 5))

        # Bouton de rechargement
        refresh_btn = ttk.Button(action_frame, text="Refresh", command=self.refresh_images)
        refresh_btn.pack(side="left")

        # Bouton pour basculer le mode de vue
        self.view_mode_btn = ttk.Button(action_frame, text="Show All", command=self.toggle_view_mode)
        self.view_mode_btn.pack(side="left", padx=(10, 0))
        self.update_view_mode_button()

        # Bouton pour marquer toutes les images de la page comme vues
        mark_all_btn = ttk.Button(action_frame, text="Mark All as Viewed", command=self.mark_all_as_viewed)
        mark_all_btn.pack(side="left", padx=(10, 0))

        # Quatrième ligne - Navigation et barre de progression
        nav_frame = ttk.Frame(top_frame)
        nav_frame.pack(fill="x", pady=(0, 5))
        
        # Boutons de navigation
        self.prev_btn = ttk.Button(nav_frame, text="< Previous", command=self.prev_page)
        self.prev_btn.pack(side="left")
        
        self.page_label = ttk.Label(nav_frame, text="Page 1 of 1")
        self.page_label.pack(side="left", padx=(10, 10))
        
        self.next_btn = ttk.Button(nav_frame, text="Next >", command=self.next_page)
        self.next_btn.pack(side="left")
        
        # Barre de progression
        self.progress_bar = ttk.Progressbar(nav_frame, mode='indeterminate')
        self.progress_bar.pack(side="right", padx=(10, 0))

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

    def _on_mousewheel(self, event):
        """Gérer le défilement avec la molette"""
        try:
            if event.delta:
                # Windows
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif event.num == 4:
                # Linux - scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                # Linux - scroll down
                self.canvas.yview_scroll(1, "units")
        except Exception as e:
            print(f"[ERROR] Error in mousewheel: {e}")

    def select_directory(self):
        """Sélectionner un nouveau dossier d'images"""
        directory = filedialog.askdirectory(initialdir=self.current_directory)
        if directory:
            self.current_directory = directory
            self.dir_label.config(text=f"Directory: {self.current_directory}")
            self.page = 0
            self.load_images_async()
            self.setup_directory_watcher()

    def setup_directory_watcher(self):
        """Configurer la surveillance du répertoire"""
        # try:
        #     # if self.watcher_thread:
        #     #     self.watcher_thread.stop()
            
        #     # self.watcher_thread = DirectoryWatcherThread(self)
        #     # self.watcher_thread.start()
        # except Exception as e:
        #     print(f"[ERROR] Could not setup directory watcher: {e}")

    def load_images_async(self):
        """Charger les images de manière asynchrone"""
        if self.loading:
            return
        
        def load_thread():
            with self.loading_lock:
                self.loading = True
                # Vérifier que progress_bar existe avant de l'utiliser
                if hasattr(self, 'progress_bar'):
                    self.root.after(0, lambda: self.progress_bar.start())
                
                try:
                    self.load_images()
                except Exception as e:
                    print(f"[ERROR] Error loading images: {e}")
                finally:
                    self.loading = False
                    if hasattr(self, 'progress_bar'):
                        self.root.after(0, lambda: self.progress_bar.stop())

        threading.Thread(target=load_thread, daemon=True).start()

    def load_images(self):
        """Charger et afficher les images du dossier courant"""
        try:
            if not os.path.exists(self.current_directory):
                print(f"[ERROR] Directory does not exist: {self.current_directory}")
                return

            # Extensions d'images supportées
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            
            # Lister tous les fichiers images
            all_files = []
            for file in os.listdir(self.current_directory):
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(self.current_directory, file)
                    all_files.append(full_path)
            
            # Trier par nom
            all_files.sort()
            
            # Filtrer selon le mode de vue
            if self.view_mode == "new":
                # Filtrer pour ne montrer que les images non vues pour cette fonction
                filtered_files = []
                print(f"[DEBUG] Filtering {len(all_files)} images for function '{self.title}'")
                
                for image_path in all_files:
                    if not self.is_image_viewed(image_path):
                        filtered_files.append(image_path)
                    else:
                        print(f"[DEBUG] Excluding viewed image: {os.path.basename(image_path)}")
                
                filtered_files_to_use = filtered_files
                print(f"[DEBUG] After filtering: {len(filtered_files_to_use)} new images")
            else:
                # Montrer toutes les images
                filtered_files_to_use = all_files
    
            # Stocker les fichiers filtrés pour la pagination
            self.all_files = filtered_files_to_use
            
            # Calculer la pagination sur les images filtrées
            start_idx = self.page * self.page_size
            end_idx = start_idx + self.page_size
            self.image_files = filtered_files_to_use[start_idx:end_idx]
            
            total_pages = max(1, ((len(filtered_files_to_use) - 1) // self.page_size) + 1)
            
            if self.view_mode == "new":
                print(f"[INFO] Function '{self.title}': {len(all_files)} total, {len(filtered_files_to_use)} new, showing {len(self.image_files)} on page {self.page + 1}/{total_pages}")
            else:
                print(f"[INFO] Function '{self.title}': {len(all_files)} images, showing {len(self.image_files)} on page {self.page + 1}/{total_pages}")
            
            # Afficher les images dans l'interface
            self.root.after(0, self.display_images)
            
        except Exception as e:
            print(f"[ERROR] Error in load_images: {e}")

    def display_images(self):
        """Afficher les images dans l'interface graphique"""
        try:
            # Nettoyer les widgets existants
            for widget in self.image_widgets:
                widget.destroy()
            self.image_widgets.clear()

            if not self.image_files:
                no_images_label = ttk.Label(self.scrollable_frame, text="No images found in this directory")
                no_images_label.grid(row=0, column=0, padx=10, pady=10)
                self.image_widgets.append(no_images_label)
                return

            # Vérifier quelles images n'ont pas encore de métadonnées
            images_needing_metadata = []
            for image_path in self.image_files:
                existing_metadata = self.get_image_metadata(image_path)
                if not existing_metadata:
                    images_needing_metadata.append(image_path)
    
            # Extraire les métadonnées SEULEMENT pour les nouvelles images
            if images_needing_metadata:
                print(f"[INFO] Extracting metadata for {len(images_needing_metadata)} new images")
                self.root.after(100, lambda: self.extract_and_store_metadata_batch(images_needing_metadata))
            else:
                print(f"[INFO] All displayed images already have metadata")

            # Afficher les images en grille
            cols = 4  # Nombre de colonnes
            for idx, image_path in enumerate(self.image_files):
                try:
                    row = idx // cols
                    col = idx % cols
                    
                    # Créer un frame pour l'image
                    image_frame = ttk.Frame(self.scrollable_frame)
                    image_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    
                    # Vérifier si l'image a été vue
                    is_viewed = self.is_image_viewed(image_path)
                    
                    # Récupérer les métadonnées
                    metadata = self.get_image_metadata(image_path)
                    
                    # Charger et redimensionner l'image
                    with Image.open(image_path) as img:
                        # Redimensionner en gardant les proportions
                        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                        
                        # Si l'image a été vue, réduire l'opacité
                        if is_viewed:
                            # Convertir en RGBA pour la transparence
                            img = img.convert("RGBA")
                            # Réduire l'opacité à 50%
                            img.putalpha(128)
                        
                        photo = ImageTk.PhotoImage(img)
                    
                    # Label pour l'image avec couleur de fond différente si vue
                    bg_color = "#f0f0f0" if is_viewed else "white"
                    img_label = tk.Label(image_frame, image=photo, cursor="hand2", bg=bg_color)
                    img_label.image = photo  # Garder une référence
                    img_label.pack()
                    
                    # Label pour le nom du fichier avec indication si vue
                    filename = os.path.basename(image_path)
                    if is_viewed:
                        filename = f"✓ {filename}"  # Ajouter une coche
                    
                    # Ajouter les informations de métadonnées si disponibles
                    if metadata:
                        info_text = f"{filename}\n{metadata['width']}x{metadata['height']} - {metadata['format']}"
                        if metadata['file_size']:
                            size_mb = metadata['file_size'] / (1024 * 1024)
                            info_text += f"\n{size_mb:.1f} MB"
                    
                        # Ajouter un aperçu du prompt si disponible
                        if metadata.get('positive_prompt'):
                            prompt_preview = metadata['positive_prompt'][:30] + "..." if len(metadata['positive_prompt']) > 30 else metadata['positive_prompt']
                            info_text += f"\n📝 {prompt_preview}"
                    else:
                        info_text = filename
                    
                    name_label = ttk.Label(image_frame, text=info_text, wraplength=180)
                    name_label.pack()
                    
                    # Boutons d'action
                    btn_frame = ttk.Frame(image_frame)
                    btn_frame.pack(fill="x", pady=2)
                    
                    # Bouton "Viewed" - texte différent selon l'état
                    if is_viewed:
                        viewed_btn = ttk.Button(btn_frame, text="Viewed ✓", state="disabled")
                    else:
                        viewed_btn = ttk.Button(btn_frame, text="Mark Viewed", 
                                              command=lambda path=image_path: self.mark_action_viewed(path))
                    viewed_btn.pack(side="left", padx=2)

                    # Bouton "Info" pour afficher les métadonnées complètes
                    info_btn = ttk.Button(btn_frame, text="Info", 
                                    command=lambda path=image_path: self.show_image_metadata(path))
                    info_btn.pack(side="left", padx=2)

                    if self.processor_type == "move":
                        # Bouton "Move" - toujours actif
                        move_btn = ttk.Button(btn_frame, text="Move",
                                              command=lambda path=image_path: self.mark_action_move(path))
                        move_btn.pack(side="left", padx=2)

                    # Clic sur l'image pour l'ouvrir
                    img_label.bind("<Button-1>", lambda e, path=image_path: self.open_image(path))
                    
                    # Stocker les références
                    image_frame.image_path = image_path
                    self.image_widgets.append(image_frame)
                    
                except Exception as e:
                    print(f"[ERROR] Error displaying image {image_path}: {e}")
                    continue

            # Mettre à jour les boutons de navigation
            self.update_navigation_buttons()
        except Exception as e:
            print(f"[ERROR] Error in display_images: {e}")
    
    def mark_action_viewed(self, image_path):
        """Marquer une image comme vue"""
        try:
            if self.mark_image_viewed(image_path):
                # En mode "new", recharger l'affichage pour masquer l'image
                if self.view_mode == "new":
                    self.refresh_images()
        except Exception as e:
            print(f"[ERROR] Error marking image as viewed: {e}")
            messagebox.showerror("Error", f"Failed to mark image as viewed: {e}")

    def mark_action_move(self, image_path):
        """Déplacer une image vers le dossier cible"""
        try:
            if not self.cible_directory or not os.path.exists(self.cible_directory):
                messagebox.showerror("Error", "Target directory not configured or does not exist")
                return
            
            filename = os.path.basename(image_path)
            target_path = os.path.join(self.cible_directory, filename)
            
            # Confirmer l'action
            #result = messagebox.askyesno("Confirm Move", f"Move {filename} to {self.cible_directory}?")
            result=True
            if result:
                # Déplacer le fichier
                shutil.move(image_path, target_path)
                
                # Supprimer les métadonnées de la base de données
                self.remove_image_metadata(image_path)
                
                # Recharge la page pour tout réafficher proprement
                self.refresh_images()
                
                #messagebox.showinfo("Success", f"Image moved: {filename}")
                
        except Exception as e:
            print(f"[ERROR] Error moving image: {e}")
            messagebox.showerror("Error", f"Failed to move image: {e}")

    def hide_image_widget_immediately(self, image_path):
        """Masquer immédiatement le widget d'une image spécifique"""
        try:
            for widget in self.image_widgets[:]:  # Copie de la liste pour éviter les modifications pendant l'itération
                if hasattr(widget, 'image_path') and widget.image_path == image_path:
                    # Détruire le widget
                    widget.destroy()
                    # Retirer de la liste des widgets
                    self.image_widgets.remove(widget)
                    print(f"[INFO] Image widget removed: {os.path.basename(image_path)}")
                    
                    # Réorganiser les widgets restants
                    self.reorganize_image_grid()
                    break
                    
        except Exception as e:
            print(f"[ERROR] Error hiding image widget: {e}")

    def reorganize_image_grid(self):
        """Réorganiser la grille d'images après suppression d'un élément"""
        try:
            cols = 4  # Nombre de colonnes
            
            # Repositionner tous les widgets restants
            for idx, widget in enumerate(self.image_widgets):
                if widget.winfo_exists():  # Vérifier que le widget existe encore
                    row = idx // cols
                    col = idx % cols
                    widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Mettre à jour la région de défilement
            self.root.after(10, self.check_and_update_canvas)
            
        except Exception as e:
            print(f"[ERROR] Error reorganizing grid: {e}")

    def remove_image_metadata(self, image_path):
        """Supprimer les métadonnées d'une image de la base de données"""
        try:
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            # Supprimer les métadonnées
            cursor.execute(
                "DELETE FROM image_metadata WHERE function_name = ? AND image_path = ?",
                (self.title, image_path)
            )
            
            # Supprimer l'entrée "viewed" aussi
            cursor.execute(
                "DELETE FROM viewed_images WHERE function_name = ? AND image_path = ?",
                (self.title, image_path)
            )
            
            conn.commit()
            conn.close()
            
            print(f"[INFO] Metadata removed for: {os.path.basename(image_path)}")
            
        except Exception as e:
            print(f"[ERROR] Error removing metadata: {e}")

    def check_and_update_canvas(self):
        """Mettre à jour la région de défilement du canvas"""
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            print(f"[ERROR] Error updating canvas: {e}")

    def open_image(self, image_path):
        """Ouvrir une image avec l'application par défaut du système"""
        try:
            import os
            import platform
            import subprocess
            
            system = platform.system()
            if system == "Windows":
                os.startfile(image_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", image_path])
            else:  # Linux et autres
                subprocess.run(["xdg-open", image_path])
                
        except Exception as e:
            print(f"[ERROR] Error opening image: {e}")
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def toggle_view_mode(self):
        """Basculer entre le mode 'new' et 'all'"""
        self.view_mode = "all" if self.view_mode == "new" else "new"
        self.update_view_mode_button()
        self.page = 0  # Reset à la première page
        self.load_images_async()

    def update_view_mode_button(self):
        """Mettre à jour le texte du bouton selon le mode"""
        if self.view_mode == "new":
            self.view_mode_btn.config(text="Show All")
        else:
            self.view_mode_btn.config(text="Show New Only")

    def refresh_images(self):
        """Rafraîchir l'affichage des images"""
        self.page = 0
        self.load_images_async()

    def mark_all_as_viewed(self):
        """Marquer toutes les images de la page courante comme vues"""
        try:
            marked_count = 0
            for image_path in self.image_files:
                if not self.is_image_viewed(image_path):
                    if self.mark_image_viewed(image_path):
                        marked_count += 1
            
            if marked_count > 0:
                messagebox.showinfo("Success", f"{marked_count} images marked as viewed")
                if self.view_mode == "new":
                    self.refresh_images()
            else:
                messagebox.showinfo("Info", "No new images to mark")
                
        except Exception as e:
            print(f"[ERROR] Error marking all as viewed: {e}")
            messagebox.showerror("Error", f"Failed to mark images as viewed: {e}")

    def prev_page(self):
        """Page précédente"""
        if self.page > 0:
            self.page -= 1
            self.load_images_async()

    def next_page(self):
        """Page suivante"""
        total_pages = max(1, ((len(self.all_files) - 1) // self.page_size) + 1)
        if self.page < total_pages - 1:
            self.page += 1
            self.load_images_async()

    def update_navigation_buttons(self):
        """Mettre à jour l'état des boutons de navigation"""
        try:
            total_pages = max(1, ((len(self.all_files) - 1) // self.page_size) + 1)
            current_page = self.page + 1
            
            # Mettre à jour le label de page
            self.page_label.config(text=f"Page {current_page} of {total_pages}")
            
            # Activer/désactiver les boutons
            self.prev_btn.config(state="normal" if self.page > 0 else "disabled")
            self.next_btn.config(state="normal" if self.page < total_pages - 1 else "disabled")
            
        except Exception as e:
            print(f"[ERROR] Error updating navigation: {e}")

    def show_function_stats(self):
        """Afficher les statistiques de la fonction"""
        try:
            conn, cursor = self.get_db_connection()
            
            # Compter les images vues pour cette fonction
            cursor.execute(
                "SELECT COUNT(*) FROM viewed_images WHERE function_name = ?",
                (self.title,)
            )
            viewed_count = cursor.fetchone()[0]
            
            # Compter le total d'images dans le dossier
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            total_count = 0
            if os.path.exists(self.current_directory):
                for file in os.listdir(self.current_directory):
                    if file.lower().endswith(image_extensions):
                        total_count += 1
            
            conn.close()
            
            stats_text = f"""Function: {self.title}
Directory: {self.current_directory}

Total images: {total_count}
Viewed images: {viewed_count}
Remaining: {total_count - viewed_count}
Progress: {(viewed_count/total_count*100):.1f}% completed"""
            
            messagebox.showinfo("Function Statistics", stats_text)
            
        except Exception as e:
            print(f"[ERROR] Error showing stats: {e}")
            messagebox.showerror("Error", f"Failed to get statistics: {e}")

    def clear_function_viewed_images(self):
        """Effacer toutes les images vues pour cette fonction"""
        try:
            result = messagebox.askyesno("Confirm Clear", 
                                       f"Clear all viewed images for function '{self.title}'?\nThis will mark all images as new.")
            if result:
                conn, cursor = self.get_db_connection()
                cursor.execute(
                    "DELETE FROM viewed_images WHERE function_name = ?",
                    (self.title,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", f"Cleared {deleted_count} viewed images")
                self.refresh_images()
                
        except Exception as e:
            print(f"[ERROR] Error clearing viewed images: {e}")
            messagebox.showerror("Error", f"Failed to clear viewed images: {e}")

    def calculate_file_hash(self, file_path):
        """Calculer le hash SHA256 d'un fichier"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"[ERROR] Error calculating hash for {file_path}: {e}")
            return None

    def extract_image_metadata(self, image_path):
        """Extraire les métadonnées d'une image"""
        try:
            # Informations du fichier
            file_stats = os.stat(image_path)
            file_size = file_stats.st_size
            creation_date = file_stats.st_ctime
            modified_date = file_stats.st_mtime
            
            # Hash du fichier
            file_hash = self.calculate_file_hash(image_path)
            
            # Métadonnées de l'image avec PIL
            with Image.open(image_path) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
                
                # Extraire les données EXIF
                exif_data = {}
                if hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif is not None:
                        for tag, value in exif.items():
                            tag_name = TAGS.get(tag, tag)
                            exif_data[tag_name] = str(value)
            
            # Extraire les métadonnées ComfyUI
            comfyui_metadata = self.extract_comfyui_metadata(image_path)
            
            metadata = {
                'file_size': file_size,
                'width': width,
                'height': height,
                'format': format_type,
                'mode': mode,
                'file_hash': file_hash,
                'creation_date': creation_date,
                'modified_date': modified_date,
                'exif_data': json.dumps(exif_data) if exif_data else None,
                'positive_prompt': '',
                'negative_prompt': '',
                'workflow_data': '',
                'model_info': {}
            }
            
            # Ajouter les données ComfyUI si trouvées
            if comfyui_metadata:
                metadata.update({
                    'positive_prompt': comfyui_metadata.get('positive_prompt', ''),
                    'negative_prompt': comfyui_metadata.get('negative_prompt', ''),
                    'workflow_data': comfyui_metadata.get('workflow_data', ''),
                    'model_info': comfyui_metadata.get('model_info', {})
                })
            
            return metadata
            
        except Exception as e:
            print(f"[ERROR] Error extracting metadata for {image_path}: {e}")
            return None

    def extract_comfyui_metadata(self, image_path):
        """Extraire les métadonnées spécifiques à ComfyUI"""
        try:
            prompts_data = {}
            
            with Image.open(image_path) as img:
                # ComfyUI stocke ses données dans les métadonnées PNG
                if hasattr(img, 'text') and img.text:
                    # Chercher les clés spécifiques à ComfyUI
                    if 'workflow' in img.text:
                        try:
                            workflow_data = json.loads(img.text['workflow'])
                            prompts_data['workflow'] = workflow_data
                        except json.JSONDecodeError:
                            pass
                    
                    if 'prompt' in img.text:
                        try:
                            prompt_data = json.loads(img.text['prompt'])
                            prompts_data['prompt'] = prompt_data
                        except json.JSONDecodeError:
                            pass
                    
                    # Extraire les prompts des nœuds
                    positive_prompt, negative_prompt = self.parse_comfyui_prompts(prompts_data)
                    model_info = self.extract_model_info(prompts_data)
                    
                    if positive_prompt or negative_prompt:
                        return {
                            'positive_prompt': positive_prompt,
                            'negative_prompt': negative_prompt,
                            'workflow_data': json.dumps(prompts_data) if prompts_data else None,
                            'model_info': model_info
                        }
            return None
            
        except Exception as e:
            print(f"[ERROR] Error extracting ComfyUI metadata for {image_path}: {e}")
            return None

    def parse_comfyui_prompts(self, comfyui_data):
        """Parser les prompts positifs et négatifs depuis les données ComfyUI"""
        try:
            positive_prompt = ""
            negative_prompt = ""
            
            for data_key, data_value in comfyui_data.items():
                if isinstance(data_value, dict):
                    for node_id, node_data in data_value.items():
                        if isinstance(node_data, dict) and 'inputs' in node_data:
                            inputs = node_data['inputs']
                            class_type = node_data.get('class_type', '').lower()
                            
                            # Patterns pour Flux-Schnell
                            if 'text' in inputs:
                                text_content = inputs['text']
                                
                                if 'positive' in class_type or ('clip' in class_type and 'negative' not in class_type):
                                    positive_prompt = text_content
                                elif 'negative' in class_type:
                                    negative_prompt = text_content
                                elif not positive_prompt:
                                    positive_prompt = text_content
                            
                            # Autres patterns
                            if 'positive' in inputs:
                                positive_prompt = inputs['positive']
                            if 'negative' in inputs:
                                negative_prompt = inputs['negative']
            
            return positive_prompt, negative_prompt
            
        except Exception as e:
            print(f"[ERROR] Error parsing ComfyUI prompts: {e}")
            return "", ""

    def extract_model_info(self, comfyui_data):
        """Extraire les informations du modèle utilisé"""
        try:
            model_info = {}
            
            for data_key, data_value in comfyui_data.items():
                if isinstance(data_value, dict):
                    for node_id, node_data in data_value.items():
                        if isinstance(node_data, dict):
                            class_type = node_data.get('class_type', '').lower()
                            inputs = node_data.get('inputs', {})
                            
                            # Modèles
                            if any(keyword in class_type for keyword in ['checkpoint', 'model', 'flux']):
                                if 'ckpt_name' in inputs:
                                    model_info['checkpoint'] = inputs['ckpt_name']
                                if 'model_name' in inputs:
                                    model_info['model'] = inputs['model_name']
                                if 'vae_name' in inputs:
                                    model_info['vae'] = inputs['vae_name']
                            
                            # Paramètres de génération
                            if any(keyword in class_type for keyword in ['sampler', 'scheduler']):
                                model_info.update({
                                    'steps': inputs.get('steps'),
                                    'cfg': inputs.get('cfg'),
                                    'sampler_name': inputs.get('sampler_name'),
                                    'scheduler': inputs.get('scheduler'),
                                    'seed': inputs.get('seed')
                                })
            
            return model_info
            
        except Exception as e:
            print(f"[ERROR] Error extracting model info: {e}")
            return {}

    def store_image_metadata(self, image_path, metadata):
        """Stocker les métadonnées d'une image en base"""
        try:
            if not metadata:
                return False
                
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            model_info = metadata.get('model_info', {})
            
            # Convertir les valeurs pour éviter les erreurs de type
            positive_prompt = str(metadata.get('positive_prompt', '')) if metadata.get('positive_prompt') else ''
            negative_prompt = str(metadata.get('negative_prompt', '')) if metadata.get('negative_prompt') else ''
            workflow_data = str(metadata.get('workflow_data', '')) if metadata.get('workflow_data') else ''
            
            cursor.execute('''
                INSERT OR REPLACE INTO image_metadata 
                (function_name, image_path, file_size, width, height, format, mode, 
                 file_hash, creation_date, modified_date, exif_data,
                 positive_prompt, negative_prompt, workflow_data,
                 model_checkpoint, model_vae, generation_steps, cfg_scale,
                 sampler_name, scheduler, seed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.title, 
                image_path, 
                metadata['file_size'], 
                metadata['width'], 
                metadata['height'], 
                metadata['format'], 
                metadata['mode'], 
                metadata['file_hash'],
                metadata['creation_date'], 
                metadata['modified_date'], 
                metadata['exif_data'],
                positive_prompt,
                negative_prompt,
                workflow_data,
                str(model_info.get('checkpoint', '')) if model_info.get('checkpoint') else '',
                str(model_info.get('vae', '')) if model_info.get('vae') else '',
                model_info.get('steps') if model_info.get('steps') is not None else None,
                model_info.get('cfg') if model_info.get('cfg') is not None else None,
                str(model_info.get('sampler_name', '')) if model_info.get('sampler_name') else '',
                str(model_info.get('scheduler', '')) if model_info.get('scheduler') else '',
                model_info.get('seed') if model_info.get('seed') is not None else None
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"[ERROR] Error storing metadata: {e}")
            return False

    def get_image_metadata(self, image_path):
        """Récupérer les métadonnées d'une image depuis la base"""
        try:
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            cursor.execute('''
                SELECT file_size, width, height, format, mode, file_hash, 
                       creation_date, modified_date, exif_data, extracted_date,
                       positive_prompt, negative_prompt, workflow_data,
                       model_checkpoint, model_vae, generation_steps, cfg_scale,
                       sampler_name, scheduler, seed
                FROM image_metadata 
                WHERE function_name = ? AND image_path = ?
            ''', (self.title, image_path))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'file_size': result[0],
                    'width': result[1],
                    'height': result[2],
                    'format': result[3],
                    'mode': result[4],
                    'file_hash': result[5],
                    'creation_date': result[6],
                    'modified_date': result[7],
                    'exif_data': json.loads(result[8]) if result[8] else None,
                    'extracted_date': result[9],
                    'positive_prompt': result[10] or '',
                    'negative_prompt': result[11] or '',
                    'workflow_data': result[12] or '',
                    'model_checkpoint': result[13] or '',
                    'model_vae': result[14] or '',
                    'generation_steps': result[15],
                    'cfg_scale': result[16],
                    'sampler_name': result[17] or '',
                    'scheduler': result[18] or '',
                    'seed': result[19]
                }
            return None
            
        except Exception as e:
            print(f"[ERROR] Error getting metadata: {e}")
            return None

    def extract_and_store_metadata_batch(self, image_paths):
        """Extraire et stocker les métadonnées pour un lot d'images"""
        try:
            for image_path in image_paths:
                # Vérifier si les métadonnées existent déjà
                existing_metadata = self.get_image_metadata(image_path)
                if existing_metadata:
                    continue  # Skip si déjà traité
                
                # Extraire et stocker les métadonnées
                metadata = self.extract_image_metadata(image_path)
                if metadata:
                    self.store_image_metadata(image_path, metadata)
                    
        except Exception as e:
            print(f"[ERROR] Error in batch metadata extraction: {e}")

    def extract_all_metadata_with_progress(self):
        """Extraire les métadonnées avec barre de progression"""
        try:
            # Obtenir toutes les images
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
            all_images = []
            for file in os.listdir(self.current_directory):
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(self.current_directory, file)
                    all_images.append(full_path)
            
            if not all_images:
                messagebox.showinfo("Info", "No images found in directory")
                return
            
            # Créer la fenêtre de progression
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Extracting Metadata")
            progress_window.geometry("500x200")
            progress_window.resizable(False, False)
            
            # Centrer la fenêtre
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            main_frame = ttk.Frame(progress_window, padding=20)
            main_frame.pack(fill="both", expand=True)
            
            title_label = ttk.Label(main_frame, text="Extracting ComfyUI Metadata", font=("Arial", 12, "bold"))
            title_label.pack(pady=(0, 10))
            
            self.progress_var = tk.DoubleVar()
            self.progress_label = ttk.Label(main_frame, text="Preparing...")
            self.progress_label.pack(pady=(0, 5))
            
            progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
            progress_bar.pack(fill="x", pady=(0, 10))
            
            self.status_label = ttk.Label(main_frame, text="")
            self.status_label.pack()
            
            # Bouton d'annulation
            self.cancel_extraction = False
            cancel_btn = ttk.Button(main_frame, text="Cancel", 
                                   command=lambda: setattr(self, 'cancel_extraction', True))
            cancel_btn.pack(pady=(10, 0))
            
            # Lancer l'extraction en thread
            def extraction_thread():
                results = self.extract_metadata_batch_with_progress(all_images, progress_window)
                self.root.after(0, lambda: self.show_extraction_results(results, progress_window))
            
            threading.Thread(target=extraction_thread, daemon=True).start()
            
        except Exception as e:
            print(f"[ERROR] Error starting metadata extraction: {e}")
            messagebox.showerror("Error", f"Failed to start extraction: {e}")

    def extract_metadata_batch_with_progress(self, image_paths, progress_window):
        """Extraire les métadonnées avec mise à jour de la progression"""
        try:
            total = len(image_paths)
            processed = 0
            skipped = 0
            errors = 0
            comfyui_found = 0
            results = []
            
            for i, image_path in enumerate(image_paths):
                if getattr(self, 'cancel_extraction', False):
                    break
                    
                try:
                    filename = os.path.basename(image_path)
                    
                    # Mise à jour de l'interface
                    progress = (i / total) * 100
                    self.root.after(0, lambda p=progress, f=filename: self.update_progress(p, f"Processing: {f}"))
                    
                    # Vérifier si déjà traité
                    existing_metadata = self.get_image_metadata(image_path)
                    if existing_metadata and existing_metadata.get('positive_prompt') is not None:
                        skipped += 1
                        results.append({
                            'file': filename,
                            'status': 'Skipped',
                            'reason': 'Already processed',
                            'has_comfyui': bool(existing_metadata.get('positive_prompt'))
                        })
                        continue
                    
                    # Extraire les métadonnées
                    metadata = self.extract_image_metadata(image_path)
                    if metadata:
                        if self.store_image_metadata(image_path, metadata):
                            processed += 1
                            has_comfyui = bool(metadata.get('positive_prompt'))
                            if has_comfyui:
                                comfyui_found += 1
                            
                            results.append({
                                'file': filename,
                                'status': 'Processed',
                                'width': metadata.get('width'),
                                'height': metadata.get('height'),
                                'format': metadata.get('format'),
                                'file_size': metadata.get('file_size'),
                                'has_comfyui': has_comfyui,
                                'positive_prompt': metadata.get('positive_prompt', '')[:100] + '...' if len(metadata.get('positive_prompt', '')) > 100 else metadata.get('positive_prompt', ''),
                                'model': metadata.get('model_info', {}).get('checkpoint', '')
                            })
                        else:
                            errors += 1
                            results.append({
                                'file': filename,
                                'status': 'Error',
                                'reason': 'Failed to store'
                            })
                    else:
                        errors += 1
                        results.append({
                            'file': filename,
                            'status': 'Error',
                            'reason': 'Failed to extract'
                        })
                    
                    # Petit délai pour permettre l'annulation
                    time.sleep(0.01)
                    
                except Exception as e:
                    errors += 1
                    results.append({
                        'file': os.path.basename(image_path),
                        'status': 'Error',
                        'reason': str(e)
                    })
            
            # Résumé final
            summary = {
                'total': total,
                'processed': processed,
                'skipped': skipped,
                'errors': errors,
                'comfyui_found': comfyui_found,
                'cancelled': getattr(self, 'cancel_extraction', False)
            }
            
            return {'summary': summary, 'details': results}
            
        except Exception as e:
            print(f"[ERROR] Error in batch extraction: {e}")
            return {'summary': {'total': 0, 'processed': 0, 'errors': 1}, 'details': []}

    def update_progress(self, progress, status):
        """Mettre à jour la barre de progression"""
        try:
            if hasattr(self, 'progress_var'):
                self.progress_var.set(progress)
            if hasattr(self, 'progress_label'):
                self.progress_label.config(text=f"Progress: {progress:.1f}%")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=status)
        except:
            pass

    def show_extraction_results(self, results, progress_window):
        """Afficher les résultats de l'extraction dans un formulaire"""
        try:
            progress_window.destroy()
            
            summary = results['summary']
            
            # Créer la fenêtre de résultats
            results_window = tk.Toplevel(self.root)
            results_window.title("ComfyUI Metadata Extraction Results")
            results_window.geometry("600x400")
            results_window.resizable(True, True)
            
            main_frame = ttk.Frame(results_window, padding=10)
            main_frame.pack(fill="both", expand=True)
            
            # Titre
            title_label = ttk.Label(main_frame, text="ComfyUI Metadata Extraction Results", 
                                   font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 10))
            
            # Résumé
            summary_frame = ttk.LabelFrame(main_frame, text="Summary", padding=10)
            summary_frame.pack(fill="x", pady=(0, 10))
            
            total_new = summary['total'] - summary['skipped']
            success_rate = (summary['processed'] / total_new * 100) if total_new > 0 else 0
            
            summary_text = f"""Total images: {summary['total']}
Successfully processed: {summary['processed']}
Already processed (skipped): {summary['skipped']}
Errors: {summary['errors']}
Images with ComfyUI prompts: {summary['comfyui_found']}
Success rate: {success_rate:.1f}% (of new images)"""

            if summary.get('cancelled'):
                summary_text += "\n⚠️ Extraction was cancelled"
            
            summary_label = ttk.Label(summary_frame, text=summary_text, justify="left")
            summary_label.pack()
            
            # Boutons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            close_btn = ttk.Button(button_frame, text="Close", command=results_window.destroy)
            close_btn.pack(side="right", padx=(5, 0))
            
        except Exception as e:
            print(f"[ERROR] Error showing results: {e}")
            messagebox.showerror("Error", f"Failed to show results: {e}")

    def show_image_metadata(self, image_path):
        """Afficher les métadonnées complètes d'une image dans un formulaire avec onglets"""
        try:
            metadata = self.get_image_metadata(image_path)
            if not metadata:
                # Extraire les métadonnées si pas encore fait
                meta = self.extract_image_metadata(image_path)
                if meta:
                    self.store_image_metadata(image_path, meta)
                    metadata = meta

            if metadata:
                filename = os.path.basename(image_path)
                
                # Créer la fenêtre principale
                metadata_window = tk.Toplevel(self.root)
                metadata_window.title(f"Image Metadata - {filename}")
                metadata_window.geometry("800x600")
                metadata_window.resizable(True, True)
                
                # Frame principal
                main_frame = ttk.Frame(metadata_window, padding=10)
                main_frame.pack(fill="both", expand=True)
                
                # Titre avec nom du fichier
                title_label = ttk.Label(main_frame, text=f"Metadata: {filename}", 
                                       font=("Arial", 14, "bold"))
                title_label.pack(pady=(0, 10))
                
                # Créer le notebook pour les onglets
                notebook = ttk.Notebook(main_frame)
                notebook.pack(fill="both", expand=True, pady=(0, 10))
                
                # ONGLET 1: ComfyUI Prompts
                prompts_frame = ttk.Frame(notebook, padding=10)
                notebook.add(prompts_frame, text="ComfyUI Prompts")
                
                if metadata.get('positive_prompt') or metadata.get('negative_prompt'):
                    # Positive Prompt
                    pos_label = ttk.Label(prompts_frame, text="Positive Prompt:", 
                                         font=("Arial", 10, "bold"))
                    pos_label.pack(anchor="w", pady=(0, 5))
                    
                    pos_frame = ttk.Frame(prompts_frame)
                    pos_frame.pack(fill="both", expand=True, pady=(0, 10))
                    
                    pos_text = tk.Text(pos_frame, height=8, wrap=tk.WORD)
                    pos_text.insert("1.0", metadata.get('positive_prompt', 'No positive prompt'))
                    pos_text.config(state=tk.DISABLED)
                    
                    pos_scrollbar = ttk.Scrollbar(pos_frame, orient="vertical", command=pos_text.yview)
                    pos_text.configure(yscrollcommand=pos_scrollbar.set)
                    
                    pos_text.pack(side="left", fill="both", expand=True)
                    pos_scrollbar.pack(side="right", fill="y")
                    
                    # Bouton pour copier le prompt positif
                    pos_btn_frame = ttk.Frame(prompts_frame)
                    pos_btn_frame.pack(fill="x", pady=(0, 10))
                    
                    copy_pos_btn = ttk.Button(pos_btn_frame, text="Copy Positive Prompt", 
                                             command=lambda: self.copy_to_clipboard(metadata.get('positive_prompt', '')))
                    copy_pos_btn.pack(side="left")
                    
                    # Negative Prompt
                    neg_label = ttk.Label(prompts_frame, text="Negative Prompt:", 
                                         font=("Arial", 10, "bold"))
                    neg_label.pack(anchor="w", pady=(0, 5))
                    
                    neg_frame = ttk.Frame(prompts_frame)
                    neg_frame.pack(fill="both", expand=True)
                    
                    neg_text = tk.Text(neg_frame, height=6, wrap=tk.WORD)
                    neg_text.insert("1.0", metadata.get('negative_prompt', 'No negative prompt'))
                    neg_text.config(state=tk.DISABLED)
                    
                    neg_scrollbar = ttk.Scrollbar(neg_frame, orient="vertical", command=neg_text.yview)
                    neg_text.configure(yscrollcommand=neg_scrollbar.set)
                    
                    neg_text.pack(side="left", fill="both", expand=True)
                    neg_scrollbar.pack(side="right", fill="y")
                    
                    # Bouton pour copier le prompt négatif
                    neg_btn_frame = ttk.Frame(prompts_frame)
                    neg_btn_frame.pack(fill="x", pady=(10, 0))
                    
                    copy_neg_btn = ttk.Button(neg_btn_frame, text="Copy Negative Prompt", 
                                             command=lambda: self.copy_to_clipboard(metadata.get('negative_prompt', '')))
                    copy_neg_btn.pack(side="left")
                    
                else:
                    no_prompts_label = ttk.Label(prompts_frame, text="No ComfyUI prompts found in this image", 
                                               font=("Arial", 12))
                    no_prompts_label.pack(expand=True)
                
                # ONGLET 2: Generation Parameters
                params_frame = ttk.Frame(notebook, padding=10)
                notebook.add(params_frame, text="Generation Parameters")
                
                if metadata.get('model_checkpoint') or metadata.get('generation_steps'):
                    # Paramètres de génération
                    params_data = [
                        ("Model Checkpoint", metadata.get('model_checkpoint', 'Unknown')),
                        ("VAE", metadata.get('model_vae', 'Unknown')),
                        ("Steps", metadata.get('generation_steps', 'Unknown')),
                        ("CFG Scale", metadata.get('cfg_scale', 'Unknown')),
                        ("Sampler", metadata.get('sampler_name', 'Unknown')),
                        ("Scheduler", metadata.get('scheduler', 'Unknown')),
                        ("Seed", metadata.get('seed', 'Unknown'))
                    ]
                    
                    for i, (label, value) in enumerate(params_data):
                        param_frame = ttk.Frame(params_frame)
                        param_frame.pack(fill="x", pady=2)
                        
                        param_label = ttk.Label(param_frame, text=f"{label}:", 
                                               font=("Arial", 9, "bold"), width=15)
                        param_label.pack(side="left", anchor="w")
                        
                        param_value = ttk.Label(param_frame, text=str(value))
                        param_value.pack(side="left", anchor="w", padx=(10, 0))
                    
                else:
                    no_params_label = ttk.Label(params_frame, text="No generation parameters found", 
                                              font=("Arial", 12))
                    no_params_label.pack(expand=True)
                
                # Frame pour les boutons en bas
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill="x", pady=(10, 0))
                
                # Bouton pour fermer
                close_btn = ttk.Button(button_frame, text="Close", command=metadata_window.destroy)
                close_btn.pack(side="right", padx=(5, 0))
                
                # Bouton pour ouvrir l'image
                open_btn = ttk.Button(button_frame, text="Open Image", 
                                     command=lambda: self.open_image(image_path))
                open_btn.pack(side="right", padx=(5, 0))
                
                # Bouton pour copier le chemin
                copy_path_btn = ttk.Button(button_frame, text="Copy Path", 
                                          command=lambda: self.copy_to_clipboard(image_path))
                copy_path_btn.pack(side="right", padx=(5, 0))
                
            else:
                messagebox.showwarning("Warning", "No metadata available for this image")
            
        except Exception as e:
            print(f"[ERROR] Error showing metadata: {e}")
            messagebox.showerror("Error", f"Failed to get metadata: {e}")

    def copy_to_clipboard(self, text):
        """Copier du texte dans le presse-papiers"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # Maintenir le presse-papiers
            messagebox.showinfo("Copied", "Text copied to clipboard")
        except Exception as e:
            print(f"[ERROR] Error copying to clipboard: {e}")
            messagebox.showerror("Error", "Failed to copy to clipboard")


def main(config):
    """Fonction principale pour créer et lancer l'interface"""
    root = tk.Tk()
    app = image_process(root, config)
    
    # Initialiser après la construction complète
    root.after(100, app.initialize)
    
    root.mainloop()


# Point d'entrée si le script est exécuté directement
if __name__ == "__main__":
    # Configuration de test
    test_config = {
        'title': 'Test Image Explorer',
        'default_directory': r'C:\Users\Public\Pictures',
        'cible_directory': r'C:\Users\Public\Pictures\Moved',
        'db_path': 'test_image_explorer.db',
        'processor_type': 'standard'
    }
    
    main(test_config)
