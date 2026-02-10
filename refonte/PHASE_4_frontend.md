# Phase 4 — Refonte Frontend

## Objectif
Remplacer l'interface brouillonne Windows-centric par un design system unifié,
professionnel et cohérent. Conserver la logique JS existante, refactoriser l'UX,
et remplacer les composants Tkinter par des équivalents web natifs.

---

## Contexte — Problèmes actuels

| Problème | Impact |
|---|---|
| Bootstrap chargé depuis CDN | Dépendance externe, lente, bloquante hors réseau |
| Styles inline mélangés aux classes Bootstrap | Inconsistance visuelle |
| 3 fichiers CSS sans design system | Couleurs, espacements, typo inconsistants |
| Dialogs Tkinter (Windows) | Cassés sur Linux/VPS |
| Pas de feedback visuel (loading, erreurs) | UX dégradée |
| Layout non responsive | Cassé sur petits écrans |
| Pas de topbar utilisateur | Pas d'identité, pas de logout |
| Icônes Font Awesome depuis CDN | Dépendance externe |

---

## 1. Design System — Variables CSS

Créer `static/css/tokens.css` — source de vérité pour tous les styles.

```css
:root {
  /* Couleurs principales */
  --color-primary:        #2563eb;   /* Bleu IACAS */
  --color-primary-dark:   #1d4ed8;
  --color-primary-light:  #dbeafe;
  --color-secondary:      #64748b;
  --color-success:        #16a34a;
  --color-warning:        #d97706;
  --color-danger:         #dc2626;
  --color-info:           #0891b2;

  /* Fond et surfaces */
  --color-bg:             #f8fafc;
  --color-surface:        #ffffff;
  --color-surface-alt:    #f1f5f9;
  --color-border:         #e2e8f0;
  --color-border-strong:  #cbd5e1;

  /* Texte */
  --color-text:           #0f172a;
  --color-text-muted:     #64748b;
  --color-text-disabled:  #94a3b8;

  /* Typographie */
  --font-family:          'Inter', system-ui, -apple-system, sans-serif;
  --font-size-xs:         0.75rem;
  --font-size-sm:         0.875rem;
  --font-size-base:       1rem;
  --font-size-lg:         1.125rem;
  --font-size-xl:         1.25rem;

  /* Espacements */
  --space-1:  0.25rem;
  --space-2:  0.5rem;
  --space-3:  0.75rem;
  --space-4:  1rem;
  --space-6:  1.5rem;
  --space-8:  2rem;
  --space-12: 3rem;

  /* Bordures */
  --radius-sm:  0.25rem;
  --radius-md:  0.5rem;
  --radius-lg:  0.75rem;
  --radius-xl:  1rem;

  /* Ombres */
  --shadow-sm:  0 1px 2px rgba(0,0,0,.05);
  --shadow-md:  0 4px 6px -1px rgba(0,0,0,.1);
  --shadow-lg:  0 10px 15px -3px rgba(0,0,0,.1);

  /* Transitions */
  --transition: 150ms ease;

  /* Layout */
  --sidebar-width:   280px;
  --topbar-height:   56px;
  --panel-min-width: 320px;
}
```

---

## 2. Structure des fichiers CSS

```
static/css/
├── tokens.css         ← variables (ci-dessus)
├── base.css           ← reset, typographie, liens
├── layout.css         ← topbar, sidebar, main area, panels
├── components.css     ← boutons, inputs, badges, cards
├── table.css          ← tableau principal des dossiers
├── dialogs.css        ← modales (remplace Tkinter)
├── forms.css          ← formulaires
└── utilities.css      ← helpers (m-auto, flex-center, etc.)
```

Supprimer : `styles.css`, `panels.css` (contenu à migrer dans la nouvelle structure)

---

## 3. Layout principal

```
┌──────────────────────────────────────────────────────────┐
│  TOPBAR  [Logo IACAS] [Titre]      [Notifications] [User▼]│  56px fixe
├──────────────────────────────────────────────────────────┤
│         │                                                │
│ SIDEBAR │  ZONE PRINCIPALE                               │
│ 280px   │                                                │
│ fixe    │  ┌──────────────────────┐ ┌─────────────────┐ │
│         │  │  TABLEAU DOSSIERS    │ │  PANNEAU DETAIL  │ │
│ [Menu]  │  │  (liste principale)  │ │  (tabs: texte,  │ │
│ [Dirs]  │  │                      │ │   AI, notes...) │ │
│ [Config]│  │                      │ │                 │ │
│         │  └──────────────────────┘ └─────────────────┘ │
│         │       Redimensionnable via handle central       │
└──────────────────────────────────────────────────────────┘
```

### Topbar
- Logo/nom de l'app à gauche
- Breadcrumb ou titre de section au centre
- Cloche notifications (optionnel) + avatar utilisateur + menu dropdown (profil, logout)

### Sidebar
- Navigation entre sections (Dossiers, Répertoires, Configuration)
- Indicateur section active
- Affichage du répertoire courant (tronqué)
- Bouton "Changer de répertoire"
- Pliable sur petits écrans

---

## 4. Composants UI à créer/refactoriser

### Boutons (3 niveaux)
```html
<button class="btn btn-primary">Action principale</button>
<button class="btn btn-secondary">Action secondaire</button>
<button class="btn btn-ghost">Action tertiaire</button>
<button class="btn btn-danger">Action destructive</button>
```

### Badges d'état (remplacent les cellules colorées)
```html
<span class="badge badge-success">Validé</span>
<span class="badge badge-warning">En cours</span>
<span class="badge badge-danger">Refusé</span>
<span class="badge badge-neutral">Nouveau</span>
```

### Toast notifications (remplace les alert JS)
```javascript
// cy_toast.js — module unique pour toutes les notifications
Toast.success("Dossier sauvegardé");
Toast.error("Erreur de connexion à l'agent local");
Toast.warning("Fichier introuvable");
Toast.info("Synchronisation en cours...");
```

### Loading states
```html
<!-- Overlay sur le tableau pendant chargement -->
<div class="table-loading-overlay">
  <div class="spinner"></div>
  <p>Chargement des dossiers...</p>
</div>
```

---

## 5. Remplacement du sélecteur Tkinter

Créer un **explorateur de dossiers web** dans une modale Bootstrap.

### Comportement
1. Bouton "Changer de répertoire" → ouvre modale
2. La modale appelle `GET localhost:5005/directories/tree?path=/`
3. L'agent retourne l'arbre de dossiers en JSON
4. La modale affiche un tree-view cliquable
5. L'utilisateur navigue, clique sur un dossier → sélectionné
6. Bouton "Confirmer" → ferme modale, met à jour l'UI

### Structure modale
```html
<div class="modal" id="dir-picker-modal">
  <div class="modal-dialog modal-lg">
    <div class="modal-header">
      <h5>Sélectionner un répertoire</h5>
      <button class="btn-close" ...></button>
    </div>
    <div class="modal-body">
      <div class="dir-breadcrumb">...</div>
      <div class="dir-tree">
        <!-- Généré dynamiquement par JS -->
        <div class="dir-item" data-path="/home/user/candidatures">
          <i class="icon-folder"></i> candidatures
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <span class="selected-path-preview">/home/user/...</span>
      <button class="btn btn-primary" id="confirm-dir">Confirmer</button>
    </div>
  </div>
</div>
```

---

## 6. Tableau des dossiers — améliorations

### Colonnes responsive
- Masquer les colonnes secondaires sur petit écran
- Colonnes redimensionnables (resize handle)
- Tri par colonne (clic sur header)

### Ligne de tableau
```html
<tr class="dossier-row" data-id="2025-01_Entreprise_X">
  <td class="col-numero">001</td>
  <td class="col-entreprise">Entreprise X</td>
  <td class="col-etat"><span class="badge badge-warning">En cours</span></td>
  <td class="col-date">2025-01-15</td>
  <td class="col-actions">
    <button class="btn-icon" title="Ouvrir"><i class="icon-external"></i></button>
    <button class="btn-icon" title="Déplacer"><i class="icon-move"></i></button>
  </td>
</tr>
```

### Filtre/recherche intégrés
- Barre de recherche au-dessus du tableau
- Filtres par état sous forme de chips cliquables
- Compteur de résultats

---

## 7. Auto-hébergement Bootstrap et icônes

Sortir des CDN pour une app auto-suffisante.

### Bootstrap 5.3 (self-hosted)
```
static/vendor/
├── bootstrap/
│   ├── bootstrap.min.css
│   └── bootstrap.bundle.min.js
└── inter/
    ├── inter.woff2          ← police Inter (remplace Google Fonts)
    └── inter.css
```

### Icônes — Bootstrap Icons (self-hosted)
Remplacer Font Awesome (CDN) par Bootstrap Icons (self-hosted, license MIT).
```
static/vendor/bootstrap-icons/
├── bootstrap-icons.woff2
└── bootstrap-icons.css
```

Usage dans le HTML :
```html
<i class="bi bi-folder2-open"></i>
<i class="bi bi-robot"></i>
<i class="bi bi-file-pdf"></i>
```

---

## 8. Page de connexion

```
┌────────────────────────────────────┐
│                                    │
│          [Logo IACAS]              │
│        Gestionnaire de             │
│         candidatures               │
│                                    │
│  ┌──────────────────────────────┐  │
│  │  Identifiant                 │  │
│  │  [________________________]  │  │
│  │                              │  │
│  │  Mot de passe                │  │
│  │  [________________________]  │  │
│  │                              │  │
│  │      [  Se connecter  ]      │  │
│  └──────────────────────────────┘  │
│                                    │
│    v1.0.0 — IACAS OTA              │
└────────────────────────────────────┘
```

---

## 9. Indicateur de statut de l'agent local

Dans la topbar, un indicateur discret montre si l'agent local répond.

```
● Agent connecté     (vert — ping localhost:5005 OK)
○ Agent déconnecté   (rouge — localhost:5005 injoignable)
```

Si l'agent est déconnecté, les opérations fichiers sont désactivées avec un
message explicatif : "L'agent local n'est pas démarré sur votre PC."

---

## 10. Internationalisation (i18n)

L'app est actuellement en français. Prévoir un fichier de traduction simple.

```javascript
// static/js/cy_i18n.js
const I18N = {
  fr: {
    'agent.connected': 'Agent connecté',
    'agent.disconnected': 'Agent déconnecté',
    'dossier.saved': 'Dossier sauvegardé',
    // ...
  }
};
```

---

## Structure des fichiers JS après refonte

```
static/js/
├── cy_main.js          ← init, routing, vérification agent
├── cy_api.js           ← client VPS (remplace cy_http_client.js)
├── cy_agent.js         ← client agent local (localhost:5005)
├── cy_auth.js          ← login, logout, session
├── cy_state.js         ← state management (renommé)
├── cy_tableau.js       ← tableau principal (refactorisé)
├── cy_dossiers.js      ← CRUD dossiers
├── cy_dirs.js          ← explorateur répertoires web
├── cy_panel.js         ← panneau détail
├── cy_ai.js            ← assistant AI
├── cy_toast.js         ← NOUVEAU — notifications
├── cy_modal.js         ← NOUVEAU — gestion modales
├── cy_columns.js       ← configuration colonnes
└── cy_i18n.js          ← NOUVEAU — traductions
```

---

## Templates HTML

```
templates/
├── base.html           ← NOUVEAU — layout commun (topbar, sidebar)
├── login.html          ← hérite base (layout minimal)
├── index.html          ← hérite base (app principale)
├── admin.html          ← hérite base (gestion utilisateurs)
└── column_manager.html ← hérite base (configuration colonnes)
```

---

## Tests à réaliser

- [ ] Layout correct sur 1920px, 1440px, 1280px, 1024px
- [ ] Login s'affiche sans agent local actif
- [ ] Indicateur agent vert/rouge selon état
- [ ] Sélecteur de répertoire web fonctionne (navigation, confirmation)
- [ ] Tableau se charge avec loading overlay
- [ ] Toast success/error s'affiche et disparaît après 3s
- [ ] Logout redirige vers login
- [ ] Aucun appel vers CDN externe (vérifier dans DevTools Network)
- [ ] Toutes les polices se chargent en self-hosted
- [ ] Badges d'état cohérents avec les valeurs métier

---

## Livrable Phase 4

- [ ] `tokens.css` créé et utilisé partout
- [ ] Bootstrap + Inter + Bootstrap Icons auto-hébergés
- [ ] Topbar avec utilisateur connecté + logout
- [ ] Sidebar navigation
- [ ] Sélecteur répertoire web (modale avec tree-view)
- [ ] Indicateur statut agent local
- [ ] Toast notifications uniformes
- [ ] Loading states sur tableau et opérations async
- [ ] `templates/base.html` créé et utilisé
- [ ] Aucun CDN externe
