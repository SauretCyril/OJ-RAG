import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import importlib
import sys

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
                    type TEXT DEFAULT "default"
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not create table: {str(e)}")
            raise
    
    def get_all_functions(self):
        """Récupérer toutes les fonctions de la table"""
        try:
            self.cursor.execute("SELECT id, name, default_directory, cible_directory, db_path, type FROM functions")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not retrieve functions: {str(e)}")
            return []
    
    def get_function_by_id(self, function_id):
        """Récupérer une fonction par son ID"""
        try:
            self.cursor.execute(
                "SELECT id, name, default_directory, cible_directory, db_path, type FROM functions WHERE id = ?",
                (function_id,)
            )
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not retrieve function: {str(e)}")
            return None
    
    def add_function(self, name, default_directory, cible_directory, db_path, function_type="default"):
        """Ajouter une nouvelle fonction à la table"""
        try:
            self.cursor.execute(
                "INSERT INTO functions (name, default_directory, cible_directory, db_path, type) VALUES (?, ?, ?, ?, ?)",
                (name, default_directory, cible_directory, db_path, function_type)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"A function with the name '{name}' already exists.")
            return None
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not add function: {str(e)}")
            return None
    
    def update_function(self, function_id, name, default_directory, cible_directory, db_path, function_type):
        """Mettre à jour une fonction existante"""
        try:
            self.cursor.execute(
                """UPDATE functions SET 
                   name = ?, default_directory = ?, cible_directory = ?, 
                   db_path = ?, type = ? 
                   WHERE id = ?""",
                (name, default_directory, cible_directory, db_path, function_type, function_id)
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"A function with the name '{name}' already exists.")
            return False
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not update function: {str(e)}")
            return False
    
    def delete_function(self, function_id):
        """Supprimer une fonction de la table"""
        try:
            self.cursor.execute("DELETE FROM functions WHERE id = ?", (function_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
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
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Champs du formulaire
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        ttk.Label(main_frame, text="Default Directory:").grid(row=1, column=0, sticky="w", pady=5)
        self.default_dir_frame = ttk.Frame(main_frame)
        self.default_dir_frame.grid(row=1, column=1, sticky="ew", pady=5)
        self.default_dir_entry = ttk.Entry(self.default_dir_frame, width=30)
        self.default_dir_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(self.default_dir_frame, text="Browse", command=lambda: self.browse_directory(self.default_dir_entry)).pack(side="right", padx=5)
        
        ttk.Label(main_frame, text="Cible Directory:").grid(row=2, column=0, sticky="w", pady=5)
        self.cible_dir_frame = ttk.Frame(main_frame)
        self.cible_dir_frame.grid(row=2, column=1, sticky="ew", pady=5)
        self.cible_dir_entry = ttk.Entry(self.cible_dir_frame, width=30)
        self.cible_dir_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(self.cible_dir_frame, text="Browse", command=lambda: self.browse_directory(self.cible_dir_entry)).pack(side="right", padx=5)
        
        ttk.Label(main_frame, text="Database Path:").grid(row=3, column=0, sticky="w", pady=5)
        self.db_path_frame = ttk.Frame(main_frame)
        self.db_path_frame.grid(row=3, column=1, sticky="ew", pady=5)
        self.db_path_entry = ttk.Entry(self.db_path_frame, width=30)
        self.db_path_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(self.db_path_frame, text="Browse", command=lambda: self.browse_file(self.db_path_entry)).pack(side="right", padx=5)
        
        ttk.Label(main_frame, text="Type:").grid(row=4, column=0, sticky="w", pady=5)
        self.type_entry = ttk.Entry(main_frame, width=40)
        self.type_entry.grid(row=4, column=1, sticky="ew", pady=5)
        self.type_entry.insert(0, "default")  # Valeur par défaut
        
        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.save_function).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left", padx=10)
        
        # Configurer le redimensionnement
        main_frame.columnconfigure(1, weight=1)
    
    def browse_directory(self, entry_widget):
        """Ouvrir un dialogue pour sélectionner un répertoire"""
        directory = filedialog.askdirectory()
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, os.path.normpath(directory))
    
    def browse_file(self, entry_widget):
        """Ouvrir un dialogue pour sélectionner un fichier"""
        file_path = filedialog.askopenfilename()
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, os.path.normpath(file_path))
    
    def load_function_data(self):
        """Charger les données d'une fonction existante dans le formulaire"""
        function_data = self.db.get_function_by_id(self.function_id)
        if function_data:
            self.name_entry.insert(0, function_data[1])
            self.default_dir_entry.insert(0, function_data[2])
            self.cible_dir_entry.insert(0, function_data[3])
            self.db_path_entry.insert(0, function_data[4])
            self.type_entry.delete(0, tk.END)
            self.type_entry.insert(0, function_data[5])
    
    def validate_form(self):
        """Valider les champs du formulaire"""
        errors = []
        
        name = self.name_entry.get().strip()
        if not name:
            errors.append("Name is required")
        
        default_dir = self.default_dir_entry.get().strip()
        if not default_dir:
            errors.append("Default directory is required")
        
        cible_dir = self.cible_dir_entry.get().strip()
        if not cible_dir:
            errors.append("Cible directory is required")
        
        db_path = self.db_path_entry.get().strip()
        if not db_path:
            errors.append("Database path is required")
        
        function_type = self.type_entry.get().strip()
        if not function_type:
            errors.append("Type is required")
        
        return errors, name, default_dir, cible_dir, db_path, function_type
    
    def save_function(self):
        """Sauvegarder la fonction (ajouter ou mettre à jour)"""
        errors, name, default_dir, cible_dir, db_path, function_type = self.validate_form()
        
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        if self.function_id:
            # Mettre à jour une fonction existante
            success = self.db.update_function(
                self.function_id, name, default_dir, cible_dir, db_path, function_type
            )
            if success:
                messagebox.showinfo("Success", "Function updated successfully")
                self.parent.refresh_function_list()
                self.destroy()
        else:
            # Ajouter une nouvelle fonction
            function_id = self.db.add_function(name, default_dir, cible_dir, db_path, function_type)
            if function_id:
                messagebox.showinfo("Success", "Function added successfully")
                self.parent.refresh_function_list()
                self.destroy()


class FunctionManager(tk.Tk):
    """Interface principale pour gérer les fonctions"""
    
    def __init__(self, db_path):
        super().__init__()
        self.title("Function Manager")
        self.geometry("900x500")
        self.minsize(800, 400)
        
        # Initialiser la base de données
        self.db = FunctionDatabase(db_path)
        
        self.create_widgets()
        self.refresh_function_list()
        
        # Configurer la fermeture de l'application
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Titre
        title_label = ttk.Label(main_frame, text="Function Manager", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Frame pour les boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=5)
        
        add_btn = ttk.Button(button_frame, text="Add Function", command=self.add_function)
        add_btn.pack(side="left", padx=5)
        
        delete_btn = ttk.Button(button_frame, text="Delete Function", command=self.delete_function)
        delete_btn.pack(side="left", padx=5)
        
        execute_btn = ttk.Button(
            button_frame, 
            text="Execute Function", 
            command=self.execute_function,
            style="Execute.TButton"
        )
        execute_btn.pack(side="right", padx=5)
        
        # Style pour le bouton d'exécution
        self.style = ttk.Style()
        self.style.configure("Execute.TButton", background="green", foreground="white")
        
        # Frame pour la liste des fonctions
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Liste des fonctions
        columns = ("ID", "Name", "Default Directory", "Cible Directory", "Database Path", "Type")
        self.function_tree = ttk.Treeview(
            list_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=scrollbar.set
        )
        
        # Configurer les colonnes
        self.function_tree.heading("ID", text="ID")
        self.function_tree.heading("Name", text="Name")
        self.function_tree.heading("Default Directory", text="Default Directory")
        self.function_tree.heading("Cible Directory", text="Cible Directory")
        self.function_tree.heading("Database Path", text="Database Path")
        self.function_tree.heading("Type", text="Type")
        
        # Définir les largeurs des colonnes
        self.function_tree.column("ID", width=50, minwidth=50)
        self.function_tree.column("Name", width=150, minwidth=100)
        self.function_tree.column("Default Directory", width=200, minwidth=150)
        self.function_tree.column("Cible Directory", width=200, minwidth=150)
        self.function_tree.column("Database Path", width=200, minwidth=150)
        self.function_tree.column("Type", width=100, minwidth=80)
        
        self.function_tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.function_tree.yview)
        
        # Lier le double-clic pour éditer une fonction
        self.function_tree.bind("<Double-1>", self.edit_function)
    
    def refresh_function_list(self):
        """Rafraîchir la liste des fonctions"""
        # Effacer la liste actuelle
        for item in self.function_tree.get_children():
            self.function_tree.delete(item)
        
        # Récupérer toutes les fonctions
        functions = self.db.get_all_functions()
        
        # Ajouter les fonctions à la liste
        for function in functions:
            self.function_tree.insert("", "end", values=function)
    
    def add_function(self):
        """Ouvrir le formulaire pour ajouter une nouvelle fonction"""
        FunctionForm(self, self.db)
    
    def edit_function(self, event):
        """Ouvrir le formulaire pour modifier une fonction existante"""
        # Récupérer l'élément sélectionné
        selection = self.function_tree.selection()
        if not selection:
            return
        
        # Récupérer l'ID de la fonction
        function_id = self.function_tree.item(selection[0], "values")[0]
        
        # Ouvrir le formulaire d'édition
        FunctionForm(self, self.db, function_id)
    
    def delete_function(self):
        """Supprimer la fonction sélectionnée"""
        selection = self.function_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a function to delete")
            return
        
        function_id = self.function_tree.item(selection[0], "values")[0]
        function_name = self.function_tree.item(selection[0], "values")[1]
        
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
    
    def execute_function(self):
        """Exécuter la fonction sélectionnée"""
        selection = self.function_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a function to execute")
            return
        
        # Récupérer les informations de la fonction
        values = self.function_tree.item(selection[0], "values")
        function_id = values[0]
        function_name = values[1]
        default_dir = values[2]
        cible_dir = values[3]
        db_path = values[4]
        function_type = values[5]
        
        # Vérifier que les chemins existent
        if not os.path.exists(default_dir):
            messagebox.showerror("Error", f"Default directory does not exist: {default_dir}")
            return
        
        if not os.path.exists(os.path.dirname(db_path)):
            messagebox.showerror("Error", f"Database directory does not exist: {os.path.dirname(db_path)}")
            return
        
        try:
            # Ajouter le répertoire parent au path pour pouvoir importer le module
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
            
            # Importer dynamiquement le module image_process
            module = importlib.import_module("backend.image_process")
            
            # Selon le type de fonction, exécuter la fonction appropriée
            if function_type == "default":
                # Minimiser la fenêtre actuelle
                self.iconify()
                
                # Créer une nouvelle fenêtre Tkinter pour l'application
                root = tk.Tk()
                # Exécuter process_default avec les paramètres de la fonction
                module.image_process(root, db_path, default_dir, cible_dir)
                root.mainloop()
                
                # Restaurer la fenêtre après la fermeture de l'application
                self.deiconify()
            else:
                messagebox.showerror("Error", f"Unsupported function type: {function_type}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error executing function: {str(e)}")
    
    def on_closing(self):
        """Fermer proprement l'application"""
        self.db.close()
        self.destroy()


def main():
    """Fonction principale pour démarrer l'application"""
    # Chemin par défaut pour la base de données des fonctions
    db_path = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "..", 
        "data", 
        "functions.db"
    ))
    
    # Créer le répertoire parent si nécessaire
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Démarrer l'application
    app = FunctionManager(db_path)
    app.mainloop()


if __name__ == "__main__":
    main()