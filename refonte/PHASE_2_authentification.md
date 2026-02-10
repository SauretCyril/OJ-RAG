# Phase 2 — Authentification et gestion des utilisateurs

## Objectif
Ajouter un système d'authentification sur le VPS avant tout déploiement réseau.
Chaque utilisateur possède un compte, une session sécurisée, et une configuration
applicative isolée. Aucune donnée métier ne transite par le VPS.

---

## Contexte

Actuellement :
- Zéro authentification — n'importe qui peut accéder à l'app
- `cookies.json` stocke les préférences sans session
- Pas de notion d'utilisateur dans le code

Après Phase 2 :
- Login/logout par compte
- Session sécurisée (Flask-Login + SECRET_KEY forte)
- Profil par utilisateur (config, prompts AI, filtres)
- TOKEN transmis à l'agent local pour sécuriser les appels fichiers

---

## Stockage des utilisateurs

Pas de base de données — fichier JSON chiffré (bcrypt sur les mots de passe).

```
backend/data/
├── users.json              ← comptes (jamais exposé via API)
├── users/
│   ├── alice/
│   │   ├── config.json     ← colonnes, préférences UI
│   │   ├── prompts.json    ← rôles AI personnalisés
│   │   ├── filters.json    ← filtres sauvegardés
│   │   └── directories.json← liste des répertoires de travail
│   └── bob/
│       ├── config.json
│       ├── prompts.json
│       ├── filters.json
│       └── directories.json
```

### Format `users.json`
```json
[
  {
    "id": "uuid-alice",
    "username": "alice",
    "email": "alice@example.com",
    "password_hash": "$2b$12$...",
    "role": "user",
    "created_at": "2026-01-15",
    "active": true
  },
  {
    "id": "uuid-admin",
    "username": "admin",
    "email": "admin@example.com",
    "password_hash": "$2b$12$...",
    "role": "admin",
    "created_at": "2026-01-01",
    "active": true
  }
]
```

---

## Fichiers à créer

### Backend VPS

| Fichier | Rôle |
|---|---|
| `backend/cy_auth.py` | Blueprint Flask : login, logout, register |
| `backend/cy_users.py` | CRUD utilisateurs (lecture/écriture users.json) |
| `backend/cy_session.py` | Gestion session + génération TOKEN agent |
| `templates/login.html` | Page de connexion |
| `templates/register.html` | Page d'inscription (admin uniquement) |

### Modifications existantes

| Fichier | Modification |
|---|---|
| `backend/app.py` | Enregistrer blueprint auth, configurer Flask-Login |
| `backend/cy_routes.py` | Ajouter `@login_required` sur toutes les routes |
| `backend/cy_cookies.py` | Migrer cookies vers profil utilisateur par session |
| `backend/cy_paths.py` | `GetRoot()` → lire depuis le profil utilisateur |

---

## Flux d'authentification complet

```
1. GET /login
   ← page HTML de connexion

2. POST /login  { username, password }
   → VPS vérifie bcrypt
   → Crée session Flask (httponly cookie)
   → Génère TOKEN = HMAC(user_id + timestamp, SECRET_KEY)
   → Stocke TOKEN en session
   ← { token: "xyz...", user: { id, username, role } }

3. Navigateur stocke TOKEN dans sessionStorage
   (sessionStorage = effacé à la fermeture du navigateur)

4. Chaque requête API VPS :
   → Session cookie Flask (automatique)

5. Chaque requête agent local (localhost:5005) :
   → Header : Authorization: Bearer <TOKEN>
   → Agent valide le TOKEN

6. POST /logout
   → Détruit la session Flask
   → TOKEN invalidé
   ← Redirect vers /login
```

---

## Sécurité des sessions

### Configuration Flask
```python
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY"),  # 32 bytes aléatoires minimum
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,          # HTTPS uniquement
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_COOKIE_NAME='iacas_session'
)
```

### Génération du TOKEN agent
```python
import hmac, hashlib, time

def generate_agent_token(user_id: str) -> str:
    timestamp = str(int(time.time()))
    message = f"{user_id}:{timestamp}"
    token = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{message}:{token}"
```

### Protection CSRF
- Utiliser `Flask-WTF` pour les formulaires login/register
- Token CSRF sur le form de login
- Routes API protégées via session (pas CSRF car API JSON)

---

## Gestion des profils utilisateurs

### Chargement à la connexion
```
GET /api/me
← {
    user: { id, username, role },
    config: { colonnes, preferences_ui },
    prompts: [ { id, nom, contenu } ],
    filters: { ... },
    directories: [ "/chemin/1", "/chemin/2" ]
  }
```

### Sauvegarde
```
POST /api/me/config      ← sauvegarde les préférences UI
POST /api/me/prompts     ← sauvegarde les rôles AI
POST /api/me/filters     ← sauvegarde les filtres
POST /api/me/directories ← sauvegarde la liste des répertoires de travail
```

Ces routes remplacent les actuels :
- `cy_cookies.py` → `/save_cookie`, `/load_cookies`, `/get_cookie`
- `cy_columns.py` → `/save_conf_cols`, `/load_conf_cols`

---

## Rôles et permissions

| Rôle | Permissions |
|---|---|
| `admin` | Créer/supprimer des comptes, voir tous les utilisateurs |
| `user` | Accéder à sa propre configuration, utiliser l'app |

### Admin panel (minimal)
```
GET  /admin/users       ← liste des utilisateurs
POST /admin/users       ← créer un utilisateur
PUT  /admin/users/:id   ← activer/désactiver
DELETE /admin/users/:id ← supprimer
```

---

## Page de login — spécifications UI

- Design cohérent avec l'app (Phase 4)
- Logo IACAS centré
- Formulaire centré, fond sobre
- Champ username + password (type=password)
- Bouton "Se connecter"
- Message d'erreur inline (pas d'alert JS)
- Pas de "Se souvenir de moi" (sécurité)
- Redirect automatique vers `/` si déjà connecté

---

## Migration des cookies existants

Les `cookies.json` et `data/cookies.json` actuels contiennent les préférences.
À la première connexion d'un utilisateur :
- Si `cookies.json` existe → importer dans `users/{username}/config.json`
- Supprimer `cookies.json` après migration

---

## Dépendances à ajouter

```
Flask-Login>=0.6
Flask-WTF>=1.2
bcrypt>=4.0
```

---

## Variables d'environnement à ajouter dans `.env`

```
SECRET_KEY=<32 bytes aléatoires — générer avec python -c "import secrets; print(secrets.token_hex(32))">
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<mot de passe initial de l'admin>
```

---

## Tests à réaliser

- [ ] Login avec identifiants corrects → session créée, TOKEN généré
- [ ] Login avec mauvais mdp → rejeté, message d'erreur
- [ ] Accès `/` sans être connecté → redirect `/login`
- [ ] TOKEN transmis à l'agent local → agent accepte les requêtes
- [ ] Logout → session détruite, TOKEN invalide, redirect login
- [ ] Deux utilisateurs connectés simultanément → données isolées
- [ ] Session expirée (8h) → redirect login automatique
- [ ] Admin peut créer un compte
- [ ] Un `user` ne peut pas accéder à `/admin/`

---

## Livrable Phase 2

- [ ] `cy_auth.py` créé et fonctionnel
- [ ] `cy_users.py` créé (CRUD users.json)
- [ ] `templates/login.html` créé
- [ ] `users.json` initialisé avec compte admin
- [ ] Toutes les routes protégées par `@login_required`
- [ ] Profil utilisateur chargeable via `/api/me`
- [ ] TOKEN agent généré et validé
- [ ] Anciens `cy_cookies.py` endpoints migrés vers `/api/me/*`
