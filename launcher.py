"""
Launcher de l'application principale IACAS-OTA.
Lance uniquement l'app Flask principale (port 5001).

L'agent local (local_agent/agent.py) est un processus séparé
à lancer sur le PC de l'utilisateur.
"""
import os
import sys

# Ajouter le dossier du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    from backend.app import app

    if __name__ == "__main__":
        from cy_app_config import app_config
        app_config.setup_logging()
        port = app_config.constants.get("port", 5001)
        print(f"[IACAS] Démarrage sur http://127.0.0.1:{port}")
        app.run(debug=True, port=port, use_reloader=False)

except Exception as e:
    print(f"ERREUR DE DÉMARRAGE: {str(e)}")
    import traceback
    traceback.print_exc()
    input("\nAppuyez sur Entrée pour quitter...")
