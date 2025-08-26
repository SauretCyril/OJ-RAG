import requests
import os
from tkinter import messagebox
from cy3_annonces_backend import AnnouncementManager
from cy_cookies import *

def get_current_db():
    try:
        response = requests.get("http://localhost:5000/get_directory_root")
        response.raise_for_status()
        data = response.json()
        db_path = data.get("db_path")
        db_path = get_cookie_value("current_dossier")
        print(f"dbg121: DB Path récupéré: {db_path}")
        if not db_path:
            return False, None, None

        db_path = os.path.join(db_path, "_index_.db")
        if not os.path.exists(db_path):
            return False, None, None

        current_directory = db_path
        print(f"dbg121a: DB Path récupéré: {current_directory}")
        manager = AnnouncementManager(db_path)
        return True, current_directory, manager

    except Exception as e:
        print(f"Erreur lors de la récupération du DB path: {str(e)}")
        messagebox.showerror("Erreur", f"Impossible de récupérer le chemin de la base de données: {str(e)}\nUtilisation du chemin par défaut.")
        return False, None, None