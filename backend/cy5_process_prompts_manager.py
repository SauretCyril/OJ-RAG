import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import sqlite3
import json
import time  # Ajout de cette ligne
from cy6_wkf001_Basic import comfyui_basic_task
import tempfile
from dotenv import load_dotenv


class process_prompts_manager:
    def __init__(self, root, db_path="g:/tmp/prompts_manager.db", mode="init"):
        self.root = root
        self.db_path = db_path
        self.prompts = []
        self.selected_prompt_id = None

        # Charger la configuration
        self.config = self.load_config()
        self.images_dir_var = tk.StringVar(value=self.config.get("images_dir", "./output"))

        self.root.title("Prompts Manager")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        self.init_database(mode)
        self.setup_ui()
        self.load_prompts()

    def init_database(self, mode="init"):
        """
        Initialise la base de données
        mode="init" : Recrée la base et ajoute le prompt par défaut
        mode="dev"  : Crée la base si elle n'existe pas, n'ajoute pas le prompt par défaut
        """
        if mode == "init":
            # Mode init: Supprime la base existante et recrée
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    image TEXT,
                    url TEXT
                )
            ''')
            self.conn.commit()
            self.add_default_basic_prompt()
        else:  # mode == "dev"
            # Mode dev: Crée la base si elle n'existe pas
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    image TEXT,
                    url TEXT
                )
            ''')
            self.conn.commit()

    def setup_ui(self):
        """Créer l'interface utilisateur avec panneau divisé"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titre
        title_label = ttk.Label(main_frame, text="Gestionnaire de Prompts", font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))  # Réduit l'espace sous le titre

        # Affichage du chemin de la base de données
        db_path_label = ttk.Label(main_frame, text=f"Base de données : {self.db_path}", font=("Arial", 10, "italic"))
        db_path_label.pack(pady=(0, 15))  # Ajoute un espace sous le label

        # Boutons d'action
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="Nouvelle Prompt", command=self.new_prompt).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Actualiser", command=self.load_prompts).pack(side=tk.LEFT, padx=5)

        # PanedWindow pour diviser en deux parties
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Frame gauche : tableau des prompts
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)

        # Frame droite : formulaire de détails
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)

        self.create_table_frame(left_frame)
        self.create_form_frame(right_frame)

        # Zone de configuration du répertoire des images
        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(dir_frame, text="Répertoire des images:").pack(side="left", padx=5)
        ttk.Entry(dir_frame, textvariable=self.images_dir_var, width=50).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(dir_frame, text="...", width=3, command=self.select_images_dir).pack(side="left", padx=5)
        ttk.Button(dir_frame, text="Enregistrer", command=self.save_images_dir).pack(side="left", padx=5)

    def create_table_frame(self, parent):
        """Créer le tableau des prompts"""
        table_frame = ttk.LabelFrame(parent, text="Liste des Prompts")
        table_frame.pack(fill="both", expand=True, padx=(0, 5))

        # Configuration du tableau
        columns = ("name", "image")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=300)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Placement des widgets
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Événements
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Boutons sous le tableau
        buttons_frame = ttk.Frame(table_frame)
        buttons_frame.pack(fill="x", pady=5)
        ttk.Button(buttons_frame, text="Modifier", command=self.edit_prompt).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Supprimer", command=self.delete_prompt).pack(side="left", padx=5)

    def create_form_frame(self, parent):
        """Créer le formulaire de détails permanent"""
        form_frame = ttk.LabelFrame(parent, text="Détails du Prompt")
        form_frame.pack(fill="both", expand=True, padx=(5, 0))

        # Variables pour les champs
        self.name_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.image_var = tk.StringVar()

        # Frame pour les champs
        fields_frame = ttk.Frame(form_frame)
        fields_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Champ Nom
        ttk.Label(fields_frame, text="Nom:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(fields_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        # Champ URL
        ttk.Label(fields_frame, text="URL:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(fields_frame, textvariable=self.url_var, width=40).grid(row=1, column=1, sticky="ew", padx=(10, 0))

        # Champ Image
        ttk.Label(fields_frame, text="Image:").grid(row=2, column=0, sticky="w", pady=5)
        image_frame = ttk.Frame(fields_frame)
        image_frame.grid(row=2, column=1, sticky="ew", padx=(10, 0))
        ttk.Entry(image_frame, textvariable=self.image_var).pack(side="left", fill="x", expand=True)
        ttk.Button(image_frame, text="...", width=3, 
                  command=lambda: self.select_image(self.image_var)).pack(side="left", padx=5)

        # Tableau des valeurs JSON
        ttk.Label(fields_frame, text="Values:").grid(row=3, column=0, sticky="nw", pady=5)
        values_frame = ttk.Frame(fields_frame, height=200)
        values_frame.grid(row=3, column=1, sticky="nsew", padx=(10, 0), pady=5)
        values_frame.pack_propagate(False)

        columns = ("id", "type", "value", "action")
        self.values_tree = ttk.Treeview(values_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.values_tree.heading(col, text=col)
            self.values_tree.column(col, width=150 if col != "action" else 60)

        scrollbar = ttk.Scrollbar(values_frame, orient="vertical", command=self.values_tree.yview)
        self.values_tree.configure(yscrollcommand=scrollbar.set)
        self.values_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Boutons pour les valeurs
        values_btn_frame = ttk.Frame(fields_frame)
        values_btn_frame.grid(row=4, column=1, sticky="ew", padx=(10, 0))
        ttk.Button(values_btn_frame, text="Ajouter ligne", command=self.add_values_row).pack(side="left", padx=5)
        ttk.Button(values_btn_frame, text="Supprimer ligne", command=self.delete_values_row).pack(side="left", padx=5)

        # Tableau du workflow
        ttk.Label(fields_frame, text="Workflow:").grid(row=5, column=0, sticky="nw", pady=5)
        workflow_frame = ttk.Frame(fields_frame, height=200)
        workflow_frame.grid(row=5, column=1, sticky="nsew", padx=(10, 0), pady=5)
        workflow_frame.pack_propagate(False)

        wf_columns = ("id", "class_type", "input", "title")
        self.workflow_tree = ttk.Treeview(workflow_frame, columns=wf_columns, show="headings", height=6)
        for col in wf_columns:
            self.workflow_tree.heading(col, text=col)
            self.workflow_tree.column(col, width=150)

        wf_scrollbar = ttk.Scrollbar(workflow_frame, orient="vertical", command=self.workflow_tree.yview)
        self.workflow_tree.configure(yscrollcommand=wf_scrollbar.set)
        self.workflow_tree.pack(side="left", fill="both", expand=True)
        wf_scrollbar.pack(side="right", fill="y")

        # Configuration de la grille
        fields_frame.grid_columnconfigure(1, weight=1)
        fields_frame.grid_rowconfigure(3, weight=1)
        fields_frame.grid_rowconfigure(5, weight=1)

        # Boutons du formulaire
        form_buttons = ttk.Frame(form_frame)
        form_buttons.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(form_buttons, text="Sauvegarder", command=self.save_prompt).pack(side="left", padx=5)
        ttk.Button(form_buttons, text="Exécuter", command=self.execute_workflow).pack(side="left", padx=5)
        ttk.Button(form_buttons, text="Annuler", command=self.clear_form).pack(side="left", padx=5)
        ttk.Button(form_buttons, text="Nouveau", command=self.new_prompt).pack(side="left", padx=5)

    # Méthodes pour gérer le formulaire permanent
    def on_select(self, event):
        """Gérer la sélection d'une ligne dans le tableau"""
        selection = self.tree.selection()
        if selection:
            prompt_id = selection[0]  # L'ID est stocké comme iid
            self.load_prompt_details(prompt_id)

    def on_double_click(self, event):
        """Gérer le double-clic sur une ligne"""
        self.edit_prompt()

    def delete_prompt(self):
        """Supprimer le prompt sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sélectionner un prompt à supprimer.")
            return
        
        prompt_id = selection[0]
        
        # Récupérer le nom du prompt pour confirmation
        self.cursor.execute("SELECT name FROM prompts WHERE id=?", (prompt_id,))
        row = self.cursor.fetchone()
        if not row:
            return
        
        name = row[0]
        
        # Demander confirmation
        confirm = messagebox.askyesno(
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le prompt '{name}'?"
        )
        
        if confirm:
            # Supprimer de la base de données
            self.cursor.execute("DELETE FROM prompts WHERE id=?", (prompt_id,))
            self.conn.commit()
            
            # Recharger et effacer le formulaire
            self.load_prompts()
            self.clear_form()
            messagebox.showinfo("Succès", f"Prompt '{name}' supprimé avec succès.")

    # Méthodes pour charger et sauvegarder la configuration
    def load_config(self):
        config_path = "data/config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")
        return {"images_dir": "./output"}

    def save_config(self, config):
        os.makedirs("data", exist_ok=True)
        config_path = "data/config.json"
        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def select_images_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.images_dir_var.set(directory)
            self.save_images_dir()

    def save_images_dir(self):
        images_dir = self.images_dir_var.get().strip()
        if not images_dir:
            messagebox.showwarning("Attention", "Le répertoire ne peut pas être vide.")
            return
        self.config["images_dir"] = images_dir
        self.save_config(self.config)
        messagebox.showinfo("Succès", f"Répertoire des images configuré: {images_dir}")

    def load_prompts(self):
        self.tree.delete(*self.tree.get_children())
        self.cursor.execute("SELECT id, name, image FROM prompts")
        for row in self.cursor.fetchall():
            id_, name, image = row
            self.tree.insert("", "end", iid=id_, values=(name, image))

    def on_select(self, event):
        """Gérer la sélection d'une ligne dans le tableau"""
        selection = self.tree.selection()
        if selection:
            prompt_id = selection[0]  # L'ID est stocké comme iid
            self.load_prompt_details(prompt_id)

    def on_double_click(self, event):
        """Gérer le double-clic sur une ligne"""
        self.edit_prompt()

    def open_large_edit_window(self, item_id):
        """Ouvre une fenêtre pour éditer une valeur de type prompt"""
        # Récupérer les données de la ligne sélectionnée
        values = self.values_tree.item(item_id, "values")
        prompt_value = values[2]  # La colonne "value"

        # Créer une fenêtre popup
        popup = tk.Toplevel(self.root)
        popup.title("Édition du prompt")
        popup.geometry("600x400")
        popup.transient(self.root)
        popup.grab_set()

        # Zone de texte pour éditer le prompt
        text_area = tk.Text(popup, wrap="word")
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        text_area.insert("1.0", prompt_value)  # Insérer la valeur actuelle

        # Bouton pour enregistrer les modifications
        def save_changes():
            new_value = text_area.get("1.0", "end-1c").strip()  # Récupérer le texte
            values = list(self.values_tree.item(item_id, "values"))
            values[2] = new_value  # Mettre à jour la colonne "value"
            self.values_tree.item(item_id, values=values)  # Mettre à jour la ligne
            popup.destroy()

        ttk.Button(popup, text="OK", command=save_changes).pack(pady=10)

    def load_prompt_details(self, prompt_id):
        """Charger les détails d'un prompt dans le formulaire"""
        try:
            self.cursor.execute("SELECT name, prompt_values, workflow, image, url FROM prompts WHERE id=?", (prompt_id,))
            row = self.cursor.fetchone()
            if row:
                name, prompt_values, workflow, image, url = row
                self.selected_prompt_id = prompt_id
                self.name_var.set(name)
                self.image_var.set(image or "")
                self.url_var.set(url or "")
                
                # Charger les valeurs dans le tableau
                self.values_tree.delete(*self.values_tree.get_children())
                try:
                    values_dict = json.loads(prompt_values) if prompt_values else {}
                    for k, v in values_dict.items():
                        action = "🔁" if v.get("type", "") == "prompt" else ""
                        self.values_tree.insert("", "end", iid=k, values=(v.get("id", ""), v.get("type", ""), v.get("value", ""), action))
                except Exception:
                    pass
                
                # Charger le workflow
                self.workflow_tree.delete(*self.workflow_tree.get_children())
                try:
                    workflow_dict = json.loads(workflow) if workflow else {}
                    for node_id, node in workflow_dict.items():
                        class_type = node.get("class_type", "")
                        inputs = node.get("inputs", {})
                        input_display = ""
                        if inputs:
                            input_key = next(iter(inputs))
                            input_val = inputs[input_key]
                            input_display = f"{input_key}: {input_val}"
                        title = node.get("_meta", {}).get("title", "")
                        self.workflow_tree.insert("", "end", iid=str(node_id), 
                                                values=(node_id, class_type, input_display, title))
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")

    def clear_form(self):
        """Vider le formulaire"""
        self.selected_prompt_id = None
        self.name_var.set("")
        self.url_var.set("")
        self.image_var.set("")
        self.values_tree.delete(*self.values_tree.get_children())
        self.workflow_tree.delete(*self.workflow_tree.get_children())

    def new_prompt(self):
        """Préparer le formulaire pour un nouveau prompt"""
        self.clear_form()

    def edit_prompt(self):
        """Modifier le prompt sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sélectionner un prompt à modifier.")
            return
        # Le reste est géré par on_select qui a déjà chargé les détails

    def add_values_row(self):
        """Ajouter une ligne au tableau des valeurs"""
        new_id = str(len(self.values_tree.get_children()) + 1)
        self.values_tree.insert("", "end", iid=new_id, values=("", "", "", ""))

    def delete_values_row(self):
        """Supprimer une ligne du tableau des valeurs"""
        selected = self.values_tree.selection()
        for iid in selected:
            self.values_tree.delete(iid)

    def save_prompt(self):
        """Sauvegarder le prompt (nouveau ou modification)"""
        name = self.name_var.get().strip()
        image = self.image_var.get().strip()
        url = self.url_var.get().strip()
        
        if not name:
            messagebox.showerror("Erreur", "Le nom est obligatoire.")
            return
        
        # Récupérer le tableau en dict JSON
        values_dict = {}
        for idx, iid in enumerate(self.values_tree.get_children(), 1):
            vals = self.values_tree.item(iid, "values")
            values_dict[str(idx)] = {
                "id": vals[0],
                "type": vals[1],
                "value": vals[2]
            }
        prompt_values_val = json.dumps(values_dict, ensure_ascii=False)
        
        try:
            if self.selected_prompt_id:
                # Préserver le workflow existant
                self.cursor.execute("SELECT workflow FROM prompts WHERE id=?", (self.selected_prompt_id,))
                workflow = self.cursor.fetchone()[0]
                
                # Mise à jour
                self.cursor.execute(
                    "UPDATE prompts SET name=?, prompt_values=?, image=?, url=? WHERE id=?",
                    (name, prompt_values_val, image, url, self.selected_prompt_id)
                )
                message = "Prompt modifié avec succès"
            else:
                # Nouveau prompt avec workflow vide
                workflow = "{}"
                self.cursor.execute(
                    "INSERT INTO prompts (name, prompt_values, workflow, image, url) VALUES (?, ?, ?, ?, ?)",
                    (name, prompt_values_val, workflow, image, url)
                )
                message = "Nouveau prompt ajouté avec succès"
            
            self.conn.commit()
            messagebox.showinfo("Succès", message)
            self.load_prompts()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def execute_workflow(self):
        """Exécuter le workflow avec comfyui_basic_task"""
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Veuillez sélectionner un prompt.")
            return
        
        try:
            self.cursor.execute("SELECT workflow, prompt_values, name FROM prompts WHERE id=?", (self.selected_prompt_id,))
            row = self.cursor.fetchone()
            if row:
                workflow_json, prompt_values_json, name = row
                
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
                
                # Exécuter le workflow
                messagebox.showinfo("Information", "Lancement du workflow ComfyUI...")
                tsk1 = comfyui_basic_task()
                
                # Ne passer que les noms de fichiers (sans le chemin complet)
                # Pour que run_now puisse les préfixer correctement
                tsk1.run_now(
                    os.path.basename(workflow_file_path),
                    os.path.basename(prompt_values_file_path)
                )
                
                # Nettoyer les fichiers
                try:
                    os.unlink(workflow_file_path)
                    os.unlink(prompt_values_file_path)
                except:
                    pass
                    
                messagebox.showinfo("Succès", "Workflow exécuté avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exécution: {str(e)}")
            print(f"Erreur détaillée: {str(e)}")

    def delete_prompt(self):
        """Supprimer le prompt sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sélectionner un prompt à supprimer.")
            return
        
        prompt_id = selection[0]
        
        # Récupérer le nom du prompt pour confirmation
        self.cursor.execute("SELECT name FROM prompts WHERE id=?", (prompt_id,))
        row = self.cursor.fetchone()
        if not row:
            return
        
        name = row[0]
        
        # Demander confirmation
        confirm = messagebox.askyesno(
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le prompt '{name}'?"
        )
        
        if confirm:
            # Supprimer de la base de données
            self.cursor.execute("DELETE FROM prompts WHERE id=?", (prompt_id,))
            self.conn.commit()
            
            # Recharger et effacer le formulaire
            self.load_prompts()
            self.clear_form()
            messagebox.showinfo("Succès", f"Prompt '{name}' supprimé avec succès.")

    def add_default_basic_prompt(self):
        name = "basic"
        prompt_values = json.dumps({
            "1": {
                "id": "6",
                "type": "prompt",
                "value": "beautiful scenery nature glass bottle landscape, purple galaxy bottle"
            },
            "2": {
                "id": "7",
                "type": "prompt",
                "value": "text, watermark"
            },
            "3": {
                "id": "3",
                "type": "seed",
                "value": 1234567
            },
             "4": {
                "id": "9",
                "type": "SaveImage",
                "filename_prefix": "basic"
            }
        }, ensure_ascii=False)
        workflow = json.dumps({
            "3": {
                "inputs": {
                    "seed": 934966995009374,
                    "steps": 20,
                    "cfg": 8,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "6": {
                "inputs": {"text": "", "speak_and_recognation": True, "clip": ["4", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "positive"}
            },
            "7": {
                "inputs": {"text": "", "speak_and_recognation": True, "clip": ["4", 1]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "negative"}
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            }
        }, ensure_ascii=False)
        image = ""
        url = ""
        self.cursor.execute(
            "INSERT INTO prompts (name, prompt_values, workflow, image, url) VALUES (?, ?, ?, ?, ?)",
            (name, prompt_values, workflow, image, url)
        )
        self.conn.commit()

def main(db_path="g:/tmp/prompts_manager.db"):
    root = tk.Tk()
    app = process_prompts_manager(root, db_path=db_path, mode="dev")  # Passer db_path à l'instance
    root.mainloop()

if __name__ == "__main__":
    load_dotenv()
    db_path = os.getenv("PROMPTS_DB", "g:/tmp/prompts_manager.db")
    main(db_path=db_path)