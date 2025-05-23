import os
import sys

# Ajouter le dossier du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configurer les variables d'environnement si nécessaire
os.environ["PYTHONIOENCODING"] = "utf-8"

# Importer et exécuter l'application
try:
    from app import app
    
    if __name__ == "__main__":
        from multiprocessing import freeze_support
        freeze_support()
        app.run(debug=True)
        
except Exception as e:
    print(f"ERREUR DE DÉMARRAGE: {str(e)}")
    print("\nTraceback complet:")
    import traceback
    traceback.print_exc()
    
    # Attendre avant de fermer
    input("\nAppuyez sur Entrée pour quitter...")