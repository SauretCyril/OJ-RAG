import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from cy_mistral import get_mistral_answer
import os



class PromptConverterApp(tk.Tk):
    def __init__(self, conversion_question, default_prompt=None):
        super().__init__()
        self.title("Convertisseur de Prompt")
        self.geometry("700x500")
        self.minsize(500, 400)
        self.conversion_question = conversion_question
        self.default_prompt = default_prompt
        self.question_file_path = None
        self.role = "Tu es un expert en prompts d'image. Réponds uniquement par le prompt reformulé. ne pas retourner 'Key adjustments from original:' ou commentaire, que le prompt"

        # Frame pour la question
        question_frame = ttk.Frame(self)
        question_frame.pack(fill="x", padx=10, pady=(10, 0))

        # Affichage du chemin du fichier question
        self.question_file_label = ttk.Label(question_frame, text="Aucun fichier chargé", foreground="blue")
        self.question_file_label.pack(anchor="w")

        # Bouton pour charger un fichier question
        load_btn = ttk.Button(question_frame, text="Charger fichier question...", command=self.load_question_file)
        load_btn.pack(anchor="e", pady=(0, 2))

        # Zone pour éditer la question de conversion
        ttk.Label(self, text="Question de conversion :", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(0, 2))
        self.question_text = tk.Text(self, height=4, wrap="word")
        self.question_text.pack(fill="both", expand=False, padx=10)
        self.question_text.insert("1.0", self.conversion_question)
        self.question_text.bind("<<Modified>>", self.on_question_modified)

        ttk.Label(self, text="Prompt à convertir :", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.prompt_text = tk.Text(self, height=7, wrap="word")
        self.prompt_text.pack(fill="both", expand=False, padx=10)
        if self.default_prompt is not None:
            self.prompt_text.insert("1.0", self.default_prompt)

        convert_btn = ttk.Button(self, text="Convertir le prompt", command=self.convert_prompt_ui)
        convert_btn.pack(pady=10)

        ttk.Label(self, text="Prompt converti :", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.result_text = tk.Text(self, height=7, wrap="word", state="normal")
        self.result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def load_question_file(self):
        file_path = filedialog.askopenfilename(
            title="Charger un fichier texte pour la question",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.question_file_path = file_path
            self.question_file_label.config(text=file_path)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.question_text.delete("1.0", tk.END)
                self.question_text.insert("1.0", content)
                self.conversion_question = content
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")

    def on_question_modified(self, event=None):
        # Sauvegarde automatique dans le fichier si chargé
        if self.question_text.edit_modified():
            self.conversion_question = self.question_text.get("1.0", tk.END).strip()
            if self.question_file_path:
                try:
                    with open(self.question_file_path, "w", encoding="utf-8") as f:
                        f.write(self.conversion_question)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible d'enregistrer la question : {e}")
            self.question_text.edit_modified(False)

    def convert_prompt_ui(self):
        self.default_prompt = self.prompt_text.get("1.0", tk.END).strip()
        self.conversion_question = self.question_text.get("1.0", tk.END).strip()
        result = self.convert_prompt()
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", result)

    def convert_prompt(self):
       
        if not self.default_prompt:
            messagebox.showwarning("Attention", "Veuillez saisir un prompt à convertir.")
            return
        if not self.conversion_question:
            messagebox.showwarning("Attention", "Veuillez saisir une question de conversion.")
            return
        try:
            result = get_mistral_answer(self.default_prompt, self.role, self.conversion_question)
            return result
        except Exception as e:
            return  f"Erreur lors de la conversion : {e}"

# Exemple d'utilisation sans interface graphique
# result = convert_prompt_text("your prompt here", "votre question ici")

if __name__ == "__main__":
    CONVERSION_QUESTION = (
        "Peux-tu reformuler ce prompt pour le personnaliser mais tout en ne changeant pas le style, l'ambiance, la lumiere "
        ", le prompt est en anglais, "
        "la réponse devra l'être aussi"
    )
    app = PromptConverterApp(CONVERSION_QUESTION)
    app.mainloop()