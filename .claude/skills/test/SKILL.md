---
name: test
description: Exécuter les tests du projet backend et frontend
allowed-tools: Bash, Read
---

# Skill de test

## Tests Backend (NestJS)

```bash
cd backend && npm test
```

Tests disponibles:
- Test de connexion MySQL
- Tests unitaires des services
- Tests d'intégration des controllers

## Tests Frontend (React)

```bash
cd frontend && npm test
```

Note: Les tests frontend ne sont pas encore implémentés.

## Vérification complète

1. Lancer les tests backend:
   ```bash
   cd backend && npm test
   ```

2. Vérifier le build backend:
   ```bash
   cd backend && npm run build
   ```

3. Vérifier le build frontend:
   ```bash
   cd frontend && npm run build
   ```

## En cas d'échec

- Analyser les messages d'erreur
- Vérifier les dépendances (npm install)
- S'assurer que MySQL est accessible pour les tests d'intégration
