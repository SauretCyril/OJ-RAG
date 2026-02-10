---
name: deploy
description: Deployer l'application IACAS sur Docker ou Kubernetes via GitLab CI/CD
allowed-tools: Bash, Read, Grep, Glob
---

# Skill de deploiement IACAS

## Architecture du pipeline

Le pipeline GitLab CI/CD s'execute sur la branche `prod` avec les stages suivants:

```
install -> build -> test -> docker -> deploy (manuel)
```

**GitLab Runner:** `iacas.fr-full` (heberge sur le VPS)

## Variables CI/CD GitLab

### Variables OBLIGATOIRES a configurer dans GitLab > Settings > CI/CD > Variables

| Variable | Type | Masked | Description |
|----------|------|--------|-------------|
| `KUBECONFIG_CONTENT` | Variable | Oui | Contenu du fichier kubeconfig encode en base64 |
| `VITE_API_URL` | Variable | Non | URL de l'API backend (ex: `https://api.iacas.fr/api`) |
| `MYSQL_ROOT_PASSWORD` | Variable | Oui | Mot de passe root MySQL |
| `MYSQL_DATABASE` | Variable | Non | Nom de la base de donnees |
| `MYSQL_USER` | Variable | Non | Utilisateur MySQL |
| `MYSQL_PASSWORD` | Variable | Oui | Mot de passe MySQL |
| `SMTP_HOST` | Variable | Non | Serveur SMTP (ex: `smtp.gmail.com`) |
| `SMTP_PORT` | Variable | Non | Port SMTP (ex: `587`) |
| `SMTP_USER` | Variable | Non | Utilisateur SMTP |
| `SMTP_PASS` | Variable | Oui | Mot de passe SMTP |

### Variables AUTOMATIQUES (fournies par GitLab)

| Variable | Description |
|----------|-------------|
| `CI_REGISTRY` | URL du registre GitLab (`registry.gitlab.com`) |
| `CI_REGISTRY_USER` | Utilisateur du registre |
| `CI_REGISTRY_PASSWORD` | Token d'acces au registre |
| `CI_COMMIT_SHA` | SHA du commit (utilise pour tagger les images) |
| `CI_PROJECT_DIR` | Repertoire du projet |

## Comment generer KUBECONFIG_CONTENT

```bash
# Sur le VPS, encoder le fichier kubeconfig en base64
cat ~/.kube/config | base64 -w 0
```

Copier le resultat et le coller dans la variable GitLab `KUBECONFIG_CONTENT`.

## Images Docker

Les images sont poussees sur le registre GitLab:
- Backend: `registry.gitlab.com/sauretcyril/iacas/backend:$CI_COMMIT_SHA`
- Frontend: `registry.gitlab.com/sauretcyril/iacas/frontend:$CI_COMMIT_SHA`

## Fichiers Kubernetes

| Fichier | Description |
|---------|-------------|
| `iacas3-backend-deployment.yaml` | Deployment backend (port 8080) |
| `iacas3-frontend-deployment.yaml` | Deployment frontend (port 80) |
| `iacas3-service.yaml` | Service backend |
| `iacas3-frontend-service.yaml` | Service frontend |
| `iacas3-ingress-https.yaml` | Ingress avec HTTPS/TLS |
| `mysql-deployment.yaml` | Deployment MySQL |
| `letsencrypt-prod-issuer.yaml` | Issuer Let's Encrypt |
| `traefik-values.yaml` | Configuration Traefik |

## Deploiement local (Docker Compose)

### Prerequis
Creer un fichier `.env` a la racine:
```env
DOCKER_IMAGE_FRONTEND=registry.gitlab.com/sauretcyril/iacas/frontend:latest
DOCKER_IMAGE_BACKEND=registry.gitlab.com/sauretcyril/iacas/backend:latest
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=iacas_db
MYSQL_USER=iacas_user
MYSQL_PASSWORD=your_password
VITE_API_URL=http://localhost:4000/api
```

### Commandes
```bash
# Build et lancement
docker-compose up --build -d

# Voir les logs
docker-compose logs -f

# Arreter
docker-compose down

# Arreter et supprimer les volumes
docker-compose down -v
```

### URLs locales
- Frontend: http://localhost:3000
- Backend: http://localhost:4000

## Deploiement Kubernetes (via GitLab)

### Declenchement automatique
1. Pusher sur la branche `prod`
2. Le pipeline s'execute automatiquement
3. Les stages install/build/test/docker s'executent
4. Le stage `deploy` est **manuel** - cliquer sur le bouton dans GitLab

### Workflow recommande (main -> prod)
1. Developper sur `main` (ou branches features)
2. Tester localement
3. Quand pret pour la production, merger `main` dans `prod`
4. Le pipeline se declenche automatiquement sur `prod`

### Declenchement manuel du deploy
```bash
# Via l'API GitLab
curl --request POST \
  --header "PRIVATE-TOKEN: <votre-token>" \
  "https://gitlab.com/api/v4/projects/<project-id>/jobs/<job-id>/play"
```

### Verification du deploiement
```bash
# Se connecter au VPS et verifier
kubectl get pods -n iacas
kubectl get services -n iacas
kubectl get ingress -n iacas

# Logs d'un pod
kubectl logs -f <pod-name> -n iacas

# Decrire un pod
kubectl describe pod <pod-name> -n iacas
```

## Script de deploiement

Le script `dploy-ssh-job.sh` est execute par le job deploy:
1. Configure KUBECONFIG
2. Applique les manifests YAML dans le namespace `iacas`
3. Genere un README.md avec les ressources deployees

## Troubleshooting

### Le pipeline echoue au stage docker
- Verifier que `KUBECONFIG_CONTENT` est correctement encode en base64
- Verifier les credentials du registre GitLab

### Le deploiement Kubernetes echoue
- Verifier que le namespace `iacas` existe: `kubectl get ns iacas`
- Verifier les secrets: `kubectl get secrets -n iacas`
- Verifier l'ImagePullSecret: `kubectl get secret gitlab-registry -n iacas`

### Creer le secret gitlab-registry
```bash
kubectl create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com \
  --docker-username=<gitlab-user> \
  --docker-password=<gitlab-token> \
  --docker-email=<email> \
  -n iacas
```

### Les variables SMTP ne sont pas injectees
Les placeholders `__SMTP_HOST__`, `__SMTP_PORT__`, etc. sont remplaces par `sed` dans le job docker.
Verifier que les variables sont definies dans GitLab CI/CD.

## URLs de production

- Frontend: https://iacas.fr
- Backend API: https://api.iacas.fr/api
