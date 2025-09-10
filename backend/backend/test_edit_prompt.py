#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json

# Test simple pour reproduire le problème
def test_edit_prompt():
    # Connexion à la base de données
    conn = sqlite3.connect("g:/tmp/prompts_manager.db")
    cursor = conn.cursor()
    
    # Récupérer le premier prompt
    cursor.execute("SELECT id, name, prompt_values, workflow, image, url FROM prompts LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        prompt_id, name, prompt_values, workflow, image, url = row
        print(f"Données récupérées:")
        print(f"ID: {prompt_id}")
        print(f"Name: {name}")
        print(f"prompt_values: {prompt_values}")
        print(f"workflow: {workflow}")
        print(f"image: {image}")
        print(f"url: {url}")
        
        # Test de création de popup
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale
        
        popup = tk.Toplevel(root)
        popup.title(f"Test - Modifier le prompt: {name}")
        popup.geometry("700x500")
        
        # Variables pour les champs
        name_var = tk.StringVar(value=name)
        url_var = tk.StringVar(value=url or "")
        image_var = tk.StringVar(value=image or "")
        
        print(f"StringVar values:")
        print(f"name_var: '{name_var.get()}'")
        print(f"url_var: '{url_var.get()}'")
        print(f"image_var: '{image_var.get()}'")
        
        # Champs de saisie
        ttk.Label(popup, text="Nom:").pack(anchor="w", padx=10, pady=5)
        name_entry = ttk.Entry(popup, textvariable=name_var, width=60)
        name_entry.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(popup, text="URL:").pack(anchor="w", padx=10, pady=5)
        url_entry = ttk.Entry(popup, textvariable=url_var, width=60)
        url_entry.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(popup, text="Image:").pack(anchor="w", padx=10, pady=5)
        image_entry = ttk.Entry(popup, textvariable=image_var, width=60)
        image_entry.pack(fill="x", padx=10, pady=5)
        
        # Après création, vérifier les valeurs
        print(f"Entry values après création:")
        print(f"name_entry: '{name_entry.get()}'")
        print(f"url_entry: '{url_entry.get()}'")
        print(f"image_entry: '{image_entry.get()}'")
        
        # JSON formaté
        ttk.Label(popup, text="Values (JSON):").pack(anchor="w", padx=10, pady=(10,5))
        values_text = tk.Text(popup, height=8, wrap="word")
        values_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        try:
            values_dict = json.loads(prompt_values) if prompt_values else {}
            values_formatted = json.dumps(values_dict, indent=2, ensure_ascii=False)
            values_text.insert("1.0", values_formatted)
            print(f"JSON Values inséré: {values_formatted[:100]}...")
        except json.JSONDecodeError as e:
            values_text.insert("1.0", prompt_values or "{}")
            print(f"Erreur JSON Values: {e}")
        
        ttk.Label(popup, text="Workflow (JSON):").pack(anchor="w", padx=10, pady=(10,5))
        workflow_text = tk.Text(popup, height=8, wrap="word")
        workflow_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        try:
            workflow_dict = json.loads(workflow) if workflow else {}
            workflow_formatted = json.dumps(workflow_dict, indent=2, ensure_ascii=False)
            workflow_text.insert("1.0", workflow_formatted)
            print(f"JSON Workflow inséré: {workflow_formatted[:100]}...")
        except json.JSONDecodeError as e:
            workflow_text.insert("1.0", workflow or "{}")
            print(f"Erreur JSON Workflow: {e}")
        
        def close_test():
            popup.destroy()
            root.destroy()
        
        ttk.Button(popup, text="Fermer", command=close_test).pack(pady=10)
        
        print("Popup créée, lancement de mainloop...")
        root.mainloop()
        
    else:
        print("Aucun prompt trouvé dans la base de données")
    
    conn.close()

if __name__ == "__main__":
    test_edit_prompt()
