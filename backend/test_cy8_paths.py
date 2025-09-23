"""
Script de test pour la gestion des chemins - Version cy8
Teste la cohérence des chemins cross-platform
"""

import os
import sys
import tempfile

# Ajouter le chemin du backend si nécessaire
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cy8_paths import cy8_paths_manager, get_default_db_path, normalize_path

def test_path_consistency():
    """Tester la cohérence des chemins"""
    print("=== Test de cohérence des chemins cy8 ===\n")
    
    # Test des chemins par défaut
    print("=== Chemins par défaut ===")
    default_db = get_default_db_path()
    data_dir = cy8_paths_manager.get_data_directory()
    
    print(f"Base par défaut: {default_db}")
    print(f"Répertoire de données: {data_dir}")
    print(f"OS détecté: {os.name}")
    print(f"Séparateur système: '{os.sep}'")
    print()
    
    # Test de normalisation
    print("=== Test de normalisation ===")
    test_paths = [
        "g:/tmp/test.db",           # Style Unix
        "g:\\tmp\\test.db",         # Style Windows  
        "g:/tmp/../tmp/test.db",    # Avec navigation
        "./test.db",                # Relatif
        "test.db",                  # Nom seul
        "",                         # Vide
        None                        # None
    ]
    
    for path in test_paths:
        try:
            normalized = normalize_path(path) if path is not None else "None"
            print(f"'{path}' -> '{normalized}'")
        except Exception as e:
            print(f"'{path}' -> ERREUR: {e}")
    print()
    
    # Test de comparaison
    print("=== Test de comparaison ===")
    path_pairs = [
        ("g:/tmp/test.db", "g:\\tmp\\test.db"),
        ("g:/tmp/test.db", "G:/TMP/TEST.DB"),
        ("./test.db", os.path.abspath("test.db")),
        ("test.db", "autre.db")
    ]
    
    for path1, path2 in path_pairs:
        try:
            are_same = cy8_paths_manager.compare_paths(path1, path2)
            result = "IDENTIQUES" if are_same else "DIFFÉRENTS"
            print(f"'{path1}' vs '{path2}' -> {result}")
        except Exception as e:
            print(f"'{path1}' vs '{path2}' -> ERREUR: {e}")
    print()
    
    # Test des utilitaires
    print("=== Test des utilitaires ===")
    test_path = normalize_path("g:/tmp/subdir/test.db")
    
    print(f"Chemin de test: {test_path}")
    print(f"Répertoire parent: {cy8_paths_manager.get_directory_from_path(test_path)}")
    print(f"Nom de fichier: {cy8_paths_manager.get_filename_from_path(test_path)}")
    print(f"Extension: {cy8_paths_manager.get_file_extension(test_path)}")
    print(f"Est absolu: {cy8_paths_manager.is_absolute_path(test_path)}")
    print()
    
    # Test de nettoyage de nom de fichier
    print("=== Test de nettoyage de noms ===")
    bad_names = [
        "test<>file.db",
        "test:file.db", 
        "CON.db",
        "test\\file.db",
        "test/file.db",
        "  test file  .db",
        "test|file?.db"
    ]
    
    for bad_name in bad_names:
        clean_name = cy8_paths_manager.sanitize_filename(bad_name)
        print(f"'{bad_name}' -> '{clean_name}'")
    print()
    
    # Test de création de répertoire
    print("=== Test de création de répertoire ===")
    temp_dir = tempfile.gettempdir()
    test_file = os.path.join(temp_dir, "cy8_test", "subdir", "test.db")
    
    print(f"Fichier de test: {test_file}")
    print(f"Répertoire existe avant: {os.path.exists(os.path.dirname(test_file))}")
    
    # Utiliser ensure_dir
    result_file = cy8_paths_manager.ensure_directory_exists(test_file)
    print(f"Fichier résultat: {result_file}")
    print(f"Répertoire existe après: {os.path.exists(os.path.dirname(test_file))}")
    
    # Nettoyer
    try:
        import shutil
        test_root = os.path.join(temp_dir, "cy8_test")
        if os.path.exists(test_root):
            shutil.rmtree(test_root)
            print(f"Répertoire de test supprimé: {test_root}")
    except Exception as e:
        print(f"Erreur lors du nettoyage: {e}")
    
    print("\n=== Test terminé ===")

if __name__ == "__main__":
    test_path_consistency()