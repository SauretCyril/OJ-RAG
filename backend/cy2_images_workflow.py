import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import sqlite3
import threading

# Importer la classe parente
from cy2_image_process import image_process

class images_workflow(image_process):
    """
    Classe spécialisée pour le workflow d'images avec gestion des statuts
    Hérite de la classe image_process
    """
    
    def __init__(self, root, config):
        # Appeler le constructeur de la classe parent
        super().__init__(root, config)
        
        # Initialiser les attributs nécessaires
        self.current_filter = "all"  # Attribut manquant qui causait l'erreur
        self.pending_changes = []    # Pour suivre les changements en attente
        
        # Extraire les options de statut de la configuration
        status_options_str = config.get('status_options', "new,viewed,approved,rejected,favorite")
        self.status_options = [s.strip() for s in status_options_str.split(',')]
        print(f"[INFO] Using status options: {self.status_options}")
        
        # Initialiser la table de statuts dans la base de données
        self.init_status_table()
        
        # Créer les contrôles spécifiques au workflow
        self.setup_workflow_ui()
    
    def init_status_table(self):
        """Initialise la table de statuts d'images dans la base de données"""
        try:
            # Utiliser une connexion thread-safe
            thread_conn, thread_cursor = self.get_db_connection()
            
            thread_cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT UNIQUE,
                    previous_status TEXT DEFAULT "new",
                    current_status TEXT DEFAULT "new",
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            thread_conn.commit()
            thread_conn.close()
        except Exception as e:
            print(f"[ERROR][init_status_table] {type(e).__name__}: {e}")
            messagebox.showerror("Database Error", f"Could not initialize status table: {str(e)}")
    
    def setup_workflow_ui(self):
        """Ajoute les éléments d'interface spécifiques au workflow"""
        # Ajouter un cadre pour les filtres de statut en haut
        filter_frame = ttk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=5, after=self.dir_label.winfo_parent())
        
        ttk.Label(filter_frame, text="Filter by status:").pack(side="left", padx=(0, 10))
        
        # Créer des boutons radio pour filtrer par statut
        self.filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_var, 
                        value="all", command=self.apply_filter).pack(side="left", padx=5)
        
        for status in self.status_options:
            ttk.Radiobutton(filter_frame, text=status.capitalize(), 
                           variable=self.filter_var, value=status,
                           command=self.apply_filter).pack(side="left", padx=5)
        
        # Ajouter un bouton pour appliquer les changements
        self.save_btn = tk.Button(
            filter_frame, 
            text="Save Changes", 
            command=self.save_changes,
            bg="orange",
            fg="white",
            font=("Arial", 10, "bold"),
            state="disabled"
        )
        self.save_btn.pack(side="right", padx=(5, 0))
    
    def display_images(self):
        """Surcharge de la méthode display_images pour inclure les statuts"""
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
                    
                    # Récupérer le statut de l'image
                    status = self.get_image_status(image_path)
                        
                    # Créer un cadre pour chaque image
                    image_frame = ttk.Frame(self.scrollable_frame)
                    image_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    image_frame.image_path = image_path  # Référence pour masquage
                    
                    # Afficher les statuts en haut de l'image
                    status_text = f"Previous: {status['previous']} | Current: {status['current']}"
                    status_label = ttk.Label(image_frame, text=status_text, 
                                            background="#f0f0f0", font=("Arial", 9))
                    status_label.pack(fill="x", padx=5, pady=2)
                    
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
                    
                    # Boutons pour les différents statuts
                    status_btn_frame = ttk.Frame(btn_frame)
                    status_btn_frame.pack(pady=3)
                    
                    for status_option in self.status_options:
                        status_btn = ttk.Button(
                            status_btn_frame,
                            text=status_option.capitalize(),
                            command=lambda path=image_path, s=status_option: self.change_image_status(path, s)
                        )
                        status_btn.pack(side="left", padx=2)
                    
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
    
    def get_image_status(self, image_path, cursor=None):
        """Récupère le statut d'une image"""
        try:
            image_path = os.path.normpath(image_path)
            use_local_connection = cursor is None
            
            if use_local_connection:
                thread_conn, cursor = self.get_db_connection()
                
            cursor.execute(
                "SELECT previous_status, current_status FROM image_status WHERE image_path = ?",
                (image_path,)
            )
            result = cursor.fetchone()
            
            if use_local_connection:
                thread_conn.close()
                
            if result:
                return {"previous": result[0], "current": result[1]}
            else:
                return {"previous": "new", "current": "new"}
                
        except Exception as e:
            print(f"[ERROR][get_image_status] {type(e).__name__}: {e}")
            return {"previous": "error", "current": "error"}
    
    def change_image_status(self, image_path, new_status):
        """Change le statut d'une image et met à jour l'affichage"""
        try:
            if self.update_image_status(image_path, new_status):
                # Ajouter aux changements en attente
                self.pending_changes.append(('status_change', image_path, new_status))
                self.save_btn.config(state="normal", text=f"Save Changes ({len(self.pending_changes)})")
                
                # Mettre à jour l'affichage pour refléter le changement
                for widget in self.image_widgets:
                    if hasattr(widget, 'image_path') and widget.image_path == image_path:
                        # Chercher l'étiquette de statut dans les enfants du widget
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Label) and "Previous:" in child.cget("text"):
                                status = self.get_image_status(image_path)
                                status_text = f"Previous: {status['previous']} | Current: {status['current']}"
                                child.config(text=status_text)
                                break
        except Exception as e:
            print(f"[ERROR][change_image_status] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error changing image status: {str(e)}")
    
    def update_image_status(self, image_path, new_status):
        """Met à jour le statut d'une image"""
        try:
            image_path = os.path.normpath(image_path)
            
            # Récupérer le statut actuel
            current = self.get_image_status(image_path)
            
            # Mettre à jour : le statut actuel devient le statut précédent
            thread_conn, cursor = self.get_db_connection()
            
            cursor.execute(
                """INSERT INTO image_status (image_path, previous_status, current_status) 
                   VALUES (?, ?, ?) 
                   ON CONFLICT(image_path) 
                   DO UPDATE SET previous_status = current_status, 
                                current_status = ?, 
                                updated_date = CURRENT_TIMESTAMP""",
                (image_path, current["previous"], new_status, new_status)
            )
            
            thread_conn.commit()
            thread_conn.close()
            
            return True
        except Exception as e:
            print(f"[ERROR][update_image_status] {type(e).__name__}: {e}")
            return False
    
    def apply_filter(self):
        """Applique un filtre pour n'afficher que les images avec un statut spécifique"""
        try:
            filter_value = self.filter_var.get()
            self.current_filter = filter_value
            
            # Réinitialiser la pagination
            self.page = 0
            self.all_files = []
            
            # Recharger les images avec le filtre
            self.load_images_async()
        except Exception as e:
            print(f"[ERROR][apply_filter] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error applying filter: {str(e)}")
    
    
    
    def save_changes(self):
        """Sauvegarde tous les changements en attente"""
        if not self.pending_changes:
            return
        
        try:
            # Créer une connexion spécifique
            thread_conn, thread_cursor = self.get_db_connection()
            
            # Traiter chaque changement
            for change in self.pending_changes:
                change_type = change[0]
                image_path = change[1]
                
                if change_type == 'status_change':
                    new_status = change[2]
                    # Le statut est déjà mis à jour dans la BD, rien à faire ici
                    
                    # Si nécessaire, déplacer l'image selon son statut
                    if new_status == "approved" and os.path.exists(image_path):
                        # Déplacer vers le dossier cible
                        basename = os.path.basename(image_path)
                        target_path = os.path.join(self.cible_directory, basename)
                        
                        # Créer le dossier cible s'il n'existe pas
                        os.makedirs(self.cible_directory, exist_ok=True)
                        
                        # Déplacer le fichier
                        shutil.move(image_path, target_path)
                        print(f"[INFO] Moved image to target directory: {target_path}")
            
            # Réinitialiser les changements en attente
            self.pending_changes = []
            self.save_btn.config(state="disabled", text="Save Changes")
            
            # Fermer la connexion
            thread_conn.close()
            
            # Recharger les images pour refléter les changements
            self.load_images_async()
            
            messagebox.showinfo("Success", "All changes have been saved")
        except Exception as e:
            print(f"[ERROR][save_changes] {type(e).__name__}: {e}")
            messagebox.showerror("Error", f"Error saving changes: {str(e)}")
    
    def create_table(self):
        """Créer la table des fonctions si elle n'existe pas"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS functions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    default_directory TEXT NOT NULL,
                    cible_directory TEXT NOT NULL,
                    db_path TEXT NOT NULL,
                    processor_type TEXT DEFAULT "standard",
                    status_options TEXT DEFAULT "new,viewed,approved,rejected,favorite"
                )
            ''')
            
            # Vérifier si les colonnes existent déjà
            try:
                self.cursor.execute("PRAGMA table_info(functions)")
                columns = [column[1] for column in self.cursor.fetchall()]
                
                if "processor_type" not in columns:
                    self.cursor.execute('ALTER TABLE functions ADD COLUMN processor_type TEXT DEFAULT "standard"')
                    print("Added processor_type column to functions table")
                    
                if "status_options" not in columns:
                    self.cursor.execute('ALTER TABLE functions ADD COLUMN status_options TEXT DEFAULT "new,viewed,approved,rejected,favorite"')
                    print("Added status_options column to functions table")
            except sqlite3.Error as e:
                print(f"Error checking columns: {str(e)}")
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error-02 creating table: {str(e)}")
            messagebox.showerror("Database Error", f"Could not create table: {str(e)}")
            raise
    
    def _filter_image(self, image_path, cursor):
        """Surcharge pour ajouter le filtrage par statut"""
        # Appeler d'abord le filtre parent
        include_image = super()._filter_image(image_path, cursor)
        
        # Ajouter notre filtre par statut
        if include_image and self.current_filter != "all":
            status = self.get_image_status(image_path, cursor)
            if status["current"] != self.current_filter:
                include_image = False
        
        return include_image