"""
Fixtures et utilitaires partagés pour les tests backend
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from flask import Flask


@pytest.fixture
def temp_directory():
    """Crée un répertoire temporaire pour les tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file():
    """Crée un fichier temporaire pour les tests"""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        yield temp_file.name
    # Nettoyer après le test
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_docx_files(temp_directory):
    """Crée des fichiers .docx factices pour les tests"""
    files = []
    for i in range(3):
        file_path = os.path.join(temp_directory, f"test_doc_{i}.docx")
        # Créer un fichier vide (pour les tests, on mockera le contenu)
        with open(file_path, 'w') as f:
            f.write(f"Document {i} content")
        files.append(file_path)
    return files


@pytest.fixture
def sample_json_data():
    """Données JSON d'exemple pour les tests"""
    return {
        "annonces": [
            {
                "folder1/file1.pdf": {
                    "id": "DOSS001",
                    "entreprise": "Test Company 1",
                    "categorie": "IT",
                    "etat": "En cours",
                    "dossier": "DOSS001"
                }
            },
            {
                "folder2/file2.pdf": {
                    "id": "DOSS002", 
                    "entreprise": "Test Company 2",
                    "categorie": "Finance",
                    "etat": "Terminé",
                    "dossier": "DOSS002"
                }
            }
        ]
    }


@pytest.fixture
def mock_mistral_api_response():
    """Réponse API Mistral simulée"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "contexte": "Document de test analysé",
                    "titre": "Analyse automatique",
                    "result": "L'analyse a été effectuée avec succès",
                    "savoir_faire": ["Python", "Flask", "API"],
                    "savoir_etre": ["Rigoureux", "Analytique"]
                })
            }
        }]
    }


@pytest.fixture
def mock_pdf_content():
    """Contenu PDF simulé"""
    return """
    OFFRE D'EMPLOI
    
    Entreprise: Tech Solutions SARL
    Poste: Développeur Full-Stack
    
    Description:
    Nous recherchons un développeur expérimenté pour rejoindre notre équipe.
    
    Compétences requises:
    - Python, JavaScript
    - React, Flask
    - Base de données SQL
    
    Salaire: 45K-55K €
    Lieu: Paris, France
    """


@pytest.fixture
def flask_app():
    """Application Flask pour les tests"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Routes de test si nécessaire
    @app.route('/test')
    def test_route():
        return {'status': 'ok'}
        
    return app


@pytest.fixture
def flask_client(flask_app):
    """Client de test Flask"""
    return flask_app.test_client()


class MockDocxDocument:
    """Mock pour les documents Word"""
    
    def __init__(self, paragraphs_text=None):
        self.paragraphs_text = paragraphs_text or [
            "Premier paragraphe du document",
            "Deuxième paragraphe avec plus de contenu",
            "Troisième paragraphe final"
        ]
        self.paragraphs = [Mock(text=text) for text in self.paragraphs_text]


class MockPdfReader:
    """Mock pour le lecteur PDF"""
    
    def __init__(self, pages_text=None):
        self.pages_text = pages_text or [
            "Contenu de la page 1",
            "Contenu de la page 2", 
            "Contenu de la page 3"
        ]
        self.pages = [Mock(extract_text=Mock(return_value=text)) for text in self.pages_text]


class MockApiResponse:
    """Mock pour les réponses d'API"""
    
    def __init__(self, status_code=200, json_data=None, text_data=None):
        self.status_code = status_code
        self._json_data = json_data
        self._text_data = text_data
        
    def json(self):
        return self._json_data
        
    @property 
    def text(self):
        return self._text_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code} Error")


# Décorateurs utilitaires pour les tests
def mock_environment_variables(**env_vars):
    """Décorateur pour mocker les variables d'environnement"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with patch.dict(os.environ, env_vars):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def skip_if_no_api_key(api_key_env_var='MISTRAL_API_KEY'):
    """Skip le test si la clé API n'est pas disponible"""
    return pytest.mark.skipif(
        not os.getenv(api_key_env_var),
        reason=f"Pas de clé API {api_key_env_var} disponible"
    )


# Utilitaires pour les assertions
def assert_valid_json_response(response_data):
    """Vérifie qu'une réponse est un JSON valide"""
    assert isinstance(response_data, dict)
    assert 'status' in response_data
    

def assert_error_response(response_data, expected_error_type=None):
    """Vérifie qu'une réponse contient une erreur"""
    assert_valid_json_response(response_data)
    assert response_data['status'] == 'error'
    if expected_error_type:
        assert expected_error_type.lower() in response_data.get('message', '').lower()


def assert_success_response(response_data, expected_keys=None):
    """Vérifie qu'une réponse indique un succès"""
    assert_valid_json_response(response_data)
    assert response_data['status'] == 'success'
    if expected_keys:
        for key in expected_keys:
            assert key in response_data


# Helpers pour créer des données de test
def create_test_annonce(dossier_id="DOSS001", **kwargs):
    """Crée une annonce de test"""
    default_data = {
        "id": dossier_id,
        "entreprise": "Entreprise Test",
        "categorie": "IT",
        "etat": "En cours", 
        "dossier": dossier_id,
        "url": "https://example.com/job",
        "type": "Annonce"
    }
    default_data.update(kwargs)
    return {f"folder/{dossier_id}.pdf": default_data}


def create_test_analysis_result(file_name="test.docx", **kwargs):
    """Crée un résultat d'analyse de test"""
    default_result = {
        "file": file_name,
        "answer": json.dumps({
            "contexte": "Contexte de test",
            "titre": "Titre de test", 
            "result": "Résultat de test",
            "savoir_faire": ["Compétence 1", "Compétence 2"],
            "savoir_etre": ["Qualité 1", "Qualité 2"]
        })
    }
    default_result.update(kwargs)
    return default_result


# Constantes pour les tests
TEST_CONSTANTS = {
    "VALID_DOSSIER_FORMATS": ["DOSS001", "DOSS123", "DOSS999999"],
    "INVALID_DOSSIER_FORMATS": ["DOS001", "DOSS12", "doss001", "DOSS1234567"],
    "VALID_EMAIL_FORMATS": [
        "test@example.com",
        "user.name@company.co.uk", 
        "admin+tag@domain.org"
    ],
    "INVALID_EMAIL_FORMATS": [
        "invalid-email",
        "test@",
        "@example.com",
        "test@.com"
    ],
    "SAMPLE_PDF_TEXT": "Ceci est un exemple de texte extrait d'un PDF pour les tests.",
    "SAMPLE_DOCX_TEXT": "Ceci est un exemple de texte extrait d'un document Word pour les tests."
}


# Configuration des markers pytest
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration
pytest.mark.unit = pytest.mark.unit
pytest.mark.api = pytest.mark.api
