import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import importlib
from cy2_image_factory import create_image_processor
# Importer les modules nécessaires
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.cy2_image_process import image_process

class TitleFrame(ttk.Frame):
    """Un Frame qui implémente les méthodes title(), geometry() et autres pour compatibilité avec image_process"""
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._title = ""
        self._geometry = ""
        
    def title(self, title=None):
        """Simuler la méthode title() d'une fenêtre"""
        if title is not None:
            self._title = title
            # Mettre à jour le titre de la fenêtre principale si possible
            if hasattr(self.master, "master") and hasattr(self.master.master, "title"):
                self.master.master.title(f"Image Management System - {title}")
        return self._title
    
    def geometry(self, geometry_str=None):
        """Simuler la méthode geometry() d'une fenêtre"""
        if geometry_str is not None:
            self._geometry = geometry_str
            # On ne fait rien avec la chaîne de géométrie car les frames sont dimensionnés par leur parent
        return self._geometry
    
    def minsize(self, width=None, height=None):
        """Simuler la méthode minsize() d'une fenêtre"""
        return width, height if width and height else (200, 200)
    
    def resizable(self, width=None, height=None):
        """Simuler la méthode resizable() d'une fenêtre"""
        return True
    
    def protocol(self, protocol_name, callback):
        """Simuler la méthode protocol() d'une fenêtre"""
        pass
    
    def destroy(self):
        """Méthode destroy personnalisée pour nettoyer les ressources"""
        # Nettoyer les widgets enfants explicitement
        for widget in self.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        
        # Appeler la méthode destroy du parent
        super().destroy()


class FunctionDatabase:
    """Classe pour gérer la table des fonctions dans la base de données"""
    
    def __init__(self, db_path):
        """Initialiser la connexion à la base de données"""
        self.db_path = os.path.normpath(db_path)
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()
    
    def connect(self):
        """Établir une connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error-01 connecting to database: {str(e)}")
            messagebox.showerror("Database Error", f"Could not connect to database: {str(e)}")
            raise
    
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
                    processor_type TEXT DEFAULT "standard"
                )
            ''')
            
            # Vérifier si les colonnes nécessaires existent et les ajouter si besoin
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
    
    def get_all_functions(self):
        """Récupérer toutes les fonctions de la table"""
        try:
            # Vérifier d'abord quelles colonnes sont disponibles
            self.cursor.execute("PRAGMA table_info(functions)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            # Construire la requête en fonction des colonnes existantes
            query = "SELECT id, name, default_directory, cible_directory, db_path"
            
            # Ajouter processor_type s'il existe
            if "processor_type" in columns:
                query += ", processor_type"
            else:
                query += ", 'standard' AS processor_type"
                
            # Ajouter status_options s'il existe
            if "status_options" in columns:
                query += ", status_options"
            else:
                query += ", 'new,viewed,approved,rejected,favorite' AS status_options"
                
            query += " FROM functions"
            
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error-03 retrieving functions: {str(e)}")
            messagebox.showerror("Database Error", f"Could not retrieve functions: {str(e)}")
            return []
    
    def get_function_by_id(self, function_id):
        """Récupérer une fonction par son ID"""
        try:
            # Vérifier d'abord quelles colonnes sont disponibles
            self.cursor.execute("PRAGMA table_info(functions)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            # Construire la requête en fonction des colonnes existantes
            query = "SELECT id, name, default_directory, cible_directory, db_path"
            
            # Ajouter processor_type s'il existe
            if "processor_type" in columns:
                query += ", processor_type"
            else:
                query += ", 'standard' AS processor_type"
                
            # Ajouter status_options s'il existe
            if "status_options" in columns:
                query += ", status_options"
            else:
                query += ", 'new,viewed,approved,rejected,favorite' AS status_options"
                
            query += " FROM functions WHERE id = ?"
            
            self.cursor.execute(query, (function_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error retrieving function: {str(e)}")
            messagebox.showerror("Database Error", f"Could not retrieve function: {str(e)}")
            return None

    def add_function(self, name, default_directory, cible_directory, db_path, processor_type="standard", status_options="new,viewed,approved,rejected,favorite"):
        """Ajouter une nouvelle fonction à la table"""
        try:
            self.cursor.execute(
                "INSERT INTO functions (name, default_directory, cible_directory, db_path, processor_type, status_options) VALUES (?, ?, ?, ?, ?, ?)",
                (name, default_directory, cible_directory, db_path, processor_type, status_options)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"A function with the name '{name}' already exists.")
            return None
        except sqlite3.Error as e:
            print(f"Error-06 adding function: {str(e)}")
            messagebox.showerror("Database Error", f"Could not add function: {str(e)}")
            return None

    def update_function(self, function_id, name, default_directory, cible_directory, db_path, processor_type="standard", status_options="new,viewed,approved,rejected,favorite"):
        """Mettre à jour une fonction existante"""
        try:
            self.cursor.execute(
                """UPDATE functions SET
                   name = ?, default_directory = ?, cible_directory = ?,
                   db_path = ?, processor_type = ?, status_options = ?
                   WHERE id = ?""",
                (name, default_directory, cible_directory, db_path, processor_type, status_options, function_id)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"A function with the name '{name}' already exists.")
            return False
        except sqlite3.Error as e:
            print(f"Error-08 updating function: {str(e)}")
            messagebox.showerror("Database Error", f"Could not update function: {str(e)}")
            return False
    
    def delete_function(self, function_id):
        """Supprimer une fonction de la table"""
        try:
            self.cursor.execute("DELETE FROM functions WHERE id = ?", (function_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error-09 deleting function: {str(e)}")
            messagebox.showerror("Database Error", f"Could not delete function: {str(e)}")
            return False
    
    def close(self):
        """Fermer la connexion à la base de données"""
        if self.conn:
            self.conn.close()


class FunctionForm(tk.Toplevel):
    """Formulaire pour ajouter ou modifier une fonction"""
    
    def __init__(self, parent, db, function_id=None):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.function_id = function_id
        self.function_data = None  # Initialiser function_data à None
        
        self.title("Function Details" if function_id else "Add New Function")
        self.geometry("500x350")
        self.resizable(True, True)
        
        self.create_widgets()
        
        # Centrer la fenêtre
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Remplir le formulaire si on modifie une fonction existante
        if function_id:
            self.load_function_data()
    
    def create_widgets(self):
        """Créer les widgets du formulaire"""
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Champ Nom
        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(name_frame, text="Name:", width=15).pack(side="left")
        self.name_entry = ttk.Entry(name_frame, width=50)
        self.name_entry.pack(side="left", fill="x", expand=True)
        
        # Champ Répertoire par défaut
        self.default_dir_frame = ttk.Frame(main_frame)
        self.default_dir_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.default_dir_frame, text="Default Directory:", width=15).pack(side="left")
        self.default_dir_entry = ttk.Entry(self.default_dir_frame, width=50)
        self.default_dir_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(self.default_dir_frame, text="Browse", command=self.browse_default_dir).pack(side="left", padx=5)
        
        # Champ Répertoire cible
        self.cible_dir_frame = ttk.Frame(main_frame)
        self.cible_dir_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.cible_dir_frame, text="Target Directory:", width=15).pack(side="left")
        self.cible_dir_entry = ttk.Entry(self.cible_dir_frame, width=50)
        self.cible_dir_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(self.cible_dir_frame, text="Browse", command=self.browse_cible_dir).pack(side="left", padx=5)
        
        # Champ Chemin de la base de données
        self.db_path_frame = ttk.Frame(main_frame)
        self.db_path_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.db_path_frame, text="Database Path:", width=15).pack(side="left")
        self.db_path_entry = ttk.Entry(self.db_path_frame, width=50)
        self.db_path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(self.db_path_frame, text="Browse", command=self.browse_db_path).pack(side="left", padx=5)
        
        # NOUVEAU - Champ Processor Type
        self.processor_type_frame = ttk.Frame(main_frame)
        self.processor_type_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.processor_type_frame, text="Processor Type:", width=15).pack(side="left")
        self.processor_type_var = tk.StringVar(value="standard")
        processor_types = ["standard", "explorer", "collecter"]
        self.processor_type_combobox = ttk.Combobox(self.processor_type_frame, textvariable=self.processor_type_var, values=processor_types)
        self.processor_type_combobox.pack(side="left", fill="x", expand=True)
        
        # NOUVEAU - Champ Status Options (caché par défaut)
        self.status_options_frame = ttk.Frame(main_frame)
        self.status_options_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.status_options_frame, text="Status Options:", width=15).pack(side="left")
        self.status_options_entry = ttk.Entry(self.status_options_frame, width=50)
        self.status_options_entry.pack(side="left", fill="x", expand=True)
        
        # Boutons de sauvegarde et d'annulation
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)
        
        # Pré-remplir les champs si nécessaire
        if self.function_data:
            self.name_entry.insert(0, self.function_data[1])
            self.default_dir_entry.insert(0, self.function_data[2])
            self.cible_dir_entry.insert(0, self.function_data[3])
            self.db_path_entry.insert(0, self.function_data[4])
            
            # Initialiser le champ processor_type s'il existe
            if len(self.function_data) > 6:
                self.processor_type_var.set(self.function_data[6])

    def browse_default_dir(self):
        """Ouvrir un dialogue pour sélectionner le répertoire par défaut"""
        directory = filedialog.askdirectory()
        if directory:
            self.default_dir_entry.delete(0, tk.END)
            self.default_dir_entry.insert(0, directory)

    def browse_cible_dir(self):
        """Ouvrir un dialogue pour sélectionner le répertoire cible"""
        directory = filedialog.askdirectory()
        if directory:
            self.cible_dir_entry.delete(0, tk.END)
            self.cible_dir_entry.insert(0, directory)

    def browse_db_path(self):
        """Ouvrir un dialogue pour sélectionner le chemin de la base de données"""
        # Proposer par défaut un fichier .db
        initialdir = os.path.dirname(self.db_path_entry.get()) if self.db_path_entry.get() else os.path.expanduser("~")
        db_file = filedialog.asksaveasfilename(
            initialdir=initialdir,
            title="Select Database File",
            filetypes=(("SQLite Database", "*.db"), ("All Files", "*.*")),
            defaultextension=".db"
        )
        if db_file:
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, db_file)

    def load_function_data(self):
        """Charger les données d'une fonction existante"""
        self.function_data = self.db.get_function_by_id(self.function_id)
        if self.function_data:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self.function_data[1])
            
            self.default_dir_entry.delete(0, tk.END)
            self.default_dir_entry.insert(0, self.function_data[2])
            
            self.cible_dir_entry.delete(0, tk.END)
            self.cible_dir_entry.insert(0, self.function_data[3])
            
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, self.function_data[4])
            
            # Initialiser le champ processor_type s'il existe
            if len(self.function_data) > 6:
                self.processor_type_var.set(self.function_data[6])

    def save(self):
        """Sauvegarder les données du formulaire"""
        name = self.name_entry.get().strip()
        default_dir = self.default_dir_entry.get().strip()
        cible_dir = self.cible_dir_entry.get().strip()
        db_path = self.db_path_entry.get().strip()
        processor_type = self.processor_type_var.get()
        
        # Récupérer les options de statut uniquement si processor_type est "workflow"
        status_options = "new,viewed,approved,rejected,favorite"  # Valeur par défaut
        if processor_type == "workflow":
            user_status = self.status_options_entry.get().strip()
            if user_status:
                status_options = user_status
    
        # Vérifier que tous les champs obligatoires sont remplis
        if not all([name, default_dir, cible_dir, db_path]):
            messagebox.showerror("Error", "All fields are required.")
            return
        
        # Sauvegarder les données
        try:
            if self.function_id:
                success = self.db.update_function(
                    self.function_id, name, default_dir, cible_dir, db_path, 
                    processor_type, status_options
                )
            else:
                success = self.db.add_function(
                    name, default_dir, cible_dir, db_path, 
                    processor_type, status_options
                )
            
            if success:
                messagebox.showinfo("Success", "Function saved successfully")
                self.parent.refresh_function_list()
                self.destroy()
            else:
                messagebox.showerror("Error", "Failed to save function.")
        except Exception as e:
            print(f"Error saving function: {str(e)}")
            messagebox.showerror("Error", f"Error saving function: {str(e)}")


class SplitApplication(tk.Tk):
    """Application combinant le gestionnaire de fonctions et l'explorateur d'images"""
    
    def __init__(self):
        super().__init__()
        self.title("Image Management System")
        self.geometry("1400x800")
        self.minsize(1200, 600)
        
        # Chemin par défaut pour la base de données des fonctions
        self.db_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "..", 
            "data", 
            "functions.db"
        ))
         
        # Créer le répertoire parent si nécessaire
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialiser la base de données
        self.db = FunctionDatabase(self.db_path)
        
        # Créer l'interface utilisateur
        self.create_widgets()
        
        # Configurer la fermeture de l'application
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variable pour suivre l'image_process actif
        self.active_image_process = None
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        # Créer un PanedWindow pour diviser la fenêtre en deux parties
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Partie gauche : liste des fonctions
        self.left_frame = ttk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.left_frame, weight=1)
        
        # Partie droite : explorateur d'images
        self.right_frame = TitleFrame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=4)
        
        # Configurer la partie gauche (liste des fonctions)
        self.setup_function_list(self.left_frame)
        
        # Message initial pour la partie droite
        self.setup_initial_message(self.right_frame)
    
    def setup_function_list(self, parent_frame):
        """Configurer la liste des fonctions"""
        # Titre
        title_label = ttk.Label(parent_frame, text="Functions", font=("Arial", 12, "bold"))
        title_label.pack(pady=10)
        
        # Boutons d'action
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        add_btn = ttk.Button(button_frame, text="Add", command=self.add_function, width=5)
        add_btn.pack(side="left", padx=2)
        
        edit_btn = ttk.Button(button_frame, text="Edit", command=self.edit_selected_function, width=5)
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = ttk.Button(button_frame, text="Delete", command=self.delete_function, width=5)
        delete_btn.pack(side="left", padx=2)
        
        # Liste des fonctions
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Liste avec une seule colonne (nom)
        self.function_list = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            selectmode=tk.SINGLE,
            activestyle='dotbox',
            height=20
        )
        self.function_list.pack(fill="both", expand=True)
        scrollbar.config(command=self.function_list.yview)
        
        # Stocker les ID de fonction pour référence
        self.function_ids = []
        
        # Lier la sélection d'une fonction à son chargement
        self.function_list.bind("<<ListboxSelect>>", self.on_function_select)
        self.function_list.bind("<Double-1>", self.on_function_double_click)
        
        # Rafraîchir la liste des fonctions
        self.refresh_function_list()
    
    def setup_initial_message(self, parent_frame):
        """Afficher un message initial dans la partie droite"""
        message_label = ttk.Label(
            parent_frame, 
            text="Select a function from the list to display its images",
            font=("Arial", 14)
        )
        message_label.pack(expand=True, pady=50)
        self.initial_message = message_label
    
    def refresh_function_list(self):
        """Rafraîchir la liste des fonctions"""
        # Effacer la liste actuelle
        self.function_list.delete(0, tk.END)
        self.function_ids = []
        
        # Récupérer toutes les fonctions
        functions = self.db.get_all_functions()
        
        # Ajouter les fonctions à la liste
        for function in functions:
            function_id, name = function[0], function[1]
            self.function_list.insert(tk.END, name)
            self.function_ids.append(function_id)
    
    def on_function_select(self, event):
        """Charger l'explorateur d'images lorsqu'une fonction est sélectionnée"""
        selection = self.function_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        function_id = self.function_ids[index]
        self.load_function(function_id)
    
    def on_function_double_click(self, event):
        """Modifier une fonction lorsqu'elle est double-cliquée"""
        selection = self.function_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        function_id = self.function_ids[index]
        self.edit_function(function_id)
    
    def load_function(self, function_id):
        """Charger l'explorateur d'images pour la fonction sélectionnée"""
        function_data = self.db.get_function_by_id(function_id)
        if not function_data:
            return
        
        # Récupérer les paramètres
        name = function_data[1]
        default_dir = function_data[2]
        cible_dir = function_data[3]
        db_path = function_data[4]
        processor_type = function_data[5] if len(function_data) > 5 else 'standard'
        status_options = function_data[6] if len(function_data) > 6 else 'new,viewed,approved,rejected,favorite'
        
        # IMPORTANT: Nettoyer l'instance précédente et tous les widgets
        if self.active_image_process:
            # Appeler __del__ pour fermer proprement les ressources
            if hasattr(self.active_image_process, '__del__'):
                try:
                    self.active_image_process.__del__()
                except Exception as e:
                    print(f"Error cleaning up previous image process: {e}")
            
            # Mettre à None pour libérer la référence
            self.active_image_process = None
        
        # Supprimer tous les widgets existants dans la partie droite
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        # Créer un dictionnaire de configuration
        config = {
            'title': name,
            'default_directory': default_dir,
            'cible_directory': cible_dir,
            'db_path': db_path,
            'processor_type': processor_type,
            'status_options': status_options
        }
        
        # Utiliser la factory pour créer l'instance appropriée
        try:
            self.active_image_process = create_image_processor(self.right_frame, config)
        except Exception as e:
            print(f"Error-13 loading image_processor: {str(e)}")
            messagebox.showerror("Error", f"Error loading image_processor: {str(e)}")
            self.setup_initial_message(self.right_frame)
    
    def add_function(self):
        """Ouvrir le formulaire pour ajouter une nouvelle fonction"""
        FunctionForm(self, self.db)
    
    def edit_selected_function(self):
        """Modifier la fonction sélectionnée"""
        selection = self.function_list.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a function to edit")
            return
        
        index = selection[0]
        function_id = self.function_ids[index]
        self.edit_function(function_id)
    
    def edit_function(self, function_id):
        """Ouvrir le formulaire pour modifier une fonction existante"""
        FunctionForm(self, self.db, function_id)
    
    def delete_function(self):
        """Supprimer la fonction sélectionnée"""
        selection = self.function_list.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a function to delete")
            return
        
        index = selection[0]
        function_id = self.function_ids[index]
        function_name = self.function_list.get(index)
        
        # Demander confirmation
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the function '{function_name}'?"
        )
        
        if result:
            success = self.db.delete_function(function_id)
            if success:
                messagebox.showinfo("Success", "Function deleted successfully")
                self.refresh_function_list()
                
                # Si la fonction supprimée était active, nettoyer la partie droite
                if self.active_image_process:
                    for widget in self.right_frame.winfo_children():
                        widget.destroy()
                    self.setup_initial_message(self.right_frame)
                    self.active_image_process = None
    
    def on_closing(self):
        """Fermer proprement l'application"""
        # Fermer la base de données
        self.db.close()
        
        # Fermer l'explorateur d'images si ouvert
        if self.active_image_process:
            # Appeler manuellement la méthode __del__ de image_process si nécessaire
            if hasattr(self.active_image_process, '__del__'):
                self.active_image_process.__del__()
        
        self.destroy()


def main():
    """Fonction principale pour démarrer l'application"""
    app = SplitApplication()
    app.mainloop()


if __name__ == "__main__":
    main()

