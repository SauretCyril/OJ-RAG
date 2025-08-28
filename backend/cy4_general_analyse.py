import tkinter as tk
import json
import os
from tkinter import ttk, messagebox
from cy_mistral import get_mistral_answer
from cy_requests import extract_text_from_pdf
from cy_paths import get_cookie_value
import requests
import argparse


class cy4_general_analyse(tk.Tk):
    def __init__(self, question_file=None,numdos=None, question=None, role=None, texte=None, cv_file=None):
        super().__init__()
        self.title("Analyse Générale Mistral")
        self.geometry("900x600")
       

        ##### 1 déterminer le current dossier et le fichier de question

        self.get_current_dossier()
        self.get_file_ask()
        print("dbg-cy4_00 : current dossier = ", self.current_dossier)
        print("dbg-cy4_01 : fichier question_file = ", self.question_file)
        
        ##### 2 déterminer la question depuis un fichier
        default_question = "Posez votre question à Mistral ici."
        if question is None and self.question_file is not None:
            try:
                default_question = self.load_file()
            except Exception:
                default_question = f"Posez votre question à Mistral ici. le fichier {self.question_file} est introuvable."
        print("dbg-cy4_02 : question = ", default_question)
        
        ##### Valeurs par défaut  pour le role
        default_role = "tu es assistant expert en analyse d'offres d'emploi dans le domaine informatique"
        default_role += ": développeur, Analyste, analyste développeur, Testeur logiciel..."

        ##### Valeurs par défaut  pour le texte
        default_texte = "Texte par défaut pour l'analyse."
        # Si numdos et current_dossier sont définis, vérifier et extraire le texte du PDF
        
        if numdos is not None and self.current_dossier is not None:
            self.pdf_file = os.path.normpath(os.path.join(self.current_dossier, f"{numdos}\{numdos}_annonce_.pdf"))
            print("dbg-cy4_05 : pdf_file = ", self.pdf_file)
            if os.path.exists(self.pdf_file):
                try:
                    default_texte = extract_text_from_pdf(self.pdf_file)
                    
                except Exception as e:
                    print(f"Erreur lors de l'extraction du texte du PDF : {e}")
        print("dbg-cy4_06 : default_texte = ", default_texte)
        
        # Détermination du fichier CV et extraction du texte
        default_cv = "Aucun CV trouvé ou extrait."
        if cv_file is None and numdos and self.current_dossier:
            cv_file = os.path.normpath(os.path.join(self.current_dossier, f"{numdos}\{numdos}_CV_CyrilSauret.pdf"))
        self.cv_file = cv_file
        if self.cv_file and os.path.exists(self.cv_file):
            try:
                default_cv = extract_text_from_pdf(self.cv_file)
            except Exception as e:
                print(f"Erreur lors de l'extraction du texte du CV : {e}")

        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Question
        ttk.Label(main_frame, text="Question").pack(anchor="w")
        self.question_textbox = tk.Text(main_frame, height=10, width=100)
        self.question_textbox.pack(fill="x", pady=(0, 10))
        self.question_textbox.insert("1.0", question if question else default_question)

        # Rôle
        ttk.Label(main_frame, text="Rôle").pack(anchor="w")
        self.role_textbox = tk.Text(main_frame, height=4, width=100)
        self.role_textbox.pack(fill="x", pady=(0, 10))
        self.role_textbox.insert("1.0", role if role else default_role)

        # Texte
        ttk.Label(main_frame, text="Texte").pack(anchor="w")
        self.texte_textbox = tk.Text(main_frame, height=6, width=100)
        self.texte_textbox.pack(fill="x", pady=(0, 10))
        self.texte_textbox.insert("1.0", texte if texte else default_texte)

        # CV
        ttk.Label(main_frame, text="CV (texte extrait)").pack(anchor="w")
        self.cv_textbox = tk.Text(main_frame, height=6, width=100)
        self.cv_textbox.pack(fill="x", pady=(0, 10))
        self.cv_textbox.insert("1.0", default_cv)

        # Frame horizontal pour les deux résultats
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill="both", expand=True)

        # Frame pour la question et sa réponse
        question_frame = ttk.Frame(results_frame)
        question_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Bouton pour poser la question à Mistral
        ttk.Button(question_frame, text="Répondre", command=self.ask_mistral).pack(pady=(0, 5))
        ttk.Label(question_frame, text="Résultat question").pack(anchor="w")
        self.result_textbox = tk.Text(question_frame, height=10, width=48, state="normal")
        self.result_textbox.pack(fill="both", expand=True)

        # Frame pour la corrélation et sa réponse
        correlation_frame = ttk.Frame(results_frame)
        correlation_frame.pack(side="left", fill="both", expand=True)

        # Bouton pour calculer la corrélation
        ttk.Button(correlation_frame, text="Corrélation Annonce / CV", command=self.calc_correlation).pack(pady=(0, 5))
        ttk.Label(correlation_frame, text="Résultat corrélation").pack(anchor="w")
        self.correlation_textbox = tk.Text(correlation_frame, height=10, width=48, state="normal")
        self.correlation_textbox.pack(fill="both", expand=True)

    def get_current_dossier(self):
        response = requests.get("http://localhost:5000/get_directory_root")
        response.raise_for_status()
        data = response.json()
        self.current_dossier = get_cookie_value("current_dossier")
        print("dbg-cy4 : current_dossier =", self.current_dossier)

    def get_file_ask(self):
        if not self.current_dossier:
            print("Erreur : current_dossier est None ou vide.")
            self.question_file = None
            return
        self.question_file = os.path.normpath(os.path.join(self.current_dossier, ".ask"))
        if not os.path.exists(self.question_file):
            self.question_file = None

    def load_file(self):
        try:
            if os.path.exists(self.question_file):
                with open(self.question_file, "r", encoding="utf-8") as file:
                    return file.read().strip()
            else:
                return "pas de fichier"
        except Exception as e:
            print(f"Erreur lors du chargement du fichier depuis {self.question_file} : {e}")
            return ""

    

    def ask_mistral(self):
        question = self.question_textbox.get("1.0", tk.END).strip()
        role = self.role_textbox.get("1.0", tk.END).strip()
        texte = self.texte_textbox.get("1.0", tk.END).strip()
        if not question or not role or not texte:
            messagebox.showinfo("Info", "Veuillez remplir la question, le rôle et le texte.")
            return
        try:
            self.config(cursor="watch")
            self.update_idletasks()
            result = get_mistral_answer(question, role, texte)
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

    def calc_correlation(self):
        annonce = self.texte_textbox.get("1.0", tk.END).strip()
        cv = self.cv_textbox.get("1.0", tk.END).strip()
        question = (
            "Compare le texte d'annonce et le CV. "
            "Dis ce qui manque dans le CV par rapport à l'annonce, ce qui est en commun, "
            "et ce que le CV apporte en plus. "
            "Sois synthétique et précis."
        )
        role = "Tu es un assistant RH expert en matching de profils et annonces."
        try:
            self.config(cursor="watch")
            self.update_idletasks()
            from cy_mistral import get_mistral_answer
            result = get_mistral_answer(question, role, f"Annonce : {annonce}\nCV : {cv}")
            self.correlation_textbox.config(state="normal")
            self.correlation_textbox.delete("1.0", tk.END)
            self.correlation_textbox.insert("1.0", result)
            self.correlation_textbox.config(state="normal")
        except Exception as e:
            self.correlation_textbox.config(state="normal")
            self.correlation_textbox.delete("1.0", tk.END)
            self.correlation_textbox.insert("1.0", f"Erreur : {e}")
        finally:
            self.config(cursor="")
            self.update_idletasks()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse Générale Mistral")
    parser.add_argument("--question_file", type=str, default=None, help="Chemin du fichier question (.ask)")
    parser.add_argument("--numdos", type=str, default=None, help="Numéro de dossier")
    parser.add_argument("--question", type=str, default=None, help="Question personnalisée")
    parser.add_argument("--role", type=str, default=None, help="Rôle personnalisé")
    parser.add_argument("--texte", type=str, default=None, help="Texte personnalisé")
    parser.add_argument("--cv_file", type=str, default=None, help="Chemin du fichier CV PDF")

    args = parser.parse_args()

    app = cy4_general_analyse(
        question_file=args.question_file,
        numdos=args.numdos,
        question=args.question,
        role=args.role,
        texte=args.texte,
        cv_file=args.cv_file
    )
    app.mainloop()