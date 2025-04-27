@echo off
REM Changer de lecteur et de répertoire en une seule commande
cd /d G:\G_WCS\OJ-RAG

REM Créer l'environnement virtuel s'il n'existe pas déjà
if not exist .venv\ (
    echo Création de l'environnement virtuel...
    python -m venv .venv
    echo Environnement virtuel créé.
) else (
    echo L'environnement virtuel existe déjà.
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call .venv\Scripts\activate

REM Afficher confirmation et attendre
echo.
echo Environnement virtuel activé. Vous pouvez maintenant exécuter des commandes Python.
echo.
cmd /k