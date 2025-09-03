import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import sqlite3
import json

class process_prompts_manager:
    def __init__(self, root, db_path="g:/tmp/prompts_manager.db", mode="init"):
        self.root = root
        self.db_path = db_path
        self.prompts = []
        self.selected_prompt_id = None
        self.mode = mode  # Stocke le mode

        # Charger la configuration
        self.config = self.load_config()
        self.images_dir_var = tk.StringVar(value=self.config.get("images_dir", "./output"))

        self.root.title("Prompts Manager")
        self.root.geometry("1100x600")

        self.init_database(mode)  # Passe le mode à init_database
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
        # Tableau des prompts : seulement name et image
        columns = ("name", "image")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=300)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Boutons d'action
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Ajouter", command=self.open_add_form).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.open_edit_form).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.delete_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Afficher Image", command=self.show_image).pack(side="left", padx=5)
        
        # Zone de configuration du répertoire des images
        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(dir_frame, text="Répertoire des images:").pack(side="left", padx=5)
        ttk.Entry(dir_frame, textvariable=self.images_dir_var, width=50).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(dir_frame, text="...", width=3, command=self.select_images_dir).pack(side="left", padx=5)
        ttk.Button(dir_frame, text="Enregistrer", command=self.save_images_dir).pack(side="left", padx=5)

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
        selected = self.tree.selection()
        self.selected_prompt_id = selected[0] if selected else None

    def open_add_form(self):
        self.open_form()

    def open_edit_form(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à modifier.")
            return
        self.cursor.execute("SELECT name, prompt_values, workflow, image, url FROM prompts WHERE id=?", (self.selected_prompt_id,))
        row = self.cursor.fetchone()
        if row:
            name, prompt_values, workflow, image, url = row
            form = tk.Toplevel(self.root)
            form.title("Modifier un prompt")
            form.geometry("700x800")  # Augmentation de la hauteur
            form.transient(self.root)
            form.grab_set()

            tk.Label(form, text="Nom:").pack(anchor="w", padx=10, pady=5)
            name_var = tk.StringVar(value=name)
            tk.Entry(form, textvariable=name_var).pack(fill="x", padx=10)

            # Tableau des valeurs JSON avec hauteur fixe
            tk.Label(form, text="Values:").pack(anchor="w", padx=10, pady=5)
            values_frame = ttk.Frame(form, height=200)  # Hauteur fixe
            values_frame.pack(fill="x", padx=10, pady=5)
            values_frame.pack_propagate(False)  # Empêche le redimensionnement
            
            # Configuration du tableau avec 4 colonnes dès le départ
            columns = ("id", "type", "value", "action")
            values_tree = ttk.Treeview(values_frame, columns=columns, show="headings", height=6)
            for col in columns:
                values_tree.heading(col, text=col)
                values_tree.column(col, width=150 if col != "action" else 60)
            values_tree.pack(side="left", fill="both", expand=True)

            scrollbar = ttk.Scrollbar(values_frame, orient="vertical", command=values_tree.yview)
            values_tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            # Charger les valeurs JSON (une seule fois)
            try:
                values_dict = json.loads(prompt_values) if prompt_values else {}
            except Exception:
                values_dict = {}
                
            # Remplir le tableau avec le bouton pour les prompts
            for k, v in values_dict.items():
                action = "🔁" if v.get("type", "") == "prompt" else ""
                values_tree.insert("", "end", iid=k, values=(v.get("id", ""), v.get("type", ""), v.get("value", ""), action))

            # Boutons pour ajouter/supprimer une ligne
            btns_row = ttk.Frame(form)
            btns_row.pack(pady=5)
            ttk.Button(btns_row, text="Ajouter ligne", command=lambda: add_row()).pack(side="left", padx=5)
            ttk.Button(btns_row, text="Supprimer ligne", command=lambda: delete_row()).pack(side="left", padx=5)

            def add_row():
                new_id = str(len(values_tree.get_children()) + 1)
                values_tree.insert("", "end", iid=new_id, values=("", "", "", ""))

            def delete_row():
                selected = values_tree.selection()
                for iid in selected:
                    values_tree.delete(iid)

            # Edition inline
            def on_double_click(event):
                item = values_tree.identify_row(event.y)
                col = values_tree.identify_column(event.x)
                if not item or not col or col == "#4":  # Pas d'édition sur la colonne action
                    return
                col_idx = int(col.replace("#", "")) - 1
                x, y, width, height = values_tree.bbox(item, col)
                entry = tk.Entry(values_tree)
                entry.place(x=x, y=y, width=width, height=height)
                entry.insert(0, values_tree.item(item, "values")[col_idx])

                def save_edit(event):
                    vals = list(values_tree.item(item, "values"))
                    vals[col_idx] = entry.get()
                    values_tree.item(item, values=vals)
                    entry.destroy()

                entry.bind("<Return>", save_edit)
                entry.bind("<FocusOut>", lambda e: entry.destroy())
                entry.focus()

            values_tree.bind("<Double-1>", on_double_click)

            # Gestion du clic sur la colonne "action"
            def on_tree_click(event):
                item = values_tree.identify_row(event.y)
                col = values_tree.identify_column(event.x)
                if not item or col != "#4":  # colonne "action"
                    return
                vals = values_tree.item(item, "values")
                if vals[1] == "prompt":
                    # Afficher le texte du prompt dans une popup
                    popup = tk.Toplevel(form)
                    popup.title("Prompt complet")
                    popup.geometry("600x300")
                    txt = tk.Text(popup, wrap="word")
                    txt.pack(fill="both", expand=True)
                    txt.insert("1.0", vals[2])
                    ttk.Button(popup, text="Fermer", command=popup.destroy).pack(pady=5)

            values_tree.bind("<Button-1>", on_tree_click)

            # Tableau des éléments du workflow avec hauteur fixe
            tk.Label(form, text="Éléments du workflow:").pack(anchor="w", padx=10, pady=5)
            workflow_frame = ttk.Frame(form, height=200)  # Hauteur fixe
            workflow_frame.pack(fill="x", padx=10, pady=5)
            workflow_frame.pack_propagate(False)  # Empêche le redimensionnement
            
            wf_columns = ("id", "class_type", "input", "title")
            workflow_tree = ttk.Treeview(workflow_frame, columns=wf_columns, show="headings", height=6)
            for col in wf_columns:
                workflow_tree.heading(col, text=col)
                workflow_tree.column(col, width=150)
            workflow_tree.pack(side="left", fill="both", expand=True)

            wf_scrollbar = ttk.Scrollbar(workflow_frame, orient="vertical", command=workflow_tree.yview)
            workflow_tree.configure(yscroll=wf_scrollbar.set)
            wf_scrollbar.pack(side="right", fill="y")

            # Charger les éléments du workflow JSON ComfyUI API
            try:
                workflow_dict = json.loads(workflow) if workflow else {}
            except Exception:
                workflow_dict = {}

            for node_id, node in workflow_dict.items():
                class_type = node.get("class_type", "")
                inputs = node.get("inputs", {})
                input_key, input_val = ("", "")
                if inputs:
                    input_key = next(iter(inputs))
                    input_val = inputs[input_key]
                    input_display = f"{input_key}: {input_val}"
                else:
                    input_display = ""
                title = node.get("_meta", {}).get("title", "")
                workflow_tree.insert(
                    "", "end", iid=str(node_id),
                    values=(node_id, class_type, input_display, title)
                )

            # Champs Image et URL
            fields_frame = ttk.Frame(form)
            fields_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Label(fields_frame, text="Image:").grid(row=0, column=0, sticky="w", pady=5)
            image_var = tk.StringVar(value=image)
            tk.Entry(fields_frame, textvariable=image_var).grid(row=0, column=1, sticky="ew", padx=5)
            ttk.Button(fields_frame, text="...", command=lambda: self.select_image(image_var), width=3).grid(row=0, column=2)
            
            tk.Label(fields_frame, text="URL:").grid(row=1, column=0, sticky="w", pady=5)
            url_var = tk.StringVar(value=url)
            tk.Entry(fields_frame, textvariable=url_var).grid(row=1, column=1, sticky="ew", padx=5)
            
            fields_frame.columnconfigure(1, weight=1)

            # Boutons sur une ligne
            btns_frame = ttk.Frame(form)
            btns_frame.pack(pady=10)
            
            def save():
                name_val = name_var.get().strip()
                image_val = image_var.get().strip()
                url_val = url_var.get().strip()
                # Récupérer le tableau en dict JSON
                values_dict = {}
                for idx, iid in enumerate(values_tree.get_children(), 1):
                    vals = values_tree.item(iid, "values")
                    values_dict[str(idx)] = {
                        "id": vals[0],
                        "type": vals[1],
                        "value": vals[2]
                    }
                prompt_values_val = json.dumps(values_dict, ensure_ascii=False)
                if not name_val:
                    messagebox.showerror("Erreur", "Le nom est obligatoire.")
                    return
                try:
                    json.loads(prompt_values_val or "{}")
                except Exception as e:
                    messagebox.showerror("Erreur", f"JSON values invalide: {e}")
                    return
                self.cursor.execute(
                    "UPDATE prompts SET name=?, prompt_values=?, image=?, url=? WHERE id=?",
                    (name_val, prompt_values_val, image_val, url_val, self.selected_prompt_id)
                )
                self.conn.commit()
                self.load_prompts()
                form.destroy()
                
            ttk.Button(btns_frame, text="Enregistrer", command=save).pack(side="left", padx=5)
            ttk.Button(btns_frame, text="Annuler", command=form.destroy).pack(side="left", padx=5)

    def open_form(self, name="", prompt_values="", workflow="", image=""):
        form = tk.Toplevel(self.root)
        form.title("Ajouter / Modifier un prompt")
        form.geometry("500x400")
        form.transient(self.root)
        form.grab_set()

        tk.Label(form, text="Nom:").pack(anchor="w", padx=10, pady=5)
        name_var = tk.StringVar(value=name)
        tk.Entry(form, textvariable=name_var).pack(fill="x", padx=10)

        tk.Label(form, text="Values (JSON):").pack(anchor="w", padx=10, pady=5)
        values_var = tk.Text(form, height=4)
        values_var.pack(fill="x", padx=10)
        if prompt_values:
            values_var.insert("1.0", prompt_values)
        # tableau des éléments du workflow
        tk.Label(form, text="Workflow (JSON):").pack(anchor="w", padx=10, pady=5)
        workflow_var = tk.Text(form, height=4)
        workflow_var.pack(fill="x", padx=10)
        if workflow:
            workflow_var.insert("1.0", workflow)

        tk.Label(form, text="Image (chemin complet):").pack(anchor="w", padx=10, pady=5)
        image_var = tk.StringVar(value=image)
        tk.Entry(form, textvariable=image_var).pack(fill="x", padx=10)
        ttk.Button(form, text="Choisir...", command=lambda: self.select_image(image_var)).pack(padx=10, pady=5)

        tk.Label(form, text="URL:").pack(anchor="w", padx=10, pady=5)
        url_var = tk.StringVar()
        tk.Entry(form, textvariable=url_var).pack(fill="x", padx=10)

        def save():
            name_val = name_var.get().strip()
            prompt_values_val = values_var.get("1.0", "end").strip()
            workflow_val = workflow_var.get("1.0", "end").strip()
            image_val = image_var.get().strip()
            url_val = url_var.get().strip()
            if not name_val:
                messagebox.showerror("Erreur", "Le nom est obligatoire.")
                return
            # Vérifier JSON
            try:
                json.loads(prompt_values_val or "{}")
                json.loads(workflow_val or "{}")
            except Exception as e:
                messagebox.showerror("Erreur", f"JSON invalide: {e}")
                return
            if self.selected_prompt_id and form.title().startswith("Modifier"):
                self.cursor.execute(
                    "UPDATE prompts SET name=?, prompt_values=?, workflow=?, image=? WHERE id=?",
                    (name_val, prompt_values_val, workflow_val, image_val, self.selected_prompt_id)
                )
            else:
                self.cursor.execute(
                    "INSERT INTO prompts (name, prompt_values, workflow, image, url) VALUES (?, ?, ?, ?, ?)",
                    (name_val, prompt_values_val, workflow_val, image_val, url_val)
                )
            self.conn.commit()
            self.load_prompts()
            form.destroy()

        # Boutons sur une ligne
        btns_frame = ttk.Frame(form)
        btns_frame.pack(pady=10)
        ttk.Button(btns_frame, text="Enregistrer", command=save).pack(side="left", padx=5)
        ttk.Button(btns_frame, text="Annuler", command=form.destroy).pack(side="left", padx=5)

    def select_image(self, image_var):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp")])
        if path:
            image_var.set(path)

    def delete_prompt(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt à supprimer.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer ce prompt ?"):
            self.cursor.execute("DELETE FROM prompts WHERE id=?", (self.selected_prompt_id,))
            self.conn.commit()
            self.load_prompts()
            self.selected_prompt_id = None

    def show_image(self):
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Sélectionnez un prompt.")
            return
        self.cursor.execute("SELECT image FROM prompts WHERE id=?", (self.selected_prompt_id,))
        row = self.cursor.fetchone()
        if row and row[0]:
            # Utiliser le chemin direct si c'est un chemin absolu
            image_path = row[0]
            # Sinon, utiliser le répertoire configuré
            if not os.path.isabs(image_path):
                image_path = os.path.join(self.images_dir_var.get(), image_path)
            
            if os.path.exists(image_path):
                img_win = tk.Toplevel(self.root)
                img_win.title("Image du prompt")
                img_win.geometry("600x600")
                img = Image.open(image_path)
                img.thumbnail((500, 500))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(img_win, image=photo)
                lbl.image = photo
                lbl.pack(expand=True)
            else:
                messagebox.showerror("Erreur", f"Image introuvable: {image_path}")
        else:
            messagebox.showerror("Erreur", "Aucune image associée.")

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
                "value": "basic"
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

def main():
    root = tk.Tk()
    app = process_prompts_manager(root, mode="dev")  # Mode "dev" pour ne pas recréer la base
    root.mainloop()

if __name__ == "__main__":
    main()