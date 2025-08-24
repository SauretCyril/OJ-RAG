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
from cy2_analyse_prompt import cy2_analyse_prompt
from cy_mistral import get_nsfw_score
#from cy2_analyse_prompt import cls_local_PromptTable



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

            # Vérifier si la table existe déjà
            self.cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='viewed_images'
            """)
            table_exists = self.cursor.fetchone()

            if not table_exists:
                self.cursor.execute('''
                    CREATE TABLE viewed_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        function_name TEXT NOT NULL,
                        image_path TEXT NOT NULL,
                        viewed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(function_name, image_path)
                    )
                ''')

            # Supprimer et recréer la table des métadonnées avec tous les champs ComfyUI
            #self.cursor.execute("DROP TABLE IF EXISTS image_metadata")
            
            # Vérifier si la table image_metadata existe déjà
            self.cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='image_metadata'
            """)
            table_exists = self.cursor.fetchone()

            if not table_exists:
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
                        nsfw_score REAL DEFAULT 0,
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
                "INSERT OR IGNORE INTO viewed_images (function_name, image_path) VALUES (?, ?)",  # <-- Changement ici
                (self.title, image_path)
            )
            conn.commit()
            conn.close()
            
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
        options_btn = ttk.Button(info_frame, text="Options", command=self.open_options_dialog)
        options_btn.pack(side="right", padx=(0, 5))

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

        load_meta_btn = ttk.Button(action_frame, text="Charger toutes les métadonnées", command=self.Extract_all_metadata)
        load_meta_btn.pack(side="left", padx=(10, 0))

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
        """Charger les images de manière asynchrone avec une fenêtre modale"""
        if self.loading:
            return

        def load_thread():
            with self.loading_lock:
                self.loading = True
                self.root.after(0, self.show_loading_modal)
                try:
                    self.load_images()
                except Exception as e:
                    print(f"[ERROR] Error loading images: {e}")
                finally:
                    self.loading = False
                    self.root.after(0, self.close_loading_modal)

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
            all_files.sort(key=lambda x: x[1], reverse=True)
            
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
            # images_needing_metadata = []
            # for image_path in self.image_files:
            #     existing_metadata = self.get_image_metadata(image_path)
            #     if not existing_metadata:
            #         images_needing_metadata.append(image_path)
    
            # # Extraire les métadonnées SEULEMENT pour les nouvelles images
            # if images_needing_metadata:
            #     print(f"[INFO] Extracting metadata for {len(images_needing_metadata)} new images")
            #     self.root.after(100, lambda: self.extract_and_store_metadata_batch(images_needing_metadata))
            # else:
            #     print(f"[INFO] All displayed images already have metadata")

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
                    nsfw_score = None
                    if metadata and 'nsfw_score' in metadata:
                        nsfw_score = metadata['nsfw_score']
                    
                    # Charger et redimensionner l'image
                    with Image.open(image_path) as img:
                        # Redimensionner en gardant les proportions
                        # Utiliser la taille de thumbnail configurable
                        thumb_size = getattr(self, 'thumbnail_size', (300, 300))
                        img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                        
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
                    if nsfw_score is not None:
                        pastille = tk.Canvas(image_frame, width=40, height=24, bg='white', highlightthickness=0)
                        pastille.place(relx=1.0, y=2, anchor="ne")
                        pastille.create_oval(0, 0, 40, 24, fill="white", outline="gray")
                        pastille.create_text(20, 12, text=f"{nsfw_score:.2f}", fill="black", font=("Arial", 10, "bold"))
                    # Label pour le nom du fichier avec indication si vue
                    filename = os.path.basename(image_path)
                    if is_viewed:
                        filename = f"✓ {filename}"  # Ajouter une coche
                    
                    # Ajouter les informations de métadonnées si disponibles
                    if metadata:
                        info_text = f"{filename}\n{metadata['width']}x{metadata['height']} - {metadata['format']}"
                        # if metadata['file_size']:
                        #     size_mb = metadata['file_size'] / (1024 * 1024)
                        #     info_text += f"\n{size_mb:.1f} MB"
                    
                        # # Ajouter un aperçu du prompt si disponible
                        # if metadata.get('positive_prompt'):
                        #     prompt_preview = metadata['positive_prompt'][:30] + "..." if len(metadata['positive_prompt']) > 30 else metadata['positive_prompt']
                        #     info_text += f"\n📝 {prompt_preview}"
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
                                    #command=lambda path=image_path: self.show_image_metadata(path))
                                    command=lambda path=image_path: self.show_edit_prompt(path))
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
    def show_edit_prompt(self, image_path):
        """Afficher le prompt d'édition pour une image"""
        try:
            metadata = self.get_image_metadata(image_path)
            if metadata:
                text =metadata.get("positive_prompt")
            app = cy2_analyse_prompt(text)
            app.mainloop()
        except Exception as e:
            print(f"[ERROR] Error showing edit prompt: {e}")

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

    # def hide_image_widget_immediately(self, image_path):
    #     """Masquer immédiatement le widget d'une image spécifique"""
    #     try:
    #         for widget in self.image_widgets[:]:  # Copie de la liste pour éviter les modifications pendant l'itération
    #             if hasattr(widget, 'image_path') and widget.image_path == image_path:
    #                 # Détruire le widget
    #                 widget.destroy()
    #                 # Retirer de la liste des widgets
    #                 self.image_widgets.remove(widget)
    #                 print(f"[INFO] Image widget removed: {os.path.basename(image_path)}")
                    
    #                 # Réorganiser les widgets restants
    #                 self.reorganize_image_grid()
    #                 break
                    
    #     except Exception as e:
    #         print(f"[ERROR] Error hiding image widget: {e}")

    # def reorganize_image_grid(self):
    #     """Réorganiser la grille d'images après suppression d'un élément"""
    #     try:
    #         cols = 4  # Nombre de colonnes
            
    #         # Repositionner tous les widgets restants
    #         for idx, widget in enumerate(self.image_widgets):
    #             if widget.winfo_exists():  # Vérifier que le widget existe encore
    #                 row = idx // cols
    #                 col = idx % cols
    #                 widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
    #         # Mettre à jour la région de défilement
    #         self.root.after(10, self.check_and_update_canvas)
            
    #     except Exception as e:
    #         print(f"[ERROR] Error reorganizing grid: {e}")

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

    # def calculate_file_hash(self, file_path):
    #     """Calculer le hash SHA256 d'un fichier"""
    #     try:
    #         hash_sha256 = hashlib.sha256()
    #         with open(file_path, "rb") as f:
    #             for chunk in iter(lambda: f.read(4096), b""):
    #                 hash_sha256.update(chunk)
    #         return hash_sha256.hexdigest()
    #     except Exception as e:
    #         print(f"[ERROR] Error calculating hash for {file_path}: {e}")
    #         return None

    def extract_image_metadata(self, image_path):
        """Extraire les métadonnées d'une image et calculer le hash en une seule ouverture"""
        try:
            # Informations du fichier
            file_stats = os.stat(image_path)
            file_size = file_stats.st_size
            creation_date = file_stats.st_ctime
            modified_date = file_stats.st_mtime

            # Calculer le hash SHA256 en une seule lecture
            hash_sha256 = hashlib.sha256()
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            file_hash = hash_sha256.hexdigest()

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
                            
                            # Champs explicites
                            if not positive_prompt and 'positive' in inputs:
                                positive_prompt = inputs['positive']
                            if not negative_prompt and 'negative' in inputs:
                                negative_prompt = inputs['negative']

                            # Champs text selon le type
                            if 'text' in inputs:
                                text_content = inputs['text']
                                if not positive_prompt and (
                                    'positive' in class_type or 
                                    ('clip' in class_type and 'negative' not in class_type)
                                ):
                                    positive_prompt = text_content
                                elif not negative_prompt and 'negative' in class_type:
                                    negative_prompt = text_content
                                elif not positive_prompt:
                                    positive_prompt = text_content
            
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
                       sampler_name, scheduler, seed, nsfw_score
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
                    'seed': result[19],
                    'nsfw_score': result[20]  # <-- AJOUT ICI
                }
            return None
            
        except Exception as e:
            print(f"[ERROR] Error getting metadata: {e}")
            return None

    # def extract_and_store_metadata_batch(self, image_paths):
    #     """Extraire et stocker les métadonnées pour un lot d'images"""
    #     try:
    #         for image_path in image_paths:
    #             # Vérifier si les métadonnées existent déjà
    #             existing_metadata = self.get_image_metadata(image_path)
    #             if existing_metadata:
    #                 continue  # Skip si déjà traité
                
    #             # Extraire et stocker les métadonnées
    #             metadata = self.extract_image_metadata(image_path)
    #             if metadata:
    #                 self.store_image_metadata(image_path, metadata)
                    
    #     except Exception as e:
    #         print(f"[ERROR] Error in batch metadata extraction: {e}")

    def show_loading_modal(self, message="Chargement des images..."):
        """Affiche une fenêtre modale avec une barre de progression indéterminée"""
        self.loading_modal = tk.Toplevel(self.root)
        self.loading_modal.title("Chargement")
        self.loading_modal.geometry("350x120")
        self.loading_modal.resizable(False, False)
        self.loading_modal.transient(self.root)
        self.loading_modal.grab_set()
        self.loading_modal.protocol("WM_DELETE_WINDOW", lambda: None)  # Désactive la fermeture

        frame = ttk.Frame(self.loading_modal, padding=20)
        frame.pack(fill="both", expand=True)

        label = ttk.Label(frame, text=message, font=("Arial", 12))
        label.pack(pady=(0, 10))

        self.loading_modal_bar = ttk.Progressbar(frame, mode='indeterminate', length=300)
        self.loading_modal_bar.pack(pady=(0, 10))
        self.loading_modal_bar.start(10)

    def close_loading_modal(self):
        """Ferme la fenêtre modale de chargement si elle existe"""
        if hasattr(self, 'loading_modal') and self.loading_modal.winfo_exists():
            self.loading_modal_bar.stop()
            self.loading_modal.destroy()
            del self.loading_modal

    def open_options_dialog(self):
        """Ouvre une fenêtre d'options pour configurer la taille des thumbnails"""
        options_win = tk.Toplevel(self.root)
        options_win.title("Options")
        options_win.geometry("300x180")
        options_win.resizable(False, False)
        options_win.transient(self.root)
        options_win.grab_set()

        frame = ttk.Frame(options_win, padding=20)
        frame.pack(fill="both", expand=True)

        # Taille du thumbnail
        ttk.Label(frame, text="Thumbnail width:").grid(row=0, column=0, sticky="w")
        width_var = tk.IntVar(value=getattr(self, "thumbnail_size", (300, 300))[0])
        width_entry = ttk.Entry(frame, textvariable=width_var, width=8)
        width_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Thumbnail height:").grid(row=1, column=0, sticky="w")
        height_var = tk.IntVar(value=getattr(self, "thumbnail_size", (300, 300))[1])
        height_entry = ttk.Entry(frame, textvariable=height_var, width=8)
        height_entry.grid(row=1, column=1, sticky="w")

        def save_options():
            w = max(32, width_var.get())
            h = max(32, height_var.get())
            self.thumbnail_size = (w, h)
            self.save_options()  # <-- Ajoute ceci
            options_win.destroy()
            self.refresh_images()

        save_btn = ttk.Button(frame, text="Save", command=save_options)
        save_btn.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        close_btn = ttk.Button(frame, text="Cancel", command=options_win.destroy)
        close_btn.grid(row=3, column=0, columnspan=2, pady=(5, 0))
    
   

    def get_options_path(self):
        """Chemin du fichier d'options (à côté de la base de données)"""
        db_dir = os.path.dirname(self.db_path)
        return os.path.join(db_dir, "options.json")

    def load_options(self):
        """Charger les options depuis le fichier options.json"""
        try:
            options_path = self.get_options_path()
            if os.path.exists(options_path):
                with open(options_path, "r", encoding="utf-8") as f:
                    options = json.load(f)
                # Appliquer les options connues
                if "thumbnail_size" in options:
                    self.thumbnail_size = tuple(options["thumbnail_size"])
            else:
                # Valeur par défaut si pas de fichier
                self.thumbnail_size = (300, 300)
        except Exception as e:
            print(f"[ERROR] Error loading options: {e}")
            self.thumbnail_size = (300, 300)

    def save_options(self):
        """Sauvegarder les options dans le fichier options.json"""
        try:
            options_path = self.get_options_path()
            options = {
                "thumbnail_size": list(getattr(self, "thumbnail_size", (300, 300))),
            }
            with open(options_path, "w", encoding="utf-8") as f:
                json.dump(options, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Error saving options: {e}")

    def Extract_all_metadata(self):
        """Charger les métadonnées pour tous les fichiers présents dans la table viewed_images avec une barre de progression"""
        try:
            conn, cursor = self.get_db_connection()
            cursor.execute(
                "SELECT image_path FROM viewed_images WHERE function_name = ?",
                (self.title,)
            )
            image_paths = [row[0] for row in cursor.fetchall()]
            conn.close()

            # Vérifier quelles images n'ont pas encore de métadonnées
            images_needing_metadata = []
            for image_path in image_paths:
                existing_metadata = self.get_image_metadata(image_path)
                if not existing_metadata:
                    images_needing_metadata.append(image_path)

            total = len(images_needing_metadata)
            if total == 0:
                messagebox.showinfo("Info", "Toutes les images ont déjà des métadonnées.")
                return

            # Créer une fenêtre de progression
            progress_win = tk.Toplevel(self.root)
            progress_win.title("Extraction des métadonnées")
            progress_win.geometry("400x120")
            progress_win.resizable(False, False)
            progress_label = ttk.Label(progress_win, text="Extraction des métadonnées...")
            progress_label.pack(pady=(20, 10))
            progress_bar = ttk.Progressbar(progress_win, length=350, mode="determinate", maximum=total)
            progress_bar.pack(pady=(0, 10))
            percent_label = ttk.Label(progress_win, text="0%")
            percent_label.pack()

            self.root.update_idletasks()

            for idx, image_path in enumerate(images_needing_metadata, 1):
                metadata = self.extract_image_metadata(image_path)
                if metadata:
                    self.store_image_metadata(image_path, metadata)
                progress_bar["value"] = idx
                percent_label.config(text=f"{int(idx/total*100)}%")
                progress_win.update_idletasks()

            progress_win.destroy()
            messagebox.showinfo("Terminé", f"Métadonnées extraites pour {total} images.")

        except Exception as e:
            print(f"[ERROR] Erreur lors du chargement des métadonnées : {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des métadonnées : {e}")


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

def on_close():
    app.save_options()
    root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)
