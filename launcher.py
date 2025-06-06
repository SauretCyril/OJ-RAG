import os
import sys
import subprocess
import pkg_resources

# Ajouter le dossier du projet au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
print(f"Chemin actuel : {current_dir}")
print(f"Chemin du backend : {backend_dir}")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configurer les variables d'environnement si nécessaire
os.environ["PYTHONIOENCODING"] = "utf-8"

""" # Vérifier si Flask est installé avec le support async
try:
    pkg_resources.get_distribution('flask[async]')
    print("Flask avec support async est déjà installé")
except pkg_resources.DistributionNotFound:
    print("Flask avec support async n'est pas installé. Installation en cours...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask[async]"])
        print("Flask avec support async a été installé avec succès")
    except subprocess.CalledProcessError:
        print("Erreur lors de l'installation de Flask avec support async")
 """
# Importer et exécuter l'application
try:
    # Utilisation de l'application originale
    from backend.app import app
    
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