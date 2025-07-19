import os
import glob

# Récupère toutes les variables du .env
with open('.env', 'r', encoding='utf-8') as f:
    env_vars = [line.split('=')[0].strip() for line in f if '=' in line and not line.startswith('#')]

# Cherche chaque variable dans tous les fichiers .py
unused = []
for var in env_vars:
    found = False
    for pyfile in glob.glob('**/*.py', recursive=True):
        with open(pyfile, 'r', encoding='utf-8') as f:
            if var in f.read():
                found = True
                break
    if not found:
        unused.append(var)

for var in unused:
    print(var)