"""
Utilitaire de gestion des préférences cy8
Permet de visualiser et gérer les cookies et préférences utilisateur
"""

import os
import sys
import json
import argparse

# Ajouter le chemin du backend si nécessaire
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cy8_user_preferences import cy8_user_preferences

def show_info(prefs):
    """Afficher les informations détaillées"""
    print("=== INFORMATIONS SYSTÈME ===")
    info = prefs.get_preferences_info()
    for key, value in info.items():
        print(f"{key:25}: {value}")
    print()
    
    print("=== DERNIÈRE BASE DE DONNÉES ===")
    last_db = prefs.get_last_database_path()
    if last_db:
        exists = "✓ EXISTE" if os.path.exists(last_db) else "✗ INTROUVABLE"
        print(f"Chemin: {last_db}")
        print(f"Statut: {exists}")
    else:
        print("Aucune base définie")
    print()
    
    print("=== BASES RÉCENTES ===")
    recent = prefs.get_recent_databases()
    if recent:
        for i, db_path in enumerate(recent, 1):
            exists = "✓" if os.path.exists(db_path) else "✗"
            current = " (ACTUELLE)" if db_path == last_db else ""
            print(f"{i:2}. {exists} {db_path}{current}")
    else:
        print("Aucune base récente")
    print()
    
    print("=== GÉOMÉTRIE FENÊTRE ===")
    geometry = prefs.get_window_geometry()
    print(f"Géométrie sauvegardée: {geometry or 'Aucune'}")
    print()

def clean_recent(prefs):
    """Nettoyer les bases récentes inexistantes"""
    recent = prefs.get_recent_databases()
    print(f"Vérification de {len(recent)} bases récentes...")
    
    cleaned = 0
    for db_path in recent[:]:  # Copie pour modification pendant iteration
        if not os.path.exists(db_path):
            print(f"Suppression: {db_path} (introuvable)")
            prefs.remove_recent_database(db_path)
            cleaned += 1
    
    if cleaned > 0:
        print(f"✓ {cleaned} base(s) nettoyée(s)")
        print(f"Bases restantes: {len(prefs.get_recent_databases())}")
    else:
        print("✓ Toutes les bases récentes existent")

def clear_all(prefs):
    """Effacer toutes les données"""
    response = input("Effacer TOUTES les préférences et cookies ? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        prefs.clear_recent_databases()
        prefs.set_cookie("last_database_path", "")
        prefs.set_cookie("window_geometry", "")
        print("✓ Toutes les données effacées")
    else:
        print("Annulé")

def clear_recent_only(prefs):
    """Effacer seulement les bases récentes"""
    recent_count = len(prefs.get_recent_databases())
    if recent_count > 0:
        response = input(f"Effacer {recent_count} base(s) récente(s) ? (oui/non): ")
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            prefs.clear_recent_databases()
            print(f"✓ {recent_count} base(s) récente(s) effacée(s)")
        else:
            print("Annulé")
    else:
        print("Aucune base récente à effacer")

def set_default_db(prefs, db_path):
    """Définir une base par défaut"""
    if os.path.exists(db_path):
        prefs.set_last_database_path(db_path)
        print(f"✓ Base par défaut définie: {db_path}")
    else:
        print(f"✗ Erreur: Le fichier {db_path} n'existe pas")

def main():
    parser = argparse.ArgumentParser(description="Gestionnaire des préférences cy8")
    parser.add_argument('--info', action='store_true', help="Afficher les informations")
    parser.add_argument('--clean', action='store_true', help="Nettoyer les bases inexistantes")
    parser.add_argument('--clear-all', action='store_true', help="Effacer toutes les données")
    parser.add_argument('--clear-recent', action='store_true', help="Effacer les bases récentes")
    parser.add_argument('--set-default', metavar='PATH', help="Définir une base par défaut")
    
    args = parser.parse_args()
    
    prefs = cy8_user_preferences()
    
    if args.info or not any(vars(args).values()):
        show_info(prefs)
    
    if args.clean:
        clean_recent(prefs)
    
    if args.clear_all:
        clear_all(prefs)
    
    if args.clear_recent:
        clear_recent_only(prefs)
    
    if args.set_default:
        set_default_db(prefs, args.set_default)

if __name__ == "__main__":
    main()