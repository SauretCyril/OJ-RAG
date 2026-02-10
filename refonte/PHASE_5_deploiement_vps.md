# Phase 5 — Déploiement VPS Ubuntu

## Objectif
Mettre l'application en production sur un VPS Ubuntu avec HTTPS,
démarrage automatique, logs, et séparation claire des responsabilités.

---

## Architecture cible

```
Internet
    │ HTTPS (443)
    ▼
[nginx]  ← reverse proxy, SSL, compression, static files
    │ HTTP (5000) — interne uniquement
    ▼
[gunicorn]  ← WSGI server, N workers
    │
    ▼
[Flask app]  ← backend/app.py

Chaque utilisateur (sur son PC) :
    Navigateur → VPS:443 (app web)
    Navigateur → localhost:5005 (agent local — reste sur son PC)
```

---

## Prérequis VPS

```bash
# Ubuntu 22.04 LTS recommandé
# Minimum : 1 vCPU, 1 GB RAM, 20 GB SSD

# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer les dépendances système
sudo apt install -y python3.11 python3.11-venv python3-pip \
                   nginx certbot python3-certbot-nginx \
                   libreoffice-common  # pour conversion DOCX→PDF headless
```

---

## Arborescence sur le VPS

```
/srv/iacas-ota/
├── backend/               ← code Python (cloné depuis git)
├── static/                ← assets frontend
├── templates/             ← HTML templates
├── logs/
│   ├── iacas.log          ← logs applicatifs
│   └── access.log         ← logs nginx
├── data/
│   ├── users.json         ← comptes utilisateurs
│   └── users/             ← profils par utilisateur
├── .env                   ← variables d'environnement (NON dans git)
├── .venv/                 ← virtualenv Python
└── gunicorn.conf.py       ← configuration gunicorn
```

---

## 1. Utilisateur système dédié

```bash
# Créer un utilisateur sans droits sudo pour l'app
sudo useradd -m -s /bin/bash iacas
sudo passwd iacas

# L'app tourne avec cet utilisateur (pas root)
sudo chown -R iacas:iacas /srv/iacas-ota/
```

---

## 2. Déploiement du code

```bash
# Se connecter en tant qu'iacas
sudo su - iacas

# Cloner le dépôt
git clone <repo_url> /srv/iacas-ota
cd /srv/iacas-ota

# Créer le virtualenv
python3.11 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
pip install gunicorn

# Créer le fichier .env (NE PAS commit)
cp .env.example .env
nano .env
```

### Contenu `.env` de production
```env
FLASK_ENV=production
SECRET_KEY=<générer avec: python3 -c "import secrets; print(secrets.token_hex(32))">
MISTRAL_API_KEY=<votre clé Mistral>
ROOT_DIR=                    # vide sur le VPS
ANNONCES_FILE_DIR=
ANNONCES_DIR_FILTER=
ANNONCES_DIR_STATE=
DIR_REA_FILE=
DIR_SOFT_SK_FILE=
AIXPLO_DIR=data/
AIXPLO_FILE=AixPlo.json
LOG_LEVEL=INFO
```

---

## 3. Configuration Gunicorn

### `gunicorn.conf.py`
```python
# Nombre de workers = (2 * CPU) + 1
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1

# Binding interne uniquement (nginx fait le reverse proxy)
bind = "127.0.0.1:5000"

# Timeout (en secondes) — augmenter pour les opérations PDF/AI longues
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logs
accesslog = "/srv/iacas-ota/logs/gunicorn-access.log"
errorlog  = "/srv/iacas-ota/logs/gunicorn-error.log"
loglevel  = "info"

# Worker class async (pour Flask async)
worker_class = "gthread"
threads = 4

# Sécurité
limit_request_line = 4096
limit_request_fields = 100
```

### Lancer gunicorn (test)
```bash
source .venv/bin/activate
gunicorn -c gunicorn.conf.py "backend.app:app"
```

---

## 4. Service systemd

### `/etc/systemd/system/iacas-ota.service`
```ini
[Unit]
Description=IACAS OTA - Gestionnaire de candidatures
After=network.target

[Service]
User=iacas
Group=iacas
WorkingDirectory=/srv/iacas-ota
Environment="PATH=/srv/iacas-ota/.venv/bin"
EnvironmentFile=/srv/iacas-ota/.env
ExecStart=/srv/iacas-ota/.venv/bin/gunicorn -c gunicorn.conf.py "backend.app:app"
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

# Sécurité système
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Activer et démarrer
```bash
sudo systemctl daemon-reload
sudo systemctl enable iacas-ota
sudo systemctl start iacas-ota
sudo systemctl status iacas-ota
```

---

## 5. Configuration Nginx

### `/etc/nginx/sites-available/iacas-ota`
```nginx
server {
    listen 80;
    server_name iacas.example.com;

    # Redirect HTTP → HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name iacas.example.com;

    # SSL — Let's Encrypt (rempli par certbot)
    ssl_certificate     /etc/letsencrypt/live/iacas.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iacas.example.com/privkey.pem;

    # SSL sécurité
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Logs
    access_log /srv/iacas-ota/logs/nginx-access.log;
    error_log  /srv/iacas-ota/logs/nginx-error.log;

    # Taille max upload (PDF, DOCX)
    client_max_body_size 15M;

    # Static files — servis directement par nginx (plus rapide)
    location /static/ {
        alias /srv/iacas-ota/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy vers gunicorn pour tout le reste
    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

### Activer le site
```bash
sudo ln -s /etc/nginx/sites-available/iacas-ota /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Let's Encrypt SSL
```bash
sudo certbot --nginx -d iacas.example.com
# Renouvellement automatique via cron — déjà configuré par certbot
```

---

## 6. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # ports 80 et 443
sudo ufw deny 5000/tcp        # gunicorn — interne uniquement
sudo ufw enable
sudo ufw status
```

---

## 7. Rotation des logs

### `/etc/logrotate.d/iacas-ota`
```
/srv/iacas-ota/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload iacas-ota
    endscript
}
```

---

## 8. Procédure de mise à jour (déploiement continu)

```bash
# Sur le VPS, en tant qu'iacas
cd /srv/iacas-ota

# Récupérer les mises à jour
git pull origin main

# Mettre à jour les dépendances si nécessaire
source .venv/bin/activate
pip install -r requirements.txt

# Redémarrer l'app sans interruption (graceful reload)
sudo systemctl reload iacas-ota
# ou si changements majeurs :
sudo systemctl restart iacas-ota
```

---

## 9. Monitoring minimal

### Vérifier que l'app tourne
```bash
sudo systemctl status iacas-ota
curl -I https://iacas.example.com/ping
```

### Voir les logs en temps réel
```bash
sudo journalctl -u iacas-ota -f
tail -f /srv/iacas-ota/logs/iacas.log
```

### Espace disque
```bash
df -h /srv/iacas-ota/
du -sh /srv/iacas-ota/logs/
```

---

## 10. Checklist déploiement final

### Avant mise en ligne
- [ ] `.env` présent et complet (non committé)
- [ ] `FLASK_ENV=production` et `debug=False`
- [ ] `SECRET_KEY` forte (32+ chars aléatoires)
- [ ] `MISTRAL_API_KEY` valide
- [ ] Certificat SSL valide (`certbot --test-cert` d'abord)
- [ ] `sudo nginx -t` → pas d'erreur
- [ ] `gunicorn` démarre sans erreur

### Après mise en ligne
- [ ] `https://iacas.example.com` accessible depuis navigateur
- [ ] HTTP redirige vers HTTPS
- [ ] Login fonctionne
- [ ] Headers sécurité présents (tester sur https://securityheaders.com)
- [ ] Logs nginx et gunicorn se remplissent normalement
- [ ] `sudo systemctl enable iacas-ota` → démarrage auto après reboot
- [ ] `sudo ufw status` → seuls ports 22, 80, 443 ouverts

### Test multi-utilisateur
- [ ] Alice se connecte → voit sa config
- [ ] Bob se connecte simultanément → voit sa config
- [ ] Alice ne peut pas voir les données de Bob

---

## Livrable Phase 5

- [ ] VPS Ubuntu configuré avec utilisateur `iacas` dédié
- [ ] Code déployé dans `/srv/iacas-ota/`
- [ ] Gunicorn configuré et démarré via systemd
- [ ] Nginx reverse proxy avec SSL Let's Encrypt
- [ ] HTTP → HTTPS forcé
- [ ] Firewall activé (ufw)
- [ ] Logs rotatifs configurés
- [ ] URL de production accessible et sécurisée
