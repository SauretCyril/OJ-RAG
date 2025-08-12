#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# db_structure_checker.py - Outil de vérification de la structure de functions.db

import os
import sqlite3
import sys

def connect_to_database(db_path):
    """Se connecte à la base de données et retourne la connexion et le curseur"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        return conn, cursor
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        sys.exit(1)

def check_table_exists(cursor, table_name):
    """Vérifie si la table existe dans la base de données"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def get_table_structure(cursor, table_name):
    """Récupère la structure de la table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def check_column_exists(table_structure, column_name):
    """Vérifie si une colonne existe dans la structure de la table"""
    return any(col[1] == column_name for col in table_structure)

def print_table_data(cursor, table_name, limit=5):
    """Affiche les premières lignes de données de la table"""
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        if rows:
            # Récupérer les noms de colonnes
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Afficher l'en-tête
            header = " | ".join(columns)
            print(f"\nDonnées de la table {table_name} (max {limit} lignes):")
            print("-" * len(header))
            print(header)
            print("-" * len(header))
            
            # Afficher les données
            for row in rows:
                print(" | ".join(str(cell) for cell in row))
            print("-" * len(header))
            print(f"Total: {len(rows)} lignes affichées")
        else:
            print(f"\nLa table {table_name} est vide.")
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des données: {e}")

def suggest_corrections(cursor, table_name, table_structure):
    """Suggère des corrections pour la structure de la table"""
    required_columns = [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("name", "TEXT UNIQUE NOT NULL"),
        ("default_directory", "TEXT NOT NULL"),
        ("cible_directory", "TEXT NOT NULL"),
        ("db_path", "TEXT NOT NULL"),
        ("change_value_2", "TEXT DEFAULT 'none'"),
        ("processor_type", "TEXT DEFAULT 'standard'")
    ]
    
    missing_columns = []
    for col_name, col_type in required_columns:
        if not check_column_exists(table_structure, col_name):
            missing_columns.append((col_name, col_type))
    
    if missing_columns:
        print("\nColonnes manquantes:")
        for col_name, col_type in missing_columns:
            print(f"  - {col_name} ({col_type})")
        
        print("\nSQL pour ajouter les colonnes manquantes:")
        for col_name, col_type in missing_columns:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
            print(f"  {sql}")
    
    # Vérifier les colonnes obsolètes ou mal nommées
    column_names = [col[1] for col in table_structure]
    if "changed_value" in column_names and "change_value_2" in column_names:
        print("\nAttention: Les colonnes 'changed_value' et 'change_value_2' existent toutes les deux.")
        print("SQL pour copier les données et supprimer l'ancienne colonne:")
        print(f"  UPDATE {table_name} SET change_value_2 = changed_value WHERE change_value_2 IS NULL;")
        # Note: SQLite ne supporte pas directement DROP COLUMN avant la version 3.35.0
        print("  -- Pour supprimer la colonne 'changed_value', il faudrait recréer la table")
    
    if "changed_value" in column_names and "change_value_2" not in column_names:
        print("\nAttention: La colonne s'appelle 'changed_value' mais le code attend 'change_value_2'.")
        print("Options possibles:")
        print("1. Renommer la colonne (nécessite de recréer la table dans SQLite)")
        print("2. Adapter le code pour utiliser 'changed_value' au lieu de 'change_value_2'")

def list_all_tables_and_fields(cursor):
    """Liste toutes les tables de la base de données et leurs champs"""
    # Récupérer la liste des tables (hors tables système SQLite)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    if not tables:
        print("\nAucune table trouvée dans la base de données.")
        return
    
    print(f"\n=== Liste des {len(tables)} tables et leurs champs ===")
    
    for table in tables:
        table_name = table[0]
        # Récupérer la structure de la table
        table_structure = get_table_structure(cursor, table_name)
        
        print(f"\n## Table: {table_name} ({len(table_structure)} champs)")
        print("-" * 60)
        print("| ID | Nom | Type | Nullable | Défaut | Clé primaire |")
        print("|" + "-"*8 + "|" + "-"*15 + "|" + "-"*10 + "|" + "-"*9 + "|" + "-"*10 + "|" + "-"*13 + "|")
        
        for col in table_structure:
            col_id = str(col[0])
            col_name = col[1]
            col_type = col[2]
            col_nullable = "Oui" if col[3] == 0 else "Non"
            col_default = col[4] or "NULL"
            col_pk = "Oui" if col[5] == 1 else "Non"
            
            print(f"| {col_id.ljust(6)} | {col_name.ljust(13)} | {col_type.ljust(8)} | {col_nullable.ljust(7)} | {str(col_default).ljust(8)} | {col_pk.ljust(11)} |")
    
    print("\n=== Fin de la liste des tables ===")

def main():
    # Demander le chemin de la base de données
    default_path = "g:/G_WCS/OJ-RAG/data/functions.db"
    db_path = input(f"Chemin de la base de données [{default_path}]: ") or default_path
    
    if not os.path.exists(default_path):
        print(f"Erreur: Le fichier {db_path} n'existe pas.")
        sys.exit(1)
    
    # Se connecter à la base de données
    conn, cursor = connect_to_database(db_path)
    list_all_tables_and_fields(cursor)
    exit(0)
    print(f"Vérification de la structure de {db_path}...")
    if not check_table_exists(cursor, "functions"):
        print("Erreur: La table 'functions' n'existe pas dans la base de données.")
        sys.exit(1)
    
    # Récupérer la structure de la table
    table_structure = get_table_structure(cursor, "functions")
    
    # Afficher la structure
    print("\nStructure de la table 'functions':")
    print("ID | Nom | Type | Nullable | Défaut | Clé primaire")
    print("-" * 60)
    for col in table_structure:
        print(f"{col[0]} | {col[1]} | {col[2]} | {'Oui' if col[3] == 0 else 'Non'} | {col[4] or 'NULL'} | {'Oui' if col[5] == 1 else 'Non'}")
    
    # Afficher quelques données
    print_table_data(cursor, "functions")
    
    # Suggérer des corrections
    suggest_corrections(cursor, "functions", table_structure)
    
    # Lister toutes les tables et leurs champs
    list_all_tables_and_fields(cursor)
    
    # Fermer la connexion
    conn.close()
    print("\nVérification terminée.")

if __name__ == "__main__":
    main()