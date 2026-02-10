# Phase 3 — Sécurité

## Objectif
Durcir l'application VPS et l'agent local contre les attaques courantes,
avant toute exposition sur internet. Cette phase couvre la sécurité réseau,
la validation des entrées, les headers HTTP et la protection de l'API AI.

---

## Contexte — État actuel (vulnérabilités identifiées)

| Vulnérabilité | Fichier | Gravité |
|---|---|---|
| Pas d'authentification | tous | Critique |
| Path traversal possible | `cy_paths.py`, `cy_routes.py` | Critique |
| `debug=True` en production | `launcher.py` | Haute |
| Pas de validation CSRF | `cy_routes.py` | Haute |
| Pas de headers sécurité | `app.py` | Haute |
| Pas de rate limiting | `cy_requests.py` | Haute |
| `shutil.move()` sans validation | `cy_paths.py` | Haute |
| `os.startfile()` non protégé | `cy_routes.py` | Moyenne |
| Logs insuffisants | partout | Moyenne |
| SECRET_KEY manquante | `app.py` | Critique |

---

## 1. Validation des chemins (Path Traversal)

Toute route qui reçoit un chemin doit passer par le validateur.

### Règle universelle
```python
def safe_path(user_input: str, base_dir: str) -> str:
    """
    Résout le chemin et vérifie qu'il reste dans base_dir.
    Lève ValueError si tentative de sortie.
    """
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, user_input))
    if not target.startswith(base + os.sep) and target != base:
        raise ValueError(f"Chemin interdit: {user_input}")
    return target
```

### Routes à corriger dans `cy_routes.py`
- `/read_annonces_json` — le path des dossiers
- `/save_annonces_json` — idem
- `/read_csv_file` — le path CSV
- `/save_csv_file` — idem
- `/read_notes` — le path du fichier notes
- `/save_notes` — idem
- `/upload_doc` — destination de l'upload
- `/move_and_rename_directory` — source + destination

### Routes à corriger dans `cy_paths.py`
- `/check_dossier_exists` — le nom du dossier
- `/move_current_dossier` — source + target

---

## 2. Headers de sécurité HTTP

Ajouter via un hook `after_request` dans `app.py` :

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "    # à durcir en Phase 4 avec nonces
        "style-src 'self' 'unsafe-inline'; "
        "font-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self' http://localhost:5005"  # agent local
    )
    if app.config.get('ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
    return response
```

---

## 3. Rate Limiting

Protection contre le spam d'appels AI (coûteux) et brute-force login.

### Installation
```
Flask-Limiter>=3.5
```

### Configuration dans `app.py`
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
```

### Limites spécifiques par route

| Route | Limite | Raison |
|---|---|---|
| `POST /login` | 5 par minute | Anti brute-force |
| `POST /get_AI_answer` | 20 par heure | Coût API Mistral |
| `POST /get_AI_answer_from_url` | 10 par heure | Coût + temps |
| `POST /extract_pdf_text` | 30 par heure | Charge serveur |
| `POST /convert_cv` | 10 par heure | Charge serveur |

---

## 4. Validation des fichiers uploadés

### Whitelist d'extensions
```python
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.csv', '.json'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_upload(file) -> bool:
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension non autorisée: {ext}")
    # Vérification magic bytes (pas seulement l'extension)
    header = file.read(16)
    file.seek(0)
    return True
```

### Magic bytes à vérifier
| Extension | Magic bytes |
|---|---|
| `.pdf` | `%PDF` (25 50 44 46) |
| `.docx` | `PK` (50 4B 03 04) ZIP format |
| `.csv` | Pas de magic bytes → vérifier UTF-8 |

---

## 5. Protection CSRF

Uniquement sur les formulaires HTML (login, register, admin).
Les routes API JSON sont protégées par la session + le TOKEN.

```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

Dans les templates :
```html
<form method="POST">
  {{ form.csrf_token }}
  ...
</form>
```

---

## 6. Configuration production

### `app.py` — variables d'environnement obligatoires
```python
import os

ENV = os.getenv("FLASK_ENV", "production")

if ENV == "production":
    assert os.getenv("SECRET_KEY"), "SECRET_KEY manquante"
    assert len(os.getenv("SECRET_KEY", "")) >= 32, "SECRET_KEY trop courte"
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
```

### Variables `.env` requises en production
```
FLASK_ENV=production
SECRET_KEY=<32+ chars>
MISTRAL_API_KEY=<clé Mistral>
ROOT_DIR=                     # vide sur le VPS (géré par agent local)
ALLOWED_HOSTS=iacas.example.com
```

---

## 7. Logs structurés

Remplacer les `print()` par un logger configuré.

### Configuration dans `app.py`
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    handler = RotatingFileHandler(
        'logs/iacas.log',
        maxBytes=10_000_000,
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
```

### Événements à logger obligatoirement
- Login réussi / échoué (avec IP)
- Toute opération fichier (lecture, écriture, déplacement)
- Erreur 4xx et 5xx
- Appels API Mistral (sans le contenu)
- Tentative de path traversal

---

## 8. Sécurité de l'agent local (rappel Phase 1)

L'agent local a sa propre couche de sécurité, mais la Phase 3 la renforce :

- TOKEN signé avec `hmac` + expiration (ex: 8h)
- L'agent rejette les TOKEN expirés
- L'agent log toute requête refusée
- Validation des chemins avec `os.path.realpath`
- Pas d'accès depuis une IP autre que `127.0.0.1`

### Validation TOKEN dans l'agent
```python
def verify_token(token: str) -> bool:
    try:
        parts = token.split(":")
        user_id, timestamp, signature = parts[0], parts[1], parts[2]
        # Vérifier expiration
        if int(time.time()) - int(timestamp) > 28800:  # 8 heures
            return False
        # Vérifier signature
        expected = hmac.new(
            SECRET_KEY.encode(),
            f"{user_id}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False
```

---

## 9. CORS — Configuration précise

Le VPS n'autorise que les origines légitimes.

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://iacas.example.com",
            "http://localhost:5000"  # dev uniquement
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

L'agent local autorise uniquement `localhost` :
```python
CORS(agent_app, origins=["https://iacas.example.com", "http://localhost:5000"])
```

---

## 10. Scan de sécurité avant mise en production

### Checklist manuelle
- [ ] `debug=False` vérifié
- [ ] Aucune clé dans le code source (grep `API_KEY`, `SECRET`, `PASSWORD`)
- [ ] `.env` absent du dépôt git (`.gitignore` vérifié)
- [ ] Tous les chemins passent par `safe_path()`
- [ ] Upload : magic bytes vérifiés
- [ ] Headers sécurité présents (vérifier avec https://securityheaders.com)
- [ ] Rate limiting actif sur les routes sensibles
- [ ] Logs activés et rotatifs
- [ ] HTTPS uniquement (redirect HTTP → HTTPS dans nginx)
- [ ] Session cookie : `httponly=True`, `secure=True`, `samesite=Lax`

### Outils recommandés
```bash
# Scanner les dépendances Python pour CVE
pip-audit

# Scanner le code pour vulnérabilités
bandit -r backend/

# Tester les headers HTTP
curl -I https://iacas.example.com
```

---

## Dépendances à ajouter

```
Flask-Limiter>=3.5
Flask-WTF>=1.2
Flask-Cors>=4.0
pip-audit         # outil dev, pas en requirements.txt app
bandit            # outil dev
```

---

## Tests à réaliser

- [ ] `curl http://vps/` sans HTTPS → redirigé vers HTTPS
- [ ] Path traversal `../../../etc/passwd` → 400 refusé
- [ ] Upload d'un `.exe` → rejeté
- [ ] 6 tentatives login en 1 minute → rate limited (429)
- [ ] 21 appels AI en 1 heure → rate limited
- [ ] Headers sécurité présents sur toutes les réponses
- [ ] TOKEN agent expiré → agent retourne 401
- [ ] `bandit -r backend/` → aucun finding critique

---

## Livrable Phase 3

- [ ] `safe_path()` utilisé sur toutes les routes fichiers
- [ ] Headers sécurité sur toutes les réponses
- [ ] Rate limiting actif (login + AI)
- [ ] Validation upload (extension + magic bytes)
- [ ] `debug=False` en production
- [ ] Logs structurés configurés
- [ ] CSRF sur formulaires HTML
- [ ] TOKEN agent avec expiration
- [ ] Scan `bandit` sans findings critiques
