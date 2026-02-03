import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import json
from cy8_database_manager import cy8_database_manager
from cy8_popup_manager import cy8_popup_manager
from cy8_editable_tables import cy8_editable_tables
from cy8_user_preferences import cy8_user_preferences
from cy8_paths import normalize_path, ensure_dir, get_default_db_path, cy8_paths_manager
from cy6_wkf001_Basic import comfyui_basic_task

class cy8_prompts_manager:
    """Gestionnaire principal des prompts - Version cy8 refactorisée"""
    
    def __init__(self, root=None, db_path=None, mode="dev"):
        self.root = root or tk.Tk()
        
        # Gestionnaire des préférences utilisateur
        self.user_prefs = cy8_user_preferences()
        
        # Déterminer le chemin de la base de données
        if db_path is None:
            # Utiliser la dernière base utilisée ou le chemin par défaut
            last_db = self.user_prefs.get_last_database_path()
            if last_db and os.path.exists(last_db):
                self.db_path = normalize_path(last_db)
                print(f"Utilisation de la dernière base: {self.db_path}")
            else:
                self.db_path = get_default_db_path()
                print(f"Utilisation de la base par défaut: {self.db_path}")
        else:
            self.db_path = normalize_path(db_path)
        
        # Gestionnaires
        self.db_manager = cy8_database_manager(self.db_path)
        self.popup_manager = cy8_popup_manager(self.root, self.db_manager)
        self.table_manager = cy8_editable_tables(self.root, self.popup_manager)
        
        # Connecter le callback de sauvegarde
        self.table_manager.set_save_callback(self.save_current_info)
        
        # Variables d'état
        self.selected_prompt_id = None
        self.execution_stack = []
        self.current_values_tree = None
        self.current_workflow_tree = None
        
        # Configuration de l'interface
        self.setup_main_window()
        self.setup_ui()
        
        # Raccourcis clavier
        self.root.bind('<Control-s>', lambda e: self.save_current_info())
        
        # Initialisation
        self.db_manager.init_database(mode)
        self.load_prompts()
        self.update_database_stats()
    
    def setup_main_window(self):
        """Configuration de la fenêtre principale"""
        self.root.title("Gestionnaire de Prompts ComfyUI - Version cy8")
        
        # Restaurer la géométrie de la fenêtre ou utiliser par défaut
        saved_geometry = self.user_prefs.get_window_geometry()
        if saved_geometry:
            try:
                self.root.geometry(saved_geometry)
                print(f"Géométrie restaurée: {saved_geometry}")
            except:
                self.root.geometry("1400x900")
        else:
            self.root.geometry("1400x900")
            
        self.root.minsize(1200, 800)
        
        # Style professionnel
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuration des couleurs et styles
        style.configure('Title.TLabel', font=('TkDefaultFont', 12, 'bold'))
        style.configure('Header.TFrame', relief='raised', borderwidth=1)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Menu principal
        self.create_menu()
        
        # Layout principal avec panneau horizontal
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Panneau gauche - Tableau des prompts (0)
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Panneau droit - Détails (1)
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # Configuration des panneaux
        self.setup_prompts_table(left_frame)  # 0) Tableau des prompts
        self.setup_details_panel(right_frame)  # 1) Panel détaillé
        
        # Barre de statut
        self.setup_status_bar()
    
    def create_menu(self):
        """Créer la barre de menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau prompt", command=self.new_prompt)
        file_menu.add_separator()
        
        # Sous-menu Base de données
        db_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Base de données", menu=db_menu)
        db_menu.add_command(label="Changer de base...", command=self.change_database)
        db_menu.add_command(label="Créer nouvelle base...", command=self.create_new_database)
        db_menu.add_separator()
        
        # Bases récentes
        self.recent_db_menu = tk.Menu(db_menu, tearoff=0)
        db_menu.add_cascade(label="Bases récentes", menu=self.recent_db_menu)
        self.update_recent_databases_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Importer JSON", command=self.import_json)
        file_menu.add_command(label="Exporter JSON", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Édition
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Hériter prompt", command=self.inherit_prompt)
        edit_menu.add_command(label="Supprimer", command=self.delete_prompt)
        
        # Menu Exécution
        exec_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Exécution", menu=exec_menu)
        exec_menu.add_command(label="Exécuter prompt", command=self.execute_workflow)
        exec_menu.add_command(label="Analyser prompt", command=self.open_prompt_analysis)
    
    def setup_prompts_table(self, parent):
        """
        0) Configuration du tableau des prompts
        Colonnes: ID, Name, Status, Model, Comment, Parent
        """
        table_frame = ttk.LabelFrame(parent, text="Liste des Prompts", padding="5")
        table_frame.pack(fill="both", expand=True)
        
        # Treeview pour les prompts
        columns = ("id", "name", "status", "model", "comment", "parent")
        self.prompts_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configuration des colonnes
        self.prompts_tree.heading("id", text="ID")
        self.prompts_tree.heading("name", text="Nom")
        self.prompts_tree.heading("status", text="Statut")
        self.prompts_tree.heading("model", text="Modèle")
        self.prompts_tree.heading("comment", text="Commentaire")
        self.prompts_tree.heading("parent", text="Parent")
        
        self.prompts_tree.column("id", width=50)
        self.prompts_tree.column("name", width=200)
        self.prompts_tree.column("status", width=80)
        self.prompts_tree.column("model", width=150)
        self.prompts_tree.column("comment", width=200)
        self.prompts_tree.column("parent", width=60)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.prompts_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.prompts_tree.xview)
        self.prompts_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement
        self.prompts_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Boutons d'action (0.2 à 0.7)
        btn_frame = ttk.Frame(table_frame, style='Header.TFrame')
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        # 0.5) Bouton New
        ttk.Button(btn_frame, text="Nouveau", 
                  command=self.new_prompt, 
                  style='Accent.TButton').pack(side="left", padx=2)
        
        # 0.2) Bouton Éditer
        ttk.Button(btn_frame, text="Éditer", 
                  command=self.edit_prompt).pack(side="left", padx=2)
        
        # 0.4) Bouton Hériter
        ttk.Button(btn_frame, text="Hériter", 
                  command=self.inherit_prompt).pack(side="left", padx=2)
        
        # 0.3) Bouton Supprimer
        ttk.Button(btn_frame, text="Supprimer", 
                  command=self.delete_prompt).pack(side="left", padx=2)
        
        # Séparateur
        ttk.Separator(btn_frame, orient="vertical").pack(side="left", fill="y", padx=5)
        
        # 0.6) Bouton Exécuter
        ttk.Button(btn_frame, text="Exécuter", 
                  command=self.execute_workflow,
                  style='Accent.TButton').pack(side="left", padx=2)
        
        # 0.7) Bouton Analyser
        ttk.Button(btn_frame, text="Analyser", 
                  command=self.open_prompt_analysis).pack(side="left", padx=2)
        
        ttk.Button(btn_frame, text="Actualiser", 
                  command=self.load_prompts).pack(side="right", padx=2)
        
        # Événements
        self.prompts_tree.bind("<<TreeviewSelect>>", self.on_prompt_select)
        self.prompts_tree.bind("<Double-1>", self.on_prompt_double_click)
    
    def setup_details_panel(self, parent):
        """
        1) Configuration du panel détaillé
        Fonction initiale: load_prompt_details
        """
        details_frame = ttk.LabelFrame(parent, text="Détails du Prompt", padding="5")
        details_frame.pack(fill="both", expand=True)
        
        # Notebook pour organiser les onglets
        notebook = ttk.Notebook(details_frame)
        notebook.pack(fill="both", expand=True)
        
        # 1.1) Onglet Prompt Values
        values_tab = ttk.Frame(notebook)
        notebook.add(values_tab, text="Prompt Values")
        
        self.values_frame, self.values_tree = self.table_manager.create_prompt_values_table(
            values_tab, self.on_data_change
        )
        self.values_frame.pack(fill="both", expand=True)
        self.current_values_tree = self.values_tree
        self.table_manager._current_values_tree = self.values_tree
        
        # 1.2) Onglet Workflow
        workflow_tab = ttk.Frame(notebook)
        notebook.add(workflow_tab, text="Workflow")
        
        self.workflow_frame, self.workflow_tree = self.table_manager.create_workflow_table(
            workflow_tab, self.on_data_change
        )
        self.workflow_frame.pack(fill="both", expand=True)
        self.current_workflow_tree = self.workflow_tree
        self.table_manager._current_workflow_tree = self.workflow_tree
        
        # Onglet Informations générales
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="Informations")
        
        self.setup_info_tab(info_tab)
        
        # Onglet Data - Gestion de la base de données
        data_tab = ttk.Frame(notebook)
        notebook.add(data_tab, text="Data")
        
        self.setup_data_tab(data_tab)
    
    def setup_info_tab(self, parent):
        """Configuration de l'onglet informations générales"""
        info_frame = ttk.Frame(parent, padding="10")
        info_frame.pack(fill="both", expand=True)
        
        # Variables
        self.name_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.comment_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.status_var = tk.StringVar()
        
        # Interface
        row = 0
        
        ttk.Label(info_frame, text="Nom:").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(info_frame, textvariable=self.name_var, width=50).grid(row=row, column=1, sticky="ew", padx=10)
        row += 1
        
        ttk.Label(info_frame, text="URL:").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(info_frame, textvariable=self.url_var, width=50).grid(row=row, column=1, sticky="ew", padx=10)
        row += 1
        
        ttk.Label(info_frame, text="Modèle:").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(info_frame, textvariable=self.model_var, width=50).grid(row=row, column=1, sticky="ew", padx=10)
        row += 1
        
        ttk.Label(info_frame, text="Statut:").grid(row=row, column=0, sticky="w", pady=5)
        status_combo = ttk.Combobox(info_frame, textvariable=self.status_var, 
                                   values=self.db_manager.status_options, 
                                   state="readonly", width=15)
        status_combo.grid(row=row, column=1, sticky="w", padx=10)
        row += 1
        
        ttk.Label(info_frame, text="Commentaire:").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(info_frame, textvariable=self.comment_var, width=50).grid(row=row, column=1, sticky="ew", padx=10)
        row += 1
        
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Bouton de sauvegarde
        ttk.Button(info_frame, text="Sauvegarder les informations", 
                  command=self.save_current_info).grid(row=row, column=0, columnspan=2, pady=20)
    
    def setup_data_tab(self, parent):
        """Configuration de l'onglet gestion des données"""
        data_frame = ttk.Frame(parent, padding="10")
        data_frame.pack(fill="both", expand=True)
        
        # Titre
        ttk.Label(data_frame, text="Gestion de la Base de Données", 
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 20))
        
        # Localisation actuelle de la base
        location_frame = ttk.LabelFrame(data_frame, text="Base de données actuelle", padding="10")
        location_frame.pack(fill="x", pady=(0, 20))
        
        # Affichage du chemin
        ttk.Label(location_frame, text="Chemin:").grid(row=0, column=0, sticky="w", pady=5)
        
        self.db_path_var = tk.StringVar(value=self.db_path)
        db_path_entry = ttk.Entry(location_frame, textvariable=self.db_path_var, 
                                 state="readonly", width=60)
        db_path_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        location_frame.grid_columnconfigure(1, weight=1)
        
        # Boutons d'action
        actions_frame = ttk.LabelFrame(data_frame, text="Actions", padding="10")
        actions_frame.pack(fill="x", pady=(0, 20))
        
        # Bouton changer de base
        ttk.Button(actions_frame, text="Changer de base...", 
                  command=self.change_database).pack(side="left", padx=(0, 10))
        
        # Bouton créer nouvelle base
        ttk.Button(actions_frame, text="Créer nouvelle base...", 
                  command=self.create_new_database).pack(side="left")
        
        # Bases récentes avec mise en page améliorée
        recent_frame = ttk.LabelFrame(data_frame, text="Bases récentes", padding="10")
        recent_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Frame principal avec grille pour la liste et les boutons
        recent_main_frame = ttk.Frame(recent_frame)
        recent_main_frame.pack(fill="both", expand=True)
        recent_main_frame.grid_columnconfigure(0, weight=1)
        recent_main_frame.grid_rowconfigure(0, weight=1)
        
        # Frame pour la liste avec scrollbar
        list_frame = ttk.Frame(recent_main_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Liste des bases récentes
        self.recent_listbox = tk.Listbox(list_frame, height=8)
        recent_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=recent_scroll.set)
        
        self.recent_listbox.grid(row=0, column=0, sticky="nsew")
        recent_scroll.grid(row=0, column=1, sticky="ns")
        
        # Frame pour les boutons (vertical à droite)
        buttons_frame = ttk.Frame(recent_main_frame)
        buttons_frame.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        
        # Boutons empilés verticalement
        ttk.Button(buttons_frame, text="Ouvrir\nsélectionnée", 
                  command=self.open_selected_recent, width=12).pack(pady=(0, 5))
        
        ttk.Button(buttons_frame, text="Actualiser", 
                  command=self.refresh_recent_list, width=12).pack(pady=(0, 5))
        
        ttk.Button(buttons_frame, text="Effacer\nliste", 
                  command=self.clear_recent_databases, width=12).pack(pady=(0, 5))
        
        # Séparateur
        ttk.Separator(buttons_frame, orient="horizontal").pack(fill="x", pady=10)
        
        # Bouton pour retirer une base sélectionnée
        ttk.Button(buttons_frame, text="Retirer\nsélectionnée", 
                  command=self.remove_selected_recent, width=12).pack(pady=(5, 0))
        
        # Statistiques
        stats_frame = ttk.LabelFrame(data_frame, text="Statistiques", padding="10")
        stats_frame.pack(fill="x")
        
        self.stats_text = tk.StringVar()
        ttk.Label(stats_frame, textvariable=self.stats_text).pack(anchor="w")
        
        # Mettre à jour les données
        self.update_database_stats()
        self.refresh_recent_list()
    
    def setup_status_bar(self):
        """Configuration de la barre de statut"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_text = tk.StringVar()
        self.status_text.set("Prêt")
        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side="left", padx=5)
        
        # Indicateur d'exécution
        self.execution_text = tk.StringVar()
        self.execution_text.set("")
        ttk.Label(self.status_bar, textvariable=self.execution_text).pack(side="right", padx=5)
    
    def load_prompts(self):
        """Charger tous les prompts dans le tableau"""
        # Effacer le tableau
        for item in self.prompts_tree.get_children():
            self.prompts_tree.delete(item)
        
        try:
            prompts = self.db_manager.get_all_prompts()
            for prompt_id, name, parent, model, workflow, status, comment in prompts:
                self.prompts_tree.insert("", "end", iid=str(prompt_id), 
                                       values=(prompt_id, name, status, model, comment, parent or ""))
            
            self.update_status(f"{len(prompts)} prompts chargés")
            # Mettre à jour les statistiques après chargement
            if hasattr(self, 'stats_text'):
                self.update_database_stats()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les prompts: {e}")
    
    def on_prompt_select(self, event):
        """Gestionnaire de sélection de prompt"""
        selection = self.prompts_tree.selection()
        if selection:
            self.selected_prompt_id = int(selection[0])
            self.load_prompt_details(self.selected_prompt_id)
    
    def on_prompt_double_click(self, event):
        """Gestionnaire de double-clic sur un prompt"""
        if self.selected_prompt_id:
            self.edit_prompt()
    
    def load_prompt_details(self, prompt_id):
        """
        Charger les détails d'un prompt - Fonction initiale: load_prompt_details
        1) Panel détaillé
        """
        try:
            data = self.db_manager.get_prompt_by_id(prompt_id)
            if data:
                name, prompt_values, workflow, url, model, comment, status = data
                
                # Mettre à jour les informations générales
                self.name_var.set(name or "")
                self.url_var.set(url or "")
                self.comment_var.set(comment or "")
                self.model_var.set(model or "")
                self.status_var.set(status or "new")
                
                # 1.1) Charger les prompt_values dans le tableau
                self.table_manager.load_prompt_values_data(self.values_tree, prompt_values or "{}")
                
                # 1.2) Charger le workflow dans le tableau
                self.table_manager.load_workflow_data(self.workflow_tree, workflow or "{}")
                
                self.update_status(f"Prompt '{name}' chargé")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les détails: {e}")
    
    def on_data_change(self):
        """Callback appelé quand les données sont modifiées"""
        self.update_status("Données modifiées - Pensez à sauvegarder")
    
    def save_current_info(self):
        """Sauvegarder les informations du prompt actuel"""
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Aucun prompt sélectionné.")
            return
        
        try:
            name = self.name_var.get().strip()
            url = self.url_var.get().strip()
            comment = self.comment_var.get().strip()
            model = self.model_var.get().strip()
            status = self.status_var.get()
            
            if not name:
                messagebox.showerror("Erreur", "Le nom est obligatoire.")
                return
            
            # Récupérer les données JSON des tableaux
            prompt_values_json = self.table_manager.get_prompt_values_json()
            workflow_json = self.table_manager.get_workflow_json()
            
            # Auto-dériver le modèle si vide
            if not model:
                model = self.db_manager.derive_model_from_workflow(workflow_json)
            
            # Sauvegarder
            self.db_manager.update_prompt(
                self.selected_prompt_id, name, prompt_values_json, workflow_json,
                url, model, comment, status
            )
            
            # Mettre à jour l'affichage
            self.prompts_tree.item(str(self.selected_prompt_id), 
                                 values=(self.selected_prompt_id, name, status, model, comment, 
                                        self.prompts_tree.item(str(self.selected_prompt_id), "values")[5]))
            
            self.update_status("Prompt sauvegardé avec succès")
            messagebox.showinfo("Succès", "Prompt sauvegardé avec succès.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    
    def new_prompt(self):
        """0.5) Créer un nouveau prompt"""
        def on_save():
            self.load_prompts()
        
        self.popup_manager.prompt_form("new", None, on_save)
    
    def edit_prompt(self):
        """0.2) Éditer un prompt de façon brute"""
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à éditer.")
            return
        
        def on_save():
            self.load_prompts()
            self.load_prompt_details(self.selected_prompt_id)
        
        self.popup_manager.prompt_form("edit", self.selected_prompt_id, on_save)
    
    def inherit_prompt(self):
        """
        0.4) Hériter d'un prompt - Fonction initiale: inherit_prompt
        Dupliquer le prompt et renseigner le parent et modifier le nom
        """
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à hériter.")
            return
        
        try:
            # Récupérer les données du prompt parent
            data = self.db_manager.get_prompt_by_id(self.selected_prompt_id)
            if not data:
                messagebox.showerror("Erreur", "Impossible de récupérer les données du prompt.")
                return
            
            name, prompt_values, workflow, url, model, comment, status = data
            
            # Générer un nouveau nom
            new_name = f"{name}_herite"
            counter = 1
            while self.db_manager.prompt_name_exists(new_name):
                new_name = f"{name}_herite_{counter}"
                counter += 1
            
            # Créer le nouveau prompt avec parent
            new_id = self.db_manager.create_prompt(
                new_name, prompt_values, workflow, url, model, "new", 
                f"Hérité de: {name}", parent=self.selected_prompt_id
            )
            
            # Recharger et sélectionner le nouveau prompt
            self.load_prompts()
            self.prompts_tree.selection_set(str(new_id))
            self.prompts_tree.focus(str(new_id))
            
            self.update_status(f"Prompt hérité créé: {new_name}")
            messagebox.showinfo("Succès", f"Prompt hérité créé avec succès: {new_name}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'héritage: {e}")
    
    def delete_prompt(self):
        """0.3) Supprimer un prompt"""
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à supprimer.")
            return
        
        # Récupérer le nom pour confirmation
        item = str(self.selected_prompt_id)
        values = self.prompts_tree.item(item, "values")
        name = values[1] if len(values) > 1 else "Inconnu"
        
        if messagebox.askyesno("Confirmer", f"Supprimer définitivement le prompt '{name}' ?"):
            try:
                self.db_manager.delete_prompt(self.selected_prompt_id)
                self.prompts_tree.delete(item)
                
                # Réinitialiser la sélection
                self.selected_prompt_id = None
                self.clear_details()
                
                self.update_status(f"Prompt '{name}' supprimé")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    def execute_workflow(self):
        """
        0.6) Exécuter le workflow - Fonction initiale: execute_workflow
        """
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à exécuter.")
            return
        
        # Simulation d'exécution (à adapter selon l'implémentation originale)
        try:
            # Récupérer les données
            data = self.db_manager.get_prompt_by_id(self.selected_prompt_id)
            if not data:
                messagebox.showerror("Erreur", "Impossible de récupérer les données du prompt.")
                return
            
            name, prompt_values, workflow, url, model, comment, status = data
            
            # Ajouter à la pile d'exécution
            execution_id = f"exec_{int(time.time())}"
            self.add_to_execution_stack(execution_id, f"En cours: {name}")
            
            # Créer un thread pour l'exécution
            thread = threading.Thread(target=self._execute_workflow_task, 
                                     args=(self.selected_prompt_id, execution_id))
            thread.daemon = True
            thread.start()
            
            self.update_status(f"Exécution démarrée pour: {name}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du démarrage de l'exécution: {e}")
    
    def _execute_workflow_task(self, prompt_id, execution_id):
        """Tâche d'exécution du workflow (en thread séparé)"""
        try:
            # Récupérer les données du prompt
            data = self.db_manager.get_prompt_by_id(prompt_id)
            if not data:
                self.update_execution_stack_status(execution_id, "Erreur: Prompt introuvable")
                self.root.after(0, lambda: self.update_prompt_status_after_execution(prompt_id, "nok"))
                return
                
            name, prompt_values_json, workflow_json, url, model, comment, status = data
            
            # Mettre à jour le statut
            self.update_execution_stack_status(execution_id, f"Préparation: {name}")
            
            # Créer le répertoire data/Workflows s'il n'existe pas
            os.makedirs("data/Workflows", exist_ok=True)
            
            # Générer des noms de fichiers uniques dans data/Workflows
            timestamp = int(time.time())
            workflow_file_path = f"data/Workflows/{name}_workflow_{timestamp}.json"
            prompt_values_file_path = f"data/Workflows/{name}_values_{timestamp}.json"
            
            # Écrire les fichiers directement dans data/Workflows
            with open(workflow_file_path, "w", encoding="utf-8") as wf_file:
                wf_file.write(workflow_json)
                
            with open(prompt_values_file_path, "w", encoding="utf-8") as pv_file:
                pv_file.write(prompt_values_json)
            
            # Mettre à jour le statut
            self.update_execution_stack_status(execution_id, f"Connexion ComfyUI: {name}")
            
            # Exécuter le workflow avec ComfyUI
            tsk1 = comfyui_basic_task()
            comfyui_prompt_id = tsk1.addToQueue(workflow_file_path, prompt_values_file_path)
            
            self.update_execution_stack_status(execution_id, f"Génération: {comfyui_prompt_id}")
            
            # Récupérer les images générées
            output_images = tsk1.GetImages(comfyui_prompt_id)
            
            if output_images:
                self.update_execution_stack_status(execution_id, f"Terminé avec succès - Images: {len(output_images)}")
                self.root.after(0, lambda: self.update_prompt_status_after_execution(prompt_id, "ok"))
            else:
                self.update_execution_stack_status(execution_id, "Terminé - Aucune image générée")
                self.root.after(0, lambda: self.update_prompt_status_after_execution(prompt_id, "ok"))
            
        except Exception as e:
            error_msg = f"Erreur ComfyUI: {str(e)}"
            self.update_execution_stack_status(execution_id, error_msg)
            self.root.after(0, lambda: self.update_prompt_status_after_execution(prompt_id, "nok"))
            print(f"Erreur dans _execute_workflow_task: {e}")
    
    def update_prompt_status_after_execution(self, prompt_id, status):
        """Mettre à jour le statut du prompt après exécution"""
        try:
            # Récupérer les données actuelles
            data = self.db_manager.get_prompt_by_id(prompt_id)
            if data:
                name, prompt_values, workflow, url, model, comment, _ = data
                
                # Mettre à jour avec le nouveau statut
                self.db_manager.update_prompt(prompt_id, name, prompt_values, workflow, 
                                            url, model, comment, status)
                
                # Mettre à jour l'affichage
                if str(prompt_id) in [self.prompts_tree.item(item, "values")[0] for item in self.prompts_tree.get_children()]:
                    for item in self.prompts_tree.get_children():
                        if self.prompts_tree.item(item, "values")[0] == str(prompt_id):
                            values = list(self.prompts_tree.item(item, "values"))
                            values[2] = status  # Colonne statut
                            self.prompts_tree.item(item, values=values)
                            break
                
                # Si c'est le prompt sélectionné, mettre à jour aussi les détails
                if self.selected_prompt_id == prompt_id:
                    self.status_var.set(status)
                
        except Exception as e:
            print(f"Erreur lors de la mise à jour du statut: {e}")
    
    def open_prompt_analysis(self):
        """
        0.7) Analyser le prompt - Fonction initiale: open_prompt_analysis
        POPUP-ID: CY8-POPUP-009
        """
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à analyser.")
            return
        
        # CY8-POPUP-009: Popup d'analyse
        popup = tk.Toplevel(self.root)
        popup.title("CY8-POPUP-009 | Analyse du Prompt")
        popup.transient(self.root)
        popup.grab_set()
        
        self.popup_manager.center_window(popup, 600, 400)
        
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        ttk.Label(main_frame, text="CY8-POPUP-009", font=("TkDefaultFont", 8, "bold"), 
                 foreground="blue").pack(anchor="e", pady=(0, 5))
        
        ttk.Label(main_frame, text="Analyse du Prompt", 
                 style='Title.TLabel').pack(pady=10)
        
        # Zone d'analyse
        analysis_text = tk.Text(main_frame, wrap="word", font=("Consolas", 10))
        analysis_text.pack(fill="both", expand=True, pady=10)
        
        # Effectuer l'analyse
        try:
            data = self.db_manager.get_prompt_by_id(self.selected_prompt_id)
            if data:
                name, prompt_values, workflow, url, model, comment, status = data
                
                analysis = f"""ANALYSE DU PROMPT: {name}
{'='*50}

INFORMATIONS GÉNÉRALES:
- ID: {self.selected_prompt_id}
- Nom: {name}
- Statut: {status}
- Modèle: {model or 'Non défini'}
- URL: {url or 'Non définie'}
- Commentaire: {comment or 'Aucun'}

PROMPT VALUES:
{'-'*20}
"""
                
                # Analyser les prompt values
                try:
                    pv_data = json.loads(prompt_values) if prompt_values else {}
                    analysis += f"Nombre d'éléments: {len(pv_data)}\\n"
                    for key, value in pv_data.items():
                        if isinstance(value, dict):
                            analysis += f"- {key}: {value.get('type', 'N/A')} -> {str(value.get('value', ''))[:50]}...\\n"
                        else:
                            analysis += f"- {key}: {str(value)[:50]}...\\n"
                except:
                    analysis += "Erreur lors de l'analyse des prompt values\\n"
                
                analysis += f"""
WORKFLOW:
{'-'*20}
"""
                
                # Analyser le workflow
                try:
                    wf_data = json.loads(workflow) if workflow else {}
                    analysis += f"Nombre de nœuds: {len(wf_data)}\\n"
                    for node_id, node_data in wf_data.items():
                        if isinstance(node_data, dict):
                            class_type = node_data.get('class_type', 'N/A')
                            title = node_data.get('_meta', {}).get('title', 'N/A')
                            analysis += f"- Nœud {node_id}: {class_type} ({title})\\n"
                except:
                    analysis += "Erreur lors de l'analyse du workflow\\n"
                
                analysis_text.insert("1.0", analysis)
        
        except Exception as e:
            analysis_text.insert("1.0", f"Erreur lors de l'analyse: {e}")
        
        analysis_text.config(state="disabled")
        
        ttk.Button(main_frame, text="Fermer", command=popup.destroy).pack(pady=10)
    
    def add_to_execution_stack(self, execution_id, message):
        """Ajouter une exécution à la pile"""
        self.execution_stack.append({"id": execution_id, "message": message, "timestamp": time.time()})
        self.update_execution_display()
    
    def update_execution_stack_status(self, execution_id, message):
        """Mettre à jour le statut d'une exécution"""
        for item in self.execution_stack:
            if item["id"] == execution_id:
                item["message"] = message
                break
        self.update_execution_display()
    
    def update_execution_display(self):
        """Mettre à jour l'affichage des exécutions"""
        if self.execution_stack:
            last_execution = self.execution_stack[-1]
            self.execution_text.set(last_execution["message"])
        else:
            self.execution_text.set("")
    
    def clear_details(self):
        """Effacer les détails affichés"""
        self.name_var.set("")
        self.url_var.set("")
        self.comment_var.set("")
        self.model_var.set("")
        self.status_var.set("")
        
        # Effacer les tableaux
        for item in self.values_tree.get_children():
            self.values_tree.delete(item)
        for item in self.workflow_tree.get_children():
            self.workflow_tree.delete(item)
        
        self.table_manager.values_data.clear()
        self.table_manager.workflow_data.clear()
    
    def update_status(self, message):
        """Mettre à jour la barre de statut"""
        self.status_text.set(message)
        self.root.update_idletasks()
    
    def update_database_stats(self):
        """Mettre à jour les statistiques de la base de données"""
        try:
            prompts = self.db_manager.get_all_prompts()
            total_prompts = len(prompts)
            
            # Statistiques par statut
            status_counts = {}
            for _, _, _, _, _, status, _ in prompts:
                status_counts[status] = status_counts.get(status, 0) + 1
            
            stats_text = f"Total prompts: {total_prompts}"
            if status_counts:
                stats_text += "\n" + " | ".join([f"{status}: {count}" for status, count in status_counts.items()])
            
            self.stats_text.set(stats_text)
        except Exception as e:
            self.stats_text.set(f"Erreur lors du calcul des statistiques: {e}")
    
    def change_database(self):
        """Changer de base de données existante"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Sélectionner une base de données",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
            initialdir=cy8_paths_manager.get_directory_from_path(self.db_path)
        )
        
        if file_path:
            self.switch_to_database(normalize_path(file_path))
    
    def create_new_database(self):
        """Créer une nouvelle base de données
        POPUP-ID: CY8-POPUP-010
        """
        # CY8-POPUP-010: Popup création nouvelle base
        popup = tk.Toplevel(self.root)
        popup.title("CY8-POPUP-010 | Créer nouvelle base de données")
        popup.transient(self.root)
        popup.grab_set()
        
        self.popup_manager.center_window(popup, 500, 300)
        
        main_frame = ttk.Frame(popup, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        ttk.Label(main_frame, text="CY8-POPUP-010", font=("TkDefaultFont", 8, "bold"), 
                 foreground="blue").pack(anchor="e", pady=(0, 10))
        
        # Titre
        ttk.Label(main_frame, text="Créer une nouvelle base de données", 
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 20))
        
        # Nom de la base
        ttk.Label(main_frame, text="Nom de la base:").pack(anchor="w", pady=(0, 5))
        name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=50)
        name_entry.pack(fill="x", pady=(0, 15))
        name_entry.focus_set()
        
        # Chemin de destination
        ttk.Label(main_frame, text="Répertoire de destination:").pack(anchor="w", pady=(0, 5))
        
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill="x", pady=(0, 20))
        
        path_var = tk.StringVar(value=cy8_paths_manager.get_directory_from_path(self.db_path))
        path_entry = ttk.Entry(path_frame, textvariable=path_var, width=40)
        path_entry.pack(side="left", fill="x", expand=True)
        
        def browse_directory():
            from tkinter import filedialog
            directory = filedialog.askdirectory(
                title="Sélectionner le répertoire",
                initialdir=path_var.get()
            )
            if directory:
                path_var.set(directory)
        
        ttk.Button(path_frame, text="Parcourir...", 
                  command=browse_directory).pack(side="right", padx=(5, 0))
        
        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        def create_database():
            name = name_var.get().strip()
            path = path_var.get().strip()
            
            if not name:
                messagebox.showerror("Erreur", "Le nom de la base est obligatoire.")
                return
            
            if not path or not os.path.isdir(path):
                messagebox.showerror("Erreur", "Le chemin spécifié n'est pas valide.")
                return
            
            # Construire le chemin complet
            if not name.endswith('.db'):
                name += '.db'
            
            # Nettoyer le nom de fichier et construire le chemin
            clean_name = cy8_paths_manager.sanitize_filename(name)
            full_path = normalize_path(cy8_paths_manager.join_path(path, clean_name))
            
            if os.path.exists(full_path):
                if not messagebox.askyesno("Confirmer", 
                                         f"Le fichier {full_path} existe déjà. L'écraser ?"):
                    return
            
            try:
                # S'assurer que le répertoire existe
                ensure_dir(full_path)
                
                # Créer et basculer vers la nouvelle base
                self.switch_to_database(full_path, create_new=True)
                popup.destroy()
                messagebox.showinfo("Succès", f"Base de données créée avec succès: {full_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création: {e}")
        
        def cancel():
            popup.destroy()
        
        ttk.Button(button_frame, text="Créer", command=create_database).pack(side="right", padx=(5, 0))
        ttk.Button(button_frame, text="Annuler", command=cancel).pack(side="right")
    
    def switch_to_database(self, new_db_path, create_new=False):
        """Basculer vers une nouvelle base de données"""
        try:
            # Normaliser le chemin
            normalized_path = normalize_path(new_db_path)
            
            # Fermer l'ancienne connexion
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()
            
            # Créer le nouveau gestionnaire de base
            self.db_path = normalized_path
            self.db_manager = cy8_database_manager(normalized_path)
            
            # Initialiser la base (créer les tables si nécessaire)
            if create_new:
                self.db_manager.init_database("init")  # Mode init pour créer avec prompt par défaut
            else:
                self.db_manager.init_database("dev")   # Mode dev pour ouvrir existante
            
            # Recréer tous les gestionnaires avec le nouveau db_manager  
            self.popup_manager = cy8_popup_manager(self.root, self.db_manager)
            self.table_manager = cy8_editable_tables(self.root, self.popup_manager)
            
            # Reconnector le callback de sauvegarde
            self.table_manager.set_save_callback(self.save_current_info)
            
            # Reconnecter les références vers les arbres dans table_manager
            if hasattr(self, 'values_tree'):
                self.table_manager._current_values_tree = self.values_tree
            if hasattr(self, 'workflow_tree'):
                self.table_manager._current_workflow_tree = self.workflow_tree
            
            # Sauvegarder la nouvelle base dans les cookies
            self.user_prefs.set_last_database_path(normalized_path)
            print(f"Base sauvegardée dans les cookies: {normalized_path}")
            
            # Mettre à jour l'affichage
            self.db_path_var.set(normalized_path)
            self.clear_details()
            self.load_prompts()
            self.update_database_stats()
            
            # Mettre à jour les menus et listes
            if hasattr(self, 'recent_db_menu'):
                self.update_recent_databases_menu()
            if hasattr(self, 'recent_listbox'):
                self.refresh_recent_list()
            
            self.update_status(f"Base de données changée: {cy8_paths_manager.get_filename_from_path(normalized_path)}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de changer de base de données: {e}")
    
    def import_json(self):
        """Importer des données JSON"""
        messagebox.showinfo("Import", "Fonctionnalité d'import à implémenter")
    
    def export_json(self):
        """Exporter des données JSON"""
        messagebox.showinfo("Export", "Fonctionnalité d'export à implémenter")
    
    def update_recent_databases_menu(self):
        """Mettre à jour le menu des bases récentes"""
        # Effacer le menu
        self.recent_db_menu.delete(0, 'end')
        
        recent_dbs = self.user_prefs.get_recent_databases()
        
        if not recent_dbs:
            self.recent_db_menu.add_command(label="(Aucune base récente)", state="disabled")
        else:
            for db_path in recent_dbs:
                db_name = os.path.basename(db_path)
                # Limiter la longueur du nom affiché
                display_name = db_name if len(db_name) <= 30 else db_name[:27] + "..."
                
                self.recent_db_menu.add_command(
                    label=f"{display_name} ({os.path.dirname(db_path)})",
                    command=lambda path=db_path: self.open_recent_database(path)
                )
            
            # Séparateur et option pour effacer
            self.recent_db_menu.add_separator()
            self.recent_db_menu.add_command(
                label="Effacer la liste",
                command=self.clear_recent_databases
            )
    
    def open_recent_database(self, db_path):
        """Ouvrir une base de données récente"""
        if os.path.exists(db_path):
            self.switch_to_database(db_path)
        else:
            if messagebox.askyesno("Base introuvable", 
                                 f"La base {db_path} n'existe plus.\nLa retirer de la liste ?"):
                self.user_prefs.remove_recent_database(db_path)
                self.update_recent_databases_menu()
    
    def clear_recent_databases(self):
        """Effacer la liste des bases récentes"""
        if messagebox.askyesno("Confirmer", "Effacer la liste des bases récentes ?"):
            self.user_prefs.clear_recent_databases()
            self.update_recent_databases_menu()
            if hasattr(self, 'recent_listbox'):
                self.refresh_recent_list()
    
    def refresh_recent_list(self):
        """Actualiser la liste des bases récentes dans l'onglet Data"""
        if hasattr(self, 'recent_listbox'):
            # Effacer la liste
            self.recent_listbox.delete(0, tk.END)
            
            # Ajouter les bases récentes
            recent_dbs = self.user_prefs.get_recent_databases()
            for db_path in recent_dbs:
                # Marquer la base actuelle en comparant les chemins normalisés
                is_current = cy8_paths_manager.compare_paths(db_path, self.db_path)
                marker = " (ACTUELLE)" if is_current else ""
                display_text = f"{cy8_paths_manager.get_filename_from_path(db_path)} - {db_path}{marker}"
                self.recent_listbox.insert(tk.END, display_text)
    
    def open_selected_recent(self):
        """Ouvrir la base sélectionnée dans la liste des récentes"""
        if hasattr(self, 'recent_listbox'):
            selection = self.recent_listbox.curselection()
            if selection:
                index = selection[0]
                recent_dbs = self.user_prefs.get_recent_databases()
                if index < len(recent_dbs):
                    db_path = recent_dbs[index]
                    if os.path.exists(db_path):
                        # Comparer les chemins normalisés
                        if not cy8_paths_manager.compare_paths(db_path, self.db_path):
                            self.switch_to_database(db_path)
                        else:
                            messagebox.showinfo("Information", "Cette base est déjà ouverte.")
                    else:
                        if messagebox.askyesno("Base introuvable", 
                                             f"La base {db_path} n'existe plus.\nLa retirer de la liste ?"):
                            self.user_prefs.remove_recent_database(db_path)
                            self.refresh_recent_list()
                            self.update_recent_databases_menu()
            else:
                messagebox.showwarning("Sélection", "Sélectionnez une base dans la liste.")
    
    def remove_selected_recent(self):
        """Retirer la base sélectionnée de la liste des récentes"""
        if hasattr(self, 'recent_listbox'):
            selection = self.recent_listbox.curselection()
            if selection:
                index = selection[0]
                recent_dbs = self.user_prefs.get_recent_databases()
                if index < len(recent_dbs):
                    db_path = recent_dbs[index]
                    db_name = cy8_paths_manager.get_filename_from_path(db_path)
                    
                    if messagebox.askyesno("Confirmer", 
                                         f"Retirer '{db_name}' de la liste des bases récentes ?"):
                        self.user_prefs.remove_recent_database(db_path)
                        self.refresh_recent_list()
                        self.update_recent_databases_menu()
                        messagebox.showinfo("Succès", f"'{db_name}' retiré de la liste.")
            else:
                messagebox.showwarning("Sélection", "Sélectionnez une base à retirer de la liste.")
    
    def run(self):
        """Démarrer l'application"""
        self.root.mainloop()
    
    def on_closing(self):
        """Gestionnaire de fermeture"""
        try:
            # Sauvegarder la géométrie de la fenêtre
            geometry = self.root.geometry()
            self.user_prefs.set_window_geometry(geometry)
            print(f"Géométrie sauvegardée: {geometry}")
            
            # Sauvegarder la base actuelle
            if hasattr(self, 'db_path') and self.db_path:
                self.user_prefs.set_last_database_path(self.db_path)
            
            # Fermer la base de données
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()
        except Exception as e:
            print(f"Erreur lors de la fermeture: {e}")
        
        self.root.destroy()

def main():
    """Point d'entrée principal"""
    app = cy8_prompts_manager()
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()

if __name__ == "__main__":
    main()