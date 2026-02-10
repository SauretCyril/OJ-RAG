# Guide d'Installation et d'Exécution - OJ-RAG

## Vue d'ensemble de l'application

**OJ-RAG** est une application web basée sur Flask qui intègre des fonctionnalités d'analyse de documents avec l'IA (RAG - Retrieval-Augmented Generation). L'application utilise des modèles de traitement du langage naturel (Mistral AI, transformers) pour analyser des documents PDF, Word, et autres formats.

### Architecture
- **Backend**: Flask (Python) avec deux serveurs
  - Serveur principal: port 5000 (app.py)
  - Serveur local: port 5005 (app_local.py)
- **Frontend**: HTML/CSS/JavaScript (Bootstrap)
- **IA/ML**: Torch, Transformers, LangChain, Mistral AI
- **Documents**: PyPDF2, python-docx, fpdf

---

## Prérequis

### Logiciels requis
1. **Python 3.10 ou supérieur**
   - Vérifier: `python --version`
   - Télécharger depuis: https://www.python.org/downloads/

2. **Git** (pour la gestion de version)
   - Vérifier: `git --version`

3. **Windows** (scripts batch adaptés pour Windows)

### Espace disque
- Minimum **5 GB** d'espace libre (les bibliothèques ML comme torch sont volumineuses)

---

## Procédure d'Installation

### Étape 1: Vérifier l'environnement virtuel

L'environnement virtuel `.venv` existe déjà dans le projet.

**Actions à vérifier:**
```bash
# Vérifier la présence de .venv
dir .venv
```

**Si .venv n'existe pas ou est corrompu:**
```bash
# Supprimer l'ancien environnement
rmdir /s /q .venv

# Créer un nouvel environnement virtuel
python -m venv .venv
```

### Étape 2: Activer l'environnement virtuel

**Option A - Utiliser le script fourni:**
```bash
scripts\open_venv.bat
```

**Option B - Activation manuelle:**
```bash
.venv\Scripts\activate
```

**Vérification:**
Vous devriez voir `(.venv)` au début de votre ligne de commande.

### Étape 3: Installer les dépendances Python

**⚠️ IMPORTANT:** Le fichier `requirements.txt` original contient des dépendances inutilisées (~2.8 GB).
Voir le fichier `.claude/02_analyse_dependances.md` pour les détails.

**Option A - Installation optimisée (RECOMMANDÉE):**
```bash
pip install --upgrade pip
pip install -r .claude/requirements_minimal.txt
```
- Temps d'installation: 5-10 minutes
- Espace disque: ~500 MB

**Option B - Installation complète (si incertain):**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
- Temps d'installation: 20-30 minutes
- Espace disque: ~3.5 GB
- Inclut des packages non utilisés (torch, transformers, langchain, etc.)

**Recommandation:** Utiliser l'option A (installation optimisée). Les packages suivants ont été supprimés car non utilisés dans le code:
- ❌ torch (~2 GB)
- ❌ transformers (~500 MB)
- ❌ langchain (~100 MB)
- ❌ mistralai (~20 MB) - L'API REST est utilisée directement via `requests`
- ❌ scikit-learn (~50 MB)
- ❌ nudenet (~100 MB)
- ❌ watchdog (~5 MB)

### Étape 4: Vérifier les dépendances installées

```bash
pip list
```

**Si vous avez utilisé requirements_minimal.txt (recommandé):**
Vérifier que les packages essentiels sont présents:
- flask
- werkzeug
- numpy
- pandas
- requests
- PyPDF2
- python-docx
- reportlab
- Pillow

**Packages qui NE DOIVENT PAS être présents (si installation optimisée):**
- ❌ torch
- ❌ transformers
- ❌ langchain
- ❌ mistralai
- ❌ nudenet

### Étape 5: Configuration (si nécessaire)

**Variables d'environnement:**
Vérifier si un fichier `.env` est nécessaire pour les clés API:
```bash
# Créer un fichier .env à la racine si nécessaire
# Exemple de contenu:
# MISTRAL_API_KEY=votre_cle_api
# OPENAI_API_KEY=votre_cle_api
```

**Fichiers de configuration:**
- `backend/config/constants.json` - Configuration de l'application
- `data/cookies.json` - Stockage des cookies
- `prompts.json` - Prompts pour l'IA
- `prompt_command.json` - Commandes de prompts

---

## Lancement de l'Application

### Méthode 1: Utiliser le script de démarrage (Recommandé)

```bash
scripts\start_app.bat
```

Ce script:
1. Active automatiquement l'environnement virtuel `.venv`
2. Lance `launcher.py` qui démarre les deux serveurs Flask en parallèle

### Méthode 2: Lancement manuel

```bash
# Activer l'environnement virtuel
.venv\Scripts\activate

# Lancer l'application
python launcher.py
```

### Méthode 3: Lancement individuel des serveurs

```bash
# Activer l'environnement virtuel
.venv\Scripts\activate

# Lancer le serveur principal
python backend\app.py

# Dans un autre terminal, lancer le serveur local
python backend\app_local.py
```

---

## Vérification du Démarrage

### Logs de démarrage attendus

```
Chemin actuel : E:\IACAS\50-Realiser\iacas-ota
Chemin du backend : E:\IACAS\50-Realiser\iacas-ota\backend
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Running on http://127.0.0.1:5005
```

### Accès à l'application

1. **Serveur principal**: http://127.0.0.1:5000
2. **Serveur local**: http://127.0.0.1:5005

Ouvrir votre navigateur et accéder à l'URL principale.

---

## Résolution des Problèmes Courants

### Problème 1: Erreur "ModuleNotFoundError"

**Cause:** Dépendances non installées ou environnement virtuel non activé

**Solution:**
```bash
# Activer l'environnement
.venv\Scripts\activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Problème 2: Erreur avec pywin32

**Cause:** pywin32 nécessite une installation post-install

**Solution:**
```bash
python .venv\Scripts\pywin32_postinstall.py -install
```

### Problème 3: Port déjà utilisé

**Cause:** Les ports 5000 ou 5005 sont déjà utilisés

**Solution:**
```bash
# Trouver le processus utilisant le port
netstat -ano | findstr :5000
netstat -ano | findstr :5005

# Tuer le processus (remplacer PID par le numéro du processus)
taskkill /PID <PID> /F
```

### Problème 4: Erreur de mémoire avec torch

**Cause:** Modèles trop volumineux pour la RAM disponible

**Solution:**
- Fermer les applications non nécessaires
- Utiliser des modèles plus légers
- Augmenter la mémoire virtuelle Windows

### Problème 5: Erreur d'encodage UTF-8

**Cause:** Problème d'encodage Windows

**Solution:**
```bash
# Définir la variable d'environnement
set PYTHONIOENCODING=utf-8
```
(Déjà configuré dans launcher.py)

---

## Structure des Répertoires

```
iacas-ota/
├── .venv/                  # Environnement virtuel Python
├── backend/               # Code backend Flask
│   ├── app.py            # Serveur principal (port 5000)
│   ├── app_local.py      # Serveur local (port 5005)
│   ├── cy_*.py           # Modules fonctionnels
│   └── config/           # Fichiers de configuration
├── scripts/              # Scripts batch
│   ├── start_app.bat     # Démarrer l'application
│   └── open_venv.bat     # Activer l'environnement
├── static/               # Fichiers statiques (CSS, JS)
├── templates/            # Templates HTML
├── data/                 # Données de l'application
├── cache/                # Cache temporaire
├── launcher.py           # Lanceur principal
├── requirements.txt      # Dépendances Python
└── package.json          # Configuration Node (optionnel)
```

---

## Commandes Utiles

### Gestion de l'environnement virtuel

```bash
# Activer
.venv\Scripts\activate

# Désactiver
deactivate

# Recréer l'environnement
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Gestion des dépendances

```bash
# Installer une nouvelle dépendance
pip install <package>

# Mettre à jour requirements.txt
pip freeze > requirements.txt

# Mettre à jour toutes les dépendances
pip install --upgrade -r requirements.txt
```

### Développement

```bash
# Lancer en mode debug (déjà activé dans launcher.py)
python launcher.py

# Vérifier les logs
# Les logs sont affichés dans la console et dans app.log
```

---

## Arrêt de l'Application

### Méthode 1: Arrêt normal
- Appuyer sur `Ctrl+C` dans le terminal

### Méthode 2: Arrêt forcé
```bash
# Tuer tous les processus Python
taskkill /F /IM python.exe /T
```

### Méthode 3: Arrêt sélectif
```bash
# Lister les processus Python
tasklist | findstr python

# Tuer un processus spécifique
taskkill /PID <PID> /F
```

---

## Checklist de Démarrage Rapide

- [ ] Python 3.10+ installé
- [ ] Environnement virtuel `.venv` présent
- [ ] `.venv\Scripts\activate` exécuté
- [ ] `pip install -r requirements.txt` exécuté avec succès
- [ ] `scripts\start_app.bat` ou `python launcher.py` exécuté
- [ ] Navigation vers http://127.0.0.1:5000 réussie
- [ ] Aucune erreur dans les logs de la console

---

## Configuration Avancée

### Variables d'environnement optionnelles

Créer un fichier `.env` à la racine avec:
```
MISTRAL_API_KEY=votre_cle_mistral
OPENAI_API_KEY=votre_cle_openai
FLASK_ENV=development
FLASK_DEBUG=1
```

### Optimisation des performances

1. **Utiliser un GPU** (si disponible):
   - Installer torch avec support CUDA
   - Vérifier: `torch.cuda.is_available()`

2. **Cache**:
   - Le dossier `cache/` stocke les données temporaires
   - Nettoyer régulièrement pour libérer de l'espace

3. **Logs**:
   - Les logs sont dans `app.log`
   - Configurer le niveau de log dans `backend/app.py`

---

## Support et Documentation

### Fichiers de référence
- `READ-ME.md` - Documentation technique du projet
- `DELETED_FIX_README.md` - Notes sur les corrections
- `backend/notes.py` - Notes de développement

### En cas de problème
1. Vérifier les logs dans `app.log`
2. Vérifier la console pour les erreurs Python
3. Vérifier que toutes les dépendances sont installées: `pip list`
4. Vérifier les variables d'environnement
5. Consulter la documentation Flask: https://flask.palletsprojects.com/

---

## Prochaines Étapes

Une fois l'application lancée avec succès:
1. Tester les fonctionnalités principales
2. Vérifier l'intégration avec les APIs (Mistral, etc.)
3. Charger des documents de test
4. Explorer l'interface utilisateur
5. Consulter les logs pour détecter d'éventuels problèmes

---

**Date de création:** 2026-02-03
**Version de l'application:** OJ-RAG v1.0
**Environnement:** Windows, Python 3.10+, Flask
