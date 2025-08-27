import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from flask import request, Blueprint
from cy_paths import GetRoot
from cy_mistral import get_mistral_answer

import requests
import time

TYPES = [ "personnage", "habits", "lumières", "lieux", 'lumière', "Qualité", 'Atmosphere', 'Age', "Autre"]

def wrap_text(text, width=60):
    import textwrap
    return "\n".join(textwrap.wrap(text, width=width))

class cy2_analyse_prompt(tk.Tk):
    def __init__(self, prompt_text=None):
        super().__init__()
        self.prompt_text = prompt_text

        self.title("Prompt")
        self.geometry("1100x800")
        self.prompts = []
        self.filtered_prompts = []

        # Titre en haut
        # title_label = ttk.Label(self, text=f"{self.descriptif}", font=("Arial", 14, "bold"))
        # title_label.pack(side="top", fill="x", padx=5, pady=5)

        # Frame principal pour les prompts
        prompt_frame = ttk.Frame(self)
        prompt_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Frame vertical pour anglais/français
        prompt_col_frame = ttk.Frame(prompt_frame)
        prompt_col_frame.pack(side="left", fill="y", padx=(0, 5))

        # Zone Positive Prompt (anglais)
        ttk.Label(prompt_col_frame, text="Positive Prompt (en)").pack(side="top", anchor="w", pady=(0, 2))
        self.prompt_textbox_en = tk.Text(prompt_col_frame, height=8, width=60)
        self.prompt_textbox_en.pack(side="top", fill="x", expand=True)

        # Zone Positive Prompt (français)
        ttk.Label(prompt_col_frame, text="Prompt positif (fr)").pack(side="top", anchor="w", pady=(10, 2))
        self.prompt_textbox_fr = tk.Text(prompt_col_frame, height=8, width=60)
        self.prompt_textbox_fr.pack(side="top", fill="x", expand=True)

        # Boutons de traduction au milieu
        btns_frame = ttk.Frame(prompt_frame)
        btns_frame.pack(side="left", padx=5, pady=(30,0))
        ttk.Button(btns_frame, text="fr→en", width=8, command=self.translate_fr2en).pack(pady=2)
        ttk.Button(btns_frame, text="en→fr", width=8, command=self.translate_en2fr).pack(pady=2)

        # Frame vertical pour question/réponse
        qr_frame = ttk.Frame(prompt_frame)
        qr_frame.pack(side="left", fill="y", padx=(0, 5))

        ttk.Label(qr_frame, text="Question à Mistral").pack(side="top", anchor="w")
        self.question_textbox = tk.Text(qr_frame, height=5, width=60)
        self.question_textbox.pack(side="top", fill="x", expand=True, pady=(0, 5))

        ttk.Button(qr_frame, text="Répondre", command=self.ask_mistral).pack(side="top", pady=(0, 5))

        ttk.Label(qr_frame, text="Résultat").pack(side="top", anchor="w")
        self.result_textbox = tk.Text(qr_frame, height=6, width=60, state="normal")
        self.result_textbox.pack(side="top", fill="x", expand=True)

        ttk.Button(qr_frame, text="Traduire en anglais", command=self.translate_result_to_en).pack(side="top", pady=(0, 5))

        ttk.Label(qr_frame, text="Result (en)").pack(side="top", anchor="w")
        self.result_textbox_en = tk.Text(qr_frame, height=6, width=60, state="normal")
        self.result_textbox_en.pack(side="top", fill=" x", expand=True)

        # Zone de filtre
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side="top", fill="x", padx=5, pady=5)
        #ttk.Label(filter_frame, text="Type:").pack(side="left")
        #self.filter_type = ttk.Combobox(filter_frame, values=[""] + TYPES, state="readonly")
        #self.filter_type.pack(side="left", padx=5)
        #self.filter_type.set("")
        #ttk.Button(filter_frame, text="Filtrer", command=self.apply_filter).pack(side="left", padx=5)
        #ttk.Button(filter_frame, text="Réinitialiser", command=self.reset_filter).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Décomposer", command=self.decompose_prompt_fr).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Reconstruire", command=self.rebuild_prompt).pack(side="left", padx=5)

        # Tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        columns = ("type", "fr", "delete")  # 'type' en premier, 'en' supprimé
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("type", text="Type")
        self.tree.heading("fr", text="Texte français")
        self.tree.heading("delete", text="")
        self.tree.column("type", width=100)  # largeur réduite
        self.tree.column("fr", width=500)
        self.tree.column("delete", width=40, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        # Style pour agrandir la police de la colonne Type
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=40)
        style.configure("Treeview.TypeColumn", font=("Arial", 12, "bold"))

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Boutons d'action
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="top", fill="x", padx=5, pady=5)
        #ttk.Button(btn_frame, text="Ajouter", command=self.add_prompt).pack(side="left", padx=5)
        #ttk.Button(btn_frame, text="Modifier", command=self.edit_prompt).pack(side="left", padx=5)
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
         # Préremplissage si prompt_text fourni
        if self.prompt_text:
            self.prompt_textbox_en.insert("1.0", self.prompt_text)
            self.update_idletasks()  # S'assure que l'insertion est terminée

            # Traduction anglais -> français
            self.translate_en2fr()
            time.sleep(1)  # <-- Ajoute une pause ici
            self.update_idletasks()

           
    # --- Méthodes de la classe ---

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
        if not item or column != "#2":  # "#2" = deuxième colonne ("fr")
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
        # Colonne "delete" = dernière colonne, donc "#4"
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
                    "❌" if prompt["type"].lower() != "prompt" else ""
                ),
                tags=tags + ("type_font",)
            )

   
    def delete_prompt(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Sélectionnez une ligne à supprimer.")
            return
        idx = int(selected[0])
        prompt = self.filtered_prompts[idx]
        self.prompts.remove(prompt)
        self.refresh_table()

    def decompose_text(self, texte):
        if not texte:
            messagebox.showwarning("Avertissement", "Le texte français est obligatoire.")
            return

        question = (
            "Décompose le texte suivant en lignes thématiques :\n"
            "- <personnage> : description du personnage\n"
            "- <position> : description extêmement détaillée de la position du ou des sujets\n"
            "- <habits> : description des vêtements (ou nu)\n"
            "- <poitrine> : description de la poitrine\n"
            "- <age> : âge ou apparence d'âge\n"
            "- <lieux> : description du lieu\n"
            "- <lumière> : description de la lumière\n"
            "- <atmosphere> : ambiance générale\n"
            "- <autres> : tout autre élément pertinent\n"
            "le résultat doit être sous forme de liste 'key : value', "
            "la clé est la valeur encadré par des < >  et la value est la réponse à la question qui se trouve apres les ':' .\n"
           
            f"{texte}"
        )
        role = "Tu es un assistant avec une expertise de photographe qui extrait et classe les informations d'une description d'image."

        #result = get_mistral_answer(question, role, texte)
        result = self.mistral_translate(question, src_lang="fr", tgt_lang="fr")

        if not result or not result.strip():
            messagebox.showwarning("Avertissement", "Aucune réponse de l'API Mistral.")
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
        #messagebox.showinfo("Décomposition", "Décomposition terminée et lignes ajoutées au tableau.")

    def mistral_translate(self, text, src_lang="fr", tgt_lang="en"):
        question = f"Traduis le texte suivant du {src_lang} vers le {tgt_lang} :"
        role = "Tu es un traducteur professionnel. Réponds uniquement par la traduction, sans explication."
        content = text
        try:
            self.config(cursor="watch")  # Curseur "attente"
            self.update_idletasks()
            result = get_mistral_answer(question, role, content)
            time.sleep(1)
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                messagebox.showerror("Limite atteinte", "Trop de requêtes envoyées à Mistral. Merci de patienter quelques secondes avant de réessayer.")
            else:
                messagebox.showerror("Erreur API Mistral", f"Erreur lors de l'appel à l'API Mistral: {e}")
            return ""
        finally:
            self.config(cursor="")  # Restaure le curseur normal
            self.update_idletasks()

    def rebuild_prompt(self):
        # Concaténer toutes les lignes (hors "prompt" et "negative") avec une virgule
        lignes = [p["fr"].strip() for p in self.prompts if p["type"].lower() not in ("prompt", "negative") and p["fr"].strip()]
        if not lignes:
            messagebox.showinfo("Info", "Aucune ligne à concaténer pour ce prompt.")
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
        #messagebox.showinfo("Reconstruit", "Le prompt a été reconstruit et mis à jour.")

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
        # On pose la question à Mistral en donnant le prompt comme contexte
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
            messagebox.showinfo("Info", "Aucun résultat à traduire.")
            return
        result_en = self.mistral_translate(result_fr, src_lang="fr", tgt_lang="en")
        self.result_textbox_en.config(state="normal")
        self.result_textbox_en.delete("1.0", tk.END)
        self.result_textbox_en.insert("1.0", result_en)
        self.result_textbox_en.config(state="normal")

if __name__ == "__main__":
    app = cy2_analyse_prompt()
    app.mainloop()