---
name: review
description: Revoir le code pour la qualité, sécurité et bonnes pratiques
allowed-tools: Read, Grep, Glob
---

# Skill de revue de code

## Étapes de revue

1. **Analyser les changements**
   - Identifier les fichiers modifiés
   - Comprendre l'objectif des modifications

2. **Vérifier la qualité du code**
   - Lisibilité et maintenabilité
   - Respect des conventions du projet
   - Pas de code dupliqué

3. **Contrôles de sécurité**
   - Pas d'injection SQL (utiliser TypeORM correctement)
   - Pas de XSS (échapper les données utilisateur)
   - Pas de secrets en dur dans le code
   - Validation des entrées utilisateur

4. **Performance**
   - Requêtes N+1 évitées
   - Pas de boucles inutiles
   - Utilisation correcte des hooks React (useMemo, useCallback)

5. **Tests**
   - Les fonctionnalités critiques sont testées
   - Les cas limites sont couverts

## Format du feedback

### Critique (à corriger)
- Problèmes de sécurité
- Bugs évidents

### Avertissement (à améliorer)
- Code difficile à maintenir
- Performances sous-optimales

### Suggestion (à considérer)
- Améliorations optionnelles
- Refactoring possible
