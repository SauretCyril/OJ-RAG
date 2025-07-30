import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from flask import request, Blueprint
from cy_paths import GetRoot  # Assurez-vous que cette fonction est définie dans cy_paths.py

from cy_mistral import get_mistral_answer  # en haut du fichier

TYPES = ["Prompt", "personnage", "habits", "lumières", "lieux", 'lumière', "Qualité", 'Atmosphere', 'Age',"Negative", "Autre"]
cy_analyse_prompt = Blueprint('cy_analyse_prompt', __name__)

class PromptTableApp(tk.Tk):
    def __init__(self, file_path="prompts.json", isDependOn=False, num_dossier="", chemin="", nom_fichier="", descriptif=""):
        super().__init__()
        self.isDependOn = isDependOn
        self.num_dossier = num_dossier
        self.chemin = chemin
        self.nom_fichier = nom_fichier
        self.descriptif = descriptif

        if self.isDependOn:
            root_dir = GetRoot()
            self.file_path = f"{root_dir}/{self.num_dossier}/{self.num_dossier}{self.nom_fichier}.json"
            print(f"dbg-B001-File path: {self.file_path}")
        else:
            self.file_path = file_path

        self.title("Prompt")
        self.geometry("1100x500")
        self.prompts = []
        self.filtered_prompts = []

        # Titre en haut
        title_label = ttk.Label(self, text=f"Dossier : {self.num_dossier} - {self.descriptif}", font=("Arial", 14, "bold"))
        title_label.pack(side="top", fill="x", padx=5, pady=5)

        # Zone de filtre
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side="top", fill="x", padx=5, pady=5)
        ttk.Label(filter_frame, text="Type:").pack(side="left")
        self.filter_type = ttk.Combobox(filter_frame, values=[""] + TYPES, state="readonly")
        self.filter_type.pack(side="left", padx=5)
        self.filter_type.set("")
        ttk.Button(filter_frame, text="Filtrer", command=self.apply_filter).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Réinitialiser", command=self.reset_filter).pack(side="left", padx=5)

        # Tableau
        table_frame = ttk.Frame(self)
        table_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        columns = ("fr", "type", "en", "edit", "delete")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("fr", text="Texte français")
        self.tree.heading("type", text="Type")
        self.tree.heading("en", text="")
        self.tree.heading("edit", text="")
        self.tree.heading("delete", text="")
        self.tree.column("type", width=120)
        self.tree.column("fr", width=300)
       
        self.tree.column("en", minwidth=0, width=0, stretch=False)
        self.tree.column("edit", width=40, anchor="center")
        self.tree.column("delete", width=40, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        # Style pour agrandir la police de la colonne Type
        style = ttk.Style(self)
        style.configure("Treeview.TypeColumn", font=("Arial", 14, "bold"))

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Boutons d'action
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="top", fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Ajouter", command=self.add_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.edit_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.delete_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Sauvegarder", command=self.save_json).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Charger", command=self.load_json).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Reconstruire le prompt", command=self.rebuild_prompt).pack(side="right", padx=5)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click_checkbox)
        self.tree.tag_configure("prompt_row", background="#e0e0e0")
        self.tree.tag_configure("type_font", font=("Arial", 12, "bold"))

        self.load_json()

    def apply_filter(self):
        type_ = self.filter_type.get()
        self.filtered_prompts = [
            p for p in self.prompts
            if (type_ == "" or p["type"] == type_)
        ]
        self.refresh_table()

    def reset_filter(self):
        # Supprime cette ligne :
        # self.filter_name.delete(0, tk.END)
        self.filter_type.set("")
        self.filtered_prompts = self.prompts.copy()
        self.refresh_table()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, prompt in enumerate(self.filtered_prompts):
            tags = ()
            if prompt["type"].lower() == "prompt":
                tags = ("prompt_row",)
                delete_icon = ""  # Pas d'icône de suppression
            else:
                delete_icon = "❌"
            self.tree.insert(
                "", "end", iid=idx,
                values=(
                    prompt["fr"], prompt["type"], prompt["en"],
                    "✏️", delete_icon
                ),
                tags=tags + ("type_font",) if self.tree.heading("type") else tags
            )

    def add_prompt(self):
        self.prompt_editor()

    def edit_prompt(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Sélectionnez une ligne à modifier.")
            return
        idx = int(selected[0])
        self.prompt_editor(idx)

    def delete_prompt(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Sélectionnez une ligne à supprimer.")
            return
        idx = int(selected[0])
        prompt = self.filtered_prompts[idx]
        self.prompts.remove(prompt)
        self.apply_filter()

    def prompt_editor(self, idx=None):
        win = tk.Toplevel(self)
        win.title("Édition du prompt")
        win.geometry("900x500")
        win.grid_columnconfigure(1, weight=1)
        fields = {}

        # Texte français
        ttk.Label(win, text="Texte français").grid(row=1, column=0, sticky="nw", padx=10, pady=5)
        fields["fr"] = tk.Text(win, width=60, height=8)
        fields["fr"].grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

        # Texte anglais
        ttk.Label(win, text="Texte anglais").grid(row=2, column=0, sticky="nw", padx=10, pady=5)
        fields["en"] = tk.Text(win, width=60, height=8)
        fields["en"].grid(row=2, column=1, sticky="nsew", padx=10, pady=5)

        # Bouton fr→en (après la création des deux zones)
        def translate_fr2en():
            fields["en"].delete("1.0", tk.END)
            fields["en"].insert("1.0", self.mistral_translate(fields["fr"].get("1.0", tk.END).strip(), src_lang="fr", tgt_lang="en"))

        fr2en_btn = ttk.Button(win, text="fr→en", width=8, command=translate_fr2en)
        fr2en_btn.grid(row=1, column=2, sticky="n", padx=5, pady=5)

        # Bouton en→fr (après la création des deux zones)
        def translate_en2fr():
            fields["fr"].delete("1.0", tk.END)
            fields["fr"].insert("1.0", self.mistral_translate(fields["en"].get("1.0", tk.END).strip(), src_lang="en", tgt_lang="fr"))

        en2fr_btn = ttk.Button(win, text="en→fr", width=8, command=translate_en2fr)
        en2fr_btn.grid(row=2, column=2, sticky="n", padx=5, pady=5)

        # Type
        ttk.Label(win, text="Type").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        fields["type"] = ttk.Combobox(win, values=TYPES, state="readonly")
        fields["type"].grid(row=3, column=1, padx=10, pady=5, sticky="w")
        fields["type"].set(TYPES[0])

        # Pré-remplissage si modification
        if idx is not None:
            prompt = self.filtered_prompts[idx]
            fields["fr"].insert("1.0", prompt["fr"])
            fields["en"].insert("1.0", prompt["en"])
            fields["type"].set(prompt["type"])

        def save():
            data = {
                "fr": fields["fr"].get("1.0", tk.END).strip(),
                "en": fields["en"].get("1.0", tk.END).strip(),
                "type": fields["type"].get()
            }
            # Supprime cette vérification :
            # if not data["nom"]:
            #     messagebox.showwarning("Cham p manquant", "Le nom est obligatoire.")
            #     return
            if idx is not None:
                orig = self.filtered_prompts[idx]
                orig.update(data)
            else:
                self.prompts.append(data)
            self.apply_filter()
            win.destroy()

        ttk.Button(win, text="Enregistrer", command=save).grid(row=4, column=1, pady=10, sticky="e")

        # ...dans prompt_editor, après la création des champs et boutons de traduction...

        def decompose_text():
            texte = fields["fr"].get("1.0", tk.END).strip()
            if not texte:
                messagebox.showwarning("Avertissement", "Le texte français est obligatoire.")
                return

            # Demande à Mistral la décomposition
            question = (
                "Décompose le texte suivant en lignes thématiques :\n"
                "- personnage : description du personnage\n"
                "- habits : description des vêtements (ou nu)\n"
                "- poitrine : description de la poitrine\n"
                "- age : âge ou apparence d'âge\n"
                "- lieux : description du lieu\n"
                "- lumière : description de la lumière\n"
                "- atmosphere : ambiance générale\n"
                "- autres : tout autre élément pertinent\n"
                "Pour chaque ligne, commence par le nom du thème suivi de ':' puis la description extraite ou 'N/A' si non présent.\n"
                "Texte :\n"
                f"{texte}"
            )
            role = "Tu es un assistant qui extrait et classe les informations d'une description d'image."
            result = self.mistral_translate(question, src_lang="fr", tgt_lang="fr")

            # Supprime toutes les lignes sauf 'Prompt' et 'Negative'
            self.prompts = [
                p for p in self.prompts
                if p["type"] in ("Prompt", "Negative")
            ]

            # Ajoute la ligne originelle si elle n'existe pas déjà
            if not any(p["type"] == "Prompt" for p in self.prompts):
                self.prompts.append({
                    "fr": texte,
                    "en": fields["en"].get("1.0", tk.END).strip(),
                    "type": "Prompt"
                })

            # Ajoute chaque ligne extraite comme une nouvelle ligne
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

            self.apply_filter()
            messagebox.showinfo("Décomposition", "Décomposition terminée et lignes ajoutées au tableau.")

        # Ajoute le bouton dans la fiche
        decompose_btn = ttk.Button(win, text="Décomposer", command=decompose_text)
        decompose_btn.grid(row=5, column=1, pady=10, sticky="w")

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            self.edit_prompt()

    def on_click_checkbox(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row:
            return
        idx = int(row)
        if col == "#1":  # Case à cocher
            prompt = self.filtered_prompts[idx]
            prompt["checked"] = not prompt.get("checked", False)
            self.refresh_table()
        elif col == "#6":  # edit
            self.edit_prompt(idx)
        elif col == "#7":  # delete
            if tk.messagebox.askyesno("Suppression", "Supprimer cette ligne ?"):
                prompt = self.filtered_prompts[idx]
                self.prompts.remove(prompt)
                self.apply_filter()

    def save_json(self):
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.prompts, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo("Sauvegarde", "Fichier JSON sauvegardé.")

    def load_json(self):
        
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.prompts = json.load(f)
        else:
            
            self.prompts = []
        self.filtered_prompts = self.prompts.copy()
        self.refresh_table()

    def mistral_translate(self, text, src_lang="fr", tgt_lang="en"):
        question = f"Traduis le texte suivant du {src_lang} vers le {tgt_lang} :"
        role = "Tu es un traducteur professionnel. Réponds uniquement par la traduction, sans explication."
        content = text
        return get_mistral_answer(question, role, content)

    def rebuild_prompt(self):
        # Récupère toutes les lignes sauf 'Prompt' et 'Negative'
        lignes = [p for p in self.prompts if p["type"].lower() not in ("prompt", "negative")]
        if not lignes:
            messagebox.showinfo("Info", "Aucune ligne à concaténer pour ce prompt.")
            return
        texte_concat = "\n".join(p["fr"] for p in lignes if p["fr"].strip())
        if not texte_concat:
            messagebox.showinfo("Info", "Aucun texte à concaténer pour ce prompt.")
            return
        question = (
            "À partir des éléments suivants, écris un prompt cohérent, fluide et naturel pour décrire une image. "
            "Utilise toutes les informations, mais sans répéter les thèmes. "
            "Texte à fusionner :\n"
            f"{texte_concat}"
        )
        prompt_fr = self.mistral_translate(question, src_lang="fr", tgt_lang="fr")
        # Supprime toutes les lignes sauf 'Prompt' et 'Negative'
        self.prompts = [
            p for p in self.prompts
            if p["type"].lower() in ("prompt", "negative")
        ]
        # Met à jour ou ajoute la ligne 'Prompt'
        ligne_prompt = next((p for p in self.prompts if p["type"].lower() == "prompt"), None)
        if ligne_prompt is None:
            ligne_prompt = {
                "fr": "",
                "en": "",
                "type": "Prompt"
            }
            self.prompts.append(ligne_prompt)
        ligne_prompt["fr"] = prompt_fr
        prompt_en = self.mistral_translate(prompt_fr, src_lang="fr", tgt_lang="en")
        ligne_prompt["en"] = prompt_en
        self.apply_filter()
        messagebox.showinfo("Reconstruit", "Le prompt a été reconstruit et mis à jour.")

@cy_analyse_prompt.route('/open_prompt_table', methods=['POST'])
def prompt_table_open():
    file_path = request.json.get('file_path')
    file_name = request.json.get('file_name')
    isdependon = request.json.get('isDependOn', False)
    num_dossier = request.json.get('num_dossier', "")
    descriptif = request.json.get('descriptif', "")
    print(f"File path: {file_path}, File name: {file_name}, isDependOn: {isdependon}, num_dossier: {num_dossier}, descriptif: {descriptif}")
    if not file_path:
        file_path = "prompts.json"
    app = PromptTableApp(
        file_path=file_path,
        isDependOn=isdependon,
        num_dossier=num_dossier,
        nom_fichier=file_name,
        descriptif=descriptif
    )
    app.mainloop()
    return "OK"


""" if __name__ == "__main__":
    app = PromptTableApp()
    app.mainloop() """