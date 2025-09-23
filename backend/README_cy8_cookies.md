# Système de Cookies et Préférences - cy8

## Vue d'ensemble

Le gestionnaire de prompts cy8 intègre un système de cookies et de préférences utilisateur qui permet de mémoriser :
- La dernière base de données utilisée
- Les bases de données récemment ouvertes
- La géométrie de la fenêtre (position et taille)
- Autres préférences utilisateur

## Localisation des données

### Windows
```
%APPDATA%\cy8_prompts_manager\
├── user_preferences.json    # Préférences générales
└── cookies.json            # Cookies (base récente, géométrie, etc.)
```

### Linux/Mac
```
~/.cy8_prompts_manager/
├── user_preferences.json    # Préférences générales  
└── cookies.json            # Cookies (base récente, géométrie, etc.)
```

## Fonctionnalités

### 1. Mémorisation de la dernière base
- Au démarrage, l'application ouvre automatiquement la dernière base utilisée
- Si la base n'existe plus, utilise la base par défaut
- Chaque changement de base est automatiquement sauvegardé

### 2. Bases récentes
- Liste des 10 dernières bases de données utilisées
- Accessible via le menu "Fichier > Base de données > Bases récentes"
- Affichage dans l'onglet "Data" du panneau de détails
- Nettoyage automatique des bases inexistantes

### 3. Géométrie de fenêtre
- Sauvegarde automatique de la position et taille de fenêtre à la fermeture
- Restauration automatique au démarrage suivant

## Interface utilisateur

### Menu "Fichier > Base de données"
- **Changer de base...** : Sélectionner une base existante
- **Créer nouvelle base...** : Créer une nouvelle base (popup CY8-POPUP-010)
- **Bases récentes** : Liste des bases récemment utilisées avec ouverture directe

### Onglet "Data"
- **Base de données actuelle** : Affichage du chemin complet
- **Actions** : Boutons pour changer ou créer une base
- **Bases récentes** : Liste interactive avec boutons d'action
- **Statistiques** : Informations sur la base courante

## Utilitaires de gestion

### cy8_preferences_manager.py
Script en ligne de commande pour gérer les préférences :

```bash
# Afficher les informations
python cy8_preferences_manager.py --info

# Nettoyer les bases inexistantes
python cy8_preferences_manager.py --clean

# Effacer toutes les données
python cy8_preferences_manager.py --clear-all

# Effacer seulement les bases récentes  
python cy8_preferences_manager.py --clear-recent

# Définir une base par défaut
python cy8_preferences_manager.py --set-default "chemin/vers/base.db"
```

### test_cy8_cookies.py
Script de test pour vérifier le bon fonctionnement du système.

## Architecture technique

### Classe cy8_user_preferences
- **Gestion multi-OS** : Détection automatique du répertoire utilisateur approprié
- **Persistence JSON** : Sauvegarde automatique des modifications
- **Nettoyage intelligent** : Suppression automatique des références inexistantes
- **API simple** : Méthodes get/set pour tous les types de données

### Intégration dans cy8_prompts_manager
- **Initialisation automatique** : Chargement des préférences au démarrage
- **Sauvegarde transparente** : Enregistrement automatique des changements
- **Interface utilisateur** : Menus et onglets intégrés pour la gestion

## Sécurité et robustesse

- **Gestion d'erreurs** : Récupération en cas de fichiers corrompus
- **Validation des chemins** : Vérification de l'existence des bases
- **Fallback** : Utilisation de valeurs par défaut si les préférences sont indisponibles
- **Nettoyage** : Suppression automatique des références obsolètes

## Messages de debug

L'application affiche des messages informatifs :
```
Utilisation de la dernière base: g:\tmp\prompts_manager.db
Géométrie restaurée: 1400x900+114+52
Base sauvegardée dans les cookies: g:\tmp\nouvelle_base.db
```

## Dépannage

### Base par défaut non trouvée
```bash
python cy8_preferences_manager.py --set-default "chemin/valide/base.db"
```

### Réinitialisation complète
```bash
python cy8_preferences_manager.py --clear-all
```

### Nettoyage des bases inexistantes
```bash
python cy8_preferences_manager.py --clean
```

## Notes de développement

- Les cookies sont sauvegardés à chaque modification importante
- La géométrie est sauvegardée uniquement à la fermeture de l'application
- Le système est compatible avec tous les modes de fonctionnement (dev, init, etc.)
- Les popups utilisent le système d'identification CY8-POPUP-XXX (010 pour création de base)