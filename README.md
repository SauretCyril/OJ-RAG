# OJ-RAG : Système d’Analyse et de Gestion de Dossiers

## Présentation

OJ-RAG est une application complète pour l’analyse, la gestion et le classement de dossiers, principalement orientée vers le traitement d’offres d’emploi, de CV et de documents associés. Le projet combine un backend Python (Flask) et un frontend moderne en JavaScript, avec une architecture modulaire pour faciliter l’évolution et la maintenance.

## Modules principaux

- **cy** : Module central regroupant les routes principales de l’application (API, gestion des annonces, configuration, etc.).
- **cy1** : Module dédié à l’exploration et à la gestion des fichiers (explorateur local, navigation, filtres).
- **cy2** : Module spécialisé dans le traitement et l’analyse des images (exploration, marquage, extraction de métadonnées).
- **cy3** : Module pour la gestion avancée des prompts et des interactions IA (génération, analyse, sauvegarde).
- **cy4** : Module d’analyse générale (correlation annonce/CV, extraction de texte, génération de rapports PDF).
- **cy5** : Module pour la gestion des configurations, colonnes et filtres (personnalisation de l’interface et des données).
- **cy6** : Module d’intégration et d’automatisation (scripts, batchs, gestion des versions et des migrations).

## Fonctionnalités

- Exploration et gestion de dossiers et fichiers (PDF, DOCX, images…)
- Extraction et analyse de texte (annonces, CV)
- Intégration IA (Mistral, OpenAI) pour l’analyse automatique
- Génération de rapports et d’index HTML/PDF
- Interface utilisateur réactive (Bootstrap, JS)
- Gestion des colonnes, filtres et configuration dynamique
- Système de notes et commentaires sur chaque dossier

## Installation

1. **Créer un environnement virtuel**  
   `python -m venv venv`

2. **Activer l’environnement**  
   - Windows : `venv\Scripts\activate`
   - Linux/Mac : `source venv/bin/activate`

3. **Installer les dépendances**  
   `pip install -r requirements.txt`

4. **Lancer l’application**  
   - `python launcher.py`  
   - ou `python backend/app.py`

Accéder à l’application sur [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Structure du projet

```
backend/
    cy_routes.py
    cy1_exploreur.py
    cy2_image_process.py
    cy3_prompt_manager.py
    cy4_general_analyse.py
    cy5_columns.py
    cy6_launcher.py
static/
    js/
    css/
templates/
    index.html
    ...
```

## Documentation

Chaque module dispose de commentaires et d’une documentation interne pour faciliter la prise en main.  
Pour plus de détails, consulte le fichier [READ-ME.md](READ-ME.md) ou les docstrings dans le code source.

## Licence

Projet