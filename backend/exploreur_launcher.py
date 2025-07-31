import time
import os
from cy_exploreur import FileExplorer

COMMAND_FILE = "explorer_command.txt"

def main():
    last_path = None
    while True:
        if os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()
            if path and path != last_path and os.path.exists(path):
                explorer = FileExplorer(initial_dir=path)
                explorer.run()
                last_path = path
            # Nettoyer le fichier pour éviter de relancer
            os.remove(COMMAND_FILE)
        time.sleep(2)  # Vérifie toutes les 2 secondes

if __name__ == "__main__":
    main()