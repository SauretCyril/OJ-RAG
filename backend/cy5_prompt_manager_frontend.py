import tkinter as tk
from tkinter import ttk, messagebox
from cy5_prompt_manager_backend import PromptManager
import os
from PIL import Image, ImageTk
from tkinter import filedialog

class PromptManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestionnaire de Prompts")
        self.geometry("900x600")
        self.prompt_manager = PromptManager()
        self.image_label = None
        self.current_image = None

        # Widgets
        self.create_widgets()
        self.refresh_prompt_list()

    def create_widgets(self):
        # Liste des prompts
        self.tree = ttk.Treeview(self, columns=("id", "prompt_positif", "prompt_positif_changed", "prompt_negatif", "image_path", "statut"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("prompt_positif", text="Prompt positif")
        self.tree.heading("prompt_positif_changed", text="Prompt positif modifié")
        self.tree.heading("prompt_negatif", text="Prompt négatif")
        self.tree.heading("image_path", text="Chemin image")
        self.tree.heading("statut", text="Statut")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Formulaire d'ajout
        form_frame = ttk.Frame(self)
        form_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(form_frame, text="Prompt positif:").grid(row=0, column=0, sticky="w")
        self.prompt_positif_entry = ttk.Entry(form_frame, width=40)
        self.prompt_positif_entry.grid(row=0, column=1, padx=5)

        ttk.Label(form_frame, text="Prompt positif modifié:").grid(row=1, column=0, sticky="w")
        self.prompt_positif_changed_entry = ttk.Entry(form_frame, width=40)
        self.prompt_positif_changed_entry.grid(row=1, column=1, padx=5)

        ttk.Label(form_frame, text="Prompt négatif:").grid(row=2, column=0, sticky="w")
        self.prompt_negatif_entry = ttk.Entry(form_frame, width=40)
        self.prompt_negatif_entry.grid(row=2, column=1, padx=5)

        ttk.Label(form_frame, text="Chemin image:").grid(row=3, column=0, sticky="w")
        self.image_path_entry = ttk.Entry(form_frame, width=40)
        self.image_path_entry.grid(row=3, column=1, padx=5)

        ttk.Label(form_frame, text="Statut:").grid(row=4, column=0, sticky="w")
        self.statut_var = tk.StringVar(value="new")
        self.statut_combo = ttk.Combobox(form_frame, textvariable=self.statut_var, values=["new", "next", "done"], state="readonly", width=37)
        self.statut_combo.grid(row=4, column=1, padx=5)

        add_btn = ttk.Button(form_frame, text="Ajouter", command=self.add_prompt)
        add_btn.grid(row=5, column=0, columnspan=2, pady=5)

        # Ajout du bouton Parcourir pour le champ image_path
        browse_btn = ttk.Button(form_frame, text="Parcourir...", command=self.browse_image)
        browse_btn.grid(row=3, column=2, padx=5)

        # Ajout du bouton Refresh Image
        refresh_img_btn = ttk.Button(form_frame, text="Refresh Image", command=self.refresh_image)
        refresh_img_btn.grid(row=4, column=2, padx=5)

        # Zone d'affichage de l'image
        self.image_label = ttk.Label(self)
        self.image_label.pack(pady=10)

        # Ajout d'un événement pour sélectionner une ligne et afficher l'image
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def refresh_prompt_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        prompts = self.prompt_manager.get_all_prompts()
        for prompt in prompts:
            self.tree.insert("", "end", values=prompt)

    def add_prompt(self):
        prompt_positif = self.prompt_positif_entry.get().strip()
        prompt_positif_changed = self.prompt_positif_changed_entry.get().strip()
        prompt_negatif = self.prompt_negatif_entry.get().strip()
        image_path = self.image_path_entry.get().strip()
        statut = self.statut_var.get()
        if not prompt_positif or not prompt_negatif or not image_path:
            messagebox.showwarning("Champs manquants", "Veuillez remplir tous les champs obligatoires.")
            return
        result = self.prompt_manager.add_prompt(prompt_positif, prompt_positif_changed, prompt_negatif, image_path, statut)
        if result:
            messagebox.showinfo("Succès", "Prompt ajouté avec succès.")
            self.refresh_prompt_list()
            self.prompt_positif_entry.delete(0, tk.END)
            self.prompt_positif_changed_entry.delete(0, tk.END)
            self.prompt_negatif_entry.delete(0, tk.END)
            self.image_path_entry.delete(0, tk.END)
            self.statut_var.set("new")
        else:
            messagebox.showerror("Erreur", "Erreur lors de l'ajout du prompt.")

    def browse_image(self):
        """Ouvre un dialogue pour sélectionner une image dans /images et remplit le champ image_path."""
        images_dir = os.path.join(self.prompt_manager.current_db_dir, "images")
        file_path = filedialog.askopenfilename(
            title="Choisir une image",
            initialdir=images_dir,
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            # Stocke le chemin relatif à /images
            rel_path = os.path.relpath(file_path, images_dir)
            self.image_path_entry.delete(0, tk.END)
            self.image_path_entry.insert(0, rel_path)

    def refresh_image(self):
        """Affiche l'image correspondant au champ image_path (relatif à /images)."""
        images_dir = os.path.join(self.prompt_manager.current_db_dir, "images")
        rel_path = self.image_path_entry.get().strip()
        if not rel_path:
            messagebox.showwarning("Avertissement", "Aucun chemin d'image renseigné.")
            return
        abs_path = os.path.join(images_dir, rel_path)
        if not os.path.exists(abs_path):
            messagebox.showerror("Erreur", f"Image non trouvée : {abs_path}")
            return
        try:
            img = Image.open(abs_path)
            img.thumbnail((300, 300))
            self.current_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_image)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher l'image : {e}")

    def on_tree_select(self, event):
        """Quand un prompt est sélectionné, affiche l'image correspondante."""
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if len(values) >= 5:
            rel_path = values[4]
            self.image_path_entry.delete(0, tk.END)
            self.image_path_entry.insert(0, rel_path)
            self.refresh_image()

    def on_closing(self):
        self.prompt_manager.close()
        self.destroy()

if __name__ == "__main__":
    app = PromptManagerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)