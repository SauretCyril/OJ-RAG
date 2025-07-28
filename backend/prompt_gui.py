import tkinter as tk
from tkinter import ttk
from cy_mistral import get_mistral_answer  # Assurez-vous que cette fonction est définie dans votre module


class PromptSheetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fiche de Prompt")
        self.geometry("700x500")

        self.fr_labels = ["Personnage", "Habits", "Position", "Lumière", "Style de photo", "Accessoires"]
        self.en_labels = ["Character", "Clothes", "Position", "Lighting", "Photo style", "Accessories"]

        # --- Barre d'outils en haut ---
        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x", padx=5, pady=5)

        translate_btn_en = ttk.Button(toolbar, text="Traduire → Anglais", command=self.translate_all)
        translate_btn_en.pack(side="left", padx=5)

        translate_btn_fr = ttk.Button(toolbar, text="Traduire → Français", command=self.translate_all_to_fr)
        translate_btn_fr.pack(side="left", padx=5)
        # --- Fin barre d'outils ---

        tab_control = ttk.Notebook(self)
        self.tab_fr = ttk.Frame(tab_control)
        self.tab_en = ttk.Frame(tab_control)
        tab_control.add(self.tab_fr, text='Français')
        tab_control.add(self.tab_en, text='Anglais')
        tab_control.pack(expand=1, fill='both')

        self.fr_texts = []
        self.en_texts = []

        self.create_prompt_fields(self.tab_fr, self.fr_labels, self.fr_texts)
        self.create_prompt_fields(self.tab_en, self.en_labels, self.en_texts)

    def create_prompt_fields(self, parent, labels, text_list):
        parent.columnconfigure(1, weight=1)
        for i, label in enumerate(labels):
            parent.rowconfigure(i, weight=1)
            lbl = ttk.Label(parent, text=label + " :")
            lbl.grid(row=i, column=0, sticky="nw", padx=10, pady=5)
            txt = tk.Text(parent, height=3, wrap="word")
            txt.grid(row=i, column=1, padx=10, pady=5, sticky="nsew")
            text_list.append(txt)

    def translate_all(self):
        for idx, fr_text_widget in enumerate(self.fr_texts):
            fr_text = fr_text_widget.get("1.0", tk.END).strip()
            if fr_text:
                try:
                    translated = self.mistral_translate(fr_text, src_lang="fr", tgt_lang="en")
                except Exception as e:
                    translated = f"[Erreur traduction: {e}]"
            else:
                translated = ""
            self.en_texts[idx].delete("1.0", tk.END)
            self.en_texts[idx].insert(tk.END, translated)

    def mistral_translate(self, text, src_lang="fr", tgt_lang="en"):
        question = f"Traduis le texte suivant du {src_lang} vers le {tgt_lang} :"
        role = "Tu es un traducteur professionnel. Réponds uniquement par la traduction, sans explication."
        content = text
        return get_mistral_answer(question, role, content)

    def translate_all_to_fr(self):
        for idx, en_text_widget in enumerate(self.en_texts):
            en_text = en_text_widget.get("1.0", tk.END).strip()
            if en_text:
                try:
                    translated = self.mistral_translate(en_text, src_lang="en", tgt_lang="fr")
                except Exception as e:
                    translated = f"[Erreur traduction: {e}]"
            else:
                translated = ""
            self.fr_texts[idx].delete("1.0", tk.END)
            self.fr_texts[idx].insert(tk.END, translated)

if __name__ == "__main__":
    app = PromptSheetApp()
    app.mainloop()