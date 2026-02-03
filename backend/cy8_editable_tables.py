import tkinter as tk
from tkinter import ttk, messagebox
import json

class cy8_editable_tables:
    """Gestionnaire des tableaux éditables pour prompt_values et workflow - Version cy8"""
    
    def __init__(self, root, popup_manager):
        self.root = root
        self.popup_manager = popup_manager
        self.values_data = {}
        self.workflow_data = {}
        self.save_callback = None  # Callback pour la sauvegarde
    def edit_inputs_popup(self, node_id, inputs_str, workflow_tree, on_change_callback):
        """
        Popup pour éditer les inputs du workflow
        1.2.2) Clic sur inputs -> tableau éditable attribut:valeur
        POPUP-ID: CY8-POPUP-007
        """
        popup = tk.Toplevel(self.root)
        popup.title(f"CY8-POPUP-007 | Édition Inputs - Node {node_id}")
        
        
    def create_prompt_values_table(self, parent_frame, on_change_callback=None):
        """
        Créer le tableau pour les prompt_values
        Fonction initiale: partie de load_prompt_details
        """
        # Frame principal pour les prompt values
        values_frame = ttk.LabelFrame(parent_frame, text="Prompt Values", padding="5")
        
        # Treeview pour les values
        columns = ("key", "id", "type", "value", "action")
        values_tree = ttk.Treeview(values_frame, columns=columns, show="headings", height=8)
        
        # Configuration des colonnes
        values_tree.heading("key", text="Clé")
        values_tree.heading("id", text="ID")
        values_tree.heading("type", text="Type")
        values_tree.heading("value", text="Valeur")
        values_tree.heading("action", text="Action")
        
        values_tree.column("key", width=60)
        values_tree.column("id", width=60)
        values_tree.column("type", width=100)
        values_tree.column("value", width=300)
        values_tree.column("action", width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(values_frame, orient="vertical", command=values_tree.yview)
        h_scrollbar = ttk.Scrollbar(values_frame, orient="horizontal", command=values_tree.xview)
        values_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement
        values_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        values_frame.grid_rowconfigure(0, weight=1)
        values_frame.grid_columnconfigure(0, weight=1)
        
        # Boutons d'action
        btn_frame = ttk.Frame(values_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Button(btn_frame, text="Ajouter", 
                  command=lambda: self.add_prompt_value(values_tree, on_change_callback)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer", 
                  command=lambda: self.delete_prompt_value(values_tree, on_change_callback)).pack(side="left", padx=5)
        
        # Bouton de sauvegarde
        ttk.Button(btn_frame, text="💾 Sauvegarder", 
                  command=lambda: self._save_current_prompt(on_change_callback),
                  style='Accent.TButton').pack(side="right", padx=5)
        
        # Événements
        values_tree.bind("<Double-1>", lambda e: self.on_values_double_click(e, values_tree, on_change_callback))
        
        return values_frame, values_tree
    
    def create_workflow_table(self, parent_frame, on_change_callback=None):
        """
        Créer le tableau pour le workflow
        Format des données workflow comme spécifié
        """
        # Frame principal pour le workflow
        workflow_frame = ttk.LabelFrame(parent_frame, text="Workflow", padding="5")
        
        # Treeview pour le workflow
        columns = ("id", "class_type", "inputs", "title")
        workflow_tree = ttk.Treeview(workflow_frame, columns=columns, show="headings", height=8)
        
        # Configuration des colonnes
        workflow_tree.heading("id", text="ID")
        workflow_tree.heading("class_type", text="Class Type")
        workflow_tree.heading("inputs", text="Inputs")
        workflow_tree.heading("title", text="Title")
        
        workflow_tree.column("id", width=60)
        workflow_tree.column("class_type", width=150)
        workflow_tree.column("inputs", width=300)
        workflow_tree.column("title", width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(workflow_frame, orient="vertical", command=workflow_tree.yview)
        h_scrollbar = ttk.Scrollbar(workflow_frame, orient="horizontal", command=workflow_tree.xview)
        workflow_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Placement
        workflow_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        workflow_frame.grid_rowconfigure(0, weight=1)
        workflow_frame.grid_columnconfigure(0, weight=1)
        
        # Boutons d'action
        btn_frame = ttk.Frame(workflow_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Button(btn_frame, text="Ajouter nœud", 
                  command=lambda: self.add_workflow_node(workflow_tree, on_change_callback)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer", 
                  command=lambda: self.delete_workflow_node(workflow_tree, on_change_callback)).pack(side="left", padx=5)
        
        # Bouton de sauvegarde
        ttk.Button(btn_frame, text="💾 Sauvegarder", 
                  command=lambda: self._save_current_prompt(on_change_callback),
                  style='Accent.TButton').pack(side="right", padx=5)
        
        # Événements
        workflow_tree.bind("<Double-1>", lambda e: self.on_workflow_double_click(e, workflow_tree, on_change_callback))
        
        return workflow_frame, workflow_tree
    
    def load_prompt_values_data(self, values_tree, prompt_values_json):
        """Charger les données prompt_values dans le tableau"""
        self.values_data.clear()
        values_tree.delete(*values_tree.get_children())
        self.value_row_counter = 0
        
        try:
            values_dict = json.loads(prompt_values_json) if prompt_values_json else {}
            for k, v in values_dict.items():
                key = str(k)
                entry = dict(v) if isinstance(v, dict) else {"value": v}
                
                id_val = entry.get("id", "")
                type_val = entry.get("type", "")
                display_value = entry.get("value", "")
                
                # Gérer les données extra
                extras = {ek: ev for ek, ev in entry.items() if ek not in {"id", "type", "value", "__display_value"}}
                if not display_value and extras:
                    display_value = json.dumps(extras, ensure_ascii=False)
                    entry["__display_value"] = display_value
                
                # Déterminer l'action
                action = ""
                if type_val == "prompt":
                    action = "edit"
                elif type_val == "image" or type_val == "output_image":
                    action = "image"
                elif type_val == "multiLoras":
                    action = "multiLoras"
                
                values_tree.insert("", "end", iid=key, values=(key, id_val, type_val, display_value, action))
                self.values_data[key] = entry
                
                # Mettre à jour le compteur
                try:
                    if int(key) > self.value_row_counter:
                        self.value_row_counter = int(key)
                except:
                    pass
                    
        except json.JSONDecodeError as e:
            messagebox.showerror("Erreur", f"JSON prompt_values invalide: {e}")
    
    def load_workflow_data(self, workflow_tree, workflow_json):
        """Charger les données workflow dans le tableau"""
        self.workflow_data.clear()
        workflow_tree.delete(*workflow_tree.get_children())
        
        try:
            workflow_dict = json.loads(workflow_json) if workflow_json else {}
            for node_id, node_data in workflow_dict.items():
                if isinstance(node_data, dict):
                    class_type = node_data.get("class_type", "")
                    inputs = node_data.get("inputs", {})
                    title = node_data.get("_meta", {}).get("title", "")
                    
                    # Convertir inputs en string pour l'affichage
                    inputs_str = json.dumps(inputs, ensure_ascii=False) if inputs else "{}"
                    
                    workflow_tree.insert("", "end", iid=node_id, 
                                       values=(node_id, class_type, inputs_str, title))
                    self.workflow_data[node_id] = node_data
                    
        except json.JSONDecodeError as e:
            messagebox.showerror("Erreur", f"JSON workflow invalide: {e}")
    
    def on_values_double_click(self, event, values_tree, on_change_callback):
        """
        Gérer le double-clic sur le tableau des values
        1.1.0) Édition dans le tableau
        1.1.1) Images output_image
        1.1.2) Multiloras
        1.1.3) Autres types avec popup
        """
        item = values_tree.selection()[0] if values_tree.selection() else None
        if not item:
            return
        
        region = values_tree.identify("region", event.x, event.y)
        column = values_tree.identify_column(event.x)
        
        if region == "cell":
            values = values_tree.item(item, "values")
            key, id_val, type_val, display_value, action = values
            
            # Édition inline pour les colonnes simples
            if column in ["#1", "#2", "#3"]:  # key, id, type
                self.edit_cell_inline(values_tree, item, column, on_change_callback)
            
            # Actions spéciales pour la colonne value ou action
            elif column in ["#4", "#5"]:  # value, action
                if type_val == "output_image":
                    # 1.1.1) Afficher les images
                    self.show_output_images(display_value)
                elif type_val == "multiLoras":
                    # 1.1.2) Popup multiloras
                    self.edit_multiloras(item, display_value, values_tree, on_change_callback)
                else:
                    # 1.1.3) Popup d'édition plus grande
                    self.edit_value_popup(item, key, type_val, display_value, values_tree, on_change_callback)
    
    def on_workflow_double_click(self, event, workflow_tree, on_change_callback):
        """Gérer le double-clic sur le tableau workflow"""
        item = workflow_tree.selection()[0] if workflow_tree.selection() else None
        if not item:
            return
        
        region = workflow_tree.identify("region", event.x, event.y)
        column = workflow_tree.identify_column(event.x)
        
        if region == "cell":
            values = workflow_tree.item(item, "values")
            node_id, class_type, inputs_str, title = values
            
            # Édition inline pour les colonnes simples
            if column in ["#1", "#2", "#4"]:  # id, class_type, title
                self.edit_cell_inline(workflow_tree, item, column, on_change_callback)
            
            # Édition des inputs avec tableau
            elif column == "#3":  # inputs
                self.edit_inputs_popup(node_id, inputs_str, workflow_tree, on_change_callback)
    
    def edit_cell_inline(self, tree, item, column, on_change_callback):
        """Édition inline d'une cellule"""
        values = tree.item(item, "values")
        col_index = int(column[1:]) - 1  # Convertir #1 -> 0, #2 -> 1, etc.
        current_value = values[col_index]
        
        # Créer un entry temporaire
        bbox = tree.bbox(item, column)
        if not bbox:
            return
        
        entry = ttk.Entry(tree)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.insert(0, current_value)
        entry.select_range(0, "end")
        entry.focus_set()
        
        def save_edit(event=None):
            new_value = entry.get()
            new_values = list(values)
            new_values[col_index] = new_value
            tree.item(item, values=new_values)
            
            # Mettre à jour les données
            if tree == getattr(self, '_current_values_tree', None):
                self.update_values_data(item, col_index, new_value)
            elif tree == getattr(self, '_current_workflow_tree', None):
                self.update_workflow_data(item, col_index, new_value)
            
            entry.destroy()
            if on_change_callback:
                on_change_callback()
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
    
    def show_output_images(self, images_value):
        """Afficher les images de sortie - 1.1.1)"""
        if not images_value:
            messagebox.showinfo("Info", "Aucune image à afficher.")
            return
        
        # Parser les chemins d'images
        if isinstance(images_value, str):
            if images_value.startswith('[') and images_value.endswith(']'):
                try:
                    images_paths = json.loads(images_value)
                except:
                    images_paths = [images_value]
            else:
                images_paths = [p.strip() for p in images_value.split(',') if p.strip()]
        else:
            images_paths = [images_value] if images_value else []
        
        self.popup_manager.show_output_images_popup(images_paths, "Images de sortie")
    
    def edit_multiloras(self, item_id, current_value, tree, on_change_callback):
        """Éditer les multiloras - 1.1.2)"""
        def on_save(new_value):
            # Mettre à jour l'affichage
            current_values = list(tree.item(item_id, "values"))
            current_values[3] = new_value  # Colonne value
            tree.item(item_id, values=current_values)
            
            # Mettre à jour les données
            if item_id in self.values_data:
                self.values_data[item_id]["value"] = new_value
            
            if on_change_callback:
                on_change_callback()
        
        self.popup_manager.open_multi_loras_popup(item_id, current_value, on_save)
    
    def edit_value_popup(self, item_id, key, type_val, current_value, tree, on_change_callback):
        """Popup d'édition plus grande - 1.1.3)
        POPUP-ID: CY8-POPUP-006
        """
        popup = tk.Toplevel(self.root)
        popup.title(f"CY8-POPUP-006 | Édition - {key} ({type_val})")
        popup.transient(self.root)
        popup.grab_set()
        
        self.popup_manager.center_window(popup, 500, 600)
        
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        ttk.Label(main_frame, text="CY8-POPUP-006", font=("TkDefaultFont", 8, "bold"), 
                 foreground="blue").pack(anchor="e", pady=(0, 5))
        
        # Informations
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Clé: {key}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Type: {type_val}").pack(anchor="w")
        
        # Zone d'édition
        ttk.Label(main_frame, text="Valeur:").pack(anchor="w", pady=(10, 2))
        
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        text_widget = tk.Text(text_frame, wrap="word", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Insérer la valeur actuelle
        text_widget.insert("1.0", current_value)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        def save_value():
            new_value = text_widget.get("1.0", "end-1c")
            
            # Mettre à jour l'affichage
            current_values = list(tree.item(item_id, "values"))
            current_values[3] = new_value  # Colonne value
            tree.item(item_id, values=current_values)
            
            # Mettre à jour les données
            if item_id in self.values_data:
                self.values_data[item_id]["value"] = new_value
            
            if on_change_callback:
                on_change_callback()
            
            popup.destroy()
        
        ttk.Button(button_frame, text="Sauvegarder", command=save_value).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Annuler", command=popup.destroy).pack(side="right")
        
        text_widget.focus_set()
    
    def edit_inputs_popup(self, node_id, inputs_str, workflow_tree, on_change_callback):
        """
        Popup pour éditer les inputs du workflow
        1.2.2) Tableau éditable attribut : valeur
        """
        popup = tk.Toplevel(self.root)
        popup.title(f"Édition Inputs - Node {node_id}")
        popup.transient(self.root)
        popup.grab_set()
        
        self.popup_manager.center_window(popup, 600, 600)
        
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Identifiant popup en haut
        ttk.Label(main_frame, text="CY8-POPUP-007", font=("TkDefaultFont", 8, "bold"), 
            foreground="blue").pack(anchor="e", pady=(0, 5))
        
        # Titre
        ttk.Label(main_frame, text=f"Inputs du nœud {node_id}", 
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 10))
        
        # Tableau attribut : valeur
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        columns = ("attribute", "separator", "value")
        inputs_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        inputs_tree.heading("attribute", text="Attribut")
        inputs_tree.heading("separator", text="")
        inputs_tree.heading("value", text="Valeur")
        
        inputs_tree.column("attribute", width=150)
        inputs_tree.column("separator", width=20)
        inputs_tree.column("value", width=300)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=inputs_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=inputs_tree.xview)
        inputs_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        inputs_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Parser et charger les inputs
        inputs_data = {}
        try:
            inputs_data = json.loads(inputs_str) if inputs_str else {}
        except json.JSONDecodeError:
            inputs_data = {}
        
        def refresh_inputs_table():
            for item in inputs_tree.get_children():
                inputs_tree.delete(item)
            
            for attr, value in inputs_data.items():
                display_value = json.dumps(value, ensure_ascii=False) if not isinstance(value, (str, int, float, bool)) else str(value)
                inputs_tree.insert("", "end", iid=attr, values=(attr, ":", display_value))
        
        refresh_inputs_table()
        
        # Boutons d'édition
        edit_frame = ttk.Frame(main_frame)
        edit_frame.pack(fill="x", pady=(0, 10))
        
        def add_input():
            from tkinter import simpledialog
            attr_name = simpledialog.askstring("Nouvel attribut", "Nom de l'attribut:")
            if attr_name:
                inputs_data[attr_name] = ""
                refresh_inputs_table()
        
        def edit_input():
            selection = inputs_tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Sélectionnez un attribut à modifier.")
                return
            
            attr = selection[0]
            current_value = inputs_data.get(attr, "")
            
            # CY8-POPUP-008: Popup d'édition de valeur
            edit_popup = tk.Toplevel(popup)
            edit_popup.title(f"CY8-POPUP-008 | Éditer {attr}")
            edit_popup.transient(popup)
            edit_popup.grab_set()
            self.popup_manager.center_window(edit_popup, 400, 600)
            
            frame = ttk.Frame(edit_popup, padding="10")
            frame.pack(fill="both", expand=True)
            
            # Identifiant popup
            ttk.Label(frame, text="CY8-POPUP-008", font=("TkDefaultFont", 8, "bold"), 
                     foreground="blue").pack(anchor="e", pady=(0, 5))
            
            ttk.Label(frame, text=f"Attribut: {attr}").pack(anchor="w", pady=5)
            ttk.Label(frame, text="Valeur:").pack(anchor="w", pady=2)
            
            text_widget = tk.Text(frame, height=8, wrap="word")
            text_widget.pack(fill="both", expand=True, pady=5)
            
            # Insérer la valeur actuelle
            if isinstance(current_value, (dict, list)):
                text_widget.insert("1.0", json.dumps(current_value, indent=2, ensure_ascii=False))
            else:
                text_widget.insert("1.0", str(current_value))
            
            def save_input():
                new_value_str = text_widget.get("1.0", "end-1c")
                
                # Essayer de parser comme JSON
                try:
                    new_value = json.loads(new_value_str)
                except json.JSONDecodeError:
                    # Si ce n'est pas du JSON, garder comme string
                    # Sauf pour les nombres et booleans
                    if new_value_str.lower() in ['true', 'false']:
                        new_value = new_value_str.lower() == 'true'
                    elif new_value_str.isdigit():
                        new_value = int(new_value_str)
                    else:
                        try:
                            new_value = float(new_value_str)
                        except ValueError:
                            new_value = new_value_str
                
                inputs_data[attr] = new_value
                refresh_inputs_table()
                edit_popup.destroy()
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill="x", pady=10)
            ttk.Button(btn_frame, text="Sauvegarder", command=save_input).pack(side="right", padx=5)
            ttk.Button(btn_frame, text="Annuler", command=edit_popup.destroy).pack(side="right")
        
        def delete_input():
            selection = inputs_tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Sélectionnez un attribut à supprimer.")
                return
            
            if messagebox.askyesno("Confirmer", "Supprimer cet attribut ?"):
                attr = selection[0]
                if attr in inputs_data:
                    del inputs_data[attr]
                refresh_inputs_table()
        
        ttk.Button(edit_frame, text="Ajouter", command=add_input).pack(side="left", padx=5)
        ttk.Button(edit_frame, text="Modifier", command=edit_input).pack(side="left", padx=5)
        ttk.Button(edit_frame, text="Supprimer", command=delete_input).pack(side="left", padx=5)
        
        # Double-clic pour éditer
        inputs_tree.bind("<Double-1>", lambda e: edit_input())
        
        # Boutons principaux
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        def save_inputs():
            # Mettre à jour les données workflow
            if node_id in self.workflow_data:
                self.workflow_data[node_id]["inputs"] = inputs_data
            
            # Mettre à jour l'affichage dans le tableau principal
            new_inputs_str = json.dumps(inputs_data, ensure_ascii=False)
            current_values = list(workflow_tree.item(node_id, "values"))
            current_values[2] = new_inputs_str  # Colonne inputs
            workflow_tree.item(node_id, values=current_values)
            
            if on_change_callback:
                on_change_callback()
            
            popup.destroy()
        
        ttk.Button(button_frame, text="Sauvegarder", command=save_inputs).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Annuler", command=popup.destroy).pack(side="right")
    
    def add_prompt_value(self, values_tree, on_change_callback):
        """Ajouter une nouvelle ligne dans prompt_values"""
        self.value_row_counter += 1
        new_key = str(self.value_row_counter)
        
        new_entry = {
            "id": "",
            "type": "",
            "value": ""
        }
        
        values_tree.insert("", "end", iid=new_key, values=(new_key, "", "", "", ""))
        self.values_data[new_key] = new_entry
        
        if on_change_callback:
            on_change_callback()
    
    def delete_prompt_value(self, values_tree, on_change_callback):
        """Supprimer une ligne des prompt_values"""
        selection = values_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez une ligne à supprimer.")
            return
        
        if messagebox.askyesno("Confirmer", "Supprimer cette ligne ?"):
            item = selection[0]
            values_tree.delete(item)
            if item in self.values_data:
                del self.values_data[item]
            
            if on_change_callback:
                on_change_callback()
    
    def add_workflow_node(self, workflow_tree, on_change_callback):
        """Ajouter un nouveau nœud workflow"""
        from tkinter import simpledialog
        node_id = simpledialog.askstring("Nouveau nœud", "ID du nœud:")
        if not node_id:
            return
        
        if node_id in self.workflow_data:
            messagebox.showerror("Erreur", "Cet ID existe déjà.")
            return
        
        new_node = {
            "inputs": {},
            "class_type": "",
            "_meta": {"title": ""}
        }
        
        workflow_tree.insert("", "end", iid=node_id, values=(node_id, "", "{}", ""))
        self.workflow_data[node_id] = new_node
        
        if on_change_callback:
            on_change_callback()
    
    def delete_workflow_node(self, workflow_tree, on_change_callback):
        """Supprimer un nœud workflow"""
        selection = workflow_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un nœud à supprimer.")
            return
        
        if messagebox.askyesno("Confirmer", "Supprimer ce nœud ?"):
            item = selection[0]
            workflow_tree.delete(item)
            if item in self.workflow_data:
                del self.workflow_data[item]
            
            if on_change_callback:
                on_change_callback()
    
    def update_values_data(self, item_id, col_index, new_value):
        """Mettre à jour les données values après édition inline"""
        if item_id not in self.values_data:
            self.values_data[item_id] = {}
        
        columns = ["key", "id", "type", "value", "action"]
        if col_index < len(columns):
            col_name = columns[col_index]
            if col_name in ["id", "type", "value"]:
                self.values_data[item_id][col_name] = new_value
    
    def update_workflow_data(self, item_id, col_index, new_value):
        """Mettre à jour les données workflow après édition inline"""
        if item_id not in self.workflow_data:
            self.workflow_data[item_id] = {"inputs": {}, "class_type": "", "_meta": {"title": ""}}
        
        columns = ["id", "class_type", "inputs", "title"]
        if col_index < len(columns):
            col_name = columns[col_index]
            if col_name == "class_type":
                self.workflow_data[item_id]["class_type"] = new_value
            elif col_name == "title":
                if "_meta" not in self.workflow_data[item_id]:
                    self.workflow_data[item_id]["_meta"] = {}
                self.workflow_data[item_id]["_meta"]["title"] = new_value
    
    def get_prompt_values_json(self):
        """Récupérer les données prompt_values au format JSON"""
        return json.dumps(self.values_data, ensure_ascii=False)
    
    def get_workflow_json(self):
        """Récupérer les données workflow au format JSON"""
        return json.dumps(self.workflow_data, ensure_ascii=False)
    
    def _save_current_prompt(self, on_change_callback):
        """Méthode pour sauvegarder le prompt courant"""
        if self.save_callback:
            # Utiliser le callback de sauvegarde défini
            try:
                self.save_callback()
            except Exception as e:
                messagebox.showerror("Erreur de sauvegarde", f"Erreur lors de la sauvegarde: {e}")
        else:
            # Si pas de callback, appeler on_change_callback et afficher un message d'aide
            if on_change_callback:
                on_change_callback()
            
            messagebox.showinfo("Sauvegarde", 
                "💡 Modifications enregistrées en mémoire\n\n"
                "Pour sauvegarder définitivement :\n"
                "• Allez dans l'onglet 'Informations'\n"
                "• Cliquez sur '💾 Sauvegarder les informations'\n\n"
                "Ou utilisez Ctrl+S")
    
    def set_save_callback(self, callback):
        """Définir le callback pour la sauvegarde"""
        self.save_callback = callback