import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from cy_mistral import get_mistral_answer  # en haut du fichier

TYPES = ["Prompt""personnage", "habits", "lumières", "lieux", 'lumière', "Qualité", 'Atmosphere','Age']


class PromptTableApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tableau de Prompts")
        self.geometry("1100x500")
        self.prompts = []
        self.filtered_prompts = []
        self.file_path = "prompts.json"

        # Zone de filtre
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filtrer par nom:").pack(side="left")
        self.filter_name = tk.Entry(filter_frame)
        self.filter_name.pack(side="left", padx=5)
        ttk.Label(filter_frame, text="Type:").pack(side="left")
        self.filter_type = ttk.Combobox(filter_frame, values=[""] + TYPES, state="readonly")
        self.filter_type.pack(side="left", padx=5)
        self.filter_type.set("")
        ttk.Button(filter_frame, text="Filtrer", command=self.apply_filter).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Réinitialiser", command=self.reset_filter).pack(side="left", padx=5)

        # Tableau
        columns = ("checked", "nom", "fr", "type", "en", "edit", "delete")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("checked", text="✔")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("fr", text="Texte français")
        self.tree.heading("type", text="Type")
        self.tree.heading("en", text="")  # Colonne cachée
        self.tree.heading("edit", text="")
        self.tree.heading("delete", text="")
        self.tree.column("checked", width=40, anchor="center")
        self.tree.column("nom", width=150)
        self.tree.column("fr", width=300)
        self.tree.column("type", width=120)
        self.tree.column("en", minwidth=0, width=0, stretch=False)
        self.tree.column("edit", width=40, anchor="center")
        self.tree.column("delete", width=40, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Ajout d'une scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Boutons d'action
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Ajouter", command=self.add_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.edit_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.delete_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Sauvegarder", command=self.save_json).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Charger", command=self.load_json).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Reconstruire le prompt", command=self.rebuild_prompt).pack(side="right", padx=5)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click_checkbox)

        # ...après self.tree.pack(...)
        self.tree.tag_configure("prompt_row", background="#e0e0e0")  # gris clair, ajuste la couleur si besoin

        self.load_json()

    def apply_filter(self):
        name = self.filter_name.get().lower()
        type_ = self.filter_type.get()
        self.filtered_prompts = [
            p for p in self.prompts
            if (name in p["nom"].lower()) and (type_ == "" or p["type"] == type_)
        ]
        self.refresh_table()

    def reset_filter(self):
        self.filter_name.delete(0, tk.END)
        self.filter_type.set("")
        self.filtered_prompts = self.prompts.copy()
        self.refresh_table()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, prompt in enumerate(self.filtered_prompts):
            checked = "☑" if prompt.get("checked", False) else "☐"
            tags = ()
            if prompt["type"].lower() == "prompt":
                tags = ("prompt_row",)
            self.tree.insert(
                "", "end", iid=idx,
                values=(
                    checked, prompt["nom"], prompt["fr"], prompt["type"], prompt["en"],
                    "✏️", "❌"
                ),
                tags=tags
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

        # Nom
        ttk.Label(win, text="Nom").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        fields["nom"] = tk.Entry(win, width=60)
        fields["nom"].grid(row=0, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

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
            fields["nom"].insert(0, prompt["nom"])
            fields["fr"].insert("1.0", prompt["fr"])
            fields["en"].insert("1.0", prompt["en"])
            fields["type"].set(prompt["type"])

        def save():
            data = {
                "nom": fields["nom"].get(),
                "fr": fields["fr"].get("1.0", tk.END).strip(),
                "en": fields["en"].get("1.0", tk.END).strip(),
                "type": fields["type"].get(),
                "checked": False
            }
            if not data["nom"]:
                messagebox.showwarning("Champ manquant", "Le nom est obligatoire.")
                return
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
            nom_base = fields["nom"].get().strip()
            if not texte or not nom_base:
                messagebox.showwarning("Avertissement", "Le nom et le texte français sont obligatoires.")
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

            # Supprime toutes les lignes du même nom de base SAUF type 'Prompt'
            self.prompts = [
                p for p in self.prompts
                if not (p["nom"] == nom_base and p["type"] != "Prompt")
            ]

            # Ajoute la ligne originelle si elle n'existe pas déjà
            if not any(p["nom"] == nom_base and p["type"] == "Prompt" for p in self.prompts):
                self.prompts.append({
                    "nom": nom_base,
                    "fr": texte,
                    "en": fields["en"].get("1.0", tk.END).strip(),
                    "type": "Prompt",
                    "checked": False
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
                    "nom": nom_base,
                    "fr": fr_text,
                    "en": "",
                    "type": type_clean,
                    "checked": False
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
        # Demande sur quelle "fiche" (nom) travailler
        noms = sorted(set(p["nom"] for p in self.prompts))
        if not noms:
            messagebox.showinfo("Info", "Aucune fiche à reconstruire.")
            return
        # Si plusieurs noms, demande à l'utilisateur
        if len(noms) > 1:
            win = tk.Toplevel(self)
            win.title("Choisir le nom du prompt à reconstruire")
            tk.Label(win, text="Nom du prompt :").pack(padx=10, pady=10)
            var_nom = tk.StringVar(value=noms[0])
            cb = ttk.Combobox(win, values=noms, textvariable=var_nom, state="readonly")
            cb.pack(padx=10, pady=10)
            def valider():
                win.destroy()
                self._do_rebuild_prompt(var_nom.get())
            ttk.Button(win, text="Valider", command=valider).pack(pady=10)
            win.transient(self)
            win.grab_set()
            win.wait_window()
        else:
            self._do_rebuild_prompt(noms[0])

    def _do_rebuild_prompt(self, nom_base):
        # 1. Récupère toutes les lignes du nom sauf type "Prompt"
        lignes = [p for p in self.prompts if p["nom"] == nom_base and p["type"].lower() != "prompt"]
        if not lignes:
            messagebox.showinfo("Info", "Aucune ligne à concaténer pour ce prompt.")
            return
        # 2. Concatène les textes français
        texte_concat = "\n".join(p["fr"] for p in lignes if p["fr"].strip())
        if not texte_concat:
            messagebox.showinfo("Info", "Aucun texte à concaténer pour ce prompt.")
            return
        # 3. Demande à Mistral de reformuler
        question = (
            "À partir des éléments suivants, écris un prompt cohérent, fluide et naturel pour décrire une image. "
            "Utilise toutes les informations, mais sans répéter les thèmes. "
            "Texte à fusionner :\n"
            f"{texte_concat}"
        )
        prompt_fr = self.mistral_translate(question, src_lang="fr", tgt_lang="fr")
        # 4. Met à jour la ligne de type "Prompt"
        ligne_prompt = next((p for p in self.prompts if p["nom"] == nom_base and p["type"].lower() == "prompt"), None)
        if ligne_prompt is None:
            # Crée la ligne si elle n'existe pas
            ligne_prompt = {
                "nom": nom_base,
                "fr": "",
                "en": "",
                "type": "Prompt",
                "checked": False
            }
            self.prompts.append(ligne_prompt)
        ligne_prompt["fr"] = prompt_fr
        # 5. Traduit en anglais
        prompt_en = self.mistral_translate(prompt_fr, src_lang="fr", tgt_lang="en")
        ligne_prompt["en"] = prompt_en
        self.apply_filter()
        messagebox.showinfo("Reconstruit", "Le prompt a été reconstruit et mis à jour.")

if __name__ == "__main__":
    app = PromptTableApp()
    app.mainloop()