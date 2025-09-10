import sqlite3
import os

def migrate_announcements_table(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vérifier les colonnes existantes
    cursor.execute("PRAGMA table_info(announcements)")
    columns = [row[1] for row in cursor.fetchall()]
    has_nature = "nature" in columns
    has_commentaire = "commentaire" in columns

    # 1. Renommer l’ancienne table
    cursor.execute("ALTER TABLE announcements RENAME TO announcements_old")

    # 2. Créer la nouvelle table avec la contrainte CHECK mise à jour
    cursor.execute('''
        CREATE TABLE announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            num_dossier TEXT NOT NULL,
            url TEXT NOT NULL,
            contenu TEXT NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'archive', 'créé', 'envoyé','N/A')),
            nature TEXT DEFAULT '',
            commentaire TEXT DEFAULT '',
            UNIQUE(num_dossier, url)
        )
    ''')

    # 3. Copier les données
    champs = ["id", "num_dossier", "url", "contenu", "date_creation", "date_modification", "statut"]
    if has_nature:
        champs.append("nature")
    if has_commentaire:
        champs.append("commentaire")

    champs_str = ", ".join(champs)
    cursor.execute(f'''
        INSERT INTO announcements ({champs_str})
        SELECT {champs_str}
        FROM announcements_old
    ''')

    # 4. Supprimer l’ancienne table
    cursor.execute("DROP TABLE announcements_old")

    conn.commit()
    conn.close()
    print("Migration terminée avec succès.")

# Exemple d'utilisation :
if __name__ == "__main__":
    db_path = os.path.join("data", "announcements.db")  # adapte le chemin si besoin
    migrate_announcements_table(db_path)

def addToQueue(self, fileworkflow, filevalues):
    json = self.updateWorkflow(fileworkflow, filevalues)
    
    # Log des données JSON pour débogage
    print("Données JSON envoyées au serveur :")
    print(json)
    
    print("--------------------------------")
    prompt_list = []
    prompt_list.append(queue_add(json))

    nbqueue = len(prompt_list)
    ws = server_connect()
    nb = 0
    print(f"nb workflows = {nbqueue}")

    while nb != nbqueue:
        nb = 0
        for promptId in prompt_list:
            if not workflow_is_running(ws, promptId):
                nb += 1
        print(f"workflow : {promptId}  ->  {nb}/{nbqueue}")

def updateWorkflow(self, fileworkflow, filevalues):
    fileworkflow = self.workflowRoot + "/" + fileworkflow
    filevalues = self.workflowRoot + "/" + filevalues

    print(f"Chemin du fichier workflow : {fileworkflow}")
    print(f"Chemin du fichier values : {filevalues}")

    if os.path.exists(fileworkflow):
        if os.path.exists(filevalues):
            # Générer les données JSON
            json_data = update_workflow(filevalues, fileworkflow)
            print("Données JSON générées par update_workflow :")
            print(json_data)
            return json_data
        else:
            raise ValueError("Invalid values.")
    else:
        raise ValueError("Invalid workflow file does not exist : " + fileworkflow)