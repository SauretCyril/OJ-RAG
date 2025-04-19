@echo off
echo Démarrage de l'application OJ-RAG...
echo.

cd /d "%~dp0"
call venv\Scripts\activate

echo Environnement virtuel activé.
echo Démarrage de l'application...
echo.

python launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Une erreur s'est produite lors du démarrage. Code: %ERRORLEVEL%
    echo Vérifiez que toutes les dépendances sont installées.
    pause
)