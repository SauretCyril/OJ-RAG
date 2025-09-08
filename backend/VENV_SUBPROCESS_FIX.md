# Correction des appels subprocess pour l'environnement virtuel

## Problème identifié

Plusieurs fichiers dans le projet utilisaient des appels `subprocess` qui n'utilisaient pas l'environnement virtuel `.venv`, causant des erreurs de dépendances et d'environnement.

## Solution mise en place

### 1. Module utilitaire `cy_venv_utils.py`

Un module centralisé a été créé pour gérer tous les appels subprocess :

- `get_venv_python_path()`: Retourne le chemin vers python.exe dans .venv
- `run_python_script()`: Lance un script Python avec l'environnement virtuel
- `validate_venv_setup()`: Valide la configuration de l'environnement virtuel
- `debug_python_paths()`: Affiche des informations de debug

### 2. Corrections apportées

#### `backend/app.py`
- ✅ `run_annonces_gui()`: Utilise maintenant `run_python_script('cy3_annonces_gui')`
- ✅ `run_analyse_prompt()`: Utilise maintenant `run_python_script('cy2_analyse_prompt')`
- ✅ `run_images_production()`: Utilise maintenant `run_python_script('cy2_app_images')`
- ✅ `get_local_FileExplorer()`: Utilise maintenant `run_python_script('cy_file_explorer')`
- ✅ `get_local_PromptTable()`: Utilise maintenant threading pour éviter les conflits

#### `backend/cy5_process_prompts_manager.py`
- ✅ `open_prompt_analysis()`: Utilise maintenant `run_python_script('cy2_analyse_prompt')`

### 3. Scripts créés

- `backend/cy_file_explorer.py`: Point d'entrée standalone pour l'explorateur de fichiers
- `backend/test_venv_setup.py`: Script de validation de l'environnement virtuel

## Avantages

1. **Cohérence**: Tous les subprocess utilisent le même environnement virtuel
2. **Fiabilité**: Plus d'erreurs de dépendances manquantes
3. **Maintenabilité**: Code centralisé pour les appels subprocess
4. **Debug**: Outils intégrés pour diagnostiquer les problèmes

## Utilisation

### Lancer un script Python
```python
from cy_venv_utils import run_python_script

# Lance un script dans le backend
process = run_python_script('mon_script', ['arg1', 'arg2'])
```

### Valider l'environnement virtuel
```python
from cy_venv_utils import validate_venv_setup

if validate_venv_setup():
    print("✅ Environnement virtuel OK")
else:
    print("❌ Problème avec l'environnement virtuel")
```

### Debug des chemins Python
```python
from cy_venv_utils import debug_python_paths

debug_python_paths()  # Affiche les informations de debug
```

## Test

Exécuter le script de test pour valider la configuration :
```bash
python backend/test_venv_setup.py
```

## Migration d'autres appels subprocess

Pour migrer d'anciens appels subprocess vers cette solution :

**Avant:**
```python
subprocess.Popen(['python', 'mon_script.py', 'arg1'])
```

**Après:**
```python
from cy_venv_utils import run_python_script
run_python_script('mon_script', ['arg1'])
```

## Statut des corrections

- ✅ `backend/app.py` - Toutes les routes corrigées
- ✅ `backend/cy5_process_prompts_manager.py` - Fonction corrigée
- ✅ Scripts de test créés
- ✅ Documentation créée

Le système garantit maintenant que tous les appels subprocess utilisent l'environnement virtuel `.venv` du projet.
