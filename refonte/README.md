# Plan de refonte IACAS-OTA

## Objectif
Migrer l'application de bureau Windows vers une application web déployée sur VPS Ubuntu,
multi-utilisateurs, avec toutes les données restant sur le PC local de chaque utilisateur.

---

## Architecture cible

```
                         ┌─────────────────────────────────┐
                         │           VPS Ubuntu            │
                         │  ┌─────────┐   ┌─────────────┐ │
                         │  │  nginx  │   │  gunicorn   │ │
                         │  │  HTTPS  │──▶│  Flask app  │ │
                         │  └─────────┘   └─────────────┘ │
                         │                                 │
                         │  Stocke : comptes, configs UI   │
                         │  Ne stocke PAS : fichiers métier│
                         └─────────────────────────────────┘
                                          ▲
                                          │ HTTPS
                         ┌────────────────┴────────────────┐
                         │       PC local utilisateur      │
                         │  ┌─────────────────────────┐   │
                         │  │     Navigateur web       │   │
                         │  └─────────────────────────┘   │
                         │            │ localhost          │
                         │  ┌─────────▼───────────────┐   │
                         │  │    Agent local :5005     │   │
                         │  │  (API REST fichiers)     │   │
                         │  └─────────────────────────┘   │
                         │            │                    │
                         │  ┌─────────▼───────────────┐   │
                         │  │    Fichiers locaux       │   │
                         │  │  /candidatures/...       │   │
                         │  └─────────────────────────┘   │
                         └─────────────────────────────────┘
```

**Principe clé** : le VPS sert l'interface et proxifie les appels AI.
Les fichiers ne quittent jamais le PC de l'utilisateur.

---

## Phases

| Phase | Description | Priorité |
|---|---|---|
| [Phase 1](PHASE_1_agent_local.md) | Agent local cross-platform (sans Tkinter/Windows) | Critique |
| [Phase 2](PHASE_2_authentification.md) | Authentification multi-utilisateurs sur le VPS | Critique |
| [Phase 3](PHASE_3_securite.md) | Durcissement sécurité (headers, rate limit, validation) | Critique |
| [Phase 4](PHASE_4_frontend.md) | Refonte interface (design system, composants web) | Haute |
| [Phase 5](PHASE_5_deploiement_vps.md) | Déploiement production VPS Ubuntu | Haute |

---

## Règles du projet

- **Pas de base de données** — JSON pour les configs, fichiers locaux pour les données
- **Pas de stockage fichiers sur le VPS** — tout reste sur le PC de l'utilisateur
- **Multi-utilisateurs** — chaque utilisateur a son compte, sa config, son agent local
- **Cross-platform** — l'agent local fonctionne Windows, Linux, macOS
- **Sécurité first** — aucune route accessible sans authentification
- **Pas de CDN externe** — Bootstrap, polices et icônes auto-hébergés

---

## Répartition des responsabilités

| Composant | Rôle | Hébergement |
|---|---|---|
| VPS Flask app | Sert le frontend, proxifie Mistral AI, gère les comptes | VPS |
| Agent local | Toutes les opérations fichiers/dossiers | PC utilisateur |
| Navigateur | Interface utilisateur, routing des appels | PC utilisateur |

---

## Dépendances à ajouter

```
# VPS app
Flask-Login>=0.6
Flask-WTF>=1.2
Flask-Limiter>=3.5
Flask-Cors>=4.0
bcrypt>=4.0
gunicorn>=21.0

# Agent local
flask[async]>=3.0
flask-cors>=4.0
aiofiles>=23.0
PyPDF2>=3.0
python-docx>=1.0
reportlab>=4.0
```

## Dépendances à supprimer

```
pywin32          # Windows uniquement
tkinter          # GUI Windows (dans stdlib, à ne pas importer)
pythoncom        # Windows COM
docx2pdf         # Remplacé par libreoffice --headless
```

---

## Ordre d'exécution suggéré

```
1. Phase 1 → app tourne sur Ubuntu sans erreur
2. Phase 2 → auth en place, aucune route publique
3. Phase 3 → sécurité durcie avant tout déploiement réseau
4. Phase 4 → interface refaite (peut être parallèle à 2/3)
5. Phase 5 → mise en production
```
