import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import os
import re
import webbrowser
import subprocess
import platform
from datetime import datetime
from cy3_annonces_backend import AnnouncementManager
import requests 
from cy_cookies import *
class AnnouncementGUI:
    """Interface graphique pour gérer les annonces avec AnnouncementManager"""
    
    def __init__(self, root, db_path=None):
        self.root = root 
        self.root.title("Gestionnaire d'Annonces")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Initialiser le gestionnaire d'annonces

        if not self.get_current_db():
            messagebox.showerror("Erreur", "Impossible de charger la base de données.")
            exit()
        # Le répertoire courant est celui du db_path de AnnouncementManager
        
        
        

        # Variables pour le formulaire
        self.current_announcement_id = None
        self.search_var = tk.StringVar()
        self.search_field_var = tk.StringVar(value="all")
        self.status_filter_var = tk.StringVar(value="all")
        
        # Variables pour la gestion des numéros de dossier
        self.dossier_prefix_var = tk.StringVar(value="X")
        self.dossier_counter_var = tk.StringVar(value="001")
        self.auto_increment_var = tk.BooleanVar(value=True)
        
        # Créer l'interface
        self.create_widgets()
        self.refresh_table()
        
        # Configurer la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_current_db(self):
        try:
            response = requests.get("http://localhost:5000/get_directory_root")
            response.raise_for_status()
            data = response.json()
            db_path = data.get("db_path") 
            db_path=get_cookie_value("current_dossier")
            # Récupérer le db_path de la réponse
            
            print(f"dbg121: DB Path récupéré: {db_path}")
            # Si pas de db_path dans la réponse, construire à partir du root_directory
            if not db_path:
                return False

            self.db_path = os.path.join(db_path, "_index_.db")
            if not os.path.exists(self.db_path):
                return False
            
            self.current_directory = db_path
            self.manager = AnnouncementManager(self.db_path)
            return True
            
        except Exception as e:
            print(f"Erreur lors de la récupération du DB path: {str(e)}")
            # Fallback en cas d'erreur
           
            messagebox.showerror("Erreur", f"Impossible de récupérer le chemin de la base de données: {str(e)}\nUtilisation du chemin par défaut.")
            return False  # Continuer avec le fallback

    def create_widgets(self):
        """Créer tous les widgets de l'interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Zone d'information du répertoire en haut
        self.create_directory_info_frame(main_frame)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Gestionnaire d'Annonces", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Frame pour les contrôles (recherche, filtres, boutons, gestion numéro)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # --- Ligne de boutons toggle côte à côte ---
        toggle_btns_frame = ttk.Frame(control_frame)
        toggle_btns_frame.pack(fill=tk.X, pady=(0, 5))
        self.dossier_frame_visible = True
        self.toggle_dossier_btn = ttk.Button(toggle_btns_frame, text="Cacher N°", command=self.toggle_dossier_frame)
        self.toggle_dossier_btn.pack(side=tk.LEFT, padx=(0, 2))
        self.search_frame_visible = True
        self.toggle_search_btn = ttk.Button(toggle_btns_frame, text="Cacher 🔍", command=self.toggle_search_frame)
        self.toggle_search_btn.pack(side=tk.LEFT, padx=(2, 0))
        # --- Fin ligne de boutons ---
        
        # Frame pour la gestion des numéros de dossier
        self.create_dossier_management_frame(control_frame)
        # Frame pour la recherche
        self.create_search_frame(control_frame)
        self.create_button_frame(control_frame)
        
        # PanedWindow pour diviser en deux parties
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Frame gauche : tableau des annonces
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)
        
        # Frame droite : formulaire de détails
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)
        
        self.create_table_frame(left_frame)
        self.create_form_frame(right_frame)
        
        # Frame pour les statistiques
        self.create_stats_frame(main_frame)
    
    def create_directory_info_frame(self, parent):
        """Créer la zone d'information du répertoire courant"""
        info_frame = ttk.LabelFrame(parent, text="Informations du Projet")
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Frame principal pour organiser les informations
        info_container = ttk.Frame(info_frame)
        info_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Ligne 1: Répertoire courant (basé sur AnnouncementManager.db_path)
        dir_row = ttk.Frame(info_container)
        dir_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(dir_row, text="Répertoire courant:", 
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        # Label pour le répertoire avec possibilité de le copier
        self.directory_var = tk.StringVar(value=self.current_directory)
        dir_label = ttk.Label(dir_row, textvariable=self.directory_var, 
                             font=("Arial", 9), foreground="blue")
        dir_label.pack(side=tk.LEFT, padx=(5, 10))
        
        # Boutons d'action pour le répertoire
        ttk.Button(dir_row, text="Copier", width=8,
                  command=self.copy_directory_path).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(dir_row, text="Ouvrir", width=8,
                  command=self.open_current_directory).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(dir_row, text="Actualiser", width=10,
                  command=self.refresh_directory_info).pack(side=tk.LEFT, padx=2)
        
        # Ligne 2: Informations sur la base de données
        db_row = ttk.Frame(info_container)
        db_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(db_row, text="Base de données:", 
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        # Nom du fichier de base de données
        db_name = os.path.basename(self.db_path)
        self.db_info_var = tk.StringVar(value=f"{db_name} ({self.get_db_size()})")
        db_info_label = ttk.Label(db_row, textvariable=self.db_info_var, 
                                 font=("Arial", 9), foreground="green")
        db_info_label.pack(side=tk.LEFT, padx=(5, 10))
        
        # Chemin complet de la DB
        ttk.Label(db_row, text="Chemin:", 
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 5))
        
        self.db_path_var = tk.StringVar(value=self.manager.db_path)
        db_path_label = ttk.Label(db_row, textvariable=self.db_path_var, 
                             font=("Arial", 8), foreground="gray")
        db_path_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Statut de connexion
        self.connection_status_var = tk.StringVar(value="✓ Connecté")
        status_label = ttk.Label(db_row, textvariable=self.connection_status_var, 
                                font=("Arial", 9), foreground="green")
        status_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def copy_directory_path(self):
        """Copier le chemin du répertoire dans le presse-papiers"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_directory)
            self.root.update()
            messagebox.showinfo("Info", f"Chemin copié dans le presse-papiers:\n{self.current_directory}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la copie: {str(e)}")
    
    def open_current_directory(self):
        """Ouvrir le répertoire courant dans l'explorateur"""
        try:
            self.open_file_in_explorer(self.current_directory)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du répertoire: {str(e)}")
    
    def refresh_directory_info(self):
        """Actualiser les informations du répertoire"""
        try:
            # Mettre à jour le répertoire courant basé sur AnnouncementManager.db_path
            self.current_directory = os.path.dirname(self.manager.db_path)
            self.directory_var.set(self.current_directory)
            
            # Mettre à jour le chemin de la base de données
            self.db_path_var.set(self.manager.db_path)
            
            # Mettre à jour les informations de la base de données
            db_name = os.path.basename(self.manager.db_path)
            self.db_info_var.set(f"{db_name} ({self.get_db_size()})")
            
            # Vérifier la connexion à la base de données
            try:
                stats = self.manager.get_statistics()
                self.connection_status_var.set("✓ Connecté")
            except:
                self.connection_status_var.set("✗ Déconnecté")
            
            messagebox.showinfo("Info", 
                           f"Informations actualisées avec succès\n"
                           f"Répertoire courant: {self.current_directory}\n"
                           f"Base de données: {self.manager.db_path}")
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'actualisation: {str(e)}")
    
    def get_db_size(self):
        """Obtenir la taille du fichier de base de données"""
        try:
            # Utiliser le chemin de la base de données du manager
            if os.path.exists(self.manager.db_path):
                size_bytes = os.path.getsize(self.manager.db_path)
                
                # Convertir en unités lisibles
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            else:
                return "Fichier non trouvé"
        except Exception:
            return "Taille inconnue"
    
    def create_dossier_management_frame(self, parent):
        """Créer la zone de gestion des numéros de dossier"""
        self.dossier_management_frame = ttk.LabelFrame(parent, text="Gestion des Numéros de Dossier")
        self.dossier_management_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Frame principal pour l'organisation
        main_row = ttk.Frame(self.dossier_management_frame)
        main_row.pack(fill=tk.X, padx=10, pady=5)
        
        # Colonne 1: Configuration du préfixe et compteur
        config_frame = ttk.Frame(main_row)
        config_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Ligne 1: Préfixe et compteur initial
        prefix_row = ttk.Frame(config_frame)
        prefix_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(prefix_row, text="Préfixe:").pack(side=tk.LEFT)
        prefix_entry = ttk.Entry(prefix_row, textvariable=self.dossier_prefix_var, width=5)
        prefix_entry.pack(side=tk.LEFT, padx=(5, 10))
        prefix_entry.bind('<KeyRelease>', self.on_prefix_change)
        
        ttk.Label(prefix_row, text="Numéro:").pack(side=tk.LEFT)
        counter_entry = ttk.Entry(prefix_row, textvariable=self.dossier_counter_var, width=8)
        counter_entry.pack(side=tk.LEFT, padx=(5, 10))
        counter_entry.bind('<KeyRelease>', self.on_counter_change)
        
        # Aperçu du numéro généré
        self.preview_var = tk.StringVar()
        self.update_preview()
        
        ttk.Label(prefix_row, text="Aperçu:").pack(side=tk.LEFT, padx=(10, 5))
        preview_label = ttk.Label(prefix_row, textvariable=self.preview_var, 
                                 font=("Arial", 10, "bold"), foreground="blue")
        preview_label.pack(side=tk.LEFT)
        
        # Ligne 2: Options et actions
        options_row = ttk.Frame(config_frame)
        options_row.pack(fill=tk.X, pady=2)
        
        auto_check = ttk.Checkbutton(options_row, text="Auto-incrément", 
                                    variable=self.auto_increment_var)
        auto_check.pack(side=tk.LEFT)
        
        ttk.Button(options_row, text="Détecter Prochain", 
                  command=self.detect_next_number).pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(options_row, text="Réinitialiser", 
                  command=self.reset_counter).pack(side=tk.LEFT, padx=5)
        
        # Colonne 2: Boutons d'action rapide
        action_frame = ttk.Frame(main_row)
        action_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        ttk.Button(action_frame, text="Nouvelle avec\nN° Auto", 
                  command=self.new_announcement_auto).pack(pady=2)
        
        ttk.Button(action_frame, text="Incrémenter\nManuellement", 
                  command=self.increment_counter).pack(pady=2)
    
    def update_preview(self):
        """Mettre à jour l'aperçu du numéro de dossier"""
        prefix = self.dossier_prefix_var.get()
        counter = self.dossier_counter_var.get()
        preview = f"{prefix}{counter}"
        self.preview_var.set(preview)
    
    def on_prefix_change(self, event=None):
        """Gérer le changement de préfixe"""
        self.update_preview()
    
    def on_counter_change(self, event=None):
        """Gérer le changement de compteur"""
        self.update_preview()
    
    def detect_next_number(self):
        """Détecter automatiquement le prochain numéro disponible"""
        try:
            prefix = self.dossier_prefix_var.get()
            announcements = self.manager.get_all_announcements()
            
            # Extraire tous les numéros existants avec ce préfixe
            pattern = rf"^{re.escape(prefix)}(\d+)$"
            numbers = []
            
            for announcement in announcements:
                num_dossier = announcement[1]  # num_dossier est en position 1
                match = re.match(pattern, num_dossier)
                if match:
                    numbers.append(int(match.group(1)))
            
            # Trouver le prochain numéro disponible
            if numbers:
                next_num = max(numbers) + 1
            else:
                next_num = 1
            
            # Formater avec des zéros
            counter_str = str(next_num).zfill(3)
            self.dossier_counter_var.set(counter_str)
            self.update_preview()
            
            messagebox.showinfo("Info", f"Prochain numéro détecté: {prefix}{counter_str}")
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la détection: {str(e)}")
    
    def increment_counter(self):
        """Incrémenter manuellement le compteur"""
        try:
            current = int(self.dossier_counter_var.get())
            new_counter = current + 1
            counter_str = str(new_counter).zfill(3)
            self.dossier_counter_var.set(counter_str)
            self.update_preview()
        except ValueError:
            messagebox.showerror("Erreur", "Le numéro doit être un nombre valide")
    
    def reset_counter(self):
        """Réinitialiser le compteur à 001"""
        self.dossier_counter_var.set("001")
        self.update_preview()
    
    def get_next_dossier_number(self):
        """Obtenir le prochain numéro de dossier et l'incrémenter si auto-incrément est activé"""
        prefix = self.dossier_prefix_var.get()
        counter = self.dossier_counter_var.get()
        current_number = f"{prefix}{counter}"
        
        # Si auto-incrément est activé, incrémenter pour la prochaine fois
        if self.auto_increment_var.get():
            try:
                next_counter = int(counter) + 1
                self.dossier_counter_var.set(str(next_counter).zfill(3))
                self.update_preview()
            except ValueError:
                pass  # Ignore si le compteur n'est pas un nombre valide
        
        return current_number
    
    def new_announcement_auto(self):
        """Créer une nouvelle annonce avec numéro automatique"""
        auto_number = self.get_next_dossier_number()
        self.new_announcement()
        self.num_dossier_var.set(auto_number)
    
    def create_search_frame(self, parent):
        """Créer la zone de recherche et filtres"""
        self.search_frame = ttk.LabelFrame(parent, text="Recherche et Filtres")
        self.search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ligne 1: Recherche
        search_row = ttk.Frame(self.search_frame)
        search_row.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_row, text="Rechercher:").pack(side=tk.LEFT)
        
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search_change)
        
        ttk.Label(search_row, text="Dans:").pack(side=tk.LEFT)
        
        search_field_combo = ttk.Combobox(search_row, textvariable=self.search_field_var,
                                         values=["all", "num_dossier", "url", "contenu"],
                                         state="readonly", width=15)
        search_field_combo.pack(side=tk.LEFT, padx=(5, 10))
        search_field_combo.bind('<<ComboboxSelected>>', self.on_search_change)
        
        # Ligne 2: Filtres
        filter_row = ttk.Frame(self.search_frame)
        filter_row.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_row, text="Statut:").pack(side=tk.LEFT)
        
        status_combo = ttk.Combobox(filter_row, textvariable=self.status_filter_var,
                                   values=["all", "actif", "inactif", "archive"],
                                   state="readonly", width=15)
        status_combo.pack(side=tk.LEFT, padx=(5, 10))
        status_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        ttk.Button(filter_row, text="Effacer filtres", 
                  command=self.clear_filters).pack(side=tk.LEFT, padx=(20, 0))
    
    def create_button_frame(self, parent):
        """Créer la zone des boutons d'action"""
        button_frame = ttk.LabelFrame(parent, text="Actions")
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_row = ttk.Frame(button_frame)
        btn_row.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_row, text="Nouvelle Annonce", 
                  command=self.new_announcement).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_row, text="Modifier", 
                  command=self.edit_announcement).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_row, text="Supprimer", 
                  command=self.delete_announcement).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_row, text="Dupliquer", 
                  command=self.duplicate_announcement).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_row, text="Actualiser", 
                  command=self.refresh_table).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_row, text="Exporter", 
                  command=self.export_data).pack(side=tk.LEFT, padx=5)
    
    def create_table_frame(self, parent):
        """Créer le tableau des annonces"""
        table_frame = ttk.LabelFrame(parent, text="Liste des Annonces")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tree_container = ttk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ajout de la colonne "Nature"
        columns = ("ID", "Dossier", "Nature", "URL", "Contenu", "Création", "Modification", "Statut")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=15)
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Dossier", text="N° Dossier")
        self.tree.heading("Nature", text="Nature")
        self.tree.heading("URL", text="URL (Clic pour ouvrir)")
        self.tree.heading("Contenu", text="Contenu")
        self.tree.heading("Création", text="Créé le")
        self.tree.heading("Modification", text="Modifié le")
        self.tree.heading("Statut", text="Statut")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Dossier", width=100, anchor="center")
        self.tree.column("Nature", width=100, anchor="center")
        self.tree.column("URL", width=0, minwidth=0, stretch=False)
        self.tree.column("Contenu", width=0, minwidth=0, stretch=False)
        self.tree.column("Création", width=0, minwidth=0, stretch=False)
        self.tree.column("Modification", width=0, minwidth=0, stretch=False)
        self.tree.column("Statut", width=80, anchor="center", stretch=False)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement des widgets
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Événements
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-1>", self.on_tree_click)
    
    def create_context_menu(self):
        """Créer le menu contextuel pour les URLs"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Ouvrir l'URL", command=self.open_url_from_context)
        self.context_menu.add_command(label="Copier l'URL", command=self.copy_url_to_clipboard)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Modifier l'annonce", command=self.edit_announcement)
        self.context_menu.add_command(label="Supprimer l'annonce", command=self.delete_announcement)
        
        # Bind du clic droit
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def on_tree_click(self, event):
        """Gérer le clic simple sur le tableau"""
        # Identifier la région cliquée
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            # Identifier la colonne cliquée (corrigé)
            column = self.tree.identify_column(event.x)
            
            # Si c'est la colonne URL (colonne #3)
            if column == "#3":
                item = self.tree.identify_row(event.y)
                if item:
                    # Récupérer l'URL de l'annonce
                    announcement_id = self.tree.item(item)['values'][0]
                    self.open_url_by_id(announcement_id)
    
    def show_context_menu(self, event):
        """Afficher le menu contextuel"""
        # Sélectionner l'item sous le curseur
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def open_url_from_context(self):
        """Ouvrir l'URL depuis le menu contextuel"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            announcement_id = item['values'][0]
            self.open_url_by_id(announcement_id)
    
    def copy_url_to_clipboard(self):
        """Copier l'URL dans le presse-papiers"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            announcement_id = item['values'][0]
            try:
                announcement = self.manager.get_announcement_by_id(announcement_id)
                if announcement:
                    url = announcement.get("url", "")
                    self.root.clipboard_clear()
                    self.root.clipboard_append(url)
                    self.root.update()
                    messagebox.showinfo("Info", f"URL copiée dans le presse-papiers:\n{url}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la copie: {str(e)}")

    def open_url_by_id(self, announcement_id):
        """Ouvrir l'URL d'une annonce par son ID"""
        try:
            announcement = self.manager.get_announcement_by_id(announcement_id)
            if announcement:
                url = announcement.get("url", "")
                self.open_url(url)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture de l'URL: {str(e)}")
    
    def open_url(self, url):
        """Ouvrir une URL dans le navigateur par défaut ou l'explorateur de fichiers"""
        if not url:
            messagebox.showwarning("Attention", "Aucune URL à ouvrir")
            return
        
        try:
            # Vérifier si c'est une URL web
            if url.startswith(('http://', 'https://')):
                webbrowser.open(url)
                print(f"Ouverture de l'URL web: {url}")
            
            # Vérifier si c'est un chemin de fichier local
            elif os.path.exists(url):
                self.open_file_in_explorer(url)
                print(f"Ouverture du fichier local: {url}")
            
            # Essayer de l'ouvrir comme une URL web même sans préfixe
            else:
                # Ajouter http:// si pas de protocole
                if not url.startswith(('http://', 'https://', 'ftp://', 'file://')):
                    url_with_protocol = f"http://{url}"
                    webbrowser.open(url_with_protocol)
                    print(f"Ouverture de l'URL (avec protocole ajouté): {url_with_protocol}")
                else:
                    webbrowser.open(url)
                    print(f"Ouverture de l'URL: {url}")
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'URL:\n{url}\n\nErreur: {str(e)}")
            print(f"Erreur lors de l'ouverture de l'URL {url}: {str(e)}")
    
    def open_file_in_explorer(self, file_path):
        """Ouvrir un fichier dans l'explorateur de fichiers du système"""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: utiliser explorer avec le paramètre /select pour sélectionner le fichier
                if os.path.isfile(file_path):
                    subprocess.run(['explorer', '/select,', file_path])
                else:
                    subprocess.run(['explorer', file_path])
            
            elif system == "Darwin":  # macOS
                subprocess.run(['open', '-R', file_path])
            
            elif system == "Linux":
                # Linux: essayer différents gestionnaires de fichiers
                file_managers = ['nautilus', 'dolphin', 'thunar', 'pcmanfm']
                for fm in file_managers:
                    try:
                        subprocess.run([fm, file_path], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    # Si aucun gestionnaire de fichiers n'est trouvé, essayer xdg-open
                    subprocess.run(['xdg-open', file_path])
            
            else:
                # Système non reconnu, essayer avec webbrowser
                webbrowser.open(f"file://{file_path}")
        
        except Exception as e:
            raise Exception(f"Impossible d'ouvrir le fichier dans l'explorateur: {str(e)}")
    
    def create_form_frame(self, parent):
        """Créer le formulaire de détails"""
        form_frame = ttk.LabelFrame(parent, text="Détails de l'Annonce")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Variables pour les champs
        self.num_dossier_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.contenu_var = tk.StringVar()
        self.statut_var = tk.StringVar(value="actif")
        self.nature_var = tk.StringVar()
        
        # Frame pour les champs
        fields_frame = ttk.Frame(form_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Champ N° Dossier avec bouton d'aide
        dossier_row = ttk.Frame(fields_frame)
        dossier_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Label(dossier_row, text="N° Dossier:").pack(side=tk.LEFT)
        dossier_entry = ttk.Entry(dossier_row, textvariable=self.num_dossier_var, width=20)
        dossier_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(dossier_row, text="Auto", width=6,
                  command=self.auto_fill_dossier).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(dossier_row, text="Suivant", width=8,
                  command=self.fill_next_dossier).pack(side=tk.LEFT, padx=2)
        
        # Champ URL avec bouton d'ouverture
        url_row = ttk.Frame(fields_frame)
        url_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Label(url_row, text="URL:").pack(side=tk.LEFT)
        url_entry = ttk.Entry(url_row, textvariable=self.url_var, width=25)
        url_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        
        ttk.Button(url_row, text="Ouvrir", width=8,
                  command=self.open_current_url).pack(side=tk.LEFT, padx=2)
        
        # Champ Nature
        nature_row = ttk.Frame(fields_frame)
        nature_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Label(nature_row, text="Nature:").pack(side=tk.LEFT)
        nature_entry = ttk.Entry(nature_row, textvariable=self.nature_var, width=25)
        nature_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        
        # Champ Contenu (ScrolledText)
        ttk.Label(fields_frame, text="Contenu:").grid(row=3, column=0, sticky="nw", pady=5)
        self.contenu_text = ScrolledText(fields_frame, width=30, height=10, wrap=tk.WORD)
        self.contenu_text.grid(row=3, column=1, sticky="nsew", padx=(10, 0), pady=5)
        
        # Champ Statut
        ttk.Label(fields_frame, text="Statut:").grid(row=4, column=0, sticky="w", pady=5)
        statut_combo = ttk.Combobox(fields_frame, textvariable=self.statut_var,
                                   values=["actif", "inactif", "archive"],
                                   state="readonly", width=27)
        statut_combo.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        # Configuration de la grille
        fields_frame.grid_columnconfigure(1, weight=1)
        fields_frame.grid_rowconfigure(2, weight=1)
        
        # Boutons du formulaire
        form_buttons = ttk.Frame(form_frame)
        form_buttons.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(form_buttons, text="Sauvegarder", 
                  command=self.save_announcement).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(form_buttons, text="Annuler", 
                  command=self.cancel_edit).pack(side=tk.LEFT, padx=5)

        ttk.Button(form_buttons, text="Nouveau", 
                  command=self.new_announcement).pack(side=tk.LEFT, padx=5)

        # --- Nouveau bouton pour créer le dossier via l'API ---
        ttk.Button(form_buttons, text="Créer Dossier Serveur", 
                  command=self.create_dossier_on_server).pack(side=tk.LEFT, padx=5)
    
    def open_current_url(self):
        """Ouvrir l'URL saisie dans le formulaire"""
        url = self.url_var.get().strip()
        if url:
            self.open_url(url)
        else:
            messagebox.showwarning("Attention", "Veuillez saisir une URL")
    
    def auto_fill_dossier(self):
        """Remplir automatiquement le numéro de dossier actuel"""
        auto_number = f"{self.dossier_prefix_var.get()}{self.dossier_counter_var.get()}"
        self.num_dossier_var.set(auto_number)
    
    def fill_next_dossier(self):
        """Remplir avec le prochain numéro et incrémenter"""
        next_number = self.get_next_dossier_number()
        self.num_dossier_var.set(next_number)
    
    def refresh_table(self):
        """Actualiser le tableau des annonces"""
        # Effacer le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
    
        # Récupérer les annonces selon les filtres
        try:
            search_term = self.search_var.get().strip()
            search_field = self.search_field_var.get()
            status_filter = self.status_filter_var.get()
            
            if search_term:
                announcements = self.manager.search_announcements(search_term, search_field)
                if status_filter != "all":
                    announcements = [a for a in announcements if a.get("statut", "") == status_filter]
            else:
                status = None if status_filter == "all" else status_filter
                announcements = self.manager.get_all_announcements(status)
            
            # Remplir le tableau
            for announcement in announcements:
                date_creation = self.format_date(announcement.get("date_creation", ""))
                date_modification = self.format_date(announcement.get("date_modification", ""))
                contenu = announcement.get("contenu", "")
                contenu_display = contenu[:50] + "..." if len(contenu) > 50 else contenu
                values = (
                    announcement.get("id", ""),
                    announcement.get("num_dossier", ""),
                    announcement.get("nature", ""),
                    announcement.get("url", ""),
                    contenu_display,
                    date_creation,
                    date_modification,
                    announcement.get("statut", "")
                )
                self.tree.insert("", tk.END, values=values)
    
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du rafraîchissement: {str(e)}")
    
        self.update_statistics()
    
    def format_date(self, date_str):
        """Formater une date pour l'affichage"""
        try:
            if date_str:
                # Supposer le format SQLite standard
                date_obj = datetime.fromisoformat(date_str)
                return date_obj.strftime("%d/%m/%Y %H:%M")
            return ""
        except:
            return date_str or ""
    
    def on_tree_select(self, event):
        """Gérer la sélection d'une ligne dans le tableau"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            announcement_id = item['values'][0]
            self.load_announcement_details(announcement_id)
    
    def on_tree_double_click(self, event):
        """Gérer le double-clic sur une ligne"""
        self.edit_announcement()
    
    def load_announcement_details(self, announcement_id):
        """Charger les détails d'une annonce dans le formulaire"""
        try:
            announcement = self.manager.get_announcement_by_id(announcement_id)
            if announcement:
                self.current_announcement_id = announcement_id
                self.num_dossier_var.set(announcement.get("num_dossier", ""))
                self.url_var.set(announcement.get("url", ""))
                self.nature_var.set(announcement.get("nature", ""))
                self.contenu_text.delete(1.0, tk.END)
                self.contenu_text.insert(1.0, announcement.get("contenu", ""))
                self.statut_var.set(announcement.get("statut", ""))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")
    
    def new_announcement(self):
        """Préparer le formulaire pour une nouvelle annonce"""
        self.current_announcement_id = None
        self.clear_form()
    
    def clear_form(self):
        """Vider le formulaire"""
        self.num_dossier_var.set("")
        self.url_var.set("")
        self.nature_var.set("")
        self.contenu_text.delete(1.0, tk.END)
        self.statut_var.set("actif")
    
    def save_announcement(self):
        """Sauvegarder l'annonce (nouvelle ou modification)"""
        # Récupérer les valeurs
        num_dossier = self.num_dossier_var.get().strip()
        url = self.url_var.get().strip()
        contenu = self.contenu_text.get(1.0, tk.END).strip()
        statut = self.statut_var.get()
        nature = self.nature_var.get().strip()
        
        # Validation
        if not all([num_dossier, url, contenu]):
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires.")
            return
        try:
            if self.current_announcement_id:
                # Modification
                success = self.manager.update_announcement(
                    self.current_announcement_id, num_dossier, url, contenu, nature, statut
                )
                message = "Annonce modifiée avec succès"
            else:
                # Nouvelle annonce
                success = self.manager.add_announcement(num_dossier, url, contenu, nature, statut)
                message = "Nouvelle annonce ajoutée avec succès"
            
            if success:
                messagebox.showinfo("Succès", message)
                self.refresh_table()
                self.clear_form()
                self.current_announcement_id = None
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
    
    def edit_announcement(self):
        """Modifier l'annonce sélectionnée"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sélectionner une annonce à modifier.")
            return
    
    def delete_announcement(self):
        """Supprimer l'annonce sélectionnée"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sélectionner une annonce à supprimer.")
            return
        
        item = self.tree.item(selection[0])
        announcement_id = item['values'][0]
        num_dossier = item['values'][1]
        
        # Confirmation
        result = messagebox.askyesno(
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer l'annonce du dossier '{num_dossier}' ?"
        )
        
        if result:
            try:
                success = self.manager.delete_announcement(announcement_id)
                if success:
                    messagebox.showinfo("Succès", "Annonce supprimée avec succès.")
                    self.refresh_table()
                    self.clear_form()
                    self.current_announcement_id = None
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")
    
    def duplicate_announcement(self):
        """Dupliquer l'annonce sélectionnée"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sélectionner une annonce à dupliquer.")
            return
        
        item = self.tree.item(selection[0])
        announcement_id = item['values'][0]
        
        try:
            original = self.manager.get_announcement_by_id(announcement_id)
            if original:
                new_num_dossier = self.get_next_dossier_number()
                success = self.manager.add_announcement(
                    new_num_dossier,
                    original.get("url", ""),
                    original.get("contenu", ""),
                    original.get("nature", ""),
                    original.get("statut", "")
                )
                if success:
                    messagebox.showinfo("Succès", f"Annonce dupliquée avec le numéro {new_num_dossier}.")
                    self.refresh_table()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la duplication: {str(e)}")
    
    def cancel_edit(self):
        """Annuler la modification en cours"""
        self.clear_form()
        self.current_announcement_id = None
    
    def on_search_change(self, event=None):
        """Déclencher la recherche quand le texte change"""
        self.refresh_table()
    
    def on_filter_change(self, event=None):
        """Déclencher le filtrage quand le statut change"""
        self.refresh_table()
    
    def clear_filters(self):
        """Effacer tous les filtres"""
        self.search_var.set("")
        self.search_field_var.set("all")
        self.status_filter_var.set("all")
        self.refresh_table()
    
    def create_stats_frame(self, parent):
        """Créer la zone des statistiques"""
        stats_frame = ttk.LabelFrame(parent, text="Statistiques")
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="", font=("Arial", 10))
        self.stats_label.pack(padx=10, pady=5)
        
        self.update_statistics()
    
    def update_statistics(self):
        """Mettre à jour les statistiques"""
        try:
            stats = self.manager.get_statistics()
            stats_text = f"Total: {stats.get('total', 0)} annonces | "
            stats_text += f"Dossiers uniques: {stats.get('unique_folders', 0)} | "
            
            by_status = stats.get('by_status', {})
            status_parts = []
            for status in ['actif', 'inactif', 'archive']:
                count = by_status.get(status, 0)
                if count > 0:
                    status_parts.append(f"{status.capitalize()}: {count}")
            
            if status_parts:
                stats_text += " | ".join(status_parts)
            
            self.stats_label.config(text=stats_text)
            
            # Mettre à jour aussi les informations de la base de données
            db_name = os.path.basename(self.manager.db_path)
            self.db_info_var.set(f"{db_name} ({self.get_db_size()})")
            self.connection_status_var.set("✓ Connecté")
        
        except Exception as e:
            self.stats_label.config(text="Erreur lors du calcul des statistiques")
            self.connection_status_var.set("✗ Erreur de connexion")
    
    def export_data(self):
        """Exporter les données vers un fichier CSV"""
        try:
            import csv
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Exporter les annonces"
            )
            if filename:
                announcements = self.manager.get_all_announcements()
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    # En-têtes
                    writer.writerow(['ID', 'Numéro Dossier', 'Nature', 'URL', 'Contenu', 
                                     'Date Création', 'Date Modification', 'Statut'])
                    # Données
                    for a in announcements:
                        writer.writerow([
                            a.get("id", ""),
                            a.get("num_dossier", ""),
                            a.get("nature", ""),
                            a.get("url", ""),
                            a.get("contenu", ""),
                            a.get("date_creation", ""),
                            a.get("date_modification", ""),
                            a.get("statut", "")
                        ])
                messagebox.showinfo("Succès", f"Données exportées vers {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def on_closing(self):
        """Fermer proprement l'application"""
        try:
            self.manager.close()
        except:
            pass
        self.root.destroy()
    
    def toggle_search_frame(self):
        """Afficher ou cacher la zone de recherche"""
        if self.search_frame_visible:
            self.search_frame.pack_forget()
            self.toggle_search_btn.config(text="Afficher 🔍")
            self.search_frame_visible = False
        else:
            self.search_frame.pack(fill=tk.X, pady=(0, 10))
            self.toggle_search_btn.config(text="Cacher 🔍")
            self.search_frame_visible = True
    
    def toggle_dossier_frame(self):
        """Afficher ou cacher la zone de gestion du numéro auto"""
        if self.dossier_frame_visible:
            self.dossier_management_frame.pack_forget()
            self.toggle_dossier_btn.config(text="Afficher N°")
            self.dossier_frame_visible = False
        else:
            self.dossier_management_frame.pack(fill=tk.X, pady=(0, 10))
            self.toggle_dossier_btn.config(text="Cacher N°")
            self.dossier_frame_visible = True

    def create_dossier_on_server(self):
        """Créer le dossier sur le serveur via l'API Flask"""
        num_dossier = self.num_dossier_var.get().strip()
        url = self.url_var.get().strip()
        contenu = self.contenu_text.get(1.0, tk.END).strip()
        sufix = "_annonce_"

        if not num_dossier or not url or not contenu:
            messagebox.showerror("Erreur", "Veuillez remplir le numéro de dossier, l'URL et le contenu.")
            return

        params = {
            "contentNum": num_dossier,
            "content": contenu,
            "url": url,
            "sufix": sufix
        }

        try:
            response = requests.get("http://localhost:5000/save_announcement", params=params)
            response.raise_for_status()
            data = response.json() if response.headers.get("Content-Type", "").startswith("application/json") else {}
            if response.status_code == 200:
                messagebox.showinfo("Succès", f"Dossier créé sur le serveur.\nRéponse : {data if data else response.text}")
            else:
                messagebox.showerror("Erreur", f"Erreur serveur : {data if data else response.text}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du dossier sur le serveur : {str(e)}")


def main():
    """Fonction principale pour lancer l'application"""
    root = tk.Tk()
    app = AnnouncementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()