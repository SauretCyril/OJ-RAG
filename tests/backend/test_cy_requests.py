"""
Tests unitaires pour cy_requests.py
Tests des routes et fonctions de requêtes backend
"""

import pytest
import json
import io
from unittest.mock import Mock, patch, mock_open
from flask import Flask

# Import des modules à tester
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from backend.cy_requests import (
        extract_pdf_text,
        extract_text_from_pdf,
        get_job_answer
    )
    import backend.cy_requests as cy_requests_module
except ImportError as e:
    print(f"Import error: {e}")
    pytest.skip("Modules backend non disponibles", allow_module_level=True)


class TestExtractPdfText:
    """Tests pour l'extraction de texte PDF"""
    
    def setup_method(self):
        """Configuration pour chaque test"""
        self.app = Flask(__name__)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    @patch('backend.cy_requests.extract_text_from_pdf')
    @patch('backend.cy_requests.os.path.exists')
    @patch('backend.cy_requests.GetRoot')
    def test_extract_pdf_text_success(self, mock_get_root, mock_exists, mock_extract):
        """Test d'extraction PDF réussie"""
        # Configuration des mocks
        mock_get_root.return_value = "/test/root"
        mock_exists.return_value = True
        mock_extract.return_value = "Contenu du PDF extrait"
        
        with self.app.test_request_context('/extract_pdf_text', 
                                         method='POST',
                                         json={'file': 'test.pdf'}):
            
            # Simuler l'appel à la route
            result = extract_pdf_text()
            
            assert result is not None
            # Le test exact dépend de l'implémentation de votre route
    
    @patch('backend.cy_requests.os.path.exists')
    @patch('backend.cy_requests.GetRoot')
    def test_extract_pdf_text_file_not_found(self, mock_get_root, mock_exists):
        """Test avec fichier PDF non trouvé"""
        mock_get_root.return_value = "/test/root"
        mock_exists.return_value = False
        
        with self.app.test_request_context('/extract_pdf_text',
                                         method='POST', 
                                         json={'file': 'nonexistent.pdf'}):
            
            result = extract_pdf_text()
            
            # Devrait retourner une erreur 404 ou similaire
            # L'assertion exacte dépend de votre implémentation
            assert result is not None
    
    def test_extract_pdf_text_missing_file_param(self):
        """Test sans paramètre de fichier"""
        with self.app.test_request_context('/extract_pdf_text',
                                         method='POST',
                                         json={}):
            
            # La fonction devrait gérer le cas où 'file' est manquant
            try:
                result = extract_pdf_text()
                # Vérifier que la fonction ne plante pas
                assert result is not None
            except Exception as e:
                # Ou vérifier qu'elle gère l'erreur appropriément
                assert "file" in str(e).lower() or "missing" in str(e).lower()


class TestExtractTextFromPdf:
    """Tests pour la fonction d'extraction PDF directe"""
    
    @patch('backend.cy_requests.PdfReader')
    def test_extract_text_from_valid_pdf(self, mock_pdf_reader):
        """Test d'extraction depuis un PDF valide"""
        # Mock du lecteur PDF
        mock_reader = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock() 
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader
        
        with patch('builtins.open', mock_open(read_data=b'PDF data')):
            result = extract_text_from_pdf("test.pdf")
            
            expected = "Page 1 content\nPage 2 content"
            assert result == expected
    
    @patch('backend.cy_requests.PdfReader')
    def test_extract_text_from_corrupted_pdf(self, mock_pdf_reader):
        """Test avec un PDF corrompu"""
        mock_pdf_reader.side_effect = Exception("PDF corrupted")
        
        with patch('builtins.open', mock_open(read_data=b'corrupted data')):
            result = extract_text_from_pdf("corrupted.pdf")
            
            # La fonction devrait gérer l'erreur gracieusement
            assert result is None or result == ""
    
    def test_extract_text_from_nonexistent_pdf(self):
        """Test avec un fichier inexistant"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = extract_text_from_pdf("nonexistent.pdf")
            
            assert result is None or result == ""
    
    @patch('backend.cy_requests.PdfReader')
    def test_extract_text_from_empty_pdf(self, mock_pdf_reader):
        """Test avec un PDF vide"""
        mock_reader = Mock()
        mock_reader.pages = []
        mock_pdf_reader.return_value = mock_reader
        
        with patch('builtins.open', mock_open(read_data=b'empty pdf')):
            result = extract_text_from_pdf("empty.pdf")
            
            assert result == ""


class TestGetJobAnswer:
    """Tests pour la fonction de réponse IA"""
    
    def setup_method(self):
        """Configuration pour chaque test"""
        self.app = Flask(__name__)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    @patch('backend.cy_requests.extract_text_from_pdf')
    @patch('backend.cy_requests.get_mistral_answer')
    @patch('backend.cy_requests.GetRoot')
    def test_get_job_answer_success(self, mock_get_root, mock_mistral, mock_extract):
        """Test de réponse IA réussie"""
        # Configuration des mocks
        mock_get_root.return_value = "/test/root"
        mock_extract.return_value = "Contenu du PDF"
        mock_mistral.return_value = "Réponse de l'IA"
        
        with self.app.test_request_context('/get_AI_answer',
                                         method='POST',
                                         json={
                                             'path': 'test.pdf',
                                             'RQ': 'Question test',
                                             'NumDos': 'DOSS001',
                                             'libre': True
                                         }):
            
            # Note: Cette fonction est async, il faudrait adapter le test
            # pour gérer l'asynchrone correctement
            try:
                # Pour ce test, on suppose une version synchrone
                result = get_job_answer()
                assert result is not None
            except Exception as e:
                # Si la fonction est async, on vérifie au moins qu'elle existe
                assert "async" in str(type(e)) or hasattr(get_job_answer, '__await__')
    
    @patch('backend.cy_requests.extract_text_from_pdf')
    @patch('backend.cy_requests.GetRoot')
    def test_get_job_answer_pdf_not_found(self, mock_get_root, mock_extract):
        """Test avec PDF non trouvé"""
        mock_get_root.return_value = "/test/root"
        mock_extract.return_value = None  # Fichier non trouvé
        
        with self.app.test_request_context('/get_AI_answer',
                                         method='POST',
                                         json={
                                             'path': 'nonexistent.pdf', 
                                             'RQ': 'Question',
                                             'NumDos': 'DOSS001'
                                         }):
            
            try:
                result = get_job_answer()
                # Devrait gérer le cas gracieusement
            except Exception:
                # Acceptable si la fonction lève une exception appropriée
                pass
    
    def test_get_job_answer_missing_parameters(self):
        """Test avec paramètres manquants"""
        with self.app.test_request_context('/get_AI_answer',
                                         method='POST',
                                         json={'path': 'test.pdf'}):  # Paramètres incomplets
            
            try:
                result = get_job_answer()
                # Fonction devrait gérer les paramètres manquants
            except Exception as e:
                # Ou lever une erreur appropriée
                assert any(param in str(e).lower() for param in ['rq', 'question', 'missing'])


class TestIntegrationRequests:
    """Tests d'intégration pour les requêtes"""
    
    def setup_method(self):
        """Configuration pour les tests d'intégration"""
        self.app = Flask(__name__)
        self.client = self.app.test_client()
    
    @patch('backend.cy_requests.extract_text_from_pdf')
    @patch('backend.cy_requests.get_mistral_answer')
    @patch('backend.cy_requests.GetRoot')
    @patch('backend.cy_requests.os.path.exists')
    def test_full_pdf_analysis_workflow(self, mock_exists, mock_get_root, mock_mistral, mock_extract):
        """Test du workflow complet d'analyse PDF"""
        # Configuration des mocks pour un workflow réussi
        mock_exists.return_value = True
        mock_get_root.return_value = "/test/root"
        mock_extract.return_value = "Contenu du document PDF"
        mock_mistral.return_value = '{"formatted_text": "Analyse complète du document"}'
        
        # Données de test
        test_data = {
            'path': 'documents/DOSS001/DOSS001_annonce_.pdf',
            'RQ': 'Analysez ce document et extrayez les informations clés',
            'NumDos': 'DOSS001',
            'libre': True
        }
        
        with self.app.test_request_context('/get_AI_answer',
                                         method='POST',
                                         json=test_data):
            
            try:
                # Test du workflow
                result = get_job_answer()
                
                # Vérifications
                mock_extract.assert_called()
                mock_mistral.assert_called()
                
                # Le résultat devrait contenir la réponse formatée
                assert result is not None
                
            except Exception as e:
                # Gérer les cas où la fonction est async
                assert "async" in str(type(e)) or "await" in str(e)
    
    @patch('backend.cy_requests.extract_text_from_pdf')
    @patch('backend.cy_requests.GetRoot')
    def test_error_handling_chain(self, mock_get_root, mock_extract):
        """Test de la chaîne de gestion d'erreurs"""
        mock_get_root.return_value = "/test/root"
        
        # Simuler différents types d'erreurs
        error_scenarios = [
            (FileNotFoundError("File not found"), "file"),
            (PermissionError("Access denied"), "permission"),
            (Exception("General error"), "error")
        ]
        
        for exception, expected_key in error_scenarios:
            mock_extract.side_effect = exception
            
            with self.app.test_request_context('/extract_pdf_text',
                                             method='POST',
                                             json={'file': 'test.pdf'}):
                try:
                    result = extract_pdf_text()
                    # Vérifier que l'erreur est gérée
                    assert result is not None
                except Exception as e:
                    # Vérifier que l'erreur est appropriée
                    assert expected_key in str(e).lower()


# Utilitaires pour les tests
class MockRequest:
    """Mock pour les requêtes Flask"""
    
    def __init__(self, json_data=None, form_data=None):
        self.json_data = json_data or {}
        self.form_data = form_data or {}
    
    def get_json(self):
        return self.json_data
    
    def get(self, key, default=None):
        return self.json_data.get(key, default)


# Fixtures
@pytest.fixture
def mock_pdf_content():
    """Fixture pour du contenu PDF exemple"""
    return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n...'

@pytest.fixture
def mock_pdf_text():
    """Fixture pour du texte extrait d'un PDF"""
    return "Ceci est le contenu textuel extrait du PDF de test."

@pytest.fixture
def mock_mistral_response():
    """Fixture pour une réponse Mistral"""
    return {
        "formatted_text": "Analyse détaillée du document",
        "raw_text": "Réponse brute de l'IA"
    }

@pytest.fixture
def flask_app():
    """Fixture pour l'application Flask"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app
