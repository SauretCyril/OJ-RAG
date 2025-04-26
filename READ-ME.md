Stack Technique Utilisé dans le Projet OJ-RAG
1. Backend
Flask : Framework web léger pour Python, utilisé pour créer des applications web. Il permet de définir des routes, gérer les requêtes HTTP et servir des fichiers statiques.

app.py : Point d'entrée principal de l'application Flask. Configure les routes, les blueprints et les paramètres de l'application.
RP_routes.py : Contient les routes principales pour la gestion des annonces.
cookies.py : Gère les cookies pour l'application.
JO_analyse.py : Contient les fonctions d'analyse des offres d'emploi et des CV.
JO_analyse_gpt.py : Utilise l'API OpenAI pour analyser les offres d'emploi et les CV.
list_realisations.py : Gère les réalisations.
list_requests.py : Gère les requêtes.
ST_steal.py : Contient les fonctions de scraping.
train_IA.py : Contient les fonctions d'entraînement de l'IA.
Python : Langage de programmation principal utilisé pour le backend.

numpy : Utilisé pour les calculs numériques.
torch : Utilisé pour les modèles de machine learning.
PyPDF2 : Bibliothèque Python pour lire et manipuler des fichiers PDF.
BeautifulSoup : Bibliothèque Python pour le scraping web.
dotenv : Bibliothèque Python pour charger les variables d'environnement à partir d'un fichier .env.
fpdf : Bibliothèque Python pour générer des fichiers PDF.
docx : Bibliothèque Python pour manipuler des fichiers Word.
OpenAI API : Utilisé pour l'analyse des offres d'emploi et des CV avec GPT-3.5-turbo.

2. Frontend
HTML : Langage de balisage pour structurer les pages web.

templates/ : Contient les fichiers HTML pour les différentes pages de l'application.
RP_Index.html : Page principale de l'application.
JO_index.html : Page pour la gestion des CV et des offres d'emploi.
CSS : Langage de style pour la présentation des pages web.

static/css/RP_styles.css : Contient les styles pour l'application.
JavaScript : Langage de programmation pour ajouter des fonctionnalités interactives aux pages web.

static/js/ : Contient les fichiers JavaScript pour les fonctionnalités de l'application.
Responses/ : Contient les scripts JavaScript pour les différentes fonctionnalités de l'application.
RP_main.js : Script principal pour la gestion des annonces.
RP_notes.js : Gère les notes.
RP_CRQ.js : Gère les CRQ.
RP_request.js : Gère les requêtes.
export.js : Gère l'exportation des données.
selectRep.js : Gère la sélection des répertoires.
Realisation.js : Gère les réalisations.
Job_offers/ : Contient les scripts JavaScript pour la gestion des offres d'emploi.
JO_resum.js : Gère le résumé des offres d'emploi.
JO_details.js : Affiche les détails des offres d'emploi.
Bootstrap : Framework CSS pour créer des interfaces utilisateur réactives et modernes.

https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css : Utilisé pour les styles Bootstrap.
https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js : Utilisé pour les scripts Bootstrap.
3. Outils et Dépendances
Git : Système de contrôle de version pour gérer le code source.
VS Code : Environnement de développement intégré (IDE) utilisé pour écrire et gérer le code.
pytest : Framework de test pour Python.
requests : Bibliothèque Python pour faire des requêtes HTTP.
4. Données et Configuration
.env : Contient les variables d'environnement pour la configuration de l'application.
cookies.json : Fichier JSON pour stocker les cookies.
paths.py : Contient les chemins utilisés dans l'application.
requirements.txt : Liste des dépendances Python pour l'application.

Conclusion
Le projet OJ-RAG utilise une architecture basée sur Flask pour le backend et une combinaison de HTML, CSS et JavaScript pour le frontend. Il intègre des outils et des bibliothèques modernes pour l'analyse des offres d'emploi et des CV, le scraping web, et la génération de documents. Le projet est bien structuré avec une séparation claire des responsabilités entre les différents composants.