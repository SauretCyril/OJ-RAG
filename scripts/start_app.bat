@echo off
setlocal EnableDelayedExpansion

REM Définition des variables
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "REQUIREMENTS_FILE=%PROJECT_DIR%\requirements.txt"
set "LAUNCHER_FILE=%PROJECT_DIR%\launcher.py"

echo Démarrage de l'application OJ-RAG...
echo.
echo Répertoire du script: !SCRIPT_DIR!
echo Répertoire du projet: !PROJECT_DIR!
echo.

REM Aller dans le répertoire du projet
cd /d "!PROJECT_DIR!"
if !errorlevel! neq 0 (
    echo ERREUR: Impossible d'accéder au répertoire du projet: !PROJECT_DIR!
    pause
    exit /b 1
)

REM Vérifier si l'environnement virtuel existe
if not exist "!VENV_DIR!" (
    echo Environnement virtuel non trouvé. Création en cours...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo ERREUR: Impossible de créer l'environnement virtuel
        pause
        exit /b 1
    )
    echo Environnement virtuel créé avec succès.
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call "!VENV_DIR!\Scripts\activate.bat"
if !errorlevel! neq 0 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

echo Environnement virtuel activé.

REM Installer/Mettre à jour les dépendances
echo Vérification et installation des dépendances...
pip install -r "!REQUIREMENTS_FILE!"
if !errorlevel! neq 0 (
    echo AVERTISSEMENT: Problème lors de l'installation des dépendances
)

echo Démarrage de l'application...
echo.
python "!LAUNCHER_FILE!"

if !errorlevel! neq 0 (
    echo.
    echo ERREUR lors du démarrage de l'application (Code: !errorlevel!)
    echo Vérifiez que toutes les dépendances sont correctement installées.
    pause
)

echo.
echo Application fermée.
pause