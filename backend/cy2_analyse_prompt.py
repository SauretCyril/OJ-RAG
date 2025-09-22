import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import sqlite3
from flask import request, Blueprint

from cy_mistral import get_mistral_answer
from dotenv import load_dotenv

import requests
import time
import argparse
import sys
print(f"Python utilise : {sys.executable}")

load_dotenv()
DEFAULT_DECOMPOSE_QUESTION = (
    "Decompose le texte suivant en lignes thematiques :\n"
    "- <personnage> : description du personnage\n"
    "- <position> : description extremement detaillee de la position du ou des sujets\n"
    "- <habits> : description des vetements (ou nu)\n"
    "- <poitrine> : description de la poitrine\n"
    "- <age> : age ou apparence d'age\n"
    "- <lieux> : description du lieu\n"
    "- <lumiere> : description de la lumiere\n"
    "- <atmosphere> : ambiance generale\n"
    "- <autres> : tout autre element pertinent\n"
    "Le resultat doit etre sous forme de liste 'key : value', la cle est la valeur encadree par des < > et la value est la reponse a la question qui se trouve apres les ':' .\n\n"
    "{texte}"
)

def wrap_text(text, width=60):
    import textwrap
    return "\n".join(textwrap.wrap(text, width=width))

class cy2_analyse_prompt(tk.Tk):
    def __init__(self, prompt_text=None, prompt_id=None, prompt_origin="COM", db_path=None):
        super().__init__()
        self.prompt_text = prompt_text
        self.prompt_id = prompt_id
        self.prompt_origin = prompt_origin or "COM"
        self.db_path = self._resolve_db_path(db_path)
        self.db_conn = None
        self.record_id = self._compose_prompt_key()
        self.record_exists = False
        self.data_loaded_from_db = False
        self.decompose_question = DEFAULT_DECOMPOSE_QUESTION

        self.title("Prompt")
        self.geometry("1100x800")
        self.prompts = []
        self.filtered_prompts = []

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Titre en haut
        # title_label = ttk.Label(self, text=f"{self.descriptif}", font=("Arial", 14, "bold"))
        # title_label.pack(side="top", fill="x", padx=5, pady=5)

        display_id = self.record_id if self.record_id else (str(self.prompt_id) if self.prompt_id is not None else "")
        if display_id:
            info_frame = ttk.Frame(self)
            info_frame.pack(side="top", fill="x", padx=5, pady=(5, 0))
            ttk.Label(info_frame, text=f"Prompt ID: {display_id}").pack(side="left")

        # Conteneur principal flexible
        self.main_paned = ttk.Panedwindow(self, orient="vertical")
        self.main_paned.pack(side="top", fill="both", expand=True)

        # Section superieure : prompts et analyse
        top_section = ttk.Panedwindow(self.main_paned, orient="horizontal")
        self.main_paned.add(top_section, weight=3)

        prompt_panel = ttk.Frame(top_section)
        prompt_panel.columnconfigure(0, weight=1)
        prompt_panel.rowconfigure(1, weight=1)
        prompt_panel.rowconfigure(4, weight=1)
        top_section.add(prompt_panel, weight=3)

        ttk.Label(prompt_panel, text="Positive Prompt (en)").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))
        self.prompt_textbox_en = tk.Text(prompt_panel, height=8, wrap="word")
        self.prompt_textbox_en.grid(row=1, column=0, sticky="nsew", padx=5)

        translate_frame = ttk.Frame(prompt_panel)
        translate_frame.grid(row=2, column=0, pady=5)
        ttk.Button(translate_frame, text="fr->en", width=8, command=self.translate_fr2en).pack(side="left", padx=2)
        ttk.Button(translate_frame, text="en->fr", width=8, command=self.translate_en2fr).pack(side="left", padx=2)

        ttk.Label(prompt_panel, text="Prompt positif (fr)").grid(row=3, column=0, sticky="w", padx=5, pady=(5, 2))
        self.prompt_textbox_fr = tk.Text(prompt_panel, height=8, wrap="word")
        self.prompt_textbox_fr.grid(row=4, column=0, sticky="nsew", padx=5, pady=(0, 5))

        ttk.Label(prompt_panel, text="Model").grid(row=5, column=0, sticky="w", padx=5, pady=(5, 2))
        self.model_var = tk.StringVar()
        ttk.Entry(prompt_panel, textvariable=self.model_var).grid(row=6, column=0, sticky="ew", padx=5, pady=(0, 5))

        analysis_panel = ttk.Frame(top_section)
        analysis_panel.columnconfigure(0, weight=1)
        analysis_panel.rowconfigure(1, weight=1)
        analysis_panel.rowconfigure(4, weight=1)
        analysis_panel.rowconfigure(7, weight=1)
        top_section.add(analysis_panel, weight=4)

        ttk.Label(analysis_panel, text="Question a Mistral").grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))
        self.question_textbox = tk.Text(analysis_panel, height=5, wrap="word")
        self.question_textbox.grid(row=1, column=0, sticky="nsew", padx=5)

        ttk.Button(analysis_panel, text="Repondre", command=self.ask_mistral).grid(row=2, column=0, sticky="e", padx=5, pady=5)

        ttk.Label(analysis_panel, text="Resultat").grid(row=3, column=0, sticky="w", padx=5, pady=(5, 2))
        self.result_textbox = tk.Text(analysis_panel, height=6, wrap="word")
        self.result_textbox.grid(row=4, column=0, sticky="nsew", padx=5)

        ttk.Button(analysis_panel, text="Traduire en anglais", command=self.translate_result_to_en).grid(row=5, column=0, sticky="e", padx=5, pady=5)

        ttk.Label(analysis_panel, text="Result (en)").grid(row=6, column=0, sticky="w", padx=5, pady=(5, 2))
        self.result_textbox_en = tk.Text(analysis_panel, height=6, wrap="word")
        self.result_textbox_en.grid(row=7, column=0, sticky="nsew", padx=5, pady=(0, 5))

        table_container = ttk.Frame(self.main_paned)
        self.main_paned.add(table_container, weight=4)

        filter_frame = ttk.Frame(table_container)
        filter_frame.pack(side="top", fill="x", padx=5, pady=5)
        ttk.Button(filter_frame, text="Decomposer", command=self.decompose_prompt_fr).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Question decomposer", command=self.edit_decompose_question).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Reconstruire", command=self.rebuild_prompt).pack(side="left", padx=5)

        table_frame = ttk.Frame(table_container)
        table_frame.pack(side="top", fill="both", expand=True, padx=5, pady=(0, 40))
        columns = ("type", "fr", "delete")  # 'type' en premier, 'en' supprime
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("type", text="Type")
        self.tree.heading("fr", text="Texte francais")
        self.tree.heading("delete", text="")
        self.tree.column("type", width=120, stretch=False)
        self.tree.column("fr", width=500, stretch=True)
        self.tree.column("delete", width=40, anchor="center", stretch=False)
        self.tree.pack(side="left", fill="both", expand=True)

        style = ttk.Style(self)
        style.configure("Treeview", rowheight=40)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Sauvegarder", command=self.save_work).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.delete_prompt).pack(side="left", padx=5)

        self.tree.tag_configure("prompt_row", background="#e0e0e0")
        self.tree.tag_configure("type_font", font=("Arial", 12, "bold"))

        # # Si prompt_text est fourni, on l'utilise directement
        # if self.prompt_text:
        #     self.load_prompt_from_text(self.prompt_text)
        # else:
        #     self.prompts = []
        #     self.filtered_prompts = []
        #     self.refresh_table()

        self.mode = "text" if self.prompt_text else "file"

        self.tree.bind("<Double-1>", self.edit_fr_cell)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self._initialize_storage()
         # PrAremplissage si prompt_text fourni
        if self.prompt_text and not self.data_loaded_from_db:
            self.prompt_textbox_en.insert("1.0", self.prompt_text)
            self.update_idletasks()  # S'assure que l'insertion est terminAe

            # Traduction anglais -> franAais
            self.translate_en2fr()
            time.sleep(1)  # <-- Ajoute une pause ici
            self.update_idletasks()


    # --- MAthodes de la classe ---

    def translate_fr2en(self):
        fr = self.prompt_textbox_fr.get("1.0", tk.END).strip()
        if fr:
            en = self.mistral_translate(fr, src_lang="fr", tgt_lang="en")
            self.prompt_textbox_en.delete("1.0", tk.END)
            self.prompt_textbox_en.insert("1.0", en)

    def translate_en2fr(self):
        en = self.prompt_textbox_en.get("1.0", tk.END).strip()
        if en:
            fr = self.mistral_translate(en, src_lang="en", tgt_lang="fr")
            self.prompt_textbox_fr.delete("1.0", tk.END)
            self.prompt_textbox_fr.insert("1.0", fr)

    def decompose_prompt_fr(self):
        texte = self.prompt_textbox_fr.get("1.0", tk.END).strip()
        self.decompose_text(texte)

    def edit_fr_cell(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or column != "#2":  # "#2" = deuxieme colonne ("fr")
            return
        idx = int(item)
        prompt = self.filtered_prompts[idx]
        x, y, width, height = self.tree.bbox(item, column)
        entry = tk.Text(self.tree, height=4, width=40)
        entry.insert("1.0", prompt["fr"])
        entry.place(x=x, y=y, width=width, height=height*2)
        entry.focus_set()

        def save_edit(event=None):
            new_text = entry.get("1.0", tk.END).strip()
            prompt["fr"] = new_text
            self.refresh_table()
            entry.destroy()

        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Return>", lambda e: save_edit())

    def on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        # Colonne "delete" = derniere colonne, donc "#4"
        if not item or column != "#4":
            return
        idx = int(item)
        prompt = self.filtered_prompts[idx]
        if prompt["type"].lower() == "prompt":
            return  # On ne supprime pas la ligne principale
        if messagebox.askyesno("Confirmation", "Voulez-vous supprimer la ligne ?"):
            self.prompts.remove(prompt)
            self.refresh_table()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, prompt in enumerate(self.filtered_prompts):
            fr_text = wrap_text(prompt["fr"], width=60)
            tags = ()
            if prompt["type"].lower() == "prompt":
                tags = ("prompt_row",)
            self.tree.insert(
                "", "end", iid=idx,
                values=(
                    prompt["type"],  # type en premier
                    fr_text,
                    "a" if prompt["type"].lower() != "prompt" else ""
                ),
                tags=tags + ("type_font",)
            )

    def delete_prompt(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Selectionnez une ligne a supprimer.")
            return
        idx = int(selected[0])
        prompt = self.filtered_prompts[idx]
        self.prompts.remove(prompt)
        self.refresh_table()

    def decompose_text(self, texte):
        if not texte:
            messagebox.showwarning("Avertissement", "Le texte franAais est obligatoire.")
            return

        question_template = self.decompose_question or DEFAULT_DECOMPOSE_QUESTION
        if "{texte}" in question_template:
            try:
                question = question_template.format(texte=texte)
            except KeyError:
                question = f"{question_template}\n{texte}"
        else:
            question = f"{question_template}\n{texte}"
        role = "Tu es un assistant avec une expertise de photographe qui extrait et classe les informations d'une description d'image."

        #result = get_mistral_answer(question, role, texte)
        result = self.mistral_translate(question, src_lang="fr", tgt_lang="fr")

        if not result or not result.strip():
            messagebox.showwarning("Avertissement", "Aucune rAponse de l'API Mistral.")
            return

        # Vide le tableau avant d'ajouter les nouvelles lignes
        self.prompts = []
        for line in result.splitlines():
            if ':' not in line:
                continue
            type_part, fr_part = line.split(':', 1)
            type_clean = type_part.strip().capitalize()
            fr_text = fr_part.strip()
            if not fr_text or fr_text.lower() == "n/a":
                continue
            self.prompts.append({
                "fr": fr_text,
                "en": "",
                "type": type_clean
            })

        self.filtered_prompts = self.prompts.copy()
        self.refresh_table()
        #messagebox.showinfo("DAcomposition", "DAcomposition terminAe et lignes ajoutAes au tableau.")

    def mistral_translate(self, text, src_lang="fr", tgt_lang="en"):
        question = f"Traduis le texte suivant du {src_lang} vers le {tgt_lang} :"
        role = "Tu es un traducteur professionnel. RAponds uniquement par la traduction, sans explication."
        content = text
        try:
            self.config(cursor="watch")  # Curseur "attente"
            self.update_idletasks()
            result = get_mistral_answer(question, role, content)
            time.sleep(1)
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                messagebox.showerror("Limite atteinte", "Trop de requetes envoyees a Mistral. Merci de patienter quelques secondes avant de reessayer.")
            else:
                messagebox.showerror("Erreur API Mistral", f"Erreur lors de l'appel a l'API Mistral: {e}")
            return ""
        finally:
            self.config(cursor="")  # Restaure le curseur normal
            self.update_idletasks()

    def rebuild_prompt(self):
        # ConcatAner toutes les lignes (hors "prompt" et "negative") avec une virgule
        lignes = [p["fr"].strip() for p in self.prompts if p["type"].lower() not in ("prompt", "negative") and p["fr"].strip()]
        if not lignes:
            messagebox.showinfo("Info", "Aucune ligne a concatener pour ce prompt.")
            return
        texte_concat = ", ".join(lignes)
        question = (
            "Réécris le texte suivant en un prompt cohérent, fluide et naturel pour décrire une image. "
            "Utilise toutes les informations, sans répétition. "
            "Texte à reformuler :\n"
            f"{texte_concat}"
        )
        prompt_fr = self.mistral_translate(question, src_lang="fr", tgt_lang="fr")

        # Afficher dans la zone de texte française
        self.prompt_textbox_fr.delete("1.0", tk.END)
        self.prompt_textbox_fr.insert("1.0", prompt_fr)

        self.refresh_table()
        #messagebox.showinfo("Reconstruit", "Le prompt a ete reconstruit et mis a jour.")

    def load_prompt_from_text(self, text):
        self.prompts = self.analyse_prompt_text(text)
        self.filtered_prompts = self.prompts.copy()
        self.refresh_table()

    def analyse_prompt_text(self, text):
        return [{"fr": line.strip(), "en": "", "type": "Prompt"} for line in text.splitlines() if line.strip()]

    def ask_mistral(self):
        question = self.question_textbox.get("1.0", tk.END).strip()
        prompt_fr = self.prompt_textbox_fr.get("1.0", tk.END).strip()
        if not question:
            messagebox.showinfo("Info", "Veuillez saisir une question.")
            return
        if not prompt_fr:
            messagebox.showinfo("Info", "Le prompt positif (fr) est vide.")
            return
        # On pose la question a Mistral en donnant le prompt comme contexte
        role = "Tu es un assistant expert en analyse de prompts d'image."
        content = f"Prompt : {prompt_fr}\nQuestion : {question}"
        try:
            self.config(cursor="watch")
            self.update_idletasks()
            result = get_mistral_answer(question, role, content)
            self.result_textbox.config(state="normal")
            self.result_textbox.delete("1.0", tk.END)
            self.result_textbox.insert("1.0", result)
            self.result_textbox.config(state="normal")
        except Exception as e:
            self.result_textbox.config(state="normal")
            self.result_textbox.delete("1.0", tk.END)
            self.result_textbox.insert("1.0", f"Erreur : {e}")
        finally:
            self.config(cursor="")
            self.update_idletasks()

    def translate_result_to_en(self):
        result_fr = self.result_textbox.get("1.0", tk.END).strip()
        if not result_fr:
            messagebox.showinfo("Info", "Aucun resultat a traduire.")
            return
        result_en = self.mistral_translate(result_fr, src_lang="fr", tgt_lang="en")
        self.result_textbox_en.config(state="normal")
        self.result_textbox_en.delete("1.0", tk.END)
        self.result_textbox_en.insert("1.0", result_en)
        self.result_textbox_en.config(state="normal")

    def _resolve_db_path(self, explicit_path):
        candidate = explicit_path or os.getenv("PROMPTS_WORK_DB")
        if not candidate:
            return None
        candidate = candidate.strip().strip('"').strip("'")
        if not candidate:
            return None
        return os.path.normpath(candidate)

    def _compose_prompt_key(self):
        if self.prompt_id is None:
            return None
        origin = (self.prompt_origin or "").strip()
        prompt_part = str(self.prompt_id).strip()
        if not prompt_part:
            return None
        return f"{origin}_{prompt_part}" if origin else prompt_part

    def _initialize_storage(self):
        if not self.db_path:
            return
        try:
            if not self.db_conn:
                self._init_database()
            self._load_existing_work()
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible d'initialiser la base de donnees : {exc}")
            self.db_conn = None

    def _init_database(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row
        self.db_conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts_working (
                id_prompt TEXT PRIMARY KEY,
                positive_prompt_en TEXT,
                prompt_positif_fr TEXT,
                question_reformuler TEXT,
                resultat TEXT,
                resultat_eng TEXT,
                decomposition TEXT,
                question_decomposer TEXT,
                model TEXT
            )
        """)
        self.db_conn.commit()
        # Appeler la méthode pour s'assurer que la colonne model existe
        self._ensure_model_column()

    def _ensure_model_column(self):
        if not self.db_conn:
            return
        cursor = self.db_conn.cursor()
        cursor.execute("PRAGMA table_info(prompts_working)")
        columns = {row[1] for row in cursor.fetchall()}
        if "model" not in columns:
            cursor.execute("ALTER TABLE prompts_working ADD COLUMN model TEXT")
            self.db_conn.commit()

    def _set_text(self, widget, value):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        if value:
            widget.insert("1.0", value)

    def _load_existing_work(self):
        if not self.db_conn or not self.record_id:
            return
        cursor = self.db_conn.cursor()
        
        # Vérifier d'abord quelles colonnes existent dans la table
        cursor.execute("PRAGMA table_info(prompts_working)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Construire la requête en fonction des colonnes disponibles
        base_columns = ["positive_prompt_en", "prompt_positif_fr", "question_reformuler", 
                       "resultat", "resultat_eng", "decomposition", "question_decomposer"]
        
        if "model" in columns:
            select_columns = base_columns + ["model"]
        else:
            select_columns = base_columns
            
        query = f"SELECT {', '.join(select_columns)} FROM prompts_working WHERE id_prompt=?"
        cursor.execute(query, (self.record_id,))
        row = cursor.fetchone()
        
        if not row:
            return

        self.record_exists = True
        self.data_loaded_from_db = True

        self._set_text(self.prompt_textbox_en, row["positive_prompt_en"] or "")
        self.prompt_text = row["positive_prompt_en"] or self.prompt_text
        self._set_text(self.prompt_textbox_fr, row["prompt_positif_fr"] or "")
        self._set_text(self.question_textbox, row["question_reformuler"] or "")
        self._set_text(self.result_textbox, row["resultat"] or "")
        self._set_text(self.result_textbox_en, row["resultat_eng"] or "")
        
        # Gérer la colonne model seulement si elle existe
        if "model" in columns:
            self.model_var.set(row["model"] or "")
        else:
            self.model_var.set("")

        decomposition_data = row["decomposition"] or ""
        prompts = []
        if decomposition_data:
            try:
                parsed = json.loads(decomposition_data)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict):
                            prompts.append({
                                "fr": item.get("fr", ""),
                                "en": item.get("en", ""),
                                "type": item.get("type", "")
                            })
            except json.JSONDecodeError:
                prompts = []

        self.prompts = prompts
        self.filtered_prompts = list(self.prompts)
        self.refresh_table()

        question_value = row["question_decomposer"] or DEFAULT_DECOMPOSE_QUESTION
        self.decompose_question = question_value

    def save_work(self, show_message=True):
        if not self.record_id:
            messagebox.showerror("Erreur", "Identifiant de prompt manquant.")
            return False
        if not self.db_path:
            messagebox.showerror("Erreur", "Aucun chemin de base de donnees defini.")
            return False

        try:
            if not self.db_conn:
                self._init_database()
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la base de donnees : {exc}")
            return False

        positive_en = self.prompt_textbox_en.get("1.0", tk.END).strip()
        prompt_fr = self.prompt_textbox_fr.get("1.0", tk.END).strip()
        question_reformuler = self.question_textbox.get("1.0", tk.END).strip()
        result_fr = self.result_textbox.get("1.0", tk.END).strip()
        result_en = self.result_textbox_en.get("1.0", tk.END).strip()
        decomposition_json = json.dumps(self.prompts, ensure_ascii=False)
        question_template = self.decompose_question or DEFAULT_DECOMPOSE_QUESTION
        model_value = self.model_var.get().strip()

        try:
            cursor = self.db_conn.cursor()
            
            # Vérifier quelles colonnes existent
            cursor.execute("PRAGMA table_info(prompts_working)")
            columns = {row[1] for row in cursor.fetchall()}
            
            cursor.execute("SELECT 1 FROM prompts_working WHERE id_prompt=?", (self.record_id,))
            exists = cursor.fetchone() is not None
            
            if "model" in columns:
                # Utiliser la version complète avec model
                payload = (positive_en, prompt_fr, question_reformuler, result_fr, result_en, 
                          decomposition_json, question_template, model_value)
                
                if exists:
                    cursor.execute("""
                        UPDATE prompts_working
                        SET positive_prompt_en=?, prompt_positif_fr=?, question_reformuler=?, 
                            resultat=?, resultat_eng=?, decomposition=?, question_decomposer=?, model=?
                        WHERE id_prompt=?
                    """, payload + (self.record_id,))
                else:
                    cursor.execute("""
                        INSERT INTO prompts_working 
                        (id_prompt, positive_prompt_en, prompt_positif_fr, question_reformuler, 
                         resultat, resultat_eng, decomposition, question_decomposer, model)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (self.record_id,) + payload)
            else:
                # Utiliser la version sans model
                payload = (positive_en, prompt_fr, question_reformuler, result_fr, result_en, 
                          decomposition_json, question_template)
                
                if exists:
                    cursor.execute("""
                        UPDATE prompts_working
                        SET positive_prompt_en=?, prompt_positif_fr=?, question_reformuler=?, 
                            resultat=?, resultat_eng=?, decomposition=?, question_decomposer=?
                        WHERE id_prompt=?
                    """, payload + (self.record_id,))
                else:
                    cursor.execute("""
                        INSERT INTO prompts_working 
                        (id_prompt, positive_prompt_en, prompt_positif_fr, question_reformuler, 
                         resultat, resultat_eng, decomposition, question_decomposer)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (self.record_id,) + payload)
                    
            self.db_conn.commit()
        except sqlite3.Error as exc:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer le travail : {exc}")
            return False

        self.record_exists = True
        self.data_loaded_from_db = True
        if show_message:
            messagebox.showinfo("Succes", "Travail enregistre.")
        return True

    def edit_decompose_question(self):
        editor = tk.Toplevel(self)
        editor.title("Modifier la question de decomposition")
        editor.transient(self)
        editor.grab_set()
        editor.geometry("700x400")
        editor.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (700 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (400 // 2)
        editor.geometry(f"700x400+{x}+{y}")
        editor.resizable(True, True)

        text_widget = tk.Text(editor, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", self.decompose_question or DEFAULT_DECOMPOSE_QUESTION)
        text_widget.focus_set()

        button_frame = ttk.Frame(editor)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        def apply_changes():
            new_value = text_widget.get("1.0", tk.END).strip()
            if not new_value:
                messagebox.showwarning("Avertissement", "La question ne peut pas etre vide.")
                return
            self.decompose_question = new_value
            if self.record_exists:
                if self.save_work(show_message=False):
                    messagebox.showinfo("Succes", "Question de decomposition enregistree.")
                    editor.destroy()
            else:
                messagebox.showinfo("Info", "Question mise a jour. Cliquez sur Sauvegarder pour enregistrer le prompt.")
                editor.destroy()

        ttk.Button(button_frame, text="Enregistrer", command=apply_changes).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Annuler", command=editor.destroy).pack(side="left", padx=5)

    def on_close(self):
        if self.db_conn:
            try:
                self.db_conn.close()
            except sqlite3.Error:
                pass
            self.db_conn = None
        self.destroy()


if __name__ == "__main__":
    # Gestion des arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Analyseur de prompts")
    parser.add_argument("--prompt_text", type=str, help="Texte du prompt a analyser", default=None)
    parser.add_argument("--prompt_id", type=str, help="Identifiant du prompt", default=None)
    parser.add_argument("--prompt_origin", type=str, help="Origine du prompt", default="COM")
    parser.add_argument("--db_path", type=str, help="Chemin de la base de donnees de travail", default=None)
    args = parser.parse_args()

    # Passer le prompt_text a l'application
    app = cy2_analyse_prompt(prompt_text=args.prompt_text, prompt_id=args.prompt_id, prompt_origin=args.prompt_origin, db_path=args.db_path)
    app.mainloop()

import sys
print(f"Python utilise : {sys.executable}")
