#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour valider la configuration de l'environnement virtuel
"""

import sys
import os

# Ajouter le répertoire backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cy_venv_utils import validate_venv_setup, debug_python_paths, get_venv_python_path, run_python_script

def main():
    print("=== TEST DE L'ENVIRONNEMENT VIRTUEL ===")
    print()
    
    # 1. Afficher les chemins Python actuels
    debug_python_paths()
    print()
    
    # 2. Valider l'environnement virtuel
    print("=== VALIDATION DE L'ENVIRONNEMENT VIRTUEL ===")
    if validate_venv_setup():
        print("✅ Environnement virtuel configuré correctement")
    else:
        print("❌ Problème avec l'environnement virtuel")
        return False
    
    print()
    
    # 3. Test du chemin Python venv
    try:
        venv_python = get_venv_python_path()
        print(f"✅ Chemin Python venv : {venv_python}")
    except Exception as e:
        print(f"❌ Erreur chemin Python venv : {e}")
        return False
    
    # 4. Test de lancement d'un script simple
    print()
    print("=== TEST DE LANCEMENT DE SCRIPT ===")
    try:
        # Créer un script de test temporaire
        test_script_content = '''
import sys
import os
print(f"Test script lancé avec Python : {sys.executable}")
print(f"Environnement virtuel détecté : {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")
print("Test réussi !")
'''
        
        test_script_path = os.path.join(os.path.dirname(__file__), 'test_temp_script.py')
        with open(test_script_path, 'w', encoding='utf-8') as f:
            f.write(test_script_content)
        
        print("Lancement du script de test...")
        process = run_python_script('test_temp_script')
        process.wait()  # Attendre la fin du processus
        
        if process.returncode == 0:
            print("✅ Test de lancement de script réussi")
        else:
            print(f"❌ Test de lancement de script échoué (code {process.returncode})")
            return False
            
        # Nettoyer
        os.remove(test_script_path)
        
    except Exception as e:
        print(f"❌ Erreur lors du test de lancement : {e}")
        return False
    
    print()
    print("=== RÉSUMÉ ===")
    print("🎉 Tous les tests sont passés avec succès !")
    print("L'environnement virtuel est correctement configuré pour tous les subprocess.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
