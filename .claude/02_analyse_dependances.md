# Analyse des Dépendances - OJ-RAG

## Date d'analyse
2026-02-03

## Objectif
Analyser les dépendances listées dans `requirements.txt` pour identifier celles qui sont réellement utilisées dans le code et éliminer les dépendances inutiles.

---

## Résultats de l'Analyse

### ✅ DÉPENDANCES UTILISÉES (À CONSERVER)

| Package | Utilisé dans | Ligne(s) | Raison |
|---------|--------------|----------|--------|
| **flask[async]** | backend/app.py, app_local.py, etc. | Partout | Framework web principal |
| **werkzeug** | backend/app.py | 5 | Dépendance de Flask |
| **numpy** | backend/app.py | 4, 22-28 | NumpyEncoder pour JSON |
| **python-docx** | backend/cy_mistral.py | 1, 26 | Extraction de texte depuis Word |
| **docx2pdf** | backend/cy_routes.py | Importé | Conversion Word vers PDF |
| **fpdf** | backend/cy_routes.py | Importé | Génération de PDF simples |
| **beautifulsoup4** | backend/cy_requests.py | Importé (bs4) | Parsing HTML/XML |
| **python-dotenv** | backend/cy_mistral.py | 10 | Variables d'environnement (.env) |
| **aiofiles** | backend/cy_file_manager.py | Importé | Opérations fichiers async |
| **requests** | backend/cy_mistral.py, cy_requests.py | Partout | Requêtes HTTP (API Mistral) |
| **PyPDF2** | backend/cy_requests.py | Importé | Manipulation de PDF |
| **pywin32** | backend/*.py | Importé (pythoncom) | Intégration Windows |
| **pandas** | backend/cy_mistral.py | 12, 116 | Export Excel (DataFrame) |
| **reportlab** | backend/cy_json_to_pdf.py | 15-19 | Génération PDF avancée |
| **Pillow** | backend/cls_local_FileExplorer.py | Importé (PIL) | Affichage d'images |
| **tqdm** | backend/cls_local_FileExplorer.py | Importé | Barres de progression |

**Note:** `openai` est importé dans le code (détecté dans les imports) mais peut être optionnel selon l'utilisation.

---

### ❌ DÉPENDANCES NON UTILISÉES (À SUPPRIMER)

| Package | Taille approximative | Raison de suppression |
|---------|---------------------|----------------------|
| **torch** | ~2 GB | ❌ Aucun import trouvé dans le code |
| **transformers** | ~500 MB | ❌ Aucun import trouvé dans le code |
| **langchain** | ~100 MB | ❌ Aucun import trouvé dans le code |
| **mistralai** | ~20 MB | ❌ API REST utilisée directement via `requests` |
| **scikit-learn** | ~50 MB | ❌ Aucun import trouvé dans le code |
| **nudenet** | ~100 MB | ❌ Aucun import trouvé dans le code |
| **watchdog** | ~5 MB | ❌ Aucun import trouvé dans le code |

**Gain d'espace disque total: ~2.8 GB**
**Gain de temps d'installation: 15-25 minutes**

---

## Analyse Détaillée par Package

### torch et transformers
- **Statut:** NON UTILISÉS
- **Recherche effectuée:** `import torch`, `from torch`, `import transformers`, `from transformers`
- **Résultat:** 0 occurrence
- **Conclusion:** Ces packages sont probablement des résidus d'une version antérieure du projet qui utilisait des modèles ML locaux. Maintenant, l'application utilise l'API Mistral en ligne.

### langchain
- **Statut:** NON UTILISÉ
- **Conclusion:** Probablement prévu pour une intégration future qui n'a jamais été implémentée.

### mistralai (SDK officiel)
- **Statut:** NON UTILISÉ
- **Alternative utilisée:** L'application utilise l'API REST de Mistral directement via `requests.post()` dans `cy_mistral.py:73`
- **Code concerné:**
```python
url = "https://api.mistral.ai/v1/chat/completions"
response = requests.post(url, headers=headers, json=data)
```

### nudenet
- **Statut:** NON UTILISÉ
- **Commentaire dans requirements.txt:** "# Ajout pour la détection NSFW"
- **Conclusion:** Fonctionnalité de détection NSFW jamais implémentée ou code supprimé.

### scikit-learn
- **Statut:** NON UTILISÉ
- **Conclusion:** Aucune fonctionnalité de machine learning traditionnel implémentée.

### watchdog
- **Statut:** NON UTILISÉ
- **Utilité prévue:** Surveillance de modifications de fichiers
- **Conclusion:** Fonctionnalité jamais implémentée.

---

## Dépendances Optionnelles

### openpyxl
- **Statut:** Optionnel (fallback dans cy_mistral.py:137)
- **Utilité:** Export Excel avec pandas
- **Recommandation:** AJOUTER au requirements.txt (pandas l'utilise pour .xlsx)

### openai
- **Statut:** Utilisé mais peut-être optionnel
- **Recommandation:** CONSERVER si l'API OpenAI est utilisée quelque part

---

## Nouveau fichier requirements.txt Recommandé

```txt
# Framework Web
flask[async]
werkzeug

# Traitement de données
numpy
pandas
openpyxl

# Documents
python-docx
docx2pdf
fpdf
PyPDF2
reportlab

# API et Web
requests
beautifulsoup4
python-dotenv

# Fichiers et système
aiofiles
pywin32
Pillow

# UI et utilitaires
tqdm

# APIs IA (si utilisées)
openai
```

---

## Impact de la Suppression

### Avantages
1. **Réduction de l'espace disque:** ~2.8 GB libérés
2. **Installation plus rapide:** De 30 minutes à 5-10 minutes
3. **Moins de dépendances à maintenir**
4. **Environnement virtuel plus léger**
5. **Moins de conflits potentiels de versions**

### Risques
1. **Aucun** si les packages non utilisés sont correctement identifiés
2. **Risque minimal:** Si du code commenté utilise ces packages
3. **Test recommandé:** Lancer l'application après suppression pour vérifier

---

## Plan d'Action Recommandé

### Étape 1: Sauvegarde
```bash
# Sauvegarder l'ancien requirements.txt
copy requirements.txt requirements.txt.backup
```

### Étape 2: Créer le nouveau requirements.txt
Utiliser le fichier recommandé ci-dessus.

### Étape 3: Recréer l'environnement virtuel
```bash
# Désactiver l'environnement actuel
deactivate

# Supprimer l'ancien environnement
#rmdir /s /q .venv
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue

# Créer un nouvel environnement
python -m venv .venv

# Activer le nouvel environnement
.venv\Scripts\activate

# Installer les nouvelles dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 4: Tester l'application
```bash
# Lancer l'application
python launcher.py

# Vérifier:
# - Les deux serveurs démarrent (ports 5000 et 5005)
# - L'interface web s'affiche
# - Les fonctionnalités principales fonctionnent
# - Aucune erreur d'import dans les logs
```

### Étape 5: Vérification post-installation
```bash
# Lister les packages installés
pip list

# Vérifier la taille de l'environnement
du -sh .venv  # Sur Linux/Mac
# ou
dir .venv  # Sur Windows
```

---

## Tests de Non-Régression

Après la suppression des dépendances inutiles, tester:

1. ✅ Démarrage de l'application
2. ✅ Chargement de la page principale (http://127.0.0.1:5000)
3. ✅ Upload de documents (PDF, Word)
4. ✅ Analyse de documents avec Mistral AI
5. ✅ Export Excel des résultats
6. ✅ Génération de PDF
7. ✅ Navigation dans l'explorateur de fichiers
8. ✅ Affichage d'images
9. ✅ Cookies et session utilisateur

---

## Conclusion

L'analyse révèle que **7 packages sur 24** (29%) ne sont pas utilisés dans le code, représentant environ **2.8 GB** d'espace disque et **15-25 minutes** de temps d'installation.

La suppression de ces dépendances inutiles améliorera significativement:
- La vitesse d'installation
- La taille de l'environnement virtuel
- La maintenabilité du projet
- Les temps de déploiement

**Recommandation:** Procéder à la suppression en suivant le plan d'action ci-dessus, avec tests de non-régression.

---

## Annexe: Commandes de Vérification

```bash
# Vérifier les imports dans le code
grep -r "import torch\|from torch" --include="*.py" .
grep -r "import transformers\|from transformers" --include="*.py" .
grep -r "import langchain\|from langchain" --include="*.py" .
grep -r "import mistralai\|from mistralai" --include="*.py" .
grep -r "import sklearn\|from sklearn" --include="*.py" .
grep -r "import nudenet\|from nudenet" --include="*.py" .
grep -r "import watchdog\|from watchdog" --include="*.py" .

# Lister tous les imports
grep -h "^import \|^from " backend/*.py | sort -u
```
