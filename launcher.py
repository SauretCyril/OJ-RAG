import os
import sys
import subprocess

def is_venv_active():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        'VIRTUAL_ENV' in os.environ
    )

def activate_venv_and_restart():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(current_dir, ".venv")
    if not os.path.isdir(venv_dir):
        print("Aucun environnement virtuel .venv trouvé.")
        return
    python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = os.path.join(venv_dir, "bin", "python")
    if not os.path.exists(python_exe):
        print("Impossible de trouver l'exécutable Python du venv.")
        return
    print("Activation du venv et redémarrage du launcher...")
    os.execv(python_exe, [python_exe] + sys.argv)

if not is_venv_active():
    activate_venv_and_restart()

# Ajouter le dossier du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    from backend.app import app

    if __name__ == "__main__":
        from multiprocessing import freeze_support
        freeze_support()
        # Lancer le serveur Flask (une seule instance)
        app.run(debug=True, use_reloader=False)
except Exception as e:
    print(f"ERREUR DE DÉMARRAGE: {str(e)}")
    import traceback
    traceback.print_exc()
    input("\nAppuyez sur Entrée pour quitter...")