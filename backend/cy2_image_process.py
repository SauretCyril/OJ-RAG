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
        """Initialise la base de données SQLite pour stocker les images vues"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Créer la table si elle n'existe pas
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS viewed_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT UNIQUE,
                    viewed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            print(f"[INFO] Database initialized: {self.db_path}")
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")
            
    def get_db_connection(self):
        """Créer une nouvelle connexion à la base de données pour le thread actuel"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return conn, conn.cursor()

    def is_image_viewed(self, image_path):
        """Vérifier si une image a été vue"""
        try:
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            cursor.execute(
                "SELECT COUNT(*) FROM viewed_images WHERE image_path = ?",
                (image_path,)
            )
            result = cursor.fetchone()[0] > 0
            conn.close()
            return result
        except Exception as e:
            print(f"[ERROR] Error checking if image viewed: {e}")
            return False

    def mark_image_viewed(self, image_path):
        """Marquer une image comme vue dans la base de données"""
        try:
            image_path = os.path.normpath(image_path)
            conn, cursor = self.get_db_connection()
            
            cursor.execute(
                "INSERT OR IGNORE INTO viewed_images (image_path) VALUES (?)",
                (image_path,)
            )
            conn.commit()
            conn.close()
            print(f"[INFO] Image marked as viewed: {os.path.basename(image_path)}")
            
            # Si en mode "new", masquer l'image immédiatement
            if self.view_mode == "new":
                self.hide_image_widget(image_path)
            
            return True
        except Exception as e:
            print(f"[ERROR] Error marking image as viewed: {e}")
            return False

    def setup_ui(self):
        """Initialise l'interface graphique principale"""
        # Frame du haut pour les contrôles
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Bouton pour sélectionner le dossier
        select_btn = ttk.Button(top_frame, text="Select Directory", command=self.select_directory)
        select_btn.pack(side="left")

        # Label du dossier courant
        self.dir_label = ttk.Label(top_frame, text=f"Directory: {self.current_directory}")
        self.dir_label.pack(side="left", padx=(10, 0))

        # Bouton de rechargement
        refresh_btn = ttk.Button(top_frame, text="Refresh", command=self.refresh_images)
        refresh_btn.pack(side="left", padx=(10, 0))

        # Bouton pour basculer le mode de vue
        self.view_mode_btn = ttk.Button(top_frame, text="Show All", command=self.toggle_view_mode)
        self.view_mode_btn.pack(side="left", padx=(10, 0))
        self.update_view_mode_button()

        # Bouton pour marquer toutes les images de la page comme vues
        mark_all_btn = ttk.Button(top_frame, text="Mark All as Viewed", command=self.mark_all_as_viewed)
        mark_all_btn.pack(side="left", padx=(10, 0))

        # Frame pour la barre de progression
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x")

        # Frame pour la navigation par pages
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(fill="x", padx=10, pady=5)

        self.prev_btn = ttk.Button(nav_frame, text="Previous", command=self.prev_page, state="disabled")
        self.prev_btn.pack(side="left")

        self.next_btn = ttk.Button(nav_frame, text="Next", command=self.next_page, state="disabled")
        self.next_btn.pack(side="left", padx=(10, 0))

        self.page_label = ttk.Label(nav_frame, text="Page 1")
        self.page_label.pack(side="left", padx=(10, 0))

        # Frame principal avec scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Canvas avec scrollbar
        self.canvas = tk.Canvas(main_frame, bg="white")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Gérer le défilement avec la molette"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

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
                self.root.after(0, lambda: self.progress_bar.start())
                
                try:
                    self.load_images()
                except Exception as e:
                    print(f"[ERROR] Error loading images: {e}")
                finally:
                    self.loading = False
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
            self.all_files = all_files
            
            # Filtrer selon le mode de vue
            if self.view_mode == "new":
                # Filtrer pour ne montrer que les images non vues
                filtered_files = []
                for image_path in all_files:
                    if not self.is_image_viewed(image_path):
                        filtered_files.append(image_path)
                filtered_files_to_use = filtered_files
            else:
                # Montrer toutes les images
                filtered_files_to_use = all_files
            
            # Calculer la pagination sur les images filtrées
            start_idx = self.page * self.page_size
            end_idx = start_idx + self.page_size
            self.image_files = filtered_files_to_use[start_idx:end_idx]
            
            if self.view_mode == "new":
                print(f"[INFO] Found {len(all_files)} images total, {len(filtered_files_to_use)} new (not viewed), showing {len(self.image_files)} on page {self.page + 1}")
            else:
                print(f"[INFO] Found {len(all_files)} images, showing {len(self.image_files)} on page {self.page + 1}")
            
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
                    name_label = ttk.Label(image_frame, text=filename, wraplength=180)
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
                #messagebox.showinfo("Success", f"Image marked as viewed: {os.path.basename(image_path)}")
                # Optionnellement, masquer l'image de la vue
                self.hide_image_widget(image_path)
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
        """Masquer une image de l'interface"""
        for widget in self.image_widgets:
            if hasattr(widget, 'image_path') and widget.image_path == image_path:
                widget.grid_remove()
                print(f"[INFO] Image hidden: {os.path.basename(image_path)}")
                return True
        return False

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
                    if self.mark_image_viewed(image_path):
                        marked_count += 1
                
                messagebox.showinfo("Success", f"{marked_count} images marked as viewed")
                
                # Si en mode "new", recharger pour masquer les images vues
                if self.view_mode == "new":
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

    def __del__(self):
        """Nettoyage des ressources"""
        try:
            if hasattr(self, 'watcher_thread') and self.watcher_thread:
                self.watcher_thread.stop()
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception as e:
            print(f"[ERROR] Error in cleanup: {e}")
