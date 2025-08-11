import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import importlib

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
        
        # Remplacer l'entrée de type par un ComboBox
        ttk.Label(main_frame, text="Type:").grid(row=4, column=0, sticky="w", pady=5)
        
        # Liste des types disponibles
        self.function_types = ["default", "advanced", "custom", "specialized"]
        
        # Créer le ComboBox
        self.type_combo = ttk.Combobox(main_frame, width=38, values=self.function_types)
        self.type_combo.grid(row=4, column=1, sticky="ew", pady=5)
        self.type_combo.set("default")  # Valeur par défaut
        
        # Description du type (optionnel)
        self.type_desc_label = ttk.Label(main_frame, text="", font=("Arial", 8), foreground="gray")
        self.type_desc_label.grid(row=5, column=1, sticky="w", pady=(0, 5))
        
        # Lier l'événement de changement pour mettre à jour la description
        self.type_combo.bind("<<ComboboxSelected>>", self.update_type_description)
        
        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.save_function).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left", padx=10)
        
        # Configurer le redimensionnement
        main_frame.columnconfigure(1, weight=1)
        
        # Initialiser la description du type
        self.update_type_description()
    
    def update_type_description(self, event=None):
        """Mettre à jour la description en fonction du type sélectionné"""
        selected_type = self.type_combo.get()
        
        descriptions = {
            "default": "Traitement standard des images sans options particulières",
            "advanced": "Traitement avancé avec options de filtrage et d'analyse",
            "custom": "Traitement personnalisé avec des paramètres spécifiques",
            "specialized": "Traitement spécialisé pour des cas d'usage particuliers"
        }
        
        description = descriptions.get(selected_type, "")
        self.type_desc_label.config(text=description)
    
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
            
            # Définir le type dans le ComboBox
            function_type = function_data[5]
            if function_type in self.function_types:
                self.type_combo.set(function_type)
            else:
                # Si le type n'est pas dans la liste prédéfinie, l'ajouter
                self.function_types.append(function_type)
                self.type_combo.config(values=self.function_types)
                self.type_combo.set(function_type)
            
            # Mettre à jour la description du type
            self.update_type_description()
    
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
        
        function_type = self.type_combo.get()
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
        
        # Vérifier que les chemins existent
        if not os.path.exists(default_dir):
            messagebox.showerror("Error", f"Default directory does not exist: {default_dir}")
            return
        
        if not os.path.exists(os.path.dirname(db_path)):
            messagebox.showerror("Error", f"Database directory does not exist: {os.path.dirname(db_path)}")
            return
        
        # Nettoyer la frame droite
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        # Initialiser l'explorateur d'images
        try:
            self.active_image_process = image_process(
                self.right_frame, 
                db_path, 
                default_dir, 
                cible_dir,
                name
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image explorer: {str(e)}")
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