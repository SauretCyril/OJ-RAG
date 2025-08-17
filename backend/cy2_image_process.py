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

            # Extraire les métadonnées pour les nouvelles images
            self.root.after(100, lambda: self.extract_and_store_metadata_batch(self.image_files))

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
            result = messagebox.askyesno("Confirm Move", f"Move {filename} to {self.cible_directory}?")
            if result:
                shutil.move(image_path, target_path)
                messagebox.showinfo("Success", f"Image moved: {filename}")
                self.hide_image_widget(image_path)
                
        except Exception as e:
            print(f"[ERROR] Error moving image: {e}")
            messagebox.showerror("Error", f"Failed to move image: {e}")

    def hide_image_widget(self, image_path):
        """Masquer une image de l'interface (méthode simplifiée)"""
        # Cette méthode n'est plus vraiment utilisée car on recharge l'affichage complet
        # Mais on la garde pour compatibilité
        print(f"[INFO] Triggering refresh to hide image: {os.path.basename(image_path)}")
        return True

    def open_image(self, image_path):
        """Ouvrir une image dans l'application par défaut"""
        try:
            os.startfile(image_path)  # Windows
        except:
            try:
                os.system(f'xdg-open "{image_path}"')  # Linux
            except:
                messagebox.showerror("Error", "Cannot open image")

    def add_new_image(self, image_path):
        """Ajouter une nouvelle image détectée par le watcher"""
        try:
            # Recharger les images pour inclure la nouvelle
            self.root.after(0, self.refresh_images)
        except Exception as e:
            print(f"[ERROR] Error adding new image: {e}")

    def refresh_images(self):
        """Actualiser l'affichage des images"""
        self.page = 0  # Remettre à la première page lors du refresh
        self.load_images_async()

    def toggle_view_mode(self):
        """Basculer entre montrer toutes les images et masquer les vues"""
        if self.view_mode == "new":
            self.view_mode = "all"
        else:
            self.view_mode = "new"
        
        self.update_view_mode_button()
        self.refresh_images()
        print(f"[INFO] View mode changed to: {self.view_mode}")

    def update_view_mode_button(self):
        """Mettre à jour le texte du bouton selon le mode actuel"""
        if self.view_mode == "new":
            self.view_mode_btn.config(text="Show All")
        else:
            self.view_mode_btn.config(text="Hide Viewed")

    def mark_all_as_viewed(self):
        """Marquer toutes les images de la page actuelle comme vues"""
        try:
            if not self.image_files:
                messagebox.showinfo("Info", "No images to mark on current page")
                return
            
            # Demander confirmation
            result = messagebox.askyesno(
                "Confirm Mark All", 
                f"Mark all {len(self.image_files)} images on this page as viewed?"
            )
            
            if result:
                marked_count = 0
                for image_path in self.image_files:
                    # Marquer sans masquer individuellement pour éviter les conflits
                    image_path_norm = os.path.normpath(image_path)
                    conn, cursor = self.get_db_connection()
                    
                    cursor.execute(
                        "INSERT OR IGNORE INTO viewed_images (function_name, image_path) VALUES (?, ?)",
                        (self.title, image_path_norm)
                    )
                    conn.commit()
                    conn.close()
                    marked_count += 1
                
                print(f"[INFO] {marked_count} images marked as viewed for '{self.title}'")
                messagebox.showinfo("Success", f"{marked_count} images marked as viewed")
                
                # TOUJOURS recharger l'affichage après marquage en lot
                self.refresh_images()
                    
        except Exception as e:
            print(f"[ERROR] Error marking all images as viewed: {e}")
            messagebox.showerror("Error", f"Failed to mark all images as viewed: {e}")

    def prev_page(self):
        """Page précédente"""
        if self.page > 0:
            self.page -= 1
            self.load_images_async()

    def next_page(self):
        """Page suivante"""
        max_pages = (len(self.all_files) - 1) // self.page_size
        if self.page < max_pages:
            self.page += 1
            self.load_images_async()

    def update_navigation_buttons(self):
        """Mettre à jour l'état des boutons de navigation"""
        try:
            max_pages = max(0, (len(self.all_files) - 1) // self.page_size)
            
            # Bouton précédent
            if self.page > 0:
                self.prev_btn.config(state="normal")
            else:
                self.prev_btn.config(state="disabled")
            
            # Bouton suivant
            if self.page < max_pages:
                self.next_btn.config(state="normal")
            else:
                self.next_btn.config(state="disabled")
            
            # Label de page
            self.page_label.config(text=f"Page {self.page + 1} of {max_pages + 1}")
            
        except Exception as e:
            print(f"[ERROR] Error updating navigation: {e}")

    def check_and_update_canvas(self):
        """Mettre à jour la région de défilement du canvas"""
        try:
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            print(f"[ERROR] Error updating canvas: {e}")

    def show_function_stats(self):
        """Afficher les statistiques pour cette fonction"""
        try:
            viewed_count = self.get_function_stats()
            
            # Compter le total d'images dans le répertoire
            if os.path.exists(self.current_directory):
                image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
                total_images = len([f for f in os.listdir(self.current_directory) 
                                  if f.lower().endswith(image_extensions)])
            else:
                total_images = 0
            
            new_images = total_images - viewed_count
            progress_pct = (viewed_count/total_images*100) if total_images > 0 else 0
            
            stats_text = f"""Function: {self.title}
            Directory: {self.current_directory}

            Total images: {total_images}
            Viewed images: {viewed_count}
            New images: {new_images}

            Progress: {progress_pct:.1f}% completed"""
            
            messagebox.showinfo("Function Statistics", stats_text)
            
        except Exception as e:
            print(f"[ERROR] Error showing function stats: {e}")
            messagebox.showerror("Error", f"Failed to get statistics: {e}")

    def get_function_stats(self):
        """Obtenir les statistiques pour cette fonction"""
        try:
            conn, cursor = self.get_db_connection()
            
            # Compter les images vues pour cette fonction
            cursor.execute(
                "SELECT COUNT(*) FROM viewed_images WHERE function_name = ?",
                (self.title,)
            )
            viewed_count = cursor.fetchone()[0]
            
            conn.close()
            return viewed_count
        except Exception as e:
            print(f"[ERROR] Error getting function stats: {e}")
            return 0

    def clear_function_viewed_images(self):
        """Effacer toutes les images vues pour cette fonction"""
        try:
            result = messagebox.askyesno(
                "Confirm Clear", 
                f"Clear all viewed images for function '{self.title}'?\nThis cannot be undone."
            )
            
            if result:
                conn, cursor = self.get_db_connection()
                
                cursor.execute(
                    "DELETE FROM viewed_images WHERE function_name = ?",
                    (self.title,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", f"Cleared {deleted_count} viewed images for '{self.title}'")
                self.refresh_images()
                
        except Exception as e:
            print(f"[ERROR] Error clearing function viewed images: {e}")
            messagebox.showerror("Error", f"Failed to clear viewed images: {e}")

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

    def calculate_file_hash(self, image_path):
        """Calculer le hash SHA256 d'un fichier"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"[ERROR] Error calculating hash for {image_path}: {e}")
            return None

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
        """Extraire et stocker les métadonnées pour plusieurs images"""
        try:
            processed = 0
            total = len(image_paths)
            
            for image_path in image_paths:
                # Vérifier si les métadonnées existent déjà
                existing_metadata = self.get_image_metadata(image_path)
                if existing_metadata:
                    continue  # Skip si déjà traité
                
                # Extraire les métadonnées
                metadata = self.extract_image_metadata(image_path)
                if metadata:
                    if self.store_image_metadata(image_path, metadata):
                        processed += 1
                
                # Progress feedback
                if processed % 10 == 0:
                    print(f"[INFO] Processed metadata for {processed}/{total} images")
            
            print(f"[INFO] Metadata extraction complete: {processed} new entries")
            return processed
            
        except Exception as e:
            print(f"[ERROR] Error in batch metadata extraction: {e}")
            return 0

    def show_image_metadata(self, image_path):
        """Afficher les métadonnées complètes d'une image"""
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
                
                # Formatage des dates
                import datetime
                creation_date = datetime.datetime.fromtimestamp(metadata['creation_date']).strftime('%Y-%m-%d %H:%M:%S')
                modified_date = datetime.datetime.fromtimestamp(metadata['modified_date']).strftime('%Y-%m-%d %H:%M:%S')
                
                # Formatage de la taille
                size_mb = metadata['file_size'] / (1024 * 1024)
                
                info_text = f"""Image: {filename}

Dimensions: {metadata['width']} x {metadata['height']} pixels
Format: {metadata['format']} | Mode: {metadata['mode']}
File Size: {size_mb:.2f} MB

Created: {creation_date}
Modified: {modified_date}

Function: {self.title}"""

                # Ajouter les informations ComfyUI si disponibles
                if metadata.get('positive_prompt'):
                    info_text += f"\n\n=== COMFYUI GENERATION ===\n"
                    info_text += f"Positive Prompt:\n{metadata['positive_prompt']}\n"
                
                    if metadata.get('negative_prompt'):
                        info_text += f"\nNegative Prompt:\n{metadata['negative_prompt']}\n"
                    
                    if metadata.get('model_checkpoint'):
                        info_text += f"\nModel: {metadata['model_checkpoint']}"
                    if metadata.get('generation_steps'):
                        info_text += f"\nSteps: {metadata['generation_steps']}"
                    if metadata.get('cfg_scale'):
                        info_text += f" | CFG: {metadata['cfg_scale']}"
                    if metadata.get('sampler_name'):
                        info_text += f"\nSampler: {metadata['sampler_name']}"
                    if metadata.get('scheduler'):
                        info_text += f" | Scheduler: {metadata['scheduler']}"
                    if metadata.get('seed'):
                        info_text += f"\nSeed: {metadata['seed']}"

                # Ajouter les données EXIF si disponibles
                if metadata.get('exif_data'):
                    try:
                        exif_data = metadata['exif_data']
                        if isinstance(exif_data, str):
                            exif_data = json.loads(exif_data)
                        
                        exif_text = "\n\n=== EXIF DATA ===\n"
                        for key, value in list(exif_data.items())[:5]:  # Limiter à 5 entrées
                            exif_text += f"{key}: {value}\n"
                        info_text += exif_text
                    except:
                        pass
                
                messagebox.showinfo("Image Metadata", info_text)
            else:
                messagebox.showwarning("Warning", "No metadata available for this image")
            
        except Exception as e:
            print(f"[ERROR] Error showing metadata: {e}")
            messagebox.showerror("Error", f"Failed to get metadata: {e}")

    def extract_all_metadata(self):
        """Extraire les métadonnées pour toutes les images du répertoire"""
        try:
            result = messagebox.askyesno(
                "Extract Metadata", 
                f"Extract metadata for all images in '{self.title}'?\nThis may take some time."
            )
            
            if result:
                def extract_thread():
                    # Obtenir toutes les images du répertoire
                    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
                    all_images = []
                    for file in os.listdir(self.current_directory):
                        if file.lower().endswith(image_extensions):
                            full_path = os.path.join(self.current_directory, file)
                            all_images.append(full_path)
                    
                    processed = self.extract_and_store_metadata_batch(all_images)
                    self.root.after(0, lambda: messagebox.showinfo("Complete", f"Metadata extracted for {processed} images"))
                
                threading.Thread(target=extract_thread, daemon=True).start()
                
        except Exception as e:
            print(f"[ERROR] Error extracting all metadata: {e}")
            messagebox.showerror("Error", f"Failed to extract metadata: {e}")

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
                if self.cancel_extraction:
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
                'cancelled': self.cancel_extraction
            }
            
            return {'summary': summary, 'details': results}
            
        except Exception as e:
            print(f"[ERROR] Error in batch extraction: {e}")
            return {'summary': {'total': 0, 'processed': 0, 'errors': 1}, 'details': []}

    def update_progress(self, progress, status):
        """Mettre à jour la barre de progression"""
        try:
            self.progress_var.set(progress)
            self.progress_label.config(text=f"Progress: {progress:.1f}%")
            self.status_label.config(text=status)
        except:
            pass

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
                
                # Alternative : chercher dans les métadonnées info
                if hasattr(img, 'info') and img.info:
                    for key, value in img.info.items():
                        if any(keyword in key.lower() for keyword in ['comfy', 'workflow', 'prompt']):
                            try:
                                data = json.loads(value) if isinstance(value, str) else value
                                positive_prompt, negative_prompt = self.parse_comfyui_prompts({'info': data})
                                if positive_prompt or negative_prompt:
                                    return {
                                        'positive_prompt': positive_prompt,
                                        'negative_prompt': negative_prompt,
                                        'workflow_data': value if isinstance(value, str) else json.dumps(value),
                                        'model_info': self.extract_model_info({'info': data})
                                    }
                            except:
                                continue
            
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
                                elif not positive_prompt:  # Premier prompt trouvé
                                    positive_prompt = text_content
                        
                            # Autres patterns - MAINTENANT CORRECTEMENT INDENTÉS
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

    def show_extraction_results(self, results, progress_window):
        """Afficher les résultats de l'extraction dans un formulaire"""
        try:
            progress_window.destroy()
            
            summary = results['summary']
            details = results['details']
            
            # Créer la fenêtre de résultats
            results_window = tk.Toplevel(self.root)
            results_window.title("ComfyUI Metadata Extraction Results")
            results_window.geometry("1000x700")
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
            
            summary_text = f"""Total images: {summary['total']}
Successfully processed: {summary['processed']}
Already processed (skipped): {summary['skipped']}
Errors: {summary['errors']}
Images with ComfyUI prompts: {summary['comfyui_found']}
Success rate: {(summary['processed']/(summary['total']-summary['skipped'])*100):.1f}% (of new images)"""

            if summary.get('cancelled'):
                summary_text += "\n⚠️ Extraction was cancelled"
            
            summary_label = ttk.Label(summary_frame, text=summary_text, justify="left")
            summary_label.pack()
            
            # Liste détaillée
            list_frame = ttk.LabelFrame(main_frame, text="Detailed Results", padding=10)
            list_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            # Treeview avec scrollbar
            tree_frame = ttk.Frame(list_frame)
            tree_frame.pack(fill="both", expand=True)
            
            columns = ("File", "Status", "Dimensions", "Format", "ComfyUI", "Prompt Preview", "Model")
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
            
            # Configuration des colonnes
            tree.heading("File", text="File Name")
            tree.heading("Status", text="Status")
            tree.heading("Dimensions", text="Dimensions")
            tree.heading("Format", text="Format")
            tree.heading("ComfyUI", text="ComfyUI Data")
            tree.heading("Prompt Preview", text="Prompt Preview")
            tree.heading("Model", text="Model")
            
            tree.column("File", width=200)
            tree.column("Status", width=80)
            tree.column("Dimensions", width=100)
            tree.column("Format", width=60)
            tree.column("ComfyUI", width=80)
            tree.column("Prompt Preview", width=300)
            tree.column("Model", width=150)
            
            # Scrollbars
            v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Placement
            tree.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.grid(row=0, column=1, sticky="ns")
            h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Remplir les données
            for result in details:
                file_name = result['file']
                status = result['status']
                
                if status == 'Processed':
                    dimensions = f"{result.get('width', '?')}x{result.get('height', '?')}"
                    format_type = result.get('format', '?')
                    comfyui_status = "✓ Yes" if result.get('has_comfyui') else "✗ No"
                    prompt_preview = result.get('positive_prompt', 'No prompt')
                    model = result.get('model', 'Unknown')
                    
                    tags = ('success',) if result.get('has_comfyui') else ('no_comfyui',)
                elif status == 'Skipped':
                    dimensions = "-"
                    format_type = "-"
                    comfyui_status = "✓ Yes" if result.get('has_comfyui') else "?"
                    prompt_preview = result.get('reason', 'Already processed')
                    model = "-"
                    tags = ('skipped',)
                else:  # Error
                    dimensions = "-"
                    format_type = "-"
                    comfyui_status = "✗ Error"
                    prompt_preview = result.get('reason', 'Unknown error')
                    model = "-"
                    tags = ('error',)
            
                tree.insert("", "end", values=(file_name, status, dimensions, format_type, 
                                             comfyui_status, prompt_preview, model), tags=tags)
            
            # Configuration des couleurs
            tree.tag_configure('success', background='#d4edda')
            tree.tag_configure('no_comfyui', background='#fff3cd')
            tree.tag_configure('skipped', background='#e2e3e5')
            tree.tag_configure('error', background='#f8d7da')
            
            # Boutons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            close_btn = ttk.Button(button_frame, text="Close", command=results_window.destroy)
            close_btn.pack(side="right", padx=(5, 0))
            
            export_btn = ttk.Button(button_frame, text="Export CSV", 
                                 command=lambda: self.export_extraction_results(details))
            export_btn.pack(side="right", padx=(5, 0))
            
        except Exception as e:
            print(f"[ERROR] Error showing results: {e}")
            messagebox.showerror("Error", f"Failed to show results: {e}")

    def export_extraction_results(self, details):
        """Exporter les résultats vers un fichier CSV"""
        try:
            from tkinter import filedialog
            import csv
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save extraction results"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['file', 'status', 'width', 'height', 'format', 'has_comfyui', 'positive_prompt', 'model']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for result in details:
                        writer.writerow(result)
                
                messagebox.showinfo("Export Complete", f"Results exported to {file_path}")
        
        except Exception as e:
            print(f"[ERROR] Error exporting results: {e}")
            messagebox.showerror("Error", f"Failed to export results: {e}")
