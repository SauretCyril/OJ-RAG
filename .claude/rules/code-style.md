# Règles de style de code

## Général
- Indentation: 2 espaces
- Fin de ligne: LF
- Encodage: UTF-8
- Pas de console.log en production

## Backend (NestJS/TypeScript)
- Utiliser les décorateurs NestJS (@Controller, @Injectable, etc.)
- Typer toutes les variables et paramètres
- Préférer les interfaces aux types pour les objets
- Nommer les fichiers en kebab-case: `user.service.ts`
- Nommer les classes en PascalCase: `UserService`

## Frontend (React/JavaScript)
- Composants fonctionnels uniquement (pas de classes)
- Utiliser les hooks React (useState, useEffect, etc.)
- Nommer les composants en PascalCase: `ContactModal.jsx`
- Utiliser les classes utilitaires Tailwind CSS
- Éviter les styles inline

## Git
- Messages de commit en anglais
- Format: `type: description courte`
- Types: feat, fix, chore, docs, refactor, test
- Exemple: `feat: add user authentication`
