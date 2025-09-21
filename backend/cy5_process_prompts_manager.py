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
import subprocess
import threading

# import platform
# if platform.system() == "Windows":
#     import pythoncom
# else:
#     pythoncom = None


class process_prompts_manager:
    def __init__(self, root, db_path="g:/tmp/prompts_manager.db", mode="init", DirCollecte=None):
        self.root = root
        self.db_path = db_path
        self.prompts = []
        self.selected_prompt_id = None
        self.execution_stack = []  # Pile pour surveiller les workflows
        self.values_data = {}
        self.value_row_counter = 0
        self.status_options = ("new", "test", "ok", "nok")
        self.status_editor = None
        self.status_column_identifier = None
        self.comment_editor = None
        self.comment_column_identifier = None

        # Charger la configuration
        self.config = self.load_config()
        # RÃ©cupÃ©rer la valeur de la variable d'environnement IMAGES_COLLECTE si elle existe
        images_dir_env = DirCollecte
        self.images_dir_var = tk.StringVar(
            value=images_dir_env if images_dir_env else self.config.get("images_dir", "./output")
        )

        self.root.title("Prompts Manager")
        self.root.geometry("1200x700")
        self.root.minsize(1200, 800)

        self.init_database(mode)
        self.setup_ui()
        self.load_prompts()

    def init_database(self, mode="init"):
        """
        Initialise la base de donnÃ©es
        mode="init" : RecrÃ©e la base et ajoute le prompt par dÃ©faut
        mode="dev"  : CrÃ©e la base si elle n'existe pas, n'ajoute pas le prompt par dÃ©faut
        """
        if mode == "init":
            # Mode init: Supprime la base existante et recrÃ©e
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    image TEXT,
                    url TEXT,
                    parent INTEGER,
                    model TEXT,
                    comment TEXT,
                    status TEXT DEFAULT 'new'
                )
            ''')
            self.conn.commit()
            self.ensure_additional_columns()
            self.add_default_basic_prompt()
        else:  # mode == "dev"
            # Mode dev: CrÃ©e la base si elle n'existe pas
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    image TEXT,
                    url TEXT,
                    parent INTEGER,
                    model TEXT,
                    comment TEXT,
                    status TEXT DEFAULT 'new'
                )
            ''')
            self.conn.commit()
            self.ensure_additional_columns()



    def ensure_additional_columns(self):
        """Ensure optional columns exist for backward compatibility."""
        try:
            self.cursor.execute("PRAGMA table_info(prompts)")
            columns = [row[1] for row in self.cursor.fetchall()]
            alterations = []
            status_missing = "status" not in columns
            comment_missing = "comment" not in columns
            if "parent" not in columns:
                alterations.append("ALTER TABLE prompts ADD COLUMN parent INTEGER")
            if "model" not in columns:
                alterations.append("ALTER TABLE prompts ADD COLUMN model TEXT")
            if comment_missing:
                alterations.append("ALTER TABLE prompts ADD COLUMN comment TEXT")
            if status_missing:
                alterations.append("ALTER TABLE prompts ADD COLUMN status TEXT DEFAULT 'new'")
            for statement in alterations:
                self.cursor.execute(statement)
            if alterations:
                self.conn.commit()
            if status_missing:
                try:
                    self.cursor.execute("UPDATE prompts SET status='new' WHERE status IS NULL OR TRIM(status)='' ")
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass
        except sqlite3.OperationalError as exc:
            print(f"Impossible d'ajouter des colonnes optionnelles : {exc}")


    def derive_model_from_workflow(self, workflow_data):
        """Extract model name from workflow JSON content."""
        if not workflow_data:
            return ""
        if isinstance(workflow_data, dict):
            workflow_dict = workflow_data
        else:
            try:
                workflow_dict = json.loads(workflow_data)
            except (TypeError, json.JSONDecodeError):
                return ""
        if not isinstance(workflow_dict, dict):
            return ""

        def normalize(model_name: str) -> str:
            base = os.path.basename(model_name)
            root, _ = os.path.splitext(base)
            return root or base or model_name

        def extract_model_name(raw_value):
            if isinstance(raw_value, str) and raw_value:
                return normalize(raw_value)
            if isinstance(raw_value, (list, tuple)):
                for item in raw_value:
                    if isinstance(item, str) and item:
                        return normalize(item)
            return ""

        for node in workflow_dict.values():
            if not isinstance(node, dict):
                continue
            class_type = node.get("class_type")
            if not isinstance(class_type, str):
                continue
            inputs = node.get("inputs", {})
            if not isinstance(inputs, dict):
                continue
            if class_type == "CheckpointLoaderSimple":
                model_name = extract_model_name(inputs.get("ckpt_name"))
                if model_name:
                    return model_name
            if class_type.lower() == "unetloader":
                model_name = extract_model_name(inputs.get("unet_name"))
                if model_name:
                    return model_name
        return ""

    def setup_ui(self):
        """CrÃ©er l'interface utilisateur avec panneau divisÃ©"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titre
        title_label = ttk.Label(main_frame, text="Gestionnaire de Prompts", font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 5))  # RÃ©duit l'espace sous le titre

        # Affichage du chemin de la base de donnÃ©es
        db_path_label = ttk.Label(main_frame, text=f"Base de donnÃ©es : {self.db_path}", font=("Arial", 10, "italic"))
        db_path_label.pack(pady=(0, 15))  # Ajoute un espace sous le label

        # Boutons d'action
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Actualiser", command=self.load_prompts).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="New", command=self.new_prompt).pack(side=tk.LEFT, padx=5)
        self.edit_button = ttk.Button(btn_frame, text="Edit", command=self.edit_prompt_form)
        self.delete_button = ttk.Button(btn_frame, text="Delete", command=self.delete_prompt)
        self.toggle_selection_buttons(False)

        # PanedWindow pour diviser en deux parties
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Frame gauche : tableau des prompts
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)

        # Frame droite : formulaire de dÃ©tails
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)

        self.create_table_frame(left_frame)
        self.create_form_frame(right_frame)
        # Zone de configuration du rÃ©pertoire des images
        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(dir_frame, text="RÃ©pertoire des images:").pack(side="left", padx=5)
        ttk.Entry(dir_frame, textvariable=self.images_dir_var, width=50).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(dir_frame, text="...", width=3, command=self.select_images_dir).pack(side="left", padx=5)
        ttk.Button(dir_frame, text="Enregistrer", command=self.save_images_dir).pack(side="left", padx=5)

        # Frame pour surveiller la pile des workflows
        stack_frame = ttk.LabelFrame(self.root, text="Pile d'exÃ©cution des workflows")
        stack_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("prompt_id", "status")
        self.execution_stack_tree = ttk.Treeview(stack_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.execution_stack_tree.heading(col, text=col.capitalize())
            self.execution_stack_tree.column(col, width=200)

        scrollbar = ttk.Scrollbar(stack_frame, orient="vertical", command=self.execution_stack_tree.yview)
        self.execution_stack_tree.configure(yscrollcommand=scrollbar.set)
        self.execution_stack_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def toggle_selection_buttons(self, show):
        buttons = [self.edit_button, self.delete_button]
        for button in buttons:
            managed = button.winfo_manager()
            if show and not managed:
                button.pack(side=tk.LEFT, padx=5)
            elif not show and managed:
                button.pack_forget()


    def create_table_frame(self, parent):
        """Creer le tableau des prompts"""
        table_frame = ttk.LabelFrame(parent, text="Liste des Prompts")
        table_frame.pack(fill="both", expand=True, padx=(0, 5))

        columns = ("id", "name", "status", "model", "comment", "parent", "image")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        column_titles = {
            "id": "ID",
            "name": "Name",
            "status": "Status",
            "model": "Model",
            "comment": "Comment",
            "parent": "Parent",
            "image": "Image",
        }
        for col in columns:
            self.tree.heading(col, text=column_titles.get(col, col.capitalize()))

        self.configure_prompts_tree_columns()

        self.status_column_identifier = f"#{columns.index('status') + 1}"
        self.comment_column_identifier = f"#{columns.index('comment') + 1}"

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_prompt)
        self.tree.bind("<Double-1>", self.on_double_click)



    def create_form_frame(self, parent):
        """Creer le formulaire de details permanent"""
        form_frame = ttk.LabelFrame(parent, text="Details du Prompt")
        form_frame.pack(fill="both", expand=True, padx=(5, 0))

        self.name_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.image_var = tk.StringVar()
        self.comment_var = tk.StringVar()

        fields_frame = ttk.Frame(form_frame)
        fields_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(fields_frame, text="Nom:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(fields_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", padx=(10, 0))

        ttk.Label(fields_frame, text="URL:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(fields_frame, textvariable=self.url_var, width=40).grid(row=1, column=1, sticky="ew", padx=(10, 0))

        ttk.Label(fields_frame, text="Image:").grid(row=2, column=0, sticky="w", pady=5)
        image_frame = ttk.Frame(fields_frame)
        image_frame.grid(row=2, column=1, sticky="ew", padx=(10, 0))
        ttk.Entry(image_frame, textvariable=self.image_var).pack(side="left", fill="x", expand=True)
        ttk.Button(image_frame, text="...", width=3, command=lambda: self.select_image(self.image_var)).pack(side="left", padx=5)

        ttk.Label(fields_frame, text="Commentaire:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(fields_frame, textvariable=self.comment_var, width=40).grid(row=3, column=1, sticky="ew", padx=(10, 0))

        ttk.Label(fields_frame, text="Values:").grid(row=4, column=0, sticky="nw", pady=5)
        values_frame = ttk.Frame(fields_frame, height=200)
        values_frame.grid(row=4, column=1, sticky="nsew", padx=(10, 0), pady=5)
        values_frame.pack_propagate(False)

        columns = ("key", "id", "type", "value", "action")
        self.values_tree = ttk.Treeview(values_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.values_tree.heading(col, text=col.capitalize())

        self.configure_values_tree_columns()

        scrollbar = ttk.Scrollbar(values_frame, orient="vertical", command=self.values_tree.yview)
        self.values_tree.configure(yscrollcommand=scrollbar.set)
        self.values_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        values_btn_frame = ttk.Frame(fields_frame)
        values_btn_frame.grid(row=5, column=1, sticky="ew", padx=(10, 0))
        ttk.Button(values_btn_frame, text="Ajouter ligne", command=self.add_values_row).pack(side="left", padx=5)
        ttk.Button(values_btn_frame, text="Supprimer ligne", command=self.delete_values_row).pack(side="left", padx=5)

        ttk.Label(fields_frame, text="Workflow:").grid(row=6, column=0, sticky="nw", pady=5)
        workflow_frame = ttk.Frame(fields_frame, height=200)
        workflow_frame.grid(row=6, column=1, sticky="nsew", padx=(10, 0), pady=5)
        workflow_frame.pack_propagate(False)

        wf_columns = ("id", "class_type", "input", "title")
        self.workflow_tree = ttk.Treeview(workflow_frame, columns=wf_columns, show="headings", height=6)
        for col in wf_columns:
            self.workflow_tree.heading(col, text=col)

        self.configure_workflow_tree_columns()

        wf_scrollbar = ttk.Scrollbar(workflow_frame, orient="vertical", command=self.workflow_tree.yview)
        self.workflow_tree.configure(yscrollcommand=wf_scrollbar.set)
        self.workflow_tree.pack(side="left", fill="both", expand=True)
        wf_scrollbar.pack(side="right", fill="y")

        fields_frame.grid_columnconfigure(1, weight=1)
        fields_frame.grid_rowconfigure(4, weight=1)
        fields_frame.grid_rowconfigure(6, weight=1)

        form_buttons = ttk.Frame(form_frame)
        form_buttons.pack(fill="x", padx=10, pady=10)

        ttk.Button(form_buttons, text="Sauvegarder", command=self.save_prompt).pack(side="left", padx=5)
        self.execute_button = ttk.Button(form_buttons, text="Executer", command=self.execute_workflow)
        self.execute_button.pack(side="left", padx=5)
        self.inherit_button = ttk.Button(form_buttons, text="Heriter", command=self.inherit_prompt)
        self._inherit_button_visible = False
        ttk.Button(form_buttons, text="Annuler", command=self.clear_form).pack(side="left", padx=5)
        ttk.Button(form_buttons, text="Analyser Prompt", command=self.open_prompt_analysis).pack(side="left", padx=5)

        self.update_execution_controls(False)


    def update_execution_controls(self, has_output: bool):
        """Toggle execution-related buttons based on output presence."""
        if not hasattr(self, 'execute_button') or not hasattr(self, 'inherit_button'):
            return

        if has_output:
            self.execute_button.state(['disabled'])
            if not getattr(self, '_inherit_button_visible', False):
                self.inherit_button.pack(side="left", padx=5)
                self._inherit_button_visible = True
            self.inherit_button.state(['!disabled'])
        else:
            self.execute_button.state(['!disabled'])
            if getattr(self, '_inherit_button_visible', False):
                self.inherit_button.pack_forget()
                self._inherit_button_visible = False
            self.inherit_button.state(['disabled'])


    # MÃ©thodes pour gÃ©rer le formulaire permanent

    def on_select_prompt(self, event):
        """Gerer la selection d'une ligne dans le tableau"""
        self._hide_status_editor()
        self._hide_comment_editor()
        selection = self.tree.selection()
        self.toggle_selection_buttons(bool(selection))
        if selection:
            prompt_id = selection[0]
            self.load_prompt_details(prompt_id)


    def on_double_click(self, event):
        """Gerer le double-clic sur une ligne"""
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if self.status_column_identifier and column == self.status_column_identifier and item_id:
            self.show_status_editor(item_id)
            return
        self._hide_status_editor()
        self.edit_prompt()

    def show_status_editor(self, item_id):
        """Afficher un editeur inline pour le statut."""
        if not item_id:
            return
        self._hide_status_editor()
        bbox = self.tree.bbox(item_id, "status")
        if not bbox:
            return
        x, y, width, height = bbox
        editor = ttk.Combobox(self.tree, values=self.status_options, state="readonly")
        current = self.tree.set(item_id, "status")
        if current not in self.status_options:
            current = self.status_options[0]
        editor.set(current or self.status_options[0])
        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()
        editor.bind("<<ComboboxSelected>>", lambda _event: self.commit_status(item_id))
        editor.bind("<Return>", lambda _event: self.commit_status(item_id))
        editor.bind("<Escape>", lambda _event: self._hide_status_editor())
        editor.bind("<FocusOut>", lambda _event: self._hide_status_editor())
        self.status_editor = editor

    def commit_status(self, item_id):
        """Valider la mise a jour du statut dans la base."""
        if not self.status_editor:
            return
        new_status = self.status_editor.get()
        if new_status not in self.status_options:
            new_status = self.status_options[0]
        current_status = self.tree.set(item_id, "status")
        if current_status == new_status:
            self._hide_status_editor()
            return
        try:
            prompt_id = int(item_id)
        except (TypeError, ValueError):
            prompt_id = item_id
        try:
            self.cursor.execute("UPDATE prompts SET status=? WHERE id=?", (new_status, prompt_id))
            self.conn.commit()
            self.tree.set(item_id, "status", new_status)
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible de mettre a jour le statut : {exc}")
        finally:
            self._hide_status_editor()


    def _hide_status_editor(self):
        """Masquer l'editeur de statut s'il est affiche."""
        if self.status_editor is not None:
            try:
                self.status_editor.destroy()
            except tk.TclError:
                pass
            self.status_editor = None

    def show_comment_editor(self, item_id):
        """Afficher un editeur inline pour le commentaire."""
        if not item_id:
            return
        self._hide_comment_editor()
        self._hide_status_editor()
        bbox = self.tree.bbox(item_id, "comment")
        if not bbox:
            return
        x, y, width, height = bbox
        editor = tk.Entry(self.tree)
        current = self.tree.set(item_id, "comment") or ""
        editor.insert(0, current)
        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()
        editor.bind("<Return>", lambda _event: self.commit_comment(item_id))
        editor.bind("<Escape>", lambda _event: self._hide_comment_editor())
        editor.bind("<FocusOut>", lambda _event: self._hide_comment_editor())
        self.comment_editor = editor

    def commit_comment(self, item_id):
        """Valider la mise a jour du commentaire dans la base."""
        if not self.comment_editor:
            return
        new_comment = self.comment_editor.get().strip()
        current_comment = self.tree.set(item_id, "comment")
        if new_comment == current_comment:
            self._hide_comment_editor()
            return
        try:
            prompt_id = int(item_id)
        except (TypeError, ValueError):
            prompt_id = item_id
        try:
            self.cursor.execute("UPDATE prompts SET comment=? WHERE id=?", (new_comment, prompt_id))
            self.conn.commit()
            self.tree.set(item_id, "comment", new_comment)
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible de mettre a jour le commentaire : {exc}")
        finally:
            self._hide_comment_editor()

    def _hide_comment_editor(self):
        """Masquer l'editeur de commentaire s'il est affiche."""
        if self.comment_editor is not None:
            try:
                self.comment_editor.destroy()
            except tk.TclError:
                pass
            self.comment_editor = None


    def on_double_click_values(self, event):
        """Permettre l'edition inline dans le tableau des values"""
        item_id = self.values_tree.identify_row(event.y)
        col = self.values_tree.identify_column(event.x)
        if not item_id:
            return

        # Si c'est un clic sur la colonne "action" (#5)
        if col == "#5":
            values = self.values_tree.item(item_id, "values")
            type_val = values[2]
            if type_val == "prompt":
                self.open_large_edit_window(item_id)
            elif type_val == "image":
                self.open_image_selector_window(item_id)
            return

        if col == "#1":
            return

        col_idx = int(col.replace("#", "")) - 1
        bbox = self.values_tree.bbox(item_id, col)
        if not bbox:
            return
        x, y, width, height = bbox
        entry = tk.Entry(self.values_tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, self.values_tree.item(item_id, "values")[col_idx])

        def save_edit(event):
            new_value = entry.get().strip()
            row_values = list(self.values_tree.item(item_id, "values"))
            row_values[col_idx] = new_value

            data = self.values_data.setdefault(item_id, {})
            if col_idx == 1:
                data["id"] = new_value
            elif col_idx == 2:
                data["type"] = new_value
                # Mettre Ã  jour l'action selon le nouveau type
                if new_value == "prompt":
                    row_values[4] = "edit"
                elif new_value == "image":
                    row_values[4] = "image"
                else:
                    row_values[4] = ""
            elif col_idx == 3:
                data["value"] = new_value
                data.pop("__display_value", None)

            self.values_tree.item(item_id, values=row_values)
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())
        entry.focus()

    def open_large_edit_window(self, item_id):
        """Ouvre une fenetre pour Editer une valeur de type prompt"""
        values = self.values_tree.item(item_id, "values")
        row_data = self.values_data.get(item_id, {})
        prompt_value = row_data.get("value") or values[3]

        popup = tk.Toplevel(self.root)
        popup.title("Ã‰dition du prompt")
        popup.geometry("800x400")  # FenÃªtre plus large
        popup.transient(self.root)
        popup.grab_set()
        
        # Centrer la fenÃªtre
        self.center_window(popup, 800, 400)

        # Frame principal avec padding
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Label d'information
        ttk.Label(main_frame, text="Ã‰dition du prompt:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # Zone de texte avec scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True)

        text_area = tk.Text(text_frame, wrap="word", height=10, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)

        text_area.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # InsÃ©rer le contenu existant
        text_area.insert("1.0", prompt_value)
        text_area.focus_set()

        # Frame pour les boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        def save_changes():
            new_value = text_area.get("1.0", "end-1c").strip()
            row_values = list(self.values_tree.item(item_id, "values"))
            row_values[3] = new_value
            self.values_tree.item(item_id, values=row_values)

            data = self.values_data.setdefault(item_id, {})
            data["value"] = new_value
            data.pop("__display_value", None)
            popup.destroy()

        def cancel_changes():
            popup.destroy()

        # Boutons avec espacement
        ttk.Button(button_frame, text="Sauvegarder", command=save_changes).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Annuler", command=cancel_changes).pack(side="left")

        # Raccourcis clavier
        popup.bind("<Control-Return>", lambda e: save_changes())
        popup.bind("<Escape>", lambda e: cancel_changes())

    def open_image_selector_window(self, item_id):
        """Ouvre une fenÃªtre pour sÃ©lectionner et afficher une image"""
        values = self.values_tree.item(item_id, "values")
        row_data = self.values_data.get(item_id, {})
        current_image_path = row_data.get("value") or values[3]

        popup = tk.Toplevel(self.root)
        popup.title("SÃ©lection d'image")
        popup.geometry("600x500")
        popup.transient(self.root)
        popup.grab_set()
        
        # Centrer la fenÃªtre
        self.center_window(popup, 600, 500)

        # Frame principal avec padding
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Label d'information
        ttk.Label(main_frame, text="SÃ©lection d'image:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

        # Frame pour le chemin de l'image
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(path_frame, text="Chemin:").pack(side="left", padx=(0, 5))
        image_path_var = tk.StringVar(value=current_image_path)
        path_entry = ttk.Entry(path_frame, textvariable=image_path_var)
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                title="SÃ©lectionner une image",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            if file_path:
                image_path_var.set(file_path)
                display_image(file_path)

        ttk.Button(path_frame, text="Parcourir...", command=browse_image).pack(side="left")

        # Frame pour l'affichage de l'image
        image_frame = ttk.LabelFrame(main_frame, text="AperÃ§u de l'image")
        image_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Label pour afficher l'image
        image_label = ttk.Label(image_frame, text="Aucune image sÃ©lectionnÃ©e", anchor="center")
        image_label.pack(fill="both", expand=True, padx=10, pady=10)

        def display_image(image_path):
            """Affiche l'image dans le label"""
            try:
                if os.path.exists(image_path):
                    # Ouvrir et redimensionner l'image
                    pil_image = Image.open(image_path)
                    
                    # Calculer les dimensions pour maintenir le ratio
                    max_width, max_height = 400, 300
                    image_width, image_height = pil_image.size
                    
                    ratio = min(max_width / image_width, max_height / image_height)
                    new_width = int(image_width * ratio)
                    new_height = int(image_height * ratio)
                    
                    pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convertir pour Tkinter
                    tk_image = ImageTk.PhotoImage(pil_image)
                    
                    # Afficher l'image
                    image_label.configure(image=tk_image, text="")
                    image_label.image = tk_image  # Garder une rÃ©fÃ©rence
                    
                    # Afficher les informations de l'image
                    info_text = f"Dimensions: {image_width}x{image_height}\nTaille: {os.path.getsize(image_path)} bytes"
                    ttk.Label(image_frame, text=info_text, font=("Arial", 9)).pack(pady=(5, 0))
                else:
                    image_label.configure(image="", text="Fichier image introuvable")
                    image_label.image = None
            except Exception as e:
                image_label.configure(image="", text=f"Erreur lors du chargement:\n{str(e)}")
                image_label.image = None

        # Afficher l'image actuelle si elle existe
        if current_image_path and os.path.exists(current_image_path):
            display_image(current_image_path)

        # Mettre Ã  jour l'affichage quand le chemin change
        def on_path_change(*args):
            path = image_path_var.get().strip()
            if path and os.path.exists(path):
                display_image(path)
            else:
                image_label.configure(image="", text="Aucune image sÃ©lectionnÃ©e")
                image_label.image = None

        image_path_var.trace('w', on_path_change)

        # Frame pour les boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        def save_image_path():
            new_path = image_path_var.get().strip()
            if new_path and not os.path.exists(new_path):
                messagebox.showwarning("Attention", "Le fichier image spÃ©cifiÃ© n'existe pas.")
                return
            
            # Mettre Ã  jour les donnÃ©es
            row_values = list(self.values_tree.item(item_id, "values"))
            row_values[3] = new_path
            self.values_tree.item(item_id, values=row_values)

            data = self.values_data.setdefault(item_id, {})
            data["value"] = new_path
            data.pop("__display_value", None)
            popup.destroy()

        def cancel_selection():
            popup.destroy()

        # Boutons avec espacement
        ttk.Button(button_frame, text="OK", command=save_image_path).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="Annuler", command=cancel_selection).pack(side="left")

        # Raccourcis clavier
        popup.bind("<Return>", lambda e: save_image_path())
        popup.bind("<Escape>", lambda e: cancel_selection())

    def delete_prompt(self):
        """Supprimer le prompt sÃ©lectionnÃ©"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sÃ©lectionner un prompt Ã  supprimer.")
            return

        prompt_id = selection[0]

        # RÃ©cupÃ©rer le nom du prompt pour confirmation
        self.cursor.execute("SELECT name FROM prompts WHERE id=?", (prompt_id,))
        row = self.cursor.fetchone()
        if not row:
            return

        name = row[0]

        # Demander confirmation
        confirm = messagebox.askyesno(
            "Confirmation",
            f"ÃŠtes-vous sÃ»r de vouloir supprimer le prompt '{name}'?"
        )

        if confirm:
            # Supprimer de la base de donnÃ©es
            self.cursor.execute("DELETE FROM prompts WHERE id=?", (prompt_id,))
            self.conn.commit()

            # Recharger et effacer le formulaire
            self.load_prompts()
            self.clear_form()
            messagebox.showinfo("SuccÃ¨s", f"Prompt '{name}' supprimÃ© avec succÃ¨s.")

    # MÃ©thodes pour charger et sauvegarder la configuration
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
            messagebox.showwarning("Attention", "Le rÃ©pertoire ne peut pas Ãªtre vide.")
            return
        self.config["images_dir"] = images_dir
        self.save_config(self.config)
        messagebox.showinfo("SuccÃ¨s", f"RÃ©pertoire des images configurÃ©: {images_dir}")


    def load_prompts(self):
        self._hide_status_editor()
        self._hide_comment_editor()
        self.tree.delete(*self.tree.get_children())
        self.cursor.execute("SELECT id, name, parent, image, model, workflow, status, comment FROM prompts")
        pending_updates = []
        pending_status = []
        for row in self.cursor.fetchall():
            id_, name, parent, image, model, workflow, status, comment = row
            model_to_use = model or self.derive_model_from_workflow(workflow)
            if model_to_use and model != model_to_use:
                pending_updates.append((model_to_use, id_))
            parent_display = "" if parent is None else str(parent)
            status_value = status if isinstance(status, str) and status else self.status_options[0]
            if status_value != status:
                pending_status.append((status_value, id_))
            comment_value = comment if isinstance(comment, str) else ""
            self.tree.insert("", "end", iid=id_, values=(id_, name, status_value, model_to_use or "", comment_value, parent_display, image))
        if pending_updates:
            self.cursor.executemany("UPDATE prompts SET model=? WHERE id=?", pending_updates)
        if pending_status:
            self.cursor.executemany("UPDATE prompts SET status=? WHERE id=?", pending_status)
        if pending_updates or pending_status:
            self.conn.commit()
        self.toggle_selection_buttons(False)


    def get_workflow_json(self, prompt_id):
        """Utility to fetch workflow JSON for a prompt."""
        try:
            self.cursor.execute("SELECT workflow FROM prompts WHERE id=?", (prompt_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error:
            return None


    def load_prompt_details(self, prompt_id):
        """Charger les details d'un prompt dans le formulaire"""
        has_output_type = False
        try:
            self.cursor.execute("SELECT name, prompt_values, workflow, image, url, model, comment FROM prompts WHERE id=?", (prompt_id,))
            row = self.cursor.fetchone()
            if row:
                name, prompt_values, workflow, image, url, _model, _comment = row
                self.selected_prompt_id = prompt_id
                self.name_var.set(name)
                self.image_var.set(image or "")
                self.url_var.set(url or "")
                self.comment_var.set(_comment or "")

                self.values_tree.delete(*self.values_tree.get_children())
                self.values_data.clear()
                self.value_row_counter = 0
                try:
                    values_dict = json.loads(prompt_values) if prompt_values else {}
                    for k, v in values_dict.items():
                        key = str(k)
                        entry = dict(v) if isinstance(v, dict) else {"value": v}
                        id_val = entry.get("id", "")
                        type_val = entry.get("type", "")
                        normalized_type = type_val.lower() if isinstance(type_val, str) else ""
                        if normalized_type in {"output", "output_image"}:
                            has_output_type = True
                        elif isinstance(key, str) and not normalized_type and key.lower().startswith("output"):
                            has_output_type = True
                        display_value = entry.get("value", "")
                        extras = {ek: ev for ek, ev in entry.items() if ek not in {"id", "type", "value", "__display_value"}}
                        if not display_value and extras:
                            display_value = json.dumps(extras, ensure_ascii=False)
                            entry["__display_value"] = display_value

                        action = ""
                        if type_val == "prompt":
                            action = "edit"
                        elif type_val == "image":
                            action = "image"

                        self.values_tree.insert("", "end", iid=key, values=(key, id_val, type_val, display_value, action))
                        entry.setdefault("id", id_val)
                        entry.setdefault("type", type_val)
                        self.values_data[key] = entry
                        try:
                            self.value_row_counter = max(self.value_row_counter, int(key))
                        except (TypeError, ValueError):
                            pass
                except Exception as e:
                    print(f"Erreur lors du chargement des valeurs : {e}")

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
                        self.workflow_tree.insert("", "end", iid=str(node_id), values=(node_id, class_type, input_display, title))
                except Exception as e:
                    print(f"Erreur lors du chargement du workflow : {e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement : {str(e)}")
        finally:
            self.update_execution_controls(has_output_type)



    def clear_form(self):
        """Vider le formulaire"""
        self.selected_prompt_id = None
        self._hide_status_editor()
        self._hide_comment_editor()
        if hasattr(self, 'tree'):
            self.tree.selection_remove(self.tree.selection())
        if hasattr(self, 'delete_button'):
            self.toggle_selection_buttons(False)
        self.name_var.set("")
        self.url_var.set("")
        self.image_var.set("")
        self.comment_var.set("")
        self.values_tree.delete(*self.values_tree.get_children())
        self.workflow_tree.delete(*self.workflow_tree.get_children())
        self.values_data.clear()
        self.value_row_counter = 0
        self.update_execution_controls(False)


    def new_prompt(self):
        """Ouvre une popup pour saisir les informations d'un nouveau prompt"""
        self.prompt_form(mode="new")


    def prompt_form(self, mode="new", prompt_id=None):
        """Afficher un formulaire pour ajouter ou modifier un prompt."""
        popup = tk.Toplevel(self.root)
        popup.title("Creer un nouveau prompt" if mode == "new" else "Modifier le prompt")
        popup.transient(self.root)
        popup.grab_set()

        self.center_window(popup, width=700, height=520)

        name_var = tk.StringVar()
        url_var = tk.StringVar()
        prompt_values_var = "{}"
        workflow_var = "{}"
        model_var = tk.StringVar()
        comment_var = tk.StringVar()

        if mode == "edit" and prompt_id:
            self.cursor.execute("SELECT name, prompt_values, workflow, url, model, comment FROM prompts WHERE id=?", (prompt_id,))
            row = self.cursor.fetchone()
            if row:
                name, prompt_values, workflow, url, _model, _comment = row
                name_var.set(name)
                url_var.set(url or "")
                prompt_values_var = prompt_values or "{}"
                workflow_var = workflow or "{}"
                model_var.set(_model or "")
                comment_var.set(_comment or "")
        else:
            default_prompt_values = {
                "1": {"id": "6", "type": "prompt", "value": "beautiful scenery nature glass bottle landscape, purple galaxy bottle"},
                "2": {"id": "7", "type": "prompt", "value": "text, watermark"},
                "3": {"id": "3", "type": "seed", "value": 1234567},
                "4": {"id": "9", "type": "SaveImage", "filename_prefix": "basic"},
            }
            prompt_values_var = json.dumps(default_prompt_values, indent=2, ensure_ascii=False)

        if not model_var.get():
            auto_model = self.derive_model_from_workflow(workflow_var)
            if auto_model:
                model_var.set(auto_model)

        ttk.Label(popup, text="Nom:").pack(anchor="w", padx=10, pady=5)
        ttk.Entry(popup, textvariable=name_var, width=60).pack(fill="x", padx=10, pady=5)

        ttk.Label(popup, text="URL:").pack(anchor="w", padx=10, pady=5)
        ttk.Entry(popup, textvariable=url_var, width=60).pack(fill="x", padx=10, pady=5)

        ttk.Label(popup, text="Model:").pack(anchor="w", padx=10, pady=5)
        ttk.Entry(popup, textvariable=model_var, width=60).pack(fill="x", padx=10, pady=5)

        ttk.Label(popup, text="Commentaire:").pack(anchor="w", padx=10, pady=5)
        ttk.Entry(popup, textvariable=comment_var, width=60).pack(fill="x", padx=10, pady=5)

        ttk.Label(popup, text="Prompt Values (JSON):").pack(anchor="w", padx=10, pady=5)
        prompt_values_frame = ttk.Frame(popup)
        prompt_values_frame.pack(fill="x", padx=10, pady=5)

        prompt_values_text = tk.Text(prompt_values_frame, height=5, wrap="word")
        prompt_values_text.pack(side="left", fill="both", expand=True)

        try:
            if prompt_values_var != "{}":
                formatted_json = json.dumps(json.loads(prompt_values_var), indent=2, ensure_ascii=False)
            else:
                formatted_json = prompt_values_var
            prompt_values_text.insert("1.0", formatted_json)
        except json.JSONDecodeError:
            prompt_values_text.insert("1.0", prompt_values_var)

        ttk.Button(prompt_values_frame, text="...", command=lambda: self.load_json_to_text(prompt_values_text)).pack(side="left", padx=5)

        ttk.Label(popup, text="Workflow (JSON):").pack(anchor="w", padx=10, pady=5)
        workflow_frame = ttk.Frame(popup)
        workflow_frame.pack(fill="x", padx=10, pady=5)

        workflow_text = tk.Text(workflow_frame, height=5, wrap="word")
        workflow_text.pack(side="left", fill="both", expand=True)

        try:
            if workflow_var != "{}":
                formatted_json = json.dumps(json.loads(workflow_var), indent=2, ensure_ascii=False)
            else:
                formatted_json = workflow_var
            workflow_text.insert("1.0", formatted_json)
        except json.JSONDecodeError:
            workflow_text.insert("1.0", workflow_var)

        ttk.Button(workflow_frame, text="...", command=lambda: self.load_json_to_text(workflow_text)).pack(side="left", padx=5)

        def save_prompt():
            name = name_var.get().strip()
            url = url_var.get().strip()
            model_value = model_var.get().strip()
            comment_value = comment_var.get().strip()
            prompt_values = prompt_values_text.get("1.0", "end-1c").strip()
            workflow = workflow_text.get("1.0", "end-1c").strip()

            if not name:
                messagebox.showerror("Erreur", "Le champ 'Nom' est obligatoire.")
                return

            try:
                prompt_values_dict = json.loads(prompt_values) if prompt_values else {}
                workflow_dict = json.loads(workflow) if workflow else {}
                derived_model = self.derive_model_from_workflow(workflow_dict)
                model_to_store = model_value or derived_model

                if mode == "new":
                    self.cursor.execute(
                        "INSERT INTO prompts (name, prompt_values, workflow, url, model, status, comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (name, json.dumps(prompt_values_dict, ensure_ascii=False), json.dumps(workflow_dict, ensure_ascii=False), url, model_to_store, self.status_options[0], comment_value),
                    )
                elif mode == "edit" and prompt_id:
                    self.cursor.execute(
                        "UPDATE prompts SET name=?, prompt_values=?, workflow=?, url=?, model=?, comment=? WHERE id=?",
                        (name, json.dumps(prompt_values_dict, ensure_ascii=False), json.dumps(workflow_dict, ensure_ascii=False), url, model_to_store, comment_value, prompt_id),
                    )

                self.conn.commit()
                self.load_prompts()
                popup.destroy()
                messagebox.showinfo("Succes", "Prompt sauvegarde avec succes.")
            except json.JSONDecodeError as e:
                messagebox.showerror("Erreur", f"Les champs JSON contiennent des donnees invalides : {e}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")

        ttk.Button(popup, text="Sauvegarder", command=save_prompt).pack(pady=10)


    def _next_value_key(self, values_dict):
        numeric_keys = []
        for key in values_dict.keys():
            try:
                numeric_keys.append(int(key))
            except (TypeError, ValueError):
                continue
        if numeric_keys:
            return str(max(numeric_keys) + 1)
        candidate = 1
        existing = {str(k) for k in values_dict.keys()}
        while str(candidate) in existing:
            candidate += 1
        return str(candidate)

    def _infer_output_node_id(self, values_dict, workflow_json):
        if isinstance(values_dict, dict):
            for entry in values_dict.values():
                if isinstance(entry, dict):
                    entry_type = entry.get('type')
                    normalized = entry_type.lower() if isinstance(entry_type, str) else ''
                    if normalized == 'output_image' and entry.get('id'):
                        return str(entry.get('id'))
                    if normalized == 'saveimage' and entry.get('id'):
                        return str(entry.get('id'))
        try:
            workflow_dict = json.loads(workflow_json) if workflow_json else {}
            if isinstance(workflow_dict, dict):
                for node_id, node in workflow_dict.items():
                    if isinstance(node, dict) and node.get('class_type') == 'SaveImage':
                        return str(node_id)
        except (TypeError, json.JSONDecodeError):
            pass
        return '9'


    def inherit_prompt(self):
        """Duplicate the selected prompt without output entries."""
        if not self.selected_prompt_id:
            messagebox.showwarning("Information", "Veuillez selectionner un prompt avant d'heriter.")
            return

        selected_id = self.selected_prompt_id
        try:
            prompt_pk = int(selected_id)
        except (TypeError, ValueError):
            prompt_pk = selected_id

        try:
            self.cursor.execute("SELECT name, prompt_values, workflow, image, url, model, comment FROM prompts WHERE id=?", (prompt_pk,))
            row = self.cursor.fetchone()
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible de recuperer le prompt selectionne : {exc}")
            return

        if not row:
            messagebox.showerror("Erreur", "Prompt introuvable.")
            return

        name, prompt_values, workflow, image, url, model, comment = row
        try:
            values_dict = json.loads(prompt_values) if prompt_values else {}
        except (TypeError, json.JSONDecodeError) as exc:
            messagebox.showerror("Erreur", f"Prompt values invalides : {exc}")
            return

        if not isinstance(values_dict, dict):
            values_dict = {}

        cleaned_values = {}
        for key, value in values_dict.items():
            entry_dict = dict(value) if isinstance(value, dict) else None
            entry_type = None
            normalized_type = ""
            if entry_dict is not None:
                entry_dict.pop("__display_value", None)
                entry_type = entry_dict.get("type")
                normalized_type = entry_type.lower() if isinstance(entry_type, str) else ""
                if normalized_type in {"output", "output_image"}:
                    continue
            if (not normalized_type) and isinstance(key, str) and key.lower().startswith("output"):
                continue
            cleaned_values[key] = entry_dict if entry_dict is not None else value

        new_prompt_values = json.dumps(cleaned_values, ensure_ascii=False)
        parent_value = prompt_pk if isinstance(prompt_pk, int) else None
        model_value = model or self.derive_model_from_workflow(workflow)
        new_name = self._build_inherited_name(name)

        try:
            self.cursor.execute(
                "INSERT INTO prompts (name, prompt_values, workflow, image, url, parent, model, status, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_name, new_prompt_values, workflow, image, url, parent_value, model_value, self.status_options[0], comment or ""),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible de creer le prompt herite : {exc}")
            return

        new_prompt_id = self.cursor.lastrowid
        self._refresh_prompt_after_execution(new_prompt_id)


    def _build_inherited_name(self, base_name: str) -> str:
        suffix = " (herite)"
        candidate = f"{base_name}{suffix}"
        index = 2
        while self._prompt_name_exists(candidate):
            candidate = f"{base_name}{suffix} {index}"
            index += 1
        return candidate


    def _prompt_name_exists(self, name: str) -> bool:
        try:
            self.cursor.execute("SELECT 1 FROM prompts WHERE name=? LIMIT 1", (name,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def execute_workflow(self):
        """ExÃ©cuter le workflow avec comfyui_basic_task en arriÃ¨re-plan"""
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Veuillez sÃ©lectionner un prompt.")
            return

        # Ajouter Ã  la pile d'exÃ©cution avec statut "En cours"
        execution_id = f"exec_{int(time.time())}"  # Identifiant unique pour ce job
        self.add_to_execution_stack(execution_id, f"En cours: Prompt #{self.selected_prompt_id}")

        # CrÃ©er un thread pour exÃ©cuter le workflow
        thread = threading.Thread(target=self._execute_workflow_task, 
                             args=(self.selected_prompt_id, execution_id))
        thread.daemon = True  # Permet de terminer le thread si l'application se ferme
        thread.start()

    def _execute_workflow_task(self, prompt_id, execution_id):
        """TÃ¢che d'exÃ©cution du workflow (appelÃ©e dans un thread sÃ©parÃ©)"""
        try:
            # CrÃ©er une nouvelle connexion SQLite dans ce thread
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT workflow, prompt_values, name, image, url, comment FROM prompts WHERE id=?", (prompt_id,))
            row = cursor.fetchone()
            if row:
                workflow_json, prompt_values_json, name, image, url, comment = row

                # Mettre Ã  jour le statut dans la pile d'exÃ©cution
                self.update_execution_stack_status(execution_id, f"PrÃ©paration: {name}")

                # CrÃ©er le rÃ©pertoire data/Workflows s'il n'existe pas
                os.makedirs("data/Workflows", exist_ok=True)

                # GÃ©nÃ©rer des noms de fichiers uniques dans data/Workflows
                timestamp = int(time.time())
                workflow_file_path = f"data/Workflows/{name}_workflow_{timestamp}.json"
                prompt_values_file_path = f"data/Workflows/{name}_values_{timestamp}.json"

                # Ã‰crire les fichiers directement dans data/Workflows
                with open(workflow_file_path, "w", encoding="utf-8") as wf_file:
                    wf_file.write(workflow_json)

                with open(prompt_values_file_path, "w", encoding="utf-8") as pv_file:
                    pv_file.write(prompt_values_json)

                # Mettre Ã  jour le statut
                self.update_execution_stack_status(execution_id, f"ExÃ©cution: {name}")

                # ExÃ©cuter le workflow
                tsk1 = comfyui_basic_task()
                promptId = tsk1.addToQueue(workflow_file_path, prompt_values_file_path)
                print(f"Workflow exÃ©cutÃ©. Fichier de sortie: {promptId}")

                # Mettre Ã  jour le statut avec l'ID du prompt
                self.update_execution_stack_status(execution_id, f"GÃ©nÃ©ration: {promptId}")

                # RÃ©cupÃ©rer les images gÃ©nÃ©rÃ©es
                output_images = tsk1.GetImages(promptId)
                #print(f"Images generees: {output_images}")

                updated_values = getattr(tsk1, 'values', None)
                if output_images:
                    if not isinstance(updated_values, dict):
                        updated_values = {}
                        setattr(tsk1, 'values', updated_values)

                    output_id = self._infer_output_node_id(updated_values, workflow_json)
                    existing_key = None
                    for key, entry in list(updated_values.items()):
                        if isinstance(entry, dict):
                            entry_type = entry.get('type')
                            normalized = entry_type.lower() if isinstance(entry_type, str) else ''
                            if normalized in {'output', 'output_image'}:
                                existing_key = key
                                break

                    if existing_key is None:
                        new_key = self._next_value_key(updated_values)
                        updated_values[new_key] = {'id': output_id, 'type': 'output_image', 'value': output_images}
                    else:
                        entry = updated_values.get(existing_key)
                        if isinstance(entry, dict):
                            entry['id'] = entry.get('id') or output_id
                            entry['type'] = 'output_image'
                            entry['value'] = output_images
                            entry.pop('__display_value', None)
                        else:
                            updated_values[existing_key] = {'id': output_id, 'type': 'output_image', 'value': output_images}

                updated_workflow = getattr(tsk1, 'last_workflow', None)
                try:
                    prompt_pk = int(prompt_id)
                except (TypeError, ValueError):
                    prompt_pk = prompt_id

                new_prompt_values = json.dumps(updated_values, ensure_ascii=False) if updated_values is not None else prompt_values_json
                new_workflow = json.dumps(updated_workflow, ensure_ascii=False) if updated_workflow is not None else workflow_json

                try:
                    model_value = self.derive_model_from_workflow(new_workflow)
                    cursor.execute("UPDATE prompts SET prompt_values=?, workflow=?, image=?, url=?, model=?, comment=? WHERE id=?",
                                   (new_prompt_values, new_workflow, image, url, model_value, comment or "", prompt_pk))
                    conn.commit()
                    self.root.after(0, lambda pid=prompt_pk: self._refresh_prompt_after_execution(pid))
                except Exception as update_err:
                    print(f"Erreur lors de la mise a jour du prompt: {update_err}")

                # Nettoyer les fichiers
                try:
                    os.unlink(workflow_file_path)
                    os.unlink(prompt_values_file_path)
                except:
                    pass

                # Mettre Ã  jour le statut final
                self.update_execution_stack_status(execution_id, f"TerminÃ©: {name} ({promptId})")
        except Exception as e:
            # Mettre Ã  jour le statut en cas d'erreur
            self.update_execution_stack_status(execution_id, f"Erreur: {str(e)}")
            print(f"Erreur lors de l'exÃ©cution: {str(e)}")
        finally:
            # Fermer la connexion SQLite
            conn.close()

    def _refresh_prompt_after_execution(self, prompt_id):
        if not hasattr(self, 'tree'):
            return
        target_id = str(prompt_id)
        previous_selection = self.tree.selection()
        self.load_prompts()
        try:
            self.tree.selection_set(target_id)
            self.tree.focus(target_id)
            self.tree.see(target_id)
            self.toggle_selection_buttons(True)
            self.load_prompt_details(target_id)
            return
        except tk.TclError:
            pass

        if previous_selection:
            fallback_id = previous_selection[0]
            try:
                self.tree.selection_set(fallback_id)
                self.tree.focus(fallback_id)
                self.tree.see(fallback_id)
                self.toggle_selection_buttons(True)
                self.load_prompt_details(fallback_id)
            except tk.TclError:
                self.toggle_selection_buttons(False)
        else:
            self.toggle_selection_buttons(False)

    def update_execution_stack_status(self, execution_id, status):
        """Met Ã  jour le statut d'un workflow dans la pile d'exÃ©cution"""
        for item in self.execution_stack:
            if item["prompt_id"] == execution_id:
                item["status"] = status
                break
        # Mettre Ã  jour l'UI dans le thread principal
        self.root.after(0, self.update_execution_stack_ui)

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
        default_model = self.derive_model_from_workflow(workflow)
        self.cursor.execute(
            "INSERT INTO prompts (name, prompt_values, workflow, image, url, model, status, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, prompt_values, workflow, image, url, default_model, self.status_options[0], "")
        )
        self.conn.commit()

    def open_prompt_analysis(self):
        """Ouvre le programme d'analyse du prompt avec la valeur du prompt positif"""
        if not self.selected_prompt_id:
            messagebox.showerror("Erreur", "Veuillez selectionner un prompt avant l'analyse.")
            return

        prompt_id = str(self.selected_prompt_id)

        load_dotenv()
        db_path = os.getenv("PROMPTS_WORK_DB", "").strip()
        if not db_path:
            messagebox.showerror("Erreur", "La variable PROMPTS_WORK_DB est absente dans le fichier .env.")
            return

        prompt_origin = "COM"

        for item_id in self.values_tree.get_children():
            values = self.values_tree.item(item_id, "values")
            type_val = values[2]
            if type_val == "prompt":
                prompt_value = self.values_data.get(item_id, {}).get("value") or values[3]
                if prompt_value:
                    try:
                        from cy_venv_utils import run_python_script
                        run_python_script('cy2_analyse_prompt', ['--prompt_id', prompt_id, '--prompt_origin', prompt_origin, '--db_path', f'"{db_path}"', '--prompt_text', f'"{prompt_value}"'])
                        return
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Impossible de lancer l'analyse du prompt : {e}")
                        return
        messagebox.showerror("Erreur", "Aucun prompt positif trouve dans le tableau des values.")

    def add_values_row(self):
        """Ajouter une nouvelle ligne dans le tableau des values"""
        popup = tk.Toplevel(self.root)
        popup.title("Ajouter une valeur")
        popup.geometry("400x300")
        popup.transient(self.root)
        popup.grab_set()

        # Centrer la fenÃªtre
        self.center_window(popup, width=400, height=300)

        id_var = tk.StringVar()
        type_var = tk.StringVar()

        ttk.Label(popup, text="ID:").pack(anchor="w", padx=10, pady=5)
        ttk.Entry(popup, textvariable=id_var, width=40).pack(fill="x", padx=10, pady=5)

        ttk.Label(popup, text="Type:").pack(anchor="w", padx=10, pady=5)
        type_combo = ttk.Combobox(popup, textvariable=type_var, values=["prompt", "image", "seed", "SaveImage", "steps", "cfg"], width=37)
        type_combo.pack(fill="x", padx=10, pady=5)

        ttk.Label(popup, text="Valeur:").pack(anchor="w", padx=10, pady=5)
        value_text = tk.Text(popup, height=5, wrap="word")
        value_text.pack(fill="both", expand=True, padx=10, pady=5)

        # InsÃ©rer les valeurs par dÃ©faut Ã  l'ouverture
        default_values = self.get_default_prompt_values()
        default_text = json.dumps(default_values, indent=2, ensure_ascii=False)
        value_text.insert("1.0", default_text)

        def on_type_change(*args):
            """Fonction appelÃ©e quand le type change"""
            current_type = type_var.get().strip()
            if current_type == "prompt":
                # Obtenir les valeurs par dÃ©faut des prompts
                default_values = self.get_default_prompt_values()
                
                # Si c'est le premier prompt, utiliser le prompt positif par dÃ©faut
                prompt_count = sum(1 for item_id in self.values_tree.get_children() 
                                 if self.values_tree.item(item_id, "values")[2] == "prompt")
                
                if prompt_count == 0:
                    # Premier prompt = prompt positif
                    default_text = default_values.get("positive_prompt", "beautiful scenery nature glass bottle landscape, purple galaxy bottle")
                    if not id_var.get().strip():
                        id_var.set("6")  # ID par dÃ©faut du prompt positif
                elif prompt_count == 1:
                    # DeuxiÃ¨me prompt = prompt nÃ©gatif
                    default_text = default_values.get("negative_prompt", "text, watermark")
                    if not id_var.get().strip():
                        id_var.set("7")  # ID par dÃ©faut du prompt nÃ©gatif
                else:
                    # Autres prompts
                    default_text = ""
                
                # Mettre Ã  jour le texte seulement s'il contient les valeurs par dÃ©faut
                current_content = value_text.get("1.0", "end-1c").strip()
                if current_content == json.dumps(default_values, indent=2, ensure_ascii=False) or not current_content:
                    value_text.delete("1.0", "end")
                    value_text.insert("1.0", default_text)

        # Lier l'Ã©vÃ©nement de changement de type
        type_var.trace('w', on_type_change)

        def save_value():
            type_val = type_var.get().strip()
            value_val = value_text.get("1.0", "end-1c").strip()

            if not type_val:
                messagebox.showerror("Erreur", "Le champ Type est obligatoire.")
                return

            self.value_row_counter += 1
            new_key = str(self.value_row_counter)
            id_val = id_var.get().strip() or new_key

            # DÃ©finir l'action selon le type
            action = ""
            if type_val == "prompt":
                action = "edit"
            elif type_val == "image":
                action = "image"

            self.values_tree.insert("", "end", iid=new_key, values=(new_key, id_val, type_val, value_val, action))

            entry = {"id": id_val, "type": type_val}
            if value_val:
                entry["value"] = value_val
            self.values_data[new_key] = entry

            popup.destroy()

        ttk.Button(popup, text="Ajouter", command=save_value).pack(pady=10)

    def get_default_prompt_values(self):
        """Retourne les valeurs par dÃ©faut des prompts depuis add_default_basic_prompt"""
        return {
            "positive_prompt": "beautiful scenery nature glass bottle landscape, purple galaxy bottle",
            "negative_prompt": "text, watermark",
            "seed": 1234567,
            "filename_prefix": "basic"
        }

    def delete_values_row(self):
        """Supprimer la ligne selectionnee du tableau des values"""
        selection = self.values_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez selectionner une ligne a supprimer.")
            return

        for item in selection:
            self.values_tree.delete(item)
            self.values_data.pop(item, None)


    def save_prompt(self):
        """Sauvegarder le prompt courant"""
        if not self.selected_prompt_id:
            messagebox.showwarning("Attention", "Aucun prompt selectionne a sauvegarder.")
            return

        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        image = self.image_var.get().strip()
        comment = self.comment_var.get().strip()

        if not name:
            messagebox.showerror("Erreur", "Le nom est obligatoire.")
            return

        try:
            values_dict = {}
            for item_id in self.values_tree.get_children():
                row_values = list(self.values_tree.item(item_id, "values"))
                data = dict(self.values_data.get(item_id, {}))
                data["id"] = row_values[1]
                data["type"] = row_values[2]

                display_only = data.get("__display_value")
                if "value" in data:
                    if row_values[3]:
                        data["value"] = row_values[3]
                    else:
                        data.pop("value", None)
                elif row_values[3] and row_values[3] != display_only:
                    data["value"] = row_values[3]

                data.pop("__display_value", None)
                values_dict[str(item_id)] = data

            derived_model = self.derive_model_from_workflow(self.get_workflow_json(self.selected_prompt_id))
            self.cursor.execute(
                "UPDATE prompts SET name=?, prompt_values=?, image=?, url=?, model=?, comment=? WHERE id=?",
                (name, json.dumps(values_dict, ensure_ascii=False), image, url, derived_model, comment, self.selected_prompt_id),
            )
            self.conn.commit()

            self.load_prompts()
            messagebox.showinfo("Succes", "Prompt sauvegarde avec succes.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")


    def edit_prompt(self):
        """Ouvre une popup pour Ã©diter le prompt sÃ©lectionnÃ©"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Veuillez sÃ©lectionner un prompt Ã  modifier.")
            return

        prompt_id = selection[0]  # RÃ©cupÃ©rer l'ID du prompt sÃ©lectionnÃ©
        self.prompt_form(mode="edit", prompt_id=prompt_id)

    def select_image(self, var):
        """SÃ©lectionner un fichier image"""
        file_path = filedialog.askopenfilename(
            title="SÃ©lectionner une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            var.set(file_path)

    def edit_prompt_form(self):
        """Ouvre le formulaire de creation/modification de prompt"""
        self.edit_prompt()  # Reutilise la methode `new_prompt` pour ouvrir le formulaire

    def load_json_to_text(self, text_widget):
        """Charger un fichier JSON et insÃ©rer son contenu dans une zone de texte"""
        file_path = filedialog.askopenfilename(
            title="Ouvrir un fichier JSON",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                    formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                    text_widget.delete("1.0", "end")  # Effacer le contenu existant
                    text_widget.insert("1.0", formatted_json)  # InsÃ©rer le JSON formatÃ©
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le fichier JSON : {e}")

    def center_window(self, window, width=600, height=400):
        """Centre une fenÃªtre popup par rapport Ã  la fenÃªtre principale"""
        # RÃ©cupÃ©rer les dimensions de la fenÃªtre principale
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        # Calculer la position pour centrer la fenÃªtre
        x = root_x + (root_width // 2) - (width // 2)
        y = root_y + (root_height // 2) - (height // 2)

        # Appliquer la gÃ©omÃ©trie
        window.geometry(f"{width}x{height}+{x}+{y}")

    def add_to_execution_stack(self, prompt_id, status):
        """Ajouter un workflow Ã  la pile d'exÃ©cution"""
        # VÃ©rifier si l'ID est dÃ©jÃ  dans la pile
        for item in self.execution_stack:
            if item["prompt_id"] == prompt_id:
                item["status"] = status
                self.root.after(0, self.update_execution_stack_ui)
                return
            
        # Sinon, ajouter un nouvel Ã©lÃ©ment
        self.execution_stack.append({"prompt_id": prompt_id, "status": status})
        self.root.after(0, self.update_execution_stack_ui)  # Mettre Ã  jour l'UI dans le thread principal
    
    def update_execution_stack_ui(self):
        """Mettre Ã  jour l'affichage de la pile d'exÃ©cution"""
        self.execution_stack_tree.delete(*self.execution_stack_tree.get_children())
        for item in self.execution_stack:
            self.execution_stack_tree.insert("", "end", values=(item["prompt_id"], item["status"]))

    def configure_prompts_tree_columns(self):
        """Configure column display options for le tableau des prompts."""
        if not hasattr(self, "tree"):
            return
        column_config = {
            "id": {"width": 80, "minwidth": 60, "stretch": False},
            "name": {"width": 220, "minwidth": 120, "stretch": True},
            "status": {"width": 110, "minwidth": 90, "stretch": False},
            "model": {"width": 180, "minwidth": 140, "stretch": True},
            "comment": {"width": 240, "minwidth": 160, "stretch": True},
            "parent": {"width": 120, "minwidth": 90, "stretch": False},
            "image": {"width": 220, "minwidth": 140, "stretch": True},
        }
        for col_name, config in column_config.items():
            if col_name in self.tree["columns"]:
                self.tree.column(
                    col_name,
                    width=config.get("width", 120),
                    minwidth=config.get("minwidth", 40),
                    stretch=config.get("stretch", True),
                )

    def configure_values_tree_columns(self):
        """Configure les tailles des colonnes du tableau values"""
        # Configuration personnalisÃ©e des colonnes
        column_config = {
            "key": {"width": 20, "minwidth": 20, "stretch": False},
            "id": {"width": 20, "minwidth": 20, "stretch": True},
            "type": {"width": 80, "minwidth": 60, "stretch": False},
            "value": {"width": 200, "minwidth": 250, "stretch": True},
            "action": {"width": 50, "minwidth": 60, "stretch": False}
        }
        
        for col_name, config in column_config.items():
            self.values_tree.column(
                col_name, 
                width=config["width"],
                minwidth=config["minwidth"],
                stretch=config.get("stretch", True)
            )

    def configure_workflow_tree_columns(self):
        """Configure les tailles des colonnes du tableau workflow"""
        # Configuration personnalisÃ©e des colonnes
        column_config = {
            "id": {"width": 20, "minwidth": 50, "stretch": False},
            "class_type": {"width": 150, "minwidth": 120, "stretch": True},
            "input": {"width": 200, "minwidth": 150, "stretch": True},
            "title": {"width": 120, "minwidth": 100, "stretch": True}
        }
        
        for col_name, config in column_config.items():
            self.workflow_tree.column(
                col_name, 
                width=config["width"],
                minwidth=config["minwidth"],
                stretch=config.get("stretch", True)
            )

def main(db_path="g:/tmp/prompts_manager.db", DirCollecte=None):
    root = tk.Tk()
    app = process_prompts_manager(root, db_path=db_path, mode="dev", DirCollecte=DirCollecte)  # Passer DirCollecte
    root.mainloop()

if __name__ == "__main__":
    load_dotenv()
    db_path = os.getenv("PROMPTS_DB", "g:/tmp/prompts_manager.db")
    images_dir_env = os.getenv("IMAGES_COLLECTE", "./output")
    main(db_path=db_path, DirCollecte=images_dir_env)

