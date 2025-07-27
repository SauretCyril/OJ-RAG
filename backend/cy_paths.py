from backend.cy_cookies import *
import os
import tkinter as tk
from tkinter import filedialog
import shutil

import platform
if platform.system() == "Windows":
    import pythoncom
else:
    pythoncom = None


paths = Blueprint('cookies', __name__)

@paths.route('/get_directory_root', methods=['GET'])
def get_directory_root():
    try:
        root_dir = GetRoot()
        return jsonify({'root_directory': root_dir}), 200
    except Exception as e:
        logger.error(f"Error retrieving root directory: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
def GetRoot():
    # Obtenir le répertoire de base des variables d'environnement
    root_dir = os.getenv("ROOT_DIR")
    if not root_dir:
        # Fallback si ROOT_DIR n'est pas défini
        root_dir = os.getenv("ANNONCES_FILE_DIR")
    
    # Vérifier si l'utilisateur a sélectionné un répertoire personnalisé
    newroot = get_cookie_value("current_dossier")
    
    # Utiliser le répertoire personnalisé s'il existe
    if newroot and os.path.exists(newroot):
        #print(f"[INFO] Utilisation du répertoire personnalisé: {newroot}")
        root_dir = newroot
    
    # Normaliser le chemin (remplacer les backslashes par des slashes)
    root_dir = root_dir.replace('\\', '/')
    
    # Vérification de sécurité
    if not os.path.exists(root_dir):
        print(f"[WARN] Le répertoire racine '{root_dir}' n'existe pas. Tentative de création...")
        try:
            os.makedirs(root_dir, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Impossible de créer le répertoire racine: {str(e)}")
    
    return root_dir

def GetDirFilter():
    # Récupérer le chemin relatif du filtre depuis les variables d'environnement
    path_filter = os.getenv("ANNONCES_DIR_FILTER")
    
    # Récupérer le répertoire racine
    dirroot = GetRoot()
    
    # Combiner le chemin racine et le chemin relatif
    new_path = os.path.join(dirroot, path_filter)
    
    # Normaliser le chemin (remplacer les backslashes par des slashes)
    new_path = new_path.replace('\\', '/')
    
    # S'assurer que le répertoire existe
    if not os.path.exists(new_path):
        print(f"[INFO] Création du répertoire filter: {new_path}")
        try:
            os.makedirs(new_path, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Impossible de créer le répertoire filter: {str(e)}")
    
    return new_path



def GetDirState():
    # Récupérer le chemin depuis les variables d'environnement
    path_State = os.getenv("ANNONCES_DIR_STATE")
    
    # Normaliser le chemin (remplacer les backslashes par des slashes)
    new_path = path_State.replace('\\', '/')
    
    # S'assurer que le répertoire existe
    if not os.path.exists(new_path):
        print(f"[INFO] Création du répertoire state: {new_path}")
        try:
            os.makedirs(new_path, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Impossible de créer le répertoire state: {str(e)}")
    
    return new_path

def GetDirCRQ(dir):
    path_CRQ =os.getenv(dir)
    dirroot = GetRoot()
    new_path=os.path.join(dirroot,path_CRQ)
    print("dbg652 filter dir = ",new_path)
    new_path = new_path.replace('\\', '/') 
    return new_path


def GetDirREA():
    path_REA =os.getenv("DIR_REA_FILE")
    dirroot = GetRoot()
    #print("dbg651d root = ",dirroot)
    new_path=os.path.join(dirroot,path_REA)
    new_path = new_path.replace('\\', '/')
    #print("dbg651c realisation dir = ",new_path)
    return new_path

def GetDirSoft_Sk():
    path_soft_sk = os.getenv("DIR_SOFT_SK_FILE")
    dirroot = GetRoot()
    #print("dbg651a root = ",dirroot)
    new_path=os.path.join(dirroot,path_soft_sk)
    new_path = new_path.replace('\\', '/')
    #print("dbg651b realisation dir = ",new_path)
    return new_path


def GetOneDir(envName):
    dirroot = GetRoot()
    #print("dbg651f root = ",dirroot)
    
    path = os.getenv(envName)
    print(f"dbg651e path de {envName} = ",path )
    
    new_path=os.path.join(dirroot,path)
    new_path = new_path.replace('\\', '/')
    
    #print(f"dbg651g GetOneDir ({envName}) => ",new_path)
    return new_path



def buildAllPaths():
    ''' repertoire principal des dossiers'''
    dirroot = GetRoot()
    MakeNecessariesDir(dirroot)
    ''' Repertoire des criteres d'exclusion '''
    # dirstate= GetDirState()
    # MakeNecessariesDir(dirstate)
    '''repertoire des requetes pour extraire les infos de classements'''
    #DirCRQ = GetDirCRQ()
    #MakeNecessariesDir(DirCRQ)
    
    '''repertoire des realisations'''
    # DirREA = GetDirREA()
    # MakeNecessariesDir(DirREA)
    

    
def MakeNecessariesDir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    


@paths.route('/check_dossier_exists', methods=['POST'])
def check_dossier_exist():
    try:
        directory_path = GetRoot()
        dossier = request.json.get('dossier')
        dossier_path = os.path.join(directory_path, dossier)
        if not dossier_path:
            return jsonify({'error': 'Missing dossier path'}), 400

        exists = os.path.exists(dossier_path)
        return jsonify({'exists': exists}), 200

    except Exception as e:
        logger.error(f"Error checking dossier existence: {str(e)}")
        return jsonify({'error': str(e)}), 500

@paths.route('/select_directory', methods=['POST'])
def select_directory():
    """
    Ouvre une boîte de dialogue pour sélectionner un répertoire
    """
    try:
        if pythoncom:
            pythoncom.CoInitialize()  # Initialisation COM pour Windows

        # Créer une fenêtre Tkinter cachée
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale
        root.attributes('-topmost', True)  # Placer au premier plan

        # Ouvrir la boîte de dialogue de sélection de répertoire
        selected_directory = filedialog.askdirectory(
            title="Sélectionner un répertoire de travail",
            initialdir=GetRoot()  # Commencer par le répertoire racine actuel
        )

        # Nettoyer
        root.destroy()
        if pythoncom:
            pythoncom.CoUninitialize()

        if selected_directory:
            # Normaliser le chemin
            selected_directory = selected_directory.replace('\\', '/')
            return jsonify({
                'success': True,
                'selected_directory': selected_directory
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Aucun répertoire sélectionné'
            }), 200

    except Exception as e:
        logger.error(f"Error selecting directory: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@paths.route('/move_current_dossier', methods=['POST'])
def move_current_dossier():
    try:
        data = request.get_json()
        source = data.get('source')
        target = data.get('target')
        if not source or not target:
            return jsonify({'success': False, 'error': 'Source ou cible manquante'}), 400

        # Normalisation des chemins
        source = source.replace('\\', '/')
        target = target.replace('\\', '/')

        # Annule si le dossier cible existe déjà
        if os.path.exists(target):
            return jsonify({'success': False, 'error': 'Le dossier cible existe déjà'}), 409

        # Vérifie que le dossier source existe
        if not os.path.exists(source):
            return jsonify({'success': False, 'error': 'Le dossier source est introuvable'}), 404

        # Déplace le dossier
        shutil.move(source, target)
        return jsonify({'success': True, 'message': 'Dossier déplacé'}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


