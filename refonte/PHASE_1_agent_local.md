# Phase 1 — Agent local cross-platform

## Objectif
Réécrire `app_local.py` en un agent local léger, sans dépendances Windows,
packagé en exécutable, qui tourne en arrière-plan sur le PC de l'utilisateur
et expose une API REST pour toutes les opérations fichiers.

---

## Contexte

L'architecture actuelle utilise deux serveurs Flask :
- Port 5000 : app principale (VPS à terme)
- Port 5005 : `app_local.py` → Tkinter + Windows uniquement

L'agent local remplace et nettoie le port 5005.
Il est la seule pièce qui touche au système de fichiers local.

---

## Fichiers à supprimer

| Fichier | Raison |
|---|---|
| `backend/app_local.py` | Remplacé par le nouvel agent |
| `backend/cls_local_FileExplorer.py` | Tkinter — remplacé par sélecteur web |
| `backend/cls_local_analyse_prompt.py` | Tkinter — remplacé par interface web |

---

## Fichiers Windows à nettoyer dans l'app principale

| Fichier | Ligne(s) | Problème | Correction |
|---|---|---|---|
| `backend/cy_paths.py` | 1-11 | `import tkinter`, `pythoncom` | Supprimer les imports |
| `backend/cy_paths.py` | 177-220 | `select_directory` → Tkinter | Route → déléguer à l'agent local |
| `backend/cy_routes.py` | ~1167 | `os.startfile()` | Supprimer (inutile côté serveur) |
| `backend/cy_security.py` | subprocess `start` | Windows cmd | Supprimer (inutile côté serveur) |
| `requirements.txt` | - | `pywin32` | Supprimer |

---

## Nouvel agent local — structure

```
local_agent/
├── agent.py              ← point d'entrée Flask (port 5005)
├── routes/
│   ├── files.py          ← lecture/écriture JSON, CSV, texte
│   ├── directories.py    ← liste, création, déplacement dossiers
│   ├── documents.py      ← extraction PDF, conversion DOCX→PDF
│   └── system.py         ← infos système, ping, status
├── core/
│   ├── security.py       ← validation TOKEN + validation chemins
│   ├── file_ops.py       ← opérations fichiers (async)
│   └── pdf_ops.py        ← PyPDF2, reportlab
├── config.py             ← PORT, ROOT_DIR, TOKEN_SECRET
└── requirements.txt      ← dépendances minimales
```

---

## API de l'agent local

### Authentification
Chaque requête doit inclure :
```
Authorization: Bearer <TOKEN>
```
Le TOKEN est généré au login VPS et partagé avec l'agent.

### Endpoints

#### System
| Méthode | Route | Description |
|---|---|---|
| GET | `/ping` | Vérifie que l'agent tourne |
| GET | `/status` | Version, ROOT_DIR, statut |

#### Directories
| Méthode | Route | Description |
|---|---|---|
| GET | `/directories/root` | Retourne le ROOT_DIR actuel |
| POST | `/directories/root` | Définit un nouveau ROOT_DIR |
| GET | `/directories/list` | Liste les sous-dossiers du ROOT_DIR |
| GET | `/directories/tree?path=X` | Arbre de dossiers (pour le sélecteur web) |
| POST | `/directories/create` | Crée un dossier |
| POST | `/directories/move` | Déplace/renomme un dossier |
| DELETE | `/directories/delete` | Supprime un dossier |
| GET | `/directories/exists?path=X` | Vérifie l'existence |

#### Files
| Méthode | Route | Description |
|---|---|---|
| GET | `/files/read?path=X` | Lit un fichier (JSON, TXT, CSV) |
| POST | `/files/write` | Écrit un fichier |
| DELETE | `/files/delete` | Supprime un fichier |
| GET | `/files/exists?path=X` | Vérifie l'existence |
| POST | `/files/upload` | Reçoit un fichier uploadé |

#### Documents
| Méthode | Route | Description |
|---|---|---|
| POST | `/documents/extract-pdf` | Extrait le texte d'un PDF |
| POST | `/documents/convert-docx` | Convertit DOCX en PDF (LibreOffice headless) |
| POST | `/documents/generate-pdf` | Génère un PDF depuis JSON |

---

## Sécurité de l'agent

### Règles absolues
1. L'agent n'écoute que `127.0.0.1` — jamais `0.0.0.0`
2. Tout chemin reçu est résolu avec `os.path.realpath()` et vérifié dans `ROOT_DIR`
3. Le TOKEN est vérifié sur toutes les routes (sauf `/ping`)
4. Les extensions de fichiers sont validées (whitelist)

### Validation des chemins
```python
def validate_path(requested_path: str, root_dir: str) -> str:
    """
    Lève une exception si le chemin sort de root_dir.
    Retourne le chemin absolu normalisé.
    """
    abs_path = os.path.realpath(os.path.join(root_dir, requested_path))
    if not abs_path.startswith(os.path.realpath(root_dir)):
        raise SecurityError(f"Path traversal detected: {requested_path}")
    return abs_path
```

### CORS
L'agent doit autoriser uniquement l'origine VPS :
```python
CORS(agent_app, origins=["https://iacas.example.com"])
```
Et localhost pour le développement :
```python
CORS(agent_app, origins=["https://iacas.example.com", "http://localhost:3000"])
```

---

## Packaging et déploiement local

### Windows
```bash
pyinstaller --onefile --noconsole agent.py --name iacas-agent
# → iacas-agent.exe (systray icon)
```

### Linux / macOS
```bash
pyinstaller --onefile agent.py --name iacas-agent
# Ou service systemd utilisateur :
# ~/.config/systemd/user/iacas-agent.service
```

### Démarrage automatique
- **Windows** : raccourci dans `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- **Linux** : service systemd utilisateur `--user`
- **macOS** : LaunchAgent plist

---

## Configuration de l'agent (`config.py`)

```python
PORT = 5005
HOST = "127.0.0.1"
ROOT_DIR = os.getenv("ROOT_DIR", "")   # défini par l'utilisateur au premier lancement
TOKEN_SECRET = os.getenv("AGENT_TOKEN", "")  # reçu du VPS au login
LOG_FILE = "~/.iacas-agent/agent.log"
```

---

## Tests à réaliser

- [ ] L'agent démarre sans erreur sur Windows
- [ ] L'agent démarre sans erreur sur Ubuntu 22.04
- [ ] `/ping` répond sans token
- [ ] Toutes les routes retournent 401 sans token valide
- [ ] Un chemin `../../../etc/passwd` est rejeté
- [ ] Lecture/écriture d'un fichier JSON fonctionne
- [ ] Déplacement d'un dossier fonctionne
- [ ] Extraction PDF fonctionne (PyPDF2)
- [ ] Conversion DOCX → PDF fonctionne (LibreOffice headless)
- [ ] L'agent ne répond pas depuis une IP externe (127.0.0.1 only)

---

## Dépendances minimales (requirements.txt de l'agent)

```
flask[async]>=3.0
flask-cors>=4.0
aiofiles>=23.0
PyPDF2>=3.0
python-docx>=1.0
reportlab>=4.0
python-dotenv>=1.0
```

> `pywin32`, `tkinter`, `pythoncom` → SUPPRIMÉS
> `docx2pdf` → remplacé par `libreoffice --headless` (cross-platform)

---

## Livrable Phase 1

- [ ] `local_agent/` créé et fonctionnel
- [ ] `app_local.py`, `cls_local_FileExplorer.py`, `cls_local_analyse_prompt.py` supprimés
- [ ] App principale (`app.py`) tourne sans erreur sur Ubuntu
- [ ] `requirements.txt` principal nettoyé (sans dépendances Windows)
- [ ] Agent packagé en exécutable pour Windows et Linux
