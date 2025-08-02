@echo off
echo Démarrage de l'application OJ-RAG...
echo.

cd /d "%~dp0"
cd ..
call .venv\Scripts\activate

echo Environnement virtuel activé.
echo Démarrage de l'exploreur launcher...
rem start "" python backend\exploreur_launcher.py

echo Démarrage de l'application...
python launcher.py

REM Pour arrêter le launcher, vous pouvez fermer la fenêtre ou utiliser taskkill si besoin.
rem taskkill /F /IM python.exe /T