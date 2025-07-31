import time
import os
import json
from cy_exploreur import FileExplorer
from cy_analyse_prompt import PromptTableApp

COMMAND_FILE = "explorer_command.json"

def main():
    last_command = None
    while True:
        if os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                command = json.load(f)
            if command != last_command:
                action = command.get("action")
                if action == "explorer":
                    path = command.get("path")
                    if path and os.path.exists(path):
                        explorer = FileExplorer(initial_dir=path)
                        explorer.run()
                elif action == "prompt":
                    app = PromptTableApp(
                        file_path=command.get("file_path", "prompts.json"),
                        isDependOn=command.get("isDependOn", False),
                        num_dossier=command.get("num_dossier", ""),
                        nom_fichier=command.get("nom_fichier", ""),
                        descriptif=command.get("descriptif", "")
                    )
                    app.mainloop()
                last_command = command
            os.remove(COMMAND_FILE)
        time.sleep(2)

if __name__ == "__main__":
    main()