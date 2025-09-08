#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaires pour la gestion cohérente de l'environnement virtuel

Ce module fournit des fonctions pour s'assurer que tous les appels subprocess
utilisent l'environnement virtuel .venv du projet
"""

import os
import sys
import subprocess
from typing import List, Optional


def get_venv_python_path() -> str:
    """
    Retourne le chemin vers l'exécutable Python de l'environnement virtuel
    
    Returns:
        str: Chemin absolu vers python.exe dans .venv
    
    Raises:
        FileNotFoundError: Si l'exécutable Python n'est pas trouvé
    """
    # Détecter le répertoire racine du projet
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # Remonte d'un niveau depuis backend/
    
    # Chemin vers l'environnement virtuel
    if os.name == 'nt':  # Windows
        venv_python = os.path.join(project_root, '.venv', 'Scripts', 'python.exe')
    else:  # Unix/Linux/macOS
        venv_python = os.path.join(project_root, '.venv', 'bin', 'python')
    
    venv_python = os.path.abspath(venv_python)
    
    if not os.path.isfile(venv_python):
        raise FileNotFoundError(
            f"L'exécutable Python de l'environnement virtuel n'a pas été trouvé à : {venv_python}\n"
            f"Assurez-vous que l'environnement virtuel .venv est correctement installé."
        )
    
    return venv_python


def get_backend_script_path(script_name: str) -> str:
    """
    Retourne le chemin absolu vers un script dans le dossier backend
    
    Args:
        script_name (str): Nom du script (avec ou sans .py)
    
    Returns:
        str: Chemin absolu vers le script
    
    Raises:
        FileNotFoundError: Si le script n'est pas trouvé
    """
    if not script_name.endswith('.py'):
        script_name += '.py'
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, script_name)
    script_path = os.path.abspath(script_path)
    
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Le script '{script_name}' n'a pas été trouvé à : {script_path}")
    
    return script_path


def run_python_script(script_name: str, args: Optional[List[str]] = None, 
                     cwd: Optional[str] = None) -> subprocess.Popen:
    """
    Lance un script Python en utilisant l'environnement virtuel
    
    Args:
        script_name (str): Nom du script à lancer
        args (List[str], optional): Arguments à passer au script
        cwd (str, optional): Répertoire de travail
    
    Returns:
        subprocess.Popen: Processus lancé
    
    Raises:
        FileNotFoundError: Si Python ou le script n'est pas trouvé
    """
    venv_python = get_venv_python_path()
    script_path = get_backend_script_path(script_name)
    
    if args is None:
        args = []
    
    command = [venv_python, script_path] + args
    
    print(f"[VENV] Lancement : {' '.join(command)}")
    print(f"[VENV] Python venv : {venv_python}")
    print(f"[VENV] Script : {script_path}")
    
    return subprocess.Popen(command, cwd=cwd)


def run_python_command(args: List[str], cwd: Optional[str] = None) -> subprocess.Popen:
    """
    Lance une commande Python en utilisant l'environnement virtuel
    
    Args:
        args (List[str]): Arguments Python (par ex: ["-m", "pip", "install", "package"])
        cwd (str, optional): Répertoire de travail
    
    Returns:
        subprocess.Popen: Processus lancé
    
    Raises:
        FileNotFoundError: Si Python n'est pas trouvé
    """
    venv_python = get_venv_python_path()
    command = [venv_python] + args
    
    print(f"[VENV] Commande Python : {' '.join(command)}")
    
    return subprocess.Popen(command, cwd=cwd)


def validate_venv_setup() -> bool:
    """
    Valide que l'environnement virtuel est correctement configuré
    
    Returns:
        bool: True si l'environnement virtuel est valide
    """
    try:
        venv_python = get_venv_python_path()
        print(f"[VENV] Validation : Python trouvé à {venv_python}")
        
        # Vérifier que c'est bien un environnement virtuel
        result = subprocess.run([venv_python, "-c", "import sys; print(hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip() == "True":
            print("[VENV] ✓ Environnement virtuel détecté")
            return True
        else:
            print("[VENV] ✗ L'exécutable Python ne semble pas être dans un environnement virtuel")
            return False
            
    except Exception as e:
        print(f"[VENV] ✗ Erreur lors de la validation : {e}")
        return False


# Fonction utilitaire pour debug
def debug_python_paths():
    """Affiche les informations de debug sur les chemins Python"""
    print("=== DEBUG PYTHON PATHS ===")
    print(f"sys.executable actuel: {sys.executable}")
    print(f"sys.prefix actuel: {sys.prefix}")
    
    try:
        venv_python = get_venv_python_path()
        print(f"Python venv détecté: {venv_python}")
        
        # Vérifier la version
        result = subprocess.run([venv_python, "--version"], capture_output=True, text=True)
        print(f"Version Python venv: {result.stdout.strip()}")
        
    except Exception as e:
        print(f"Erreur venv: {e}")
    
    print("==========================")
