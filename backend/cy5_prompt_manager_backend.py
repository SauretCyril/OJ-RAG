import os
import sqlite3
import requests
from cy_cookies import get_cookie_value

class PromptManager:
    def __init__(self):
        print("[PromptManager] Initialisation...")
        self.current_db_dir = self.get_current_db_dir()
        print(f"[PromptManager] current_db_dir = {self.current_db_dir}")
        if not self.current_db_dir:
            raise Exception("Impossible de récupérer le dossier courant pour la base de prompts.")
        self.db_path = os.path.join(self.current_db_dir, "_prompts_.db")
        print(f"[PromptManager] db_path = {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def get_current_db_dir(self):
        print("[PromptManager] Appel get_current_db_dir()")
        try:
            response = requests.get("http://localhost:5000/get_directory_root")
            print(f"[PromptManager] Réponse Flask status: {response.status_code}")
            response.raise_for_status()
            db_path = get_cookie_value("current_dossier")
            print(f"[PromptManager] Cookie current_dossier = {db_path}")
            if not db_path:
                print("[PromptManager] Aucun chemin de base trouvé dans le cookie.")
                return None
            return db_path
        except Exception as e:
            print(f"[PromptManager] Erreur récupération dossier courant : {e}")
            return None

    def create_table(self):
        print("[PromptManager] Création de la table des prompts...")
        """Crée la table des prompts si elle n'existe pas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_positif TEXT NOT NULL,
                    prompt_positif_changed TEXT,
                    prompt_negatif TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    statut TEXT NOT NULL DEFAULT 'new'
                )
            ''')
            self.conn.commit()
        except Exception as e:
            print(f"[PromptManager] Erreur création table : {e}")

    def add_prompt(self, prompt_positif, prompt_positif_changed, prompt_negatif, image_path, statut="new"):
        print(f"[PromptManager] Ajout prompt : {prompt_positif=} {prompt_positif_changed=} {prompt_negatif=} {image_path=} {statut=}")
        """Ajoute un prompt à la table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO prompts (prompt_positif, prompt_positif_changed, prompt_negatif, image_path, statut) VALUES (?, ?, ?, ?, ?)",
                (prompt_positif, prompt_positif_changed, prompt_negatif, image_path, statut)
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"[PromptManager] Erreur ajout prompt : {e}")
            return None

    def get_all_prompts(self):
        print("[PromptManager] Récupération de tous les prompts...")
        """Récupère tous les prompts."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, prompt_positif, prompt_positif_changed, prompt_negatif, image_path, statut FROM prompts")
            return cursor.fetchall()
        except Exception as e:
            print(f"[PromptManager] Erreur récupération prompts : {e}")
            return []

    def get_prompt_by_id(self, prompt_id):
        print(f"[PromptManager] Récupération du prompt id={prompt_id}")
        """Récupère un prompt par son id."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, prompt_positif, prompt_positif_changed, prompt_negatif, image_path, statut FROM prompts WHERE id = ?", (prompt_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[PromptManager] Erreur récupération prompt par id : {e}")
            return None

    def close(self):
        print("[PromptManager] Fermeture de la connexion à la base de données.")
        """Ferme la connexion à la base de données."""
        try:
            self.conn.close()
        except Exception:
            pass