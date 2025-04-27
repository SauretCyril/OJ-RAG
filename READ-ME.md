# Stack Technique Utilisé dans le Projet OJ-RAG

## 1. Backend

**Flask** : Framework web léger pour Python, utilisé pour créer des applications web. Il permet de définir des routes, gérer les requêtes HTTP et servir des fichiers statiques.

- `app.py` : Point d'entrée principal de l'application Flask. Configure les routes, les blueprints et les paramètres de l'application.
- `cy_routes.py` : Contient les routes principales pour la gestion de l'application.
- `cy_cookies.py` : Gère les cookies pour l'application.
- `cy_exploreur.py` : Gère la navigation et l'exploration des fichiers.
- `cy_mistral.py` : Intégration avec l'API Mistral AI pour l'analyse de documents.
- `cy_paths.py` : Gère les chemins utilisés dans l'application.
- `cy_requests.py` : Gère les requêtes HTTP.
- `cy_json_to_pdf.py` : Conversion de données JSON en fichiers PDF.

**Python** : Langage de programmation principal utilisé pour le backend.

- `numpy` : Utilisé pour les calculs numériques.
- `torch` : Utilisé pour les modèles de machine learning.
- `PyPDF2` : Bibliothèque Python pour lire et manipuler des fichiers PDF.
- `python-docx` : Bibliothèque Python pour manipuler des fichiers Word.
- `docx2pdf` : Conversion de fichiers Word en PDF.
- `fpdf` : Bibliothèque Python pour générer des fichiers PDF.
- `transformers` : Bibliothèque pour les modèles de traitement du langage naturel.
- `langchain` : Framework pour développer des applications basées sur des LLM.
- `mistralai` : API Mistral pour l'analyse de texte et la génération de contenu.
- `openai` : API OpenAI pour l'analyse de texte avec des modèles comme GPT.
- `beautifulsoup4` : Bibliothèque Python pour le scraping web.
- `dotenv` : Bibliothèque Python pour charger les variables d'environnement.
- `scikit-learn` : Bibliothèque pour le machine learning et l'analyse de données.

## 2. Frontend

**HTML** : Langage de balisage pour structurer les pages web.

- `templates/index.html` : Page principale de l'application.

**CSS** : Langage de style pour la présentation des pages web.

- `static/css/dialogs.css` : Styles pour les boîtes de dialogue.
- `static/css/RP_styles.css` : Styles généraux pour l'application.

**JavaScript** : Langage de programmation pour les fonctionnalités interactives.

- `static/js/cy_main.js` : Script principal pour l'application.
- `static/js/cy_all_cols.js`, `cy_all_dos_all_rows.js`, `cy_all_dos_filters.js`, etc. : Gestion des dossiers et de l'interface.
- `static/js/cy_dos_functions.js`, `cy_functions_utils.js` : Fonctions utilitaires.
- `static/js/cy_http_client.js` : Client HTTP pour les requêtes AJAX.
- `static/js/cy_state_manager.js`, `cy_table_manager.js` : Gestion de l'état et des tables.
- `static/js/export.js` : Gère l'exportation des données.

**Bootstrap** : Framework CSS pour créer des interfaces utilisateur réactives et modernes.

## 3. Outils et Dépendances

- **Git** : Système de contrôle de version pour gérer le code source.
- **VS Code** : Environnement de développement intégré (IDE).
- **requests** : Bibliothèque Python pour faire des requêtes HTTP.
- **pywin32** : Bibliothèque pour l'intégration avec Windows.
- **pandas** : Bibliothèque pour la manipulation et l'analyse des données.
- **aiofiles** : Opérations de fichiers asynchrones.

## 4. Données et Configuration

- `backend/config/constants.json` : Contient les constantes pour la configuration de l'application.
- `data/cookies.json` : Fichier JSON pour stocker les cookies.
- `requirements.txt` : Liste des dépendances Python pour l'application.

## 5. Scripts

- `scripts/open_venv.bat` : Script pour activer l'environnement virtuel.
- `scripts/start_app.bat` : Script pour démarrer l'application.
- `launcher.py` : Script Python pour lancer l'application.

## 6. Procédure d'Installation

Pour installer et exécuter le projet sur votre PC portable, suivez ces étapes :

1. **Prérequis** : Assurez-vous d'avoir Python installé (Python 3.10 ou supérieur recommandé).

2. **Créez un environnement virtuel** :
   ```
   python -m venv venv
   ```

3. **Activez l'environnement virtuel** :
   - Sur Windows : `venv\Scripts\activate`
   - Ou utilisez le script : `scripts\open_venv.bat`

4. **Installez les dépendances** :
   ```
   pip install -r requirements.txt
   ```
   Note : Certaines bibliothèques comme torch peuvent prendre du temps à télécharger en raison de leur taille.

5. **Lancez l'application** :
   - Utilisez le script : `scripts\start_app.bat`
   - Ou directement : `python launcher.py`
   - Ou : `python backend\app.py`

L'application devrait maintenant être accessible à l'adresse http://127.0.0.1:5000 dans votre navigateur web.

## Conclusion

Le projet OJ-RAG utilise une architecture basée sur Flask pour le backend et une combinaison de HTML, CSS et JavaScript pour le frontend. Il intègre des outils et des bibliothèques modernes pour l'analyse de documents, l'intelligence artificielle, et la génération de rapports. Le projet est bien structuré avec une séparation claire des responsabilités entre les différents composants.