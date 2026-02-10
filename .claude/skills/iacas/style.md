# Skill: IACAS Style Synchronizer

Description: Synchroniser les styles IACAS (couleurs, polices, tailles) depuis le repo iacas_site vers l'application Tailwind

Alias: "style iacas", "synchroniser style iacas", "verifier style iacas"

## Instructions

Tu es un expert en CSS et Tailwind. Tu dois synchroniser les styles du repo source (`E:\IACAS\REA\iacas_site\style.css`) vers l'application React/Tailwind actuelle.

### Source de verite

Le fichier source est: `E:\IACAS\REA\iacas_site\style.css`

Charte graphique:
- Peche Rosee: #E57373 (primary/CTA)
- The Vert: #B2DFBC (secondary/success)
- Fond: #F5F5F0 (ivoire)
- Texte: #000000 (noir)
- Header: #FFFFFF (blanc)
- Footer: #FFFFFF (blanc)
- Typo titres: Sora
- Typo texte: Lexend

### Fichiers a modifier

1. `frontend/tailwind.config.js` - Configuration Tailwind
2. `frontend/src/index.css` - Variables CSS et imports de polices
3. `frontend/index.html` - Classes body (bg-bg, text-black)
4. `frontend/src/App.jsx` - Composants Header, Footer, conteneurs principaux

### Classes a appliquer dans App.jsx

**Header:**
- Background: `bg-white` (pas bg-secondary)
- Texte: `text-black`
- Label "Iacas Server": `text-black`
- Liens menu: `text-black hover:text-primary`

**Conteneur principal:**
- Background: `bg-bg` (pas bg-primary)

**Footer:**
- Background: `bg-white`
- Texte: `text-black`
- Layout: `justify-between px-6` (copyright a gauche, bouton a droite)

### Boutons IACAS

Les styles de boutons sont definis dans `index.css` :

**Classes disponibles:**
- `.btn` - Style de base (padding, border-radius 14px, font-weight 600, transitions)
- `.btn--primary` - Bouton CTA (bg peche rosee, texte blanc, shadow)
- `.btn--ghost` - Bouton transparent avec bordure
- `.btn--sm` - Version petite (padding reduit, border-radius 12px)

**Exemple d'utilisation:**
```jsx
<a href="https://iacas.fr" className="btn btn--primary">Go to site</a>
<button className="btn btn--ghost btn--sm">Annuler</button>
```

**Styles CSS:**
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.9rem 1.1rem;
  border-radius: 14px;
  font-weight: 600;
  border: 1px solid transparent;
  transition: transform 0.08s ease, box-shadow 0.2s ease, background 0.2s ease;
  cursor: pointer;
}
.btn:active { transform: translateY(1px); }
.btn--primary {
  background: var(--primary);
  color: #fff;
  box-shadow: 0 12px 28px rgba(229,115,115,.35);
}
.btn--primary:hover { box-shadow: 0 18px 36px rgba(229,115,115,.42); }
```

### Variables CSS a synchroniser

```css
:root {
  --bg: #F5F5F0;
  --surface: #FFFFFF;
  --text: #000000;
  --muted: #6B6B6B;
  --primary: #E57373;
  --secondary: #B2DFBC;
  --header: #FFFFFF;
  --footer: #FFFFFF;
  --shadow: 0 18px 45px rgba(0,0,0,.08);
  --radius: 18px;
  --radius-sm: 12px;
  --container: 1120px;
}
```

### Configuration Tailwind cible

```javascript
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: '#E57373',    // Peche Rosee - CTA
        secondary: '#B2DFBC',  // The Vert - Success
        bg: '#F5F5F0',         // Fond ivoire
        surface: '#FFFFFF',    // Surface blanche
        text: '#000000',       // Texte noir
        muted: '#6B6B6B',      // Texte secondaire
        header: '#FFFFFF',     // Menu header blanc
      },
      fontFamily: {
        heading: ['Sora', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
        body: ['Lexend', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        'default': '18px',
        'sm': '12px',
      },
      boxShadow: {
        'default': '0 18px 45px rgba(0,0,0,.08)',
      },
      maxWidth: {
        'container': '1120px',
      },
    },
  },
  plugins: [],
};
```

### Index CSS cible

```css
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg: #F5F5F0;
  --surface: #FFFFFF;
  --text: #000000;
  --muted: #6B6B6B;
  --primary: #E57373;
  --secondary: #B2DFBC;
  --header: #FFFFFF;
  --footer: #FFFFFF;
  --shadow: 0 18px 45px rgba(0,0,0,.08);
  --radius: 18px;
  --radius-sm: 12px;
  --container: 1120px;
}

body {
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: theme('colors.bg');
  font-family: theme('fontFamily.body');
  color: theme('colors.text');
  line-height: 1.65;
}

h1, h2, h3 {
  font-family: theme('fontFamily.heading');
  line-height: 1.15;
}
```

### Workflow

1. **Lire** le fichier source `E:\IACAS\REA\iacas_site\style.css`
2. **Extraire** les variables `:root` (couleurs, polices, dimensions)
3. **Comparer** avec la configuration actuelle de l'application
4. **Proposer** les modifications necessaires
5. **Appliquer** les changements apres confirmation

### Commandes

- `/iacas:style` - Analyser et afficher les differences
- `/iacas:style apply` - Appliquer les modifications
- `/iacas:style diff` - Afficher uniquement les differences

Vous pouvez aussi demander: "synchronise avec le style iacas" ou "verifie le style iacas"

### Bonnes pratiques

- Toujours lire le fichier source avant de proposer des modifications
- Afficher un resume des changements avant d'appliquer
- Conserver les personnalisations existantes non liees a la charte
- Ajouter les imports Google Fonts si necessaire
