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
from cy2_metadata import *
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
            all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Filtrer selon le mode de vue
            if self.view_mode == "new":
                # Filtrer pour ne montrer que les images non vues pour cette fonction
                filtered_files = []
                print(f"[DEBUG] Filtering {len(all_files)} images for function '{self.title}'")
                
                for image_path in all_files:
                    if not self.is_image_viewed(image_path):
                        filtered_files.append(image_path)
                    #else:
                        #print(f"[DEBUG] Excluding viewed image: {os.path.basename(image_path)}")
                
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
                    # metadata = get_image_metadata(image_path)
                    # nsfw_score = None
                    # if metadata and 'nsfw_score' in metadata:
                    #     nsfw_score = metadata['nsfw_score']
                    
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
                    # if nsfw_score is not None:
                    #     pastille = tk.Canvas(image_frame, width=40, height=24, bg='white', highlightthickness=0)
                    #     pastille.place(relx=1.0, y=2, anchor="ne")
                    #     pastille.create_oval(0, 0, 40, 24, fill="white", outline="gray")
                    #     pastille.create_text(20, 12, text=f"{nsfw_score:.2f}", fill="black", font=("Arial", 10, "bold"))
                    # Label pour le nom du fichier avec indication si vue
                    filename = os.path.basename(image_path)
                    if is_viewed:
                        filename = f"✓ {filename}"  # Ajouter une coche
                    
                    # Ajouter les informations de métadonnées si disponibles
                    #if metadata:
                        #info_text = f"{filename}\n{metadata['width']}x{metadata['height']} - {metadata['format']}"
                        # if metadata['file_size']:
                        #     size_mb = metadata['file_size'] / (1024 * 1024)
                        #     info_text += f"\n{size_mb:.1f} MB"
                    
                        # # Ajouter un aperçu du prompt si disponible
                        # if metadata.get('positive_prompt'):
                        #     prompt_preview = metadata['positive_prompt'][:30] + "..." if len(metadata['positive_prompt']) > 30 else metadata['positive_prompt']
                        #     info_text += f"\n📝 {prompt_preview}"
                    #else:
                        #info_text = filename
                    
                    #name_label = ttk.Label(image_frame, text=info_text, wraplength=180)
                    #name_label.pack()
                    
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
            metadata = extract_comfyui_metadata(image_path)
            
            text = ""
            if metadata:
                text = metadata.get("positive_prompt", "")
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
                remove_image_metadata(image_path)
                
                # Recharge la page pour tout réafficher proprement
                self.refresh_images()
                
                #messagebox.showinfo("Success", f"Image moved: {filename}")
                
        except Exception as e:
            print(f"[ERROR] Error moving image: {e}")
            messagebox.showerror("Error", f"Failed to move image: {e}")

   

    
    # def check_and_update_canvas(self):
    #     """Mettre à jour la région de défilement du canvas"""
    #     try:
    #         self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    #     except Exception as e:
    #         print(f"[ERROR] Error updating canvas: {e}")

    def open_image(self, image_path):
        """Ouvrir une image avec l'application par défaut du système"""
        try:
            import os
            import platform
            import subprocess

            print(f"[DEBUG] open_image: {image_path}")  # Ajoute ceci pour debug

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
