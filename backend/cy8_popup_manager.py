import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

class cy8_popup_manager:
    """Gestionnaire des popups et formulaires - Version cy8"""
    
    def __init__(self, root, database_manager):
        self.root = root
        self.db_manager = database_manager
    
    def center_window(self, window, width=700, height=520):
        """Centrer une fenêtre sur l'écran"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = ((screen_height - height) // 2) 
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def load_json_to_text(self, text_widget):
        """Charger un fichier JSON dans un widget texte"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                    text_widget.delete("1.0", "end")
                    text_widget.insert("1.0", formatted_json)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le fichier JSON: {e}")
    
    def prompt_form(self, mode="new", prompt_id=None, on_save=None):
        """
        Afficher un formulaire pour ajouter ou modifier un prompt.
        Fonction initiale: prompt_form
        POPUP-ID: CY8-POPUP-001
        """
        popup = tk.Toplevel(self.root)
        popup.title("CY8-POPUP-001 | " + ("Créer un nouveau prompt" if mode == "new" else "Modifier le prompt"))
        popup.transient(self.root)
        popup.grab_set()

        self.center_window(popup, width=700, height=700)

        name_var = tk.StringVar()
        url_var = tk.StringVar()
        prompt_values_var = "{}"
        workflow_var = "{}"
        model_var = tk.StringVar()
        comment_var = tk.StringVar()
        status_var = tk.StringVar(value="new")

        if mode == "edit" and prompt_id:
            data = self.db_manager.get_prompt_by_id(prompt_id)
            if data:
                name, prompt_values, workflow, url, model, comment, status = data
                name_var.set(name or "")
                url_var.set(url or "")
                prompt_values_var = prompt_values or "{}"
                workflow_var = workflow or "{}"
                model_var.set(model or "")
                comment_var.set(comment or "")
                status_var.set(status or "new")
        else:
            default_prompt_values = {
                "1": {"id": "6", "type": "prompt", "value": "beautiful scenery nature glass bottle landscape, purple galaxy bottle"},
                "2": {"id": "7", "type": "prompt", "value": "text, watermark"},
                "3": {"id": "3", "type": "seed", "value": 1234567},
                "4": {"id": "9", "type": "SaveImage", "filename_prefix": "basic"},
            }
            prompt_values_var = json.dumps(default_prompt_values, indent=2, ensure_ascii=False)

        # Interface utilisateur avec style professionnel
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        id_frame = ttk.Frame(main_frame, style='Header.TFrame')
        id_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(id_frame, text="CY8-POPUP-001", font=("TkDefaultFont", 8, "bold"), 
                 foreground="blue").pack(anchor="e")

        # Informations générales
        info_frame = ttk.LabelFrame(main_frame, text="Informations générales", padding="10")
        info_frame.pack(fill="x", pady=(0, 10))

        # Nom
        ttk.Label(info_frame, text="Nom:").grid(row=0, column=0, sticky="w", pady=2)
        name_entry = ttk.Entry(info_frame, textvariable=name_var, width=50)
        name_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=2)

        # URL
        ttk.Label(info_frame, text="URL:").grid(row=1, column=0, sticky="w", pady=2)
        url_entry = ttk.Entry(info_frame, textvariable=url_var, width=50)
        url_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=2)

        # Modèle
        ttk.Label(info_frame, text="Modèle:").grid(row=2, column=0, sticky="w", pady=2)
        model_entry = ttk.Entry(info_frame, textvariable=model_var, width=50)
        model_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=2)

        # Statut
        ttk.Label(info_frame, text="Statut:").grid(row=3, column=0, sticky="w", pady=2)
        status_combo = ttk.Combobox(info_frame, textvariable=status_var, 
                                   values=self.db_manager.status_options, 
                                   state="readonly", width=15)
        status_combo.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=2)

        # Commentaire
        ttk.Label(info_frame, text="Commentaire:").grid(row=4, column=0, sticky="w", pady=2)
        comment_entry = ttk.Entry(info_frame, textvariable=comment_var, width=50)
        comment_entry.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=2)

        info_frame.grid_columnconfigure(1, weight=1)

        # Données JSON
        json_notebook = ttk.Notebook(main_frame)
        json_notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Onglet Prompt Values
        prompt_values_frame = ttk.Frame(json_notebook)
        json_notebook.add(prompt_values_frame, text="Prompt Values")

        ttk.Label(prompt_values_frame, text="Prompt Values (JSON):").pack(anchor="w", pady=5)
        
        pv_text_frame = ttk.Frame(prompt_values_frame)
        pv_text_frame.pack(fill="both", expand=True, pady=5)

        prompt_values_text = tk.Text(pv_text_frame, wrap="word", font=("Consolas", 10))
        pv_scrollbar = ttk.Scrollbar(pv_text_frame, orient="vertical", command=prompt_values_text.yview)
        prompt_values_text.configure(yscrollcommand=pv_scrollbar.set)

        prompt_values_text.pack(side="left", fill="both", expand=True)
        pv_scrollbar.pack(side="right", fill="y")

        # Bouton pour charger JSON
        ttk.Button(prompt_values_frame, text="Charger JSON...", 
                  command=lambda: self.load_json_to_text(prompt_values_text)).pack(anchor="w", pady=5)

        # Onglet Workflow
        workflow_frame = ttk.Frame(json_notebook)
        json_notebook.add(workflow_frame, text="Workflow")

        ttk.Label(workflow_frame, text="Workflow (JSON):").pack(anchor="w", pady=5)
        
        wf_text_frame = ttk.Frame(workflow_frame)
        wf_text_frame.pack(fill="both", expand=True, pady=5)

        workflow_text = tk.Text(wf_text_frame, wrap="word", font=("Consolas", 10))
        wf_scrollbar = ttk.Scrollbar(wf_text_frame, orient="vertical", command=workflow_text.yview)
        workflow_text.configure(yscrollcommand=wf_scrollbar.set)

        workflow_text.pack(side="left", fill="both", expand=True)
        wf_scrollbar.pack(side="right", fill="y")

        # Bouton pour importer JSON
        ttk.Button(workflow_frame, text="...", width=4,
                  command=lambda: self.load_json_to_text(workflow_text)).pack(anchor="w", pady=5)

        # Remplir les textes
        try:
            if prompt_values_var != "{}":
                formatted_json = json.dumps(json.loads(prompt_values_var), indent=2, ensure_ascii=False)
            else:
                formatted_json = prompt_values_var
            prompt_values_text.insert("1.0", formatted_json)
        except json.JSONDecodeError:
            prompt_values_text.insert("1.0", prompt_values_var)

        try:
            if workflow_var != "{}":
                formatted_json = json.dumps(json.loads(workflow_var), indent=2, ensure_ascii=False)
            else:
                formatted_json = workflow_var
            workflow_text.insert("1.0", formatted_json)
        except json.JSONDecodeError:
            workflow_text.insert("1.0", workflow_var)

        # Auto-dériver le modèle si vide
        if not model_var.get():
            auto_model = self.db_manager.derive_model_from_workflow(workflow_var)
            if auto_model:
                model_var.set(auto_model)

        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        def save_prompt():
            name = name_var.get().strip()
            url = url_var.get().strip()
            model_value = model_var.get().strip()
            comment_value = comment_var.get().strip()
            status_value = status_var.get()

            if not name:
                messagebox.showerror("Erreur", "Le nom est obligatoire.")
                return

            # Validation JSON
            try:
                prompt_values_json = prompt_values_text.get("1.0", "end-1c")
                workflow_json = workflow_text.get("1.0", "end-1c")
                
                json.loads(prompt_values_json)  # Valider
                json.loads(workflow_json)       # Valider
            except json.JSONDecodeError as e:
                messagebox.showerror("Erreur JSON", f"JSON invalide: {e}")
                return

            # Auto-dériver le modèle final
            if not model_value:
                model_value = self.db_manager.derive_model_from_workflow(workflow_json)

            try:
                if mode == "edit" and prompt_id:
                    self.db_manager.update_prompt(
                        prompt_id, name, prompt_values_json, workflow_json, 
                        url, model_value, comment_value, status_value
                    )
                    messagebox.showinfo("Succès", "Prompt mis à jour avec succès.")
                else:
                    # Vérifier l'unicité du nom
                    if self.db_manager.prompt_name_exists(name):
                        messagebox.showerror("Erreur", "Ce nom existe déjà.")
                        return
                    
                    new_id = self.db_manager.create_prompt(
                        name, prompt_values_json, workflow_json, 
                        url, model_value, status_value, comment_value
                    )
                    messagebox.showinfo("Succès", f"Prompt créé avec succès (ID: {new_id}).")

                if on_save:
                    on_save()
                popup.destroy()

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

        def cancel():
            popup.destroy()

        ttk.Button(button_frame, text="Sauvegarder", command=save_prompt).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Annuler", command=cancel).pack(side="right")

        # Focus sur le nom
        name_entry.focus_set()
    
    def open_multi_loras_popup(self, item_id, current_value="", on_save=None):
        """
        Popup pour éditer les multiloras
        Fonction initiale: open_multi_loras_popup
        POPUP-ID: CY8-POPUP-002
        """
        popup = tk.Toplevel(self.root)
        popup.title("CY8-POPUP-002 | Gestionnaire Multiloras")
        popup.transient(self.root)
        popup.grab_set()
        
        self.center_window(popup, width=600, height=400)
        
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        id_frame = ttk.Frame(main_frame)
        id_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(id_frame, text="CY8-POPUP-002", font=("TkDefaultFont", 8, "bold"), 
                 foreground="blue").pack(anchor="e")
        
        # Titre
        ttk.Label(main_frame, text="Configuration Multiloras", 
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 10))
        
        # Frame pour le tableau
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Treeview pour afficher les loras
        columns = ("name", "value")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        tree.heading("name", text="Nom du Lora")
        tree.heading("value", text="Valeur")
        tree.column("name", width=300)
        tree.column("value", width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Parser la valeur actuelle
        loras_data = []
        if current_value:
            try:
                # Format: "name1:value1\nname2:value2"
                lines = current_value.split('\\n')
                for line in lines:
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            loras_data.append((parts[0].strip(), parts[1].strip()))
            except:
                pass
        
        # Remplir le tableau
        def refresh_table():
            for item in tree.get_children():
                tree.delete(item)
            for name, value in loras_data:
                tree.insert("", "end", values=(name, value))
        
        refresh_table()
        
        # Frame pour les boutons d'édition
        edit_frame = ttk.Frame(main_frame)
        edit_frame.pack(fill="x", pady=(0, 10))
        
        def add_lora():
            # CY8-POPUP-003: Popup pour ajouter un lora
            add_popup = tk.Toplevel(popup)
            add_popup.title("CY8-POPUP-003 | Ajouter Lora")
            add_popup.transient(popup)
            add_popup.grab_set()
            self.center_window(add_popup, 400, 200)
            
            frame = ttk.Frame(add_popup, padding="10")
            frame.pack(fill="both", expand=True)
            
            # Identifiant popup
            ttk.Label(frame, text="CY8-POPUP-003", font=("TkDefaultFont", 8, "bold"), 
                     foreground="blue").pack(anchor="e", pady=(0, 5))
            
            ttk.Label(frame, text="Nom du Lora:").pack(anchor="w", pady=2)
            name_var = tk.StringVar()
            ttk.Entry(frame, textvariable=name_var, width=40).pack(fill="x", pady=5)
            
            ttk.Label(frame, text="Valeur:").pack(anchor="w", pady=2)
            value_var = tk.StringVar()
            ttk.Entry(frame, textvariable=value_var, width=40).pack(fill="x", pady=5)
            
            def save_lora():
                name = name_var.get().strip()
                value = value_var.get().strip()
                if name and value:
                    loras_data.append((name, value))
                    refresh_table()
                    add_popup.destroy()
                else:
                    messagebox.showerror("Erreur", "Nom et valeur obligatoires.")
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill="x", pady=10)
            ttk.Button(btn_frame, text="Ajouter", command=save_lora).pack(side="right", padx=5)
            ttk.Button(btn_frame, text="Annuler", command=add_popup.destroy).pack(side="right")
        
        def edit_lora():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Sélectionnez un lora à modifier.")
                return
            
            item = selection[0]
            values = tree.item(item, "values")
            current_name, current_value = values
            
            # CY8-POPUP-004: Popup pour éditer
            edit_popup = tk.Toplevel(popup)
            edit_popup.title("CY8-POPUP-004 | Modifier Lora")
            edit_popup.transient(popup)
            edit_popup.grab_set()
            self.center_window(edit_popup, 400, 200)
            
            frame = ttk.Frame(edit_popup, padding="10")
            frame.pack(fill="both", expand=True)
            
            # Identifiant popup
            ttk.Label(frame, text="CY8-POPUP-004", font=("TkDefaultFont", 8, "bold"), 
                     foreground="blue").pack(anchor="e", pady=(0, 5))
            
            ttk.Label(frame, text="Nom du Lora:").pack(anchor="w", pady=2)
            name_var = tk.StringVar(value=current_name)
            ttk.Entry(frame, textvariable=name_var, width=40).pack(fill="x", pady=5)
            
            ttk.Label(frame, text="Valeur:").pack(anchor="w", pady=2)
            value_var = tk.StringVar(value=current_value)
            ttk.Entry(frame, textvariable=value_var, width=40).pack(fill="x", pady=5)
            
            def save_edit():
                new_name = name_var.get().strip()
                new_value = value_var.get().strip()
                if new_name and new_value:
                    # Trouver l'index et remplacer
                    for i, (name, value) in enumerate(loras_data):
                        if name == current_name and value == current_value:
                            loras_data[i] = (new_name, new_value)
                            break
                    refresh_table()
                    edit_popup.destroy()
                else:
                    messagebox.showerror("Erreur", "Nom et valeur obligatoires.")
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill="x", pady=10)
            ttk.Button(btn_frame, text="Sauvegarder", command=save_edit).pack(side="right", padx=5)
            ttk.Button(btn_frame, text="Annuler", command=edit_popup.destroy).pack(side="right")
        
        def delete_lora():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Sélectionnez un lora à supprimer.")
                return
            
            if messagebox.askyesno("Confirmer", "Supprimer le lora sélectionné ?"):
                item = selection[0]
                values = tree.item(item, "values")
                loras_data[:] = [x for x in loras_data if x != values]
                refresh_table()
        
        ttk.Button(edit_frame, text="Ajouter", command=add_lora).pack(side="left", padx=5)
        ttk.Button(edit_frame, text="Modifier", command=edit_lora).pack(side="left", padx=5)
        ttk.Button(edit_frame, text="Supprimer", command=delete_lora).pack(side="left", padx=5)
        
        # Boutons principaux
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        def save_multiloras():
            # Reconstruire la valeur au format original
            result_lines = []
            for name, value in loras_data:
                result_lines.append(f"{name}:{value}")
            result_value = "\\n".join(result_lines)
            
            if on_save:
                on_save(result_value)
            popup.destroy()
        
        def cancel():
            popup.destroy()
        
        ttk.Button(button_frame, text="Sauvegarder", command=save_multiloras).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Annuler", command=cancel).pack(side="right")
    
    def show_output_images_popup(self, images_paths, title="Images générées"):
        """Afficher une popup avec les images de sortie
        POPUP-ID: CY8-POPUP-005
        """
        popup = tk.Toplevel(self.root)
        popup.title(f"CY8-POPUP-005 | {title}")
        popup.transient(self.root)
        popup.grab_set()
        
        self.center_window(popup, width=800, height=600)
        
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        ttk.Label(main_frame, text="CY8-POPUP-005", font=("TkDefaultFont", 8, "bold"), 
                 foreground="blue").pack(anchor="e", pady=(0, 5))
        
        # Canvas avec scrollbar pour les images
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Afficher les images
        if isinstance(images_paths, str):
            images_paths = [p.strip() for p in images_paths.split(',') if p.strip()]
        
        for i, img_path in enumerate(images_paths):
            if os.path.exists(img_path):
                try:
                    # Charger et redimensionner l'image
                    from PIL import Image, ImageTk
                    with Image.open(img_path) as img:
                        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                    
                    # Frame pour chaque image
                    img_frame = ttk.LabelFrame(scrollable_frame, text=f"Image {i+1}: {os.path.basename(img_path)}")
                    img_frame.pack(fill="x", padx=5, pady=5)
                    
                    # Afficher l'image
                    img_label = ttk.Label(img_frame, image=photo)
                    img_label.pack(pady=5)
                    img_label.image = photo  # Garder la référence
                    
                    # Chemin complet
                    ttk.Label(img_frame, text=img_path, font=("TkDefaultFont", 8)).pack()
                    
                except Exception as e:
                    ttk.Label(scrollable_frame, text=f"Erreur lors du chargement de {img_path}: {e}").pack(pady=5)
            else:
                ttk.Label(scrollable_frame, text=f"Image non trouvée: {img_path}").pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bouton fermer
        ttk.Button(main_frame, text="Fermer", command=popup.destroy).pack(pady=10)