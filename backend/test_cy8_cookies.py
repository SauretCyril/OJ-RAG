"""
Script de test pour le système de cookies cy8
Teste la persistance des préférences utilisateur
"""

import os
import sys
import tempfile

# Ajouter le chemin du backend si nécessaire
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cy8_user_preferences import cy8_user_preferences

def test_user_preferences():
    """Tester le système de préférences utilisateur"""
    print("=== Test du système de préférences cy8 ===\n")
    
    # Créer une instance
    prefs = cy8_user_preferences()
    
    # Afficher les informations
    info = prefs.get_preferences_info()
    print("Informations sur les préférences:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # Tester les cookies de base de données
    print("=== Test des cookies de base de données ===")
    
    # Base actuelle
    current_db = prefs.get_last_database_path()
    print(f"Base actuelle: {current_db}")
    
    # Bases récentes
    recent = prefs.get_recent_databases()
    print(f"Bases récentes ({len(recent)}):")
    for i, db_path in enumerate(recent, 1):
        exists = "✓" if os.path.exists(db_path) else "✗"
        print(f"  {i}. {exists} {db_path}")
    print()
    
    # Tester la géométrie de fenêtre
    print("=== Test de la géométrie ===")
    geometry = prefs.get_window_geometry()
    print(f"Géométrie sauvegardée: {geometry}")
    print()
    
    # Ajouter une base de test
    test_db_path = os.path.join(tempfile.gettempdir(), "test_cy8.db")
    print(f"=== Test d'ajout de base: {test_db_path} ===")
    
    # Créer un fichier temporaire pour le test
    with open(test_db_path, 'w') as f:
        f.write("test database")
    
    # Définir comme dernière base
    prefs.set_last_database_path(test_db_path)
    print(f"Base ajoutée: {prefs.get_last_database_path()}")
    
    # Vérifier les récentes
    recent_after = prefs.get_recent_databases()
    print(f"Bases récentes après ajout ({len(recent_after)}):")
    for i, db_path in enumerate(recent_after, 1):
        exists = "✓" if os.path.exists(db_path) else "✗"
        current = " (ACTUELLE)" if db_path == prefs.get_last_database_path() else ""
        print(f"  {i}. {exists} {db_path}{current}")
    
    # Nettoyer
    try:
        os.remove(test_db_path)
        print(f"\nFichier de test supprimé: {test_db_path}")
    except:
        pass
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    test_user_preferences()