import os
import sqlite3
import json
from cy8_paths import normalize_path, ensure_dir, get_default_db_path

class cy8_database_manager:
    """Gestionnaire de base de données pour les prompts - Version cy8"""
    
    def __init__(self, db_path=None):
        # Utiliser le chemin par défaut si aucun chemin n'est fourni
        if db_path is None:
            db_path = get_default_db_path()
        
        # Normaliser et s'assurer que le répertoire existe
        self.db_path = normalize_path(db_path)
        ensure_dir(self.db_path)
        self.conn = None
        self.cursor = None
        self.status_options = ("new", "test", "ok", "nok")
    
    def init_database(self, mode="init"):
        """
        Initialise la base de données
        mode="init" : Recrée la base et ajoute le prompt par défaut
        mode="dev"  : Crée la base si elle n'existe pas, n'ajoute pas le prompt par défaut
        """
        if mode == "init":
            # Mode init: Supprime la base existante et recrée
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    url TEXT,
                    parent INTEGER,
                    model TEXT,
                    comment TEXT,
                    status TEXT DEFAULT 'new'
                )
            ''')
            self.conn.commit()
            self.ensure_additional_columns()
            self.add_default_basic_prompt()
        else:  # mode == "dev"
            # Mode dev: Crée la base si elle n'existe pas
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    url TEXT,
                    parent INTEGER,
                    model TEXT,
                    comment TEXT,
                    status TEXT DEFAULT 'new'
                )
            ''')
            self.conn.commit()
            self.ensure_additional_columns()
    
    def ensure_additional_columns(self):
        """Assurer que toutes les colonnes additionnelles existent"""
        try:
            # Vérifier si les colonnes existent
            self.cursor.execute("PRAGMA table_info(prompts)")
            columns = [row[1] for row in self.cursor.fetchall()]
            
            # Gestion spéciale pour la colonne image (legacy)
            if "image" in columns:
                self.remove_legacy_image_column(columns)
                # Re-vérifier les colonnes après suppression
                self.cursor.execute("PRAGMA table_info(prompts)")
                columns = [row[1] for row in self.cursor.fetchall()]
            
            # Ajouter les colonnes manquantes
            alterations = []
            status_missing = "status" not in columns
            comment_missing = "comment" not in columns
            
            if "parent" not in columns:
                alterations.append("ALTER TABLE prompts ADD COLUMN parent INTEGER")
            if "model" not in columns:
                alterations.append("ALTER TABLE prompts ADD COLUMN model TEXT")
            if comment_missing:
                alterations.append("ALTER TABLE prompts ADD COLUMN comment TEXT")
            if status_missing:
                alterations.append("ALTER TABLE prompts ADD COLUMN status TEXT DEFAULT 'new'")
            
            for statement in alterations:
                self.cursor.execute(statement)
            
            if alterations:
                self.conn.commit()
                
            # Mise à jour des valeurs par défaut pour le statut
            if status_missing:
                try:
                    self.cursor.execute("UPDATE prompts SET status='new' WHERE status IS NULL OR TRIM(status)=''")
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass
                    
        except sqlite3.OperationalError as e:
            print(f"Erreur lors de l'ajout des colonnes : {e}")
    
    def remove_legacy_image_column(self, existing_columns):
        """Supprimer la colonne image legacy et migrer les données"""
        desired_columns = [
            "id", "name", "prompt_values", "workflow", "url",
            "parent", "model", "comment", "status"
        ]
        
        try:
            self.cursor.execute("PRAGMA foreign_keys=off")
            self.cursor.execute("DROP TABLE IF EXISTS prompts_old")
            self.cursor.execute("BEGIN")
            self.cursor.execute("ALTER TABLE prompts RENAME TO prompts_old")
            
            # Créer la nouvelle table
            self.cursor.execute("""
                CREATE TABLE prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    prompt_values JSON,
                    workflow JSON,
                    url TEXT,
                    parent INTEGER,
                    model TEXT,
                    comment TEXT,
                    status TEXT DEFAULT 'new'
                )
            """)
            
            # Migrer les données
            select_parts = []
            for column in desired_columns:
                if column in existing_columns:
                    select_parts.append(column)
                elif column == "status":
                    select_parts.append("'new'")
                else:
                    select_parts.append("NULL")
            
            insert_columns = ", ".join(desired_columns)
            select_clause = ", ".join(select_parts)
            self.cursor.execute(f"INSERT INTO prompts ({insert_columns}) SELECT {select_clause} FROM prompts_old")
            self.cursor.execute("DROP TABLE prompts_old")
            self.conn.commit()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Impossible de supprimer la colonne image : {e}")
        finally:
            try:
                self.cursor.execute("PRAGMA foreign_keys=on")
            except sqlite3.Error:
                pass
    
    def add_default_basic_prompt(self):
        """Ajouter le prompt par défaut basique"""
        default_values = {
            "1": {"id": "6", "type": "prompt", "value": "beautiful scenery nature glass bottle landscape, purple galaxy bottle"},
            "2": {"id": "7", "type": "prompt", "value": "text, watermark"},
            "3": {"id": "3", "type": "seed", "value": 1234567},
            "4": {"id": "9", "type": "SaveImage", "filename_prefix": "basic"}
        }
        
        default_workflow = {
            "3": {"inputs": {"seed": 934966995009374, "steps": 20, "cfg": 8, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler", "_meta": {"title": "KSampler"}},
            "4": {"inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"}, "class_type": "CheckpointLoaderSimple", "_meta": {"title": "Load Checkpoint"}},
            "5": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage", "_meta": {"title": "Empty Latent Image"}},
            "6": {"inputs": {"text": "", "speak_and_recognation": True, "clip": ["4", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "positive"}},
            "7": {"inputs": {"text": "", "speak_and_recognation": True, "clip": ["4", 1]}, "class_type": "CLIPTextEncode", "_meta": {"title": "negative"}},
            "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode", "_meta": {"title": "VAE Decode"}},
            "9": {"inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}, "class_type": "SaveImage", "_meta": {"title": "Save Image"}}
        }
        
        self.cursor.execute(
            "INSERT INTO prompts (name, prompt_values, workflow, url, model, status, comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("basic", json.dumps(default_values, ensure_ascii=False), json.dumps(default_workflow, ensure_ascii=False), "", "", "new", "")
        )
        self.conn.commit()
    
    def derive_model_from_workflow(self, workflow_data):
        """Extraire le nom du modèle depuis le workflow JSON - Fonction originale"""
        if not workflow_data:
            return ""
            
        if isinstance(workflow_data, dict):
            workflow_dict = workflow_data
        else:
            try:
                workflow_dict = json.loads(workflow_data)
            except (TypeError, json.JSONDecodeError):
                return ""
                
        if not isinstance(workflow_dict, dict):
            return ""

        def normalize(model_name: str) -> str:
            base = os.path.basename(model_name)
            root, _ = os.path.splitext(base)
            return root or base or model_name

        def extract_model_name(raw_value):
            if isinstance(raw_value, str) and raw_value:
                return normalize(raw_value)
            if isinstance(raw_value, (list, tuple)):
                for item in raw_value:
                    if isinstance(item, str) and item:
                        return normalize(item)
            return ""

        for node in workflow_dict.values():
            if not isinstance(node, dict):
                continue
            class_type = node.get("class_type")
            if not isinstance(class_type, str):
                continue
            inputs = node.get("inputs", {})
            if not isinstance(inputs, dict):
                continue
            
            if class_type == "CheckpointLoaderSimple":
                model_name = extract_model_name(inputs.get("ckpt_name"))
                if model_name:
                    return model_name
            if class_type.lower() == "unetloader":
                model_name = extract_model_name(inputs.get("unet_name"))
                if model_name:
                    return model_name
        return ""
    
    def get_all_prompts(self):
        """Récupérer tous les prompts avec toutes les colonnes"""
        self.cursor.execute("SELECT id, name, parent, model, workflow, status, comment FROM prompts")
        results = []
        for row in self.cursor.fetchall():
            prompt_id, name, parent, model, workflow, status, comment = row
            # Dériver le modèle si vide
            if not model and workflow:
                model = self.derive_model_from_workflow(workflow)
            results.append((prompt_id, name, parent, model, workflow, status, comment))
        return results
    
    def get_prompt_by_id(self, prompt_id):
        """Récupérer un prompt par son ID"""
        self.cursor.execute("SELECT name, prompt_values, workflow, url, model, comment, status FROM prompts WHERE id=?", (prompt_id,))
        return self.cursor.fetchone()
    
    def update_prompt(self, prompt_id, name, prompt_values, workflow, url, model, comment, status):
        """Mettre à jour un prompt complet"""
        self.cursor.execute(
            "UPDATE prompts SET name=?, prompt_values=?, workflow=?, url=?, model=?, comment=?, status=? WHERE id=?",
            (name, prompt_values, workflow, url, model, comment, status, prompt_id)
        )
        self.conn.commit()
    
    def create_prompt(self, name, prompt_values, workflow, url, model, status, comment, parent=None):
        """Créer un nouveau prompt"""
        self.cursor.execute(
            "INSERT INTO prompts (name, prompt_values, workflow, url, model, status, comment, parent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, prompt_values, workflow, url, model, status, comment, parent)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def delete_prompt(self, prompt_id):
        """Supprimer un prompt"""
        self.cursor.execute("DELETE FROM prompts WHERE id=?", (prompt_id,))
        self.conn.commit()
    
    def prompt_name_exists(self, name):
        """Vérifier si un nom de prompt existe"""
        self.cursor.execute("SELECT 1 FROM prompts WHERE name=? LIMIT 1", (name,))
        return self.cursor.fetchone() is not None
    
    def close(self):
        """Fermer la connexion"""
        if self.conn:
            self.conn.close()