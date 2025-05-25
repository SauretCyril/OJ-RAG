@echo off
echo Configuration de l'environnement pour le .clas
echo --------------------------------------------

REM Copie le fichier .clas vers le nouveau répertoire de travail

set /p "TARGET_DIR=Entrez le chemin du répertoire cible (ex: G:\Actions-9-portails): "

if not exist "%TARGET_DIR%" (
    echo Le répertoire %TARGET_DIR% n'existe pas.
    echo Création du répertoire...
    mkdir "%TARGET_DIR%"
)

if exist "g:\G_WCS\OJ-RAG\.clas" (
    echo Copie du fichier .clas vers le répertoire cible...
    copy "g:\G_WCS\OJ-RAG\.clas" "%TARGET_DIR%\.clas"
    echo Fichier .clas copié avec succès.
) else (
    echo Le fichier .clas source n'a pas été trouvé.
)

echo.
echo Configuration terminée.
echo Le fichier .clas a été copié dans %TARGET_DIR%

pause
