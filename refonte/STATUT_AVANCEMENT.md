# Statut d'avancement — IACAS OTA Refonte

**Dernière mise à jour :** 2026-02-10

---

## Phases

| Phase | Statut | Détail |
|-------|--------|--------|
| Phase 1 — Agent local | ✅ Terminée | `local_agent/` créé, tkinter/pythoncom supprimés |
| Phase 2 — Authentification | ✅ Terminée | Flask-Login, users.json, login.html |
| Phase 3 — Sécurité | ✅ Terminée | Voir ci-dessous |
| Phase 4 — Frontend | 🔄 En cours | Voir ci-dessous |
| Phase 5 — Déploiement VPS | ⏳ À faire | nginx + gunicorn + systemd |

---

## Phase 3 — Terminée ✅

Tout livré :
- `cy_security.py` — `safe_path()` + `safe_absolute_path()` (realpath)
- `cy_limiter.py` — singleton Flask-Limiter
- `cy_routes.py` — 12 routes protégées contre path traversal + injection cmd `/open_url`
- `cy_paths.py` — `check_dossier_exist` + `move_current_dossier` protégés
- `app.py` — headers CSP/X-Frame/HSTS, limiter.init_app(), logs rotatifs 5MB×3
- `cy_auth.py` — rate limit 10/min sur `/login`
- `local_agent/core/security.py` — `verify_token()` HMAC+expiration 8h
- `requirements.txt` — Flask-Limiter>=3.5

---

## Phase 4 — En cours 🔄

### Tâche 4 ✅ — Vendor assets téléchargés

Fichiers dans `static/vendor/` :
- `bootstrap/bootstrap.min.css` (227 KB)
- `bootstrap/bootstrap.bundle.min.js` (78 KB)
- `bootstrap-icons/bootstrap-icons.min.css` (83 KB)
- `bootstrap-icons/fonts/bootstrap-icons.woff2` (127 KB)

### Tâche 5 🔄 — Design System CSS (EN COURS, interrompu)

Fichiers **créés** :
- `static/css/tokens.css` ✅ — variables complètes (couleurs, typo, espacements, layout)
- `static/css/base.css` ✅ — reset, typo, inputs, scrollbar

Fichiers **à créer** :
- `static/css/layout.css` — topbar, sidebar, main area, split container
- `static/css/components.css` — boutons (btn-primary/secondary/ghost/danger), badges d'état
- `static/css/table.css` — tableau principal (remplace styles.css + panels.css)
- `static/css/utilities.css` — helpers (flex, spacing, etc.)

### Tâche 6 ⏳ — Templates et JS (À faire)

- `templates/base.html` — layout commun (topbar + sidebar + agent-status + auth)
- `templates/index.html` — mettre à jour pour étendre base.html
- `templates/login.html` — utiliser tokens.css au lieu des styles inline
- `static/js/cy_toast.js` — nouveau module notifications Toast
- `static/js/cy_main.js` — ajouter ping agent status (indicateur vert/rouge topbar)

---

## Rappel Architecture

```
Browser
  ├── VPS Flask (port 5001)   — UI, auth, Mistral AI proxy
  └── Agent local (port 5005) — opérations fichiers sur le PC
```

- Token auth : HMAC format `{user_id}:{timestamp}:{signature}` signé avec SECRET_KEY
- AGENT_TOKEN dans .env doit être identique à SECRET_KEY (pour que l'agent valide les tokens VPS)

---

## Fichiers à NE PAS modifier (stabilisés)

- `backend/cy_auth.py` — auth complète
- `backend/cy_users.py` — gestion users
- `backend/cy_security.py` — fonctions sécurité
- `local_agent/` — agent complet

## Fichiers orphelins (à supprimer si confirmé)

- `backend/app_local.py`
- `backend/cls_local_FileExplorer.py`
- `backend/cls_local_analyse_prompt.py`
- `backend/prompt_gui.py`
