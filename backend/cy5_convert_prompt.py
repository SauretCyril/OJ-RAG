import tkinter as tk
from tkinter import ttk, messagebox
from cy_mistral import get_mistral_answer

CONVERSION_QUESTION = (
    "Peux-tu reformuler ce prompt pour l'améliorer, le prompt est en anglais "
    "la réponse devra l'être aussi, si il y a une ou plusieurs femme, "
    "il faut vérifier que la ou les poitrines sont naturelles, et plutôt"
    "petites, que la ou les femmes sont rousses avec les cheveux bouclés et ébouriffés."
    "il faut ajouter qu'elle doit avoir un tatouage sur le bras gauche, représentant un serpent."
)

class PromptConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convertisseur de Prompt")
        self.geometry("700x400")
        self.minsize(500, 300)

        ttk.Label(self, text="Prompt à convertir :", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.prompt_text = tk.Text(self, height=7, wrap="word")
        self.prompt_text.pack(fill="both", expand=False, padx=10)

        convert_btn = ttk.Button(self, text="Convertir le prompt", command=self.convert_prompt)
        convert_btn.pack(pady=10)

        ttk.Label(self, text="Prompt converti :", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.result_text = tk.Text(self, height=7, wrap="word", state="normal")
        self.result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def convert_prompt(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Attention", "Veuillez saisir un prompt à convertir.")
            return
        try:
            role = "Tu es un expert en prompts d'image. Réponds uniquement par le prompt reformulé."
            result = get_mistral_answer(CONVERSION_QUESTION, role, prompt)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la conversion : {e}")

if __name__ == "__main__":
    app = PromptConverterApp()
    app.mainloop()