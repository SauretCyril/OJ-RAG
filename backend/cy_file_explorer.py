#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorateur de fichiers standalone
Lance l'interface d'exploration de fichiers pour un répertoire donné

Usage:
    python cy_file_explorer.py <directory_path> [explorer_type]
    
Arguments:
    directory_path: Chemin vers le répertoire à explorer
    explorer_type: Type d'explorateur (standard, document, config, data, IA)
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Ajouter le répertoire backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cls_local_FileExplorer import cls_local_FileExplorer


def main(directory_path, explorer_type='standard'):
    """
    Lance l'explorateur de fichiers pour le répertoire spécifié
    
    Args:
        directory_path (str): Chemin vers le répertoire à explorer
        explorer_type (str): Type d'explorateur (standard, document, config, data, IA)
    
    Returns:
        bool: True si l'explorateur s'est lancé avec succès, False sinon
    """
    try:
        # Vérifier que le répertoire existe
        if not os.path.exists(directory_path):
            error_msg = f"Le répertoire '{directory_path}' n'existe pas."
            print(f"ERREUR: {error_msg}")
            
            # Afficher un message d'erreur graphique si possible
            try:
                root = tk.Tk()
                root.withdraw()  # Cacher la fenêtre principale
                messagebox.showerror("Erreur", error_msg)
                root.destroy()
            except:
                pass
            
            return False
        
        # Vérifier que c'est bien un répertoire
        if not os.path.isdir(directory_path):
            error_msg = f"'{directory_path}' n'est pas un répertoire."
            print(f"ERREUR: {error_msg}")
            
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Erreur", error_msg)
                root.destroy()
            except:
                pass
            
            return False
        
        # Normaliser le chemin
        directory_path = os.path.abspath(directory_path)
        
        print(f"Lancement de l'explorateur de fichiers...")
        print(f"  - Répertoire: {directory_path}")
        print(f"  - Type: {explorer_type}")
        
        # Créer le titre de la fenêtre
        title = f"Explorateur - {os.path.basename(directory_path)} ({explorer_type})"
        
        # Créer et lancer l'explorateur
        explorer = cls_local_FileExplorer(
            title=title,
            initial_dir=directory_path,
            explorer_type=explorer_type
        )
        
        # Lancer l'interface graphique
        success = explorer.run()
        
        print(f"Explorateur fermé {'avec succès' if success else 'avec erreur'}")
        return success
        
    except Exception as e:
        error_msg = f"Erreur lors du lancement de l'explorateur : {e}"
        print(f"ERREUR: {error_msg}")
        
        # Afficher un message d'erreur graphique si possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erreur", error_msg)
            root.destroy()
        except:
            pass
        
        return False


if __name__ == "__main__":
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python cy_file_explorer.py <directory_path> [explorer_type]")
        print("  directory_path: Chemin vers le répertoire à explorer")
        print("  explorer_type: Type d'explorateur (standard, document, config, data, IA)")
        sys.exit(1)
    
    # Récupérer les arguments
    directory_path = sys.argv[1]
    explorer_type = sys.argv[2] if len(sys.argv) > 2 else 'standard'
    
    # Valider le type d'explorateur
    valid_types = ['standard', 'document', 'config', 'data', 'IA']
    if explorer_type not in valid_types:
        print(f"ATTENTION: Type d'explorateur '{explorer_type}' non reconnu.")
        print(f"Types valides: {', '.join(valid_types)}")
        print("Utilisation du type 'standard' par défaut.")
        explorer_type = 'standard'
    
    # Lancer l'explorateur
    success = main(directory_path, explorer_type)
    
    # Code de sortie
    sys.exit(0 if success else 1)
