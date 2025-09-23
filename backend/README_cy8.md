# Gestionnaire de Prompts ComfyUI - Version cy8 Refactorisée

## Description

Cette version cy8 est une refactorisation complète du système de gestion de prompts ComfyUI, organisée en classes modulaires avec une interface utilisateur professionnelle.

## Architecture

### Classes principales :

1. **cy8_database_manager.py** - Gestionnaire de base de données
   - Gestion SQLite avec toutes les colonnes (ID, Name, Status, Model, Comment, Parent)
   - Migration automatique et nettoyage des colonnes legacy
   - Dérivation automatique du modèle depuis le workflow

2. **cy8_popup_manager.py** - Gestionnaire des popups et formulaires
   - Formulaire d'édition de prompt (fonction initiale: prompt_form)
   - Popup multiloras avec tableau éditable
   - Popup d'affichage des images de sortie

3. **cy8_editable_tables.py** - Gestionnaire des tableaux éditables
   - Tableau prompt_values avec édition inline et popups spécialisées
   - Tableau workflow avec édition des inputs
   - Support du double-clic pour différents types de données

4. **cy8_prompts_manager_main.py** - Classe principale orchestratrice
   - Interface utilisateur complète et professionnelle
   - Intégration de tous les gestionnaires
   - Gestion des événements et des actions

## Fonctionnalités implementées

### 0) Tableau des prompts :
- ✅ 0.1) Colonnes : ID, Name, Status, Model, Comment, Parent
- ✅ 0.2) Bouton 'Éditer' pour édition brute (fonction initiale: prompt_form)
- ✅ 0.3) Bouton 'Supprimer'
- ✅ 0.4) Bouton 'Hériter' (fonction initiale: inherit_prompt)
- ✅ 0.5) Bouton 'Nouveau' (fonction initiale: prompt_form)
- ✅ 0.6) Bouton 'Exécuter' (fonction initiale: execute_workflow)
- ✅ 0.7) Bouton 'Analyser' (fonction initiale: open_prompt_analysis)

### 1) Panel détaillé :
- ✅ 1.1) Données prompt_values au format JSON dans tableau éditable
  - ✅ 1.1.0) Double-clic pour édition inline
  - ✅ 1.1.1) Type "output_image" -> popup d'affichage des images
  - ✅ 1.1.2) Type "multiloras" -> popup multiloras (fonction initiale: open_multi_loras_popup)
  - ✅ 1.1.3) Autres types -> popup d'édition élargie

- ✅ 1.2) Données workflow au format JSON dans tableau éditable
  - ✅ 1.2.1) Colonnes : id, class_type, inputs, title
  - ✅ 1.2.1.0) Double-clic pour édition inline
  - ✅ 1.2.2) Clic sur inputs -> tableau éditable attribut:valeur
  - ✅ 1.2.2.1) Première colonne "attribut"
  - ✅ 1.2.2.2) Séparateur ":"
  - ✅ 1.2.2.3) Deuxième colonne "value"

### 2) Base de données :
- ✅ Fonction d'initialisation complète (comme partir de 0)
- ✅ Structure conservée pour récupération des données existantes
- ✅ Migration automatique des colonnes

## Format des données respecté

### Prompt Values (exemple) :
```json
{
    "1": {
        "id": "6",
        "type": "prompt",
        "value": "beautiful scenery nature glass bottle landscape, purple galaxy bottle"
    },
    "2": {
        "id": "7",
        "type": "prompt",
        "value": "text, watermark"
    },
    "3": {
        "id": "3",
        "type": "seed",
        "value": 1234567
    },
    "4": {
        "id": "9",
        "type": "SaveImage",
        "filename_prefix": "basic"
    }
}
```

### Workflow (exemple) :
```json
{
    "3": {
        "inputs": {
            "seed": 934966995009374,
            "steps": 20,
            "cfg": 8,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0]
        },
        "class_type": "KSampler",
        "_meta": {"title": "KSampler"}
    },
    "4": {
        "inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"},
        "class_type": "CheckpointLoaderSimple",
        "_meta": {"title": "Load Checkpoint"}
    }
}
```

## Améliorations apportées

### Design professionnel :
- Interface moderne avec ttk.Style
- Organisation en onglets et panneaux
- Colonnes redimensionnables
- Scrollbars automatiques

### Fonctionnalités avancées :
- Édition inline dans les tableaux
- Popups spécialisées par type de données
- Gestion des images de sortie
- Multiloras avec interface dédiée
- Validation JSON automatique
- Auto-dérivation du modèle

### Architecture modulaire :
- Séparation claire des responsabilités
- Classes réutilisables
- Maintenance facilitée
- Extensibilité améliorée

## Utilisation

```python
from cy8_prompts_manager_main import cy8_prompts_manager

# Lancer l'application
app = cy8_prompts_manager()
app.run()
```

## Tests

Le système a été testé et fonctionne correctement :
- ✅ Démarrage sans erreur
- ✅ Interface utilisateur responsive
- ✅ Base de données opérationnelle
- ✅ Tableaux éditables fonctionnels

## Compatibilité

- Compatible avec les données existantes du système original
- Migration automatique des structures legacy
- Préservation de toutes les fonctionnalités originales
- Interface améliorée et plus intuitive