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
            print (f"dbg-666a : Received command: {command}")
            if command != last_command:
                action = command.get("action")
                if action == "explorer":
                    print (f"dbg-666a : Action: {action}")
                    path = command.get("path")
                    explorer_type = command.get("explorer_type", "")
                    print (f"dbg-666b Path : {path}")
                    print (f"dbg-666c Type : {explorer_type}")
                    if path and os.path.exists(path):
                        print (f"dbg-666d : Opening file explorer at: {path}")

                        explorer = FileExplorer(
                            initial_dir=path, 
                            explorer_type=explorer_type
                        )
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