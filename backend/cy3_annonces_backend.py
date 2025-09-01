import sqlite3
import os
from typing import List, Tuple, Optional
from tkinter import messagebox

class AnnouncementManager:
    """Classe pour gérer un tableau d'annonces avec numéro de dossier, URL et contenu"""
    
    def __init__(self, db_path: str):
        """
        Initialiser le gestionnaire d'annonces
        
        Args:
            db_path (str): Chemin vers la base de données SQLite
        """
        self.db_path = os.path.normpath(db_path)
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()
        # self.migrate_announcements_table()

    def connect(self):
        """Établir une connexion à la base de données"""
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Activer les clés étrangères
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
        except sqlite3.Error as e:
            print(f"Erreur de connexion à la base de données: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de se connecter à la base de données: {str(e)}")
            raise
    
    def create_table(self):
        """Créer la table des annonces si elle n'existe pas et ajoute la colonne nature si besoin"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_dossier TEXT NOT NULL,
                    url TEXT NOT NULL,
                    contenu TEXT NOT NULL,
                    -- nature sera ajoutée après si besoin
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    statut TEXT DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'archive', 'créé','envoyé')),
                    UNIQUE(num_dossier, url)
                )
            ''')
            self.conn.commit()
            # # Ajout de la colonne nature si elle n'existe pas déjà
            # self.cursor.execute("PRAGMA table_info(announcements)")
            # columns = [row[1] for row in self.cursor.fetchall()]
            # if "nature" not in columns:
            #     self.cursor.execute("ALTER TABLE announcements ADD COLUMN nature TEXT DEFAULT ''")

            # # Index pour améliorer les performances de recherche
            # self.cursor.execute('''
            #     CREATE INDEX IF NOT EXISTS idx_num_dossier ON announcements(num_dossier)
            # ''')
            # self.cursor.execute('''
            #     CREATE INDEX IF NOT EXISTS idx_url ON announcements(url)
            # ''')
            # self.cursor.execute('''
            #     CREATE INDEX IF NOT EXISTS idx_statut ON announcements(statut)
            # ''')

          

        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la table: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de créer la table: {str(e)}")
            raise

    def migrate_announcements_table(self):
        try:
            print(f"dbg-2000 : migrate_announcements_table")
            # Vérifier si la colonne nature existe déjà
            self.cursor.execute("PRAGMA table_info(announcements)")
            columns = [row[1] for row in self.cursor.fetchall()]
            has_nature = "nature" in columns
            print(f"dbg-2004 : La colonne 'nature' existe : {has_nature}")
            # 1. Renommer l’ancienne table
            self.cursor.execute("ALTER TABLE announcements RENAME TO announcements_old")
            print(f"dbg-2005 : Ancienne table renommée en 'announcements_old'")
            # 2. Créer la nouvelle table avec la contrainte CHECK mise à jour
            self.cursor.execute(f'''
                CREATE TABLE announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_dossier TEXT NOT NULL,
                    url TEXT NOT NULL,
                    contenu TEXT NOT NULL,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    statut TEXT DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'archive', 'créé', 'envoyé', 'N/A')),
                    nature TEXT DEFAULT '',
                    commentaire TEXT DEFAULT '',
                    UNIQUE(num_dossier, url)
                )
            ''')
            print(f"dbg-2006 : Nouvelle table 'announcements' créée avec succès.")
            # 3. Copier les données
            if has_nature:
                self.cursor.execute('''
                    INSERT INTO announcements (id, num_dossier, url, contenu, date_creation, date_modification, statut, nature)
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut, nature
                    FROM announcements_old
                ''')
                print(f"dbg-2007 : Données copiées de 'announcements_old' vers 'announcements' avec succès.")
            else:
                self.cursor.execute('''
                    INSERT INTO announcements (id, num_dossier, url, contenu, date_creation, date_modification, statut)
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements_old
                ''')
                print(f"dbg-2008 : Données copiées de 'announcements_old' vers 'announcements' avec succès.")

            # 4. Supprimer l’ancienne table
            self.cursor.execute("DROP TABLE announcements_old")
            print(f"dbg-2009 : Ancienne table 'announcements_old' supprimée.")
            self.conn.commit()
           
            print("dbg-2010 : Migration terminée avec succès.")
        except sqlite3.Error as e:
            print(f"Erreur lors de la migration: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de migrer la table: {str(e)}")
            self.conn.rollback()
    def add_announcement(self, num_dossier, url, contenu, nature='', statut='actif', commentaire=''):
        """
        Ajouter une nouvelle annonce
        
        Args:
            num_dossier (str): Numéro de dossier
            url (str): URL de l'annonce
            contenu (str): Contenu de l'annonce
            nature (str): Nature de l'annonce
            statut (str): Statut de l'annonce ('actif', 'inactif', 'archive')
            
        Returns:
            int: ID de l'annonce créée ou None en cas d'erreur
        """
        try:
            self.cursor.execute('''
                INSERT INTO announcements (num_dossier, url, contenu, nature, statut, commentaire)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (num_dossier.strip(), url.strip(), contenu.strip(), nature.strip(), statut, commentaire))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", f"Une annonce avec le dossier '{num_dossier}' et l'URL '{url}' existe déjà.")
            return None
        except sqlite3.Error as e:
            print(f"Erreur lors de l'ajout de l'annonce: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible d'ajouter l'annonce: {str(e)}")
            return None
    
    def get_announcement_by_id(self, announcement_id: int) -> Optional[dict]:
        """
        Récupérer une annonce par son ID, retourne un dict {colonne: valeur}
        """
        try:
            columns = self.get_columns()
            self.cursor.execute(f'''
                SELECT * FROM announcements WHERE id = ?
            ''', (announcement_id,))
            row = self.cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération de l'annonce: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de récupérer l'annonce: {str(e)}")
            return None
    
    def get_announcements_by_dossier(self, num_dossier: str) -> List[Tuple]:
        """
        Récupérer toutes les annonces d'un dossier
        
        Args:
            num_dossier (str): Numéro de dossier
            
        Returns:
            list: Liste des annonces du dossier
        """
        try:
            self.cursor.execute('''
                SELECT id, num_dossier, url, contenu, nature, date_creation, date_modification, statut
                FROM announcements WHERE num_dossier = ?
                ORDER BY date_creation DESC
            ''', (num_dossier,))
            
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des annonces: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de récupérer les annonces: {str(e)}")
            return []
    
    def get_all_announcements(self, statut: Optional[str] = None) -> list:
        """
        Récupérer toutes les annonces sous forme de liste de dicts
        """
        try:
            columns = self.get_columns()
            if statut:
                self.cursor.execute(f'''
                    SELECT * FROM announcements WHERE statut = ?
                    ORDER BY date_creation DESC
                ''', (statut,))
            else:
                self.cursor.execute(f'''
                    SELECT * FROM announcements
                    ORDER BY date_creation DESC
                ''')
            rows = self.cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des annonces: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de récupérer les annonces: {str(e)}")
            return []
    
    def update_announcement(self, announcement_id: int, num_dossier: str, url: str, contenu: str, nature: str = '', statut: str = 'actif', commentaire: str = '') -> bool:
        """
        Mettre à jour une annonce existante
        
        Args:
            announcement_id (int): ID de l'annonce
            num_dossier (str): Nouveau numéro de dossier
            url (str): Nouvelle URL
            contenu (str): Nouveau contenu
            statut (str): Nouveau statut
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            self.cursor.execute('''
                UPDATE announcements SET
                    num_dossier = ?, url = ?, contenu = ?, nature = ?, statut = ?, commentaire = ?,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (num_dossier.strip(), url.strip(), contenu.strip(), nature.strip(), statut, commentaire, announcement_id))
            
            self.conn.commit()
            return self.cursor.rowcount > 0
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", f"Une annonce avec le dossier '{num_dossier}' et l'URL '{url}' existe déjà.")
            return False
        except sqlite3.Error as e:
            print(f"Erreur lors de la mise à jour de l'annonce: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de mettre à jour l'annonce: {str(e)}")
            return False
    
    def delete_announcement(self, announcement_id: int) -> bool:
        """
        Supprimer une annonce
        
        Args:
            announcement_id (int): ID de l'annonce à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            self.cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la suppression de l'annonce: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de supprimer l'annonce: {str(e)}")
            return False
    
    def search_announcements(self, search_term: str, search_in: str = 'all') -> List[Tuple]:
        """
        Rechercher des annonces
        
        Args:
            search_term (str): Terme de recherche
            search_in (str): Champ de recherche ('num_dossier', 'url', 'contenu', 'all')
            
        Returns:
            list: Liste des annonces correspondantes
        """
        try:
            search_term = f"%{search_term}%"
            
            if search_in == 'num_dossier':
                query = '''
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements WHERE num_dossier LIKE ?
                    ORDER BY date_creation DESC
                '''
                self.cursor.execute(query, (search_term,))
            elif search_in == 'url':
                query = '''
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements WHERE url LIKE ?
                    ORDER BY date_creation DESC
                '''
                self.cursor.execute(query, (search_term,))
            elif search_in == 'contenu':
                query = '''
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements WHERE contenu LIKE ?
                    ORDER BY date_creation DESC
                '''
                self.cursor.execute(query, (search_term,))
            elif search_in == 'nature':
                query = '''
                    SELECT id, num_dossier, url, contenu, nature, date_creation, date_modification, statut
                    FROM announcements WHERE nature LIKE ?
                    ORDER BY date_creation DESC
                '''
                self.cursor.execute(query, (search_term,))
            else:  # search_in == 'all'
                query = '''
                    SELECT id, num_dossier, url, contenu, nature, date_creation, date_modification, statut
                    FROM announcements 
                    WHERE num_dossier LIKE ? OR url LIKE ? OR contenu LIKE ? OR nature LIKE ?
                    ORDER BY date_creation DESC
                '''
                self.cursor.execute(query, (search_term, search_term, search_term, search_term))
            
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la recherche: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible d'effectuer la recherche: {str(e)}")
            return []
    
    def get_statistics(self) -> dict:
        """
        Obtenir des statistiques sur les annonces
        
        Returns:
            dict: Dictionnaire contenant les statistiques
        """
        try:
            stats = {}
            
            # Nombre total d'annonces
            self.cursor.execute("SELECT COUNT(*) FROM announcements")
            stats['total'] = self.cursor.fetchone()[0]
            
            # Nombre d'annonces par statut
            self.cursor.execute('''
                SELECT statut, COUNT(*) FROM announcements GROUP BY statut
            ''')
            stats['by_status'] = dict(self.cursor.fetchall())
            
            # Nombre de dossiers uniques
            self.cursor.execute("SELECT COUNT(DISTINCT num_dossier) FROM announcements")
            stats['unique_folders'] = self.cursor.fetchone()[0]
            
            return stats
            
        except sqlite3.Error as e:
            print(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {}
    
    def close(self):
        """Fermer la connexion à la base de données"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Destructeur pour fermer automatiquement la connexion"""
        self.close()

    def get_columns(self) -> list:
        """Retourne la liste des noms de colonnes de la table announcements"""
        try:
            self.cursor.execute("PRAGMA table_info(announcements)")
            return [row[1] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"Erreur lors de la récupération des colonnes: {str(e)}")
            return []


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du gestionnaire
    db_path = os.path.join("data", "announcements.db")
    manager = AnnouncementManager(db_path)
    
    # Ajouter quelques annonces d'exemple
    #manager.add_announcement("DOSS001", "https://example.com/annonce1", "Contenu de l'annonce 1")
    #manager.add_announcement("DOSS002", "https://example.com/annonce2", "Contenu de l'annonce 2")
    #manager.add_announcement("DOSS001", "https://example.com/annonce3", "Autre annonce pour le dossier 1")
    
    # Récupérer toutes les annonces
    all_announcements = manager.get_all_announcements()
    print(f"Nombre total d'annonces: {len(all_announcements)}")
    
    # Rechercher des annonces
    search_results = manager.search_announcements("DOSS001", "num_dossier")
    print(f"Annonces pour DOSS001: {len(search_results)}")
    
    # Afficher les statistiques
    stats = manager.get_statistics()
    print(f"Statistiques: {stats}")
    
    # Fermer la connexion
    manager.close()

