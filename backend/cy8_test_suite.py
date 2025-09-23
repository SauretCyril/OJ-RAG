#!/usr/bin/env python3
# cy8_test_suite.py - Suite de tests pour le système cy8

import unittest
import sqlite3
import json
import os
import tempfile
from datetime import datetime

# Imports des classes cy8
try:
    from cy8_database_manager import cy8_database_manager
    from cy8_popup_manager import cy8_popup_manager
    from cy8_editable_tables import cy8_editable_tables
    from cy8_prompts_manager_main import cy8_prompts_manager
    print("✅ Tous les imports cy8 réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")

class TestCy8DatabaseManager(unittest.TestCase):
    """Tests pour le gestionnaire de base de données"""
    
    def setUp(self):
        """Préparation des tests"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db_manager = cy8_database_manager(self.db_path)
    
    def tearDown(self):
        """Nettoyage après tests"""
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
        except:
            pass
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except PermissionError:
            pass  # Ignoré sur Windows si le fichier est encore utilisé
    
    def test_database_initialization(self):
        """Test de l'initialisation de la base de données"""
        self.db_manager.init_database()
        
        # Vérifier que la table existe
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result, "La table prompts doit être créée")
    
    def test_prompt_crud_operations(self):
        """Test des opérations CRUD sur les prompts"""
        self.db_manager.init_database()
        
        # Test données
        test_prompt_values = {
            "1": {"id": "1", "type": "prompt", "value": "test prompt"}
        }
        test_workflow = {
            "1": {"inputs": {"text": "test"}, "class_type": "TestNode"}
        }
        
        # CREATE
        prompt_id = self.db_manager.create_prompt(
            name="Test Prompt",
            prompt_values=json.dumps(test_prompt_values),
            workflow=json.dumps(test_workflow),
            url="",
            model="test-model",
            status="draft",
            comment="Test comment"
        )
        self.assertIsNotNone(prompt_id, "Le prompt doit être sauvegardé")
        
        # READ
        prompts = self.db_manager.get_all_prompts()
        self.assertGreaterEqual(len(prompts), 1, "Au moins un prompt doit être trouvé")
        
        # Trouver notre prompt de test
        test_prompt = None
        for prompt in prompts:
            if prompt[1] == "Test Prompt":  # Nom du prompt
                test_prompt = prompt
                break
        
        self.assertIsNotNone(test_prompt, "Le prompt de test doit être trouvé")
        self.assertEqual(test_prompt[1], "Test Prompt", "Le nom doit correspondre")
        
        # UPDATE
        try:
            self.db_manager.update_prompt(
                prompt_id,
                name="Updated Prompt",
                prompt_values=json.dumps(test_prompt_values),
                workflow=json.dumps(test_workflow),
                url="",
                model="test-model",
                comment="Updated comment",
                status="ready"
            )
            update_success = True
        except Exception as e:
            update_success = False
            print(f"Erreur lors de la mise à jour: {e}")
        
        self.assertTrue(update_success, "La mise à jour doit réussir")
        
        # DELETE
        try:
            self.db_manager.delete_prompt(prompt_id)
            delete_success = True
        except Exception as e:
            delete_success = False
            print(f"Erreur lors de la suppression: {e}")
        
        self.assertTrue(delete_success, "La suppression doit réussir")
    
    def test_model_derivation(self):
        """Test de la dérivation automatique du modèle"""
        workflow = {
            "4": {
                "inputs": {"ckpt_name": "test-model.ckpt"},
                "class_type": "CheckpointLoaderSimple"
            }
        }
        
        model = self.db_manager.derive_model_from_workflow(json.dumps(workflow))
        self.assertEqual(model, "test-model", "Le modèle doit être dérivé correctement (sans extension)")

class TestCy8Integration(unittest.TestCase):
    """Tests d'intégration du système cy8"""
    
    def setUp(self):
        """Préparation des tests d'intégration"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
    
    def tearDown(self):
        """Nettoyage après tests"""
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except PermissionError:
            pass  # Ignoré sur Windows si le fichier est encore utilisé
    
    def test_full_system_initialization(self):
        """Test d'initialisation complète du système"""
        try:
            # Initialiser le gestionnaire principal (sans UI)
            # Note: Les tests UI nécessiteraient un environnement graphique
            db_manager = cy8_database_manager(self.db_path)
            db_manager.init_database()
            
            # Vérifier que la base est correctement initialisée
            prompts = db_manager.get_all_prompts()
            self.assertIsInstance(prompts, list, "La liste des prompts doit être retournée")
            
            print("✅ Initialisation complète du système réussie")
            
        except Exception as e:
            self.fail(f"L'initialisation du système a échoué: {e}")

class TestCy8DataStructures(unittest.TestCase):
    """Tests des structures de données cy8"""
    
    def test_prompt_values_structure(self):
        """Test de la structure des prompt_values"""
        valid_prompt_values = {
            "1": {"id": "6", "type": "prompt", "value": "test"},
            "2": {"id": "7", "type": "prompt", "value": "negative"},
            "3": {"id": "3", "type": "seed", "value": 123456}
        }
        
        # Test de sérialisation/désérialisation JSON
        json_str = json.dumps(valid_prompt_values)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed, valid_prompt_values, "La structure doit être préservée")
        
        # Test des clés requises
        for key, value in parsed.items():
            self.assertIn("id", value, f"L'entrée {key} doit avoir un id")
            self.assertIn("type", value, f"L'entrée {key} doit avoir un type")
    
    def test_workflow_structure(self):
        """Test de la structure du workflow"""
        valid_workflow = {
            "3": {
                "inputs": {"seed": 123, "steps": 20},
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {"ckpt_name": "model.ckpt"},
                "class_type": "CheckpointLoaderSimple"
            }
        }
        
        # Test de sérialisation/désérialisation JSON
        json_str = json.dumps(valid_workflow)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed, valid_workflow, "La structure workflow doit être préservée")
        
        # Test des clés requises
        for node_id, node_data in parsed.items():
            self.assertIn("class_type", node_data, f"Le nœud {node_id} doit avoir class_type")
            self.assertIn("inputs", node_data, f"Le nœud {node_id} doit avoir inputs")

def run_tests():
    """Exécuter tous les tests"""
    print("🧪 Démarrage des tests cy8...")
    print("=" * 50)
    
    # Créer la suite de tests
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Ajouter les tests
    test_suite.addTests(loader.loadTestsFromTestCase(TestCy8DatabaseManager))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCy8Integration))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCy8DataStructures))
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("✅ Tous les tests cy8 ont réussi !")
    else:
        print("❌ Certains tests ont échoué")
        print(f"Échecs: {len(result.failures)}")
        print(f"Erreurs: {len(result.errors)}")
    
    return result.wasSuccessful()

def test_imports():
    """Test rapide des imports"""
    print("🔍 Test des imports cy8...")
    
    imports_status = {}
    
    modules = [
        'cy8_database_manager',
        'cy8_popup_manager', 
        'cy8_editable_tables',
        'cy8_prompts_manager_main'
    ]
    
    for module in modules:
        try:
            __import__(module)
            imports_status[module] = "✅"
        except ImportError as e:
            imports_status[module] = f"❌ {e}"
    
    print("\nRésultats des imports:")
    for module, status in imports_status.items():
        print(f"  {module}: {status}")
    
    return all("✅" in status for status in imports_status.values())

if __name__ == "__main__":
    print("🚀 Suite de tests cy8 - Système de gestion des prompts ComfyUI")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test des imports d'abord
    imports_ok = test_imports()
    print()
    
    if imports_ok:
        # Exécuter les tests complets
        tests_ok = run_tests()
        
        if tests_ok:
            print("\n🎉 Système cy8 entièrement fonctionnel !")
        else:
            print("\n⚠️  Certains tests ont échoué, vérifiez les détails ci-dessus")
    else:
        print("\n❌ Problèmes d'imports détectés, impossible d'exécuter les tests complets")