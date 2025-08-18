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
        """Créer la table des annonces si elle n'existe pas"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    num_dossier TEXT NOT NULL,
                    url TEXT NOT NULL,
                    contenu TEXT NOT NULL,
                    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    statut TEXT DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'archive')),
                    UNIQUE(num_dossier, url)
                )
            ''')
            
            # Index pour améliorer les performances de recherche
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_num_dossier ON announcements(num_dossier)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON announcements(url)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_statut ON announcements(statut)
            ''')
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la création de la table: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de créer la table: {str(e)}")
            raise
    
    def add_announcement(self, num_dossier: str, url: str, contenu: str, statut: str = 'actif') -> Optional[int]:
        """
        Ajouter une nouvelle annonce
        
        Args:
            num_dossier (str): Numéro de dossier
            url (str): URL de l'annonce
            contenu (str): Contenu de l'annonce
            statut (str): Statut de l'annonce ('actif', 'inactif', 'archive')
            
        Returns:
            int: ID de l'annonce créée ou None en cas d'erreur
        """
        try:
            self.cursor.execute('''
                INSERT INTO announcements (num_dossier, url, contenu, statut)
                VALUES (?, ?, ?, ?)
            ''', (num_dossier.strip(), url.strip(), contenu.strip(), statut))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", f"Une annonce avec le dossier '{num_dossier}' et l'URL '{url}' existe déjà.")
            return None
        except sqlite3.Error as e:
            print(f"Erreur lors de l'ajout de l'annonce: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible d'ajouter l'annonce: {str(e)}")
            return None
    
    def get_announcement_by_id(self, announcement_id: int) -> Optional[Tuple]:
        """
        Récupérer une annonce par son ID
        
        Args:
            announcement_id (int): ID de l'annonce
            
        Returns:
            tuple: (id, num_dossier, url, contenu, date_creation, date_modification, statut) ou None
        """
        try:
            self.cursor.execute('''
                SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                FROM announcements WHERE id = ?
            ''', (announcement_id,))
            
            return self.cursor.fetchone()
            
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
                SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                FROM announcements WHERE num_dossier = ?
                ORDER BY date_creation DESC
            ''', (num_dossier,))
            
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des annonces: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de récupérer les annonces: {str(e)}")
            return []
    
    def get_all_announcements(self, statut: Optional[str] = None) -> List[Tuple]:
        """
        Récupérer toutes les annonces
        
        Args:
            statut (str, optional): Filtrer par statut ('actif', 'inactif', 'archive')
            
        Returns:
            list: Liste de toutes les annonces
        """
        try:
            if statut:
                self.cursor.execute('''
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements WHERE statut = ?
                    ORDER BY date_creation DESC
                ''', (statut,))
            else:
                self.cursor.execute('''
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements
                    ORDER BY date_creation DESC
                ''')
            
            return self.cursor.fetchall()
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des annonces: {str(e)}")
            messagebox.showerror("Erreur Base de Données", f"Impossible de récupérer les annonces: {str(e)}")
            return []
    
    def update_announcement(self, announcement_id: int, num_dossier: str, url: str, contenu: str, statut: str = 'actif') -> bool:
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
                    num_dossier = ?, url = ?, contenu = ?, statut = ?,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (num_dossier.strip(), url.strip(), contenu.strip(), statut, announcement_id))
            
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
            else:  # search_in == 'all'
                query = '''
                    SELECT id, num_dossier, url, contenu, date_creation, date_modification, statut
                    FROM announcements 
                    WHERE num_dossier LIKE ? OR url LIKE ? OR contenu LIKE ?
                    ORDER BY date_creation DESC
                '''
                self.cursor.execute(query, (search_term, search_term, search_term))
            
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


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer une instance du gestionnaire
    db_path = os.path.join("data", "announcements.db")
    manager = AnnouncementManager(db_path)
    
    # Ajouter quelques annonces d'exemple
    manager.add_announcement("DOSS001", "https://example.com/annonce1", "Contenu de l'annonce 1")
    manager.add_announcement("DOSS002", "https://example.com/annonce2", "Contenu de l'annonce 2")
    manager.add_announcement("DOSS001", "https://example.com/annonce3", "Autre annonce pour le dossier 1")
    
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