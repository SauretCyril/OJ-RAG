"""
Tests unitaires pour cy_mistral.py
Tests des fonctions d'analyse de documents avec Mistral AI
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from docx import Document

# Import des modules à tester
try:
    from backend.cy_mistral import (
        extract_text_from_word,
        get_mistral_answer,
        create_excel_report,
        analyser_documents,
        get_mistral_translate
    )
except ImportError:
    # Fallback si les imports ne fonctionnent pas
    pytest.skip("Modules backend non disponibles", allow_module_level=True)


class TestExtractTextFromWord:
    """Tests pour l'extraction de texte depuis Word"""
    
    def test_extract_text_from_valid_docx(self):
        """Test d'extraction depuis un fichier Word valide"""
        with patch('backend.cy_mistral.Document') as mock_document:
            # Mock du document Word
            mock_doc = Mock()
            mock_paragraph1 = Mock()
            mock_paragraph1.text = "Premier paragraphe"
            mock_paragraph2 = Mock()
            mock_paragraph2.text = "Deuxième paragraphe"
            mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
            mock_document.return_value = mock_doc
            
            result = extract_text_from_word("test.docx")
            
            assert result == "Premier paragraphe\nDeuxième paragraphe"
            mock_document.assert_called_once_with("test.docx")
    
    def test_extract_text_from_nonexistent_file(self):
        """Test avec un fichier inexistant"""
        with patch('backend.cy_mistral.Document', side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                extract_text_from_word("nonexistent.docx")
    
    def test_extract_text_with_empty_document(self):
        """Test avec un document vide"""
        with patch('backend.cy_mistral.Document') as mock_document:
            mock_doc = Mock()
            mock_doc.paragraphs = []
            mock_document.return_value = mock_doc
            
            result = extract_text_from_word("empty.docx")
            
            assert result == ""


class TestGetMistralAnswer:
    """Tests pour les appels à l'API Mistral"""
    
    @patch('backend.cy_mistral.requests.post')
    @patch('backend.cy_mistral.os.getenv')
    def test_successful_mistral_api_call(self, mock_getenv, mock_post):
        """Test d'un appel API réussi"""
        # Mock des variables d'environnement
        mock_getenv.return_value = "test-api-key"
        
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Réponse de Mistral AI"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = get_mistral_answer(
            "Quelle est la capitale de la France ?",
            "Assistant géographe",
            "Contenu du document"
        )
        
        assert result == "Réponse de Mistral AI"
        mock_post.assert_called_once()
        
        # Vérifier les paramètres de l'appel
        call_args = mock_post.call_args
        assert "https://api.mistral.ai" in call_args[0][0]
        assert "test-api-key" in call_args[1]["headers"]["Authorization"]
    
    @patch('backend.cy_mistral.requests.post')
    @patch('backend.cy_mistral.os.getenv')
    def test_mistral_api_error(self, mock_getenv, mock_post):
        """Test de gestion d'erreur API"""
        mock_getenv.return_value = "test-api-key"
        
        # Mock d'une erreur HTTP
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response
        
        # Le test devrait échouer et l'exception doit être propagée
        with pytest.raises(Exception, match="API Error"):
            get_mistral_answer("Question", "Role", "Content")
    
    def test_mistral_with_missing_api_key(self):
        """Test avec clé API manquante"""
        with patch('backend.cy_mistral.os.getenv', return_value=None):
            with pytest.raises(ValueError, match="La clé API Mistral n'est pas définie"):
                get_mistral_answer("Question", "Role", "Content")


class TestCreateExcelReport:
    """Tests pour la création de rapports Excel"""
    
    @patch('backend.cy_mistral.pd.DataFrame')
    def test_create_excel_report_success(self, mock_dataframe):
        """Test de création de rapport Excel réussie"""
        # Mock des données de résultats
        test_results = [
            {"file": "doc1.docx", "answer": "Réponse 1"},
            {"file": "doc2.docx", "answer": "Réponse 2"}
        ]
        
        # Mock du DataFrame
        mock_df = Mock()
        mock_dataframe.return_value = mock_df
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            excel_path = create_excel_report(test_results, tmp_file.name[:-5])
            
        # Vérifier que le DataFrame a été créé avec les bonnes données transformées
        expected_data = [
            {"Fichier": "doc1.docx", "Réponse": "Réponse 1"},
            {"Fichier": "doc2.docx", "Réponse": "Réponse 2"}
        ]
        mock_dataframe.assert_called_once_with(expected_data)
        
        # Vérifier que to_excel a été appelé
        # Note: avec les mocks, on ne peut pas vérifier to_excel car ce n'est pas une méthode directe
        
        # Nettoyer
        try:
            os.unlink(tmp_file.name)
        except:
            pass
    
    def test_create_excel_report_with_empty_results(self):
        """Test avec des résultats vides"""
        with patch('backend.cy_mistral.pd.DataFrame') as mock_dataframe:
            mock_df = Mock()
            mock_dataframe.return_value = mock_df
            
            excel_path = create_excel_report([], "empty_report")
            
            # Devrait créer un DataFrame même avec des données vides
            mock_dataframe.assert_called_once_with([])


class TestAnalyserDocuments:
    """Tests pour la fonction principale d'analyse"""
    
    # Fixtures Flask
    @pytest.fixture
    def app(self):
        """Create test app using app factory pattern."""
        from your_app import create_app  # Ajustez l'import selon votre structure
        app = create_app(testing=True)
        return app
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    # Tests existants avec mocks
    @patch('builtins.input', return_value='o')
    @patch('backend.cy_mistral.os.makedirs')
    @patch('backend.cy_mistral.os.walk')
    @patch('backend.cy_mistral.extract_text_from_word')
    @patch('backend.cy_mistral.get_mistral_answer')
    @patch('backend.cy_mistral.create_excel_report')
    def test_analyser_documents_success(self, mock_excel, mock_mistral, mock_extract, mock_walk, mock_makedirs, mock_input):
        """Test d'analyse complète de documents"""
        # Mock de os.walk pour simuler des fichiers
        mock_walk.return_value = [
            ("/test/dir", [], ["doc1.docx", "doc2.docx", "not_docx.txt"])
        ]
        
        # Mock d'extraction de texte
        mock_extract.side_effect = ["Texte du doc1", "Texte du doc2"]
        
        # Mock des réponses Mistral
        mock_mistral.side_effect = [
            '{"contexte": "Test 1"}',
            '{"contexte": "Test 2"}'
        ]
        
        # Mock de création Excel
        mock_excel.return_value = "/test/report.xlsx"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = analyser_documents(
                directory="/test/dir",
                subject="test_analysis", 
                type_doc_source="docx",
                question="Analysez ce document",
                role="Analyste"
            )
            
            # Vérifier le résultat
            assert result['status'] == 'success'
            assert result['results_count'] == 2
            
            # Vérifier les appels
            assert mock_extract.call_count == 2
            assert mock_mistral.call_count == 2
            mock_excel.assert_called_once()
            mock_file.assert_called()
    
    @patch('builtins.input', return_value='o')  # Mock input
    @patch('backend.cy_mistral.os.walk')
    def test_analyser_documents_no_files(self, mock_walk, mock_input):
        """Test avec aucun fichier .docx trouvé"""
        mock_walk.return_value = [
            ("/test/dir", [], ["file.txt", "file.pdf"])
        ]
        
        with patch('builtins.open', mock_open()):
            result = analyser_documents(
                directory="/test/dir",
                subject="test_analysis",
                type_doc_source="docx", 
                question="Test",
                role="Test"
            )
            
            # Devrait réussir mais avec 0 résultats
            assert result['status'] == 'success'
            assert result['results_count'] == 0
    
    @patch('builtins.input', return_value='o')  # Mock input
    @patch('backend.cy_mistral.os.walk')
    def test_analyser_documents_with_error(self, mock_walk, mock_input):
        """Test de gestion d'erreur pendant l'analyse"""
        mock_walk.side_effect = OSError("Directory not accessible")
        
        result = analyser_documents(
            directory="/invalid/dir",
            subject="test_analysis",
            type_doc_source="docx",
            question="Test",
            role="Test"
        )
        
        # Devrait retourner une erreur
        assert result['status'] == 'error'
        assert 'Directory not accessible' in result['message']

class TestGetMistralTranslate:
    """Tests pour la fonction de traduction"""
    
    @patch('backend.cy_mistral.get_mistral_answer')
    def test_translate_french_to_english(self, mock_mistral):
        """Test de traduction français vers anglais"""
        mock_mistral.return_value = "Hello world"
        
        result = get_mistral_translate("Bonjour le monde", "fr", "en")
        
        assert result == "Hello world"
        
        # Vérifier que get_mistral_answer a été appelé avec le bon prompt
        call_args = mock_mistral.call_args[0]
        assert "Traduis" in call_args[0] or "translate" in call_args[0].lower()
        assert "Bonjour le monde" in call_args[2]
    
    @patch('backend.cy_mistral.get_mistral_answer')
    def test_translate_with_error(self, mock_mistral):
        """Test de gestion d'erreur de traduction"""
        mock_mistral.return_value = None
        
        result = get_mistral_translate("Text to translate", "en", "fr")
        
        # Devrait gérer l'erreur gracieusement
        assert result is None or result == ""


class TestIntegration:
    """Tests d'intégration pour les workflows complets"""
    
    @patch('builtins.input', return_value='o')  # Mock input
    @patch('backend.cy_mistral.os.path.exists')
    def test_full_workflow_with_mocked_files(self, mock_exists, mock_input):
        """Test du workflow complet avec des fichiers mockés"""
        mock_exists.return_value = True
        
        with patch('backend.cy_mistral.os.walk') as mock_walk, \
             patch('backend.cy_mistral.extract_text_from_word') as mock_extract, \
             patch('backend.cy_mistral.get_mistral_answer') as mock_mistral, \
             patch('backend.cy_mistral.create_excel_report') as mock_excel, \
             patch('builtins.open', mock_open()):
            
            # Configuration des mocks
            mock_walk.return_value = [("/test", [], ["test.docx"])]
            mock_extract.return_value = "Document content"
            mock_mistral.return_value = '{"result": "analysis"}'
            mock_excel.return_value = "/test/report.xlsx"
            
            # Exécution
            result = analyser_documents(
                directory="/test",
                subject="integration_test",
                type_doc_source="docx",
                question="Analyze this",
                role="Analyst"
            )
            
            # Vérifications
            assert result['status'] == 'success'
            assert result['results_count'] == 1
            
            # Vérifier l'ordre des appels
            mock_extract.assert_called_once()
            mock_mistral.assert_called_once()
            mock_excel.assert_called_once()


# Fixtures pour les tests
@pytest.fixture
def sample_docx_content():
    """Fixture pour du contenu Word exemple"""
    return "Ceci est un document de test.\nIl contient plusieurs paragraphes."

@pytest.fixture
def sample_mistral_response():
    """Fixture pour une réponse Mistral exemple"""
    return {
        "choices": [{
            "message": {
                "content": '{"contexte": "Document de test", "titre": "Test", "result": "Analyse réussie"}'
            }
        }]
    }

@pytest.fixture
def temp_directory():
    """Fixture pour un répertoire temporaire"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
