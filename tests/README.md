# Tests unitaires

## 📋 Vue d'ensemble

Ce framework de tests unitaires couvre l'ensemble de l'application OJ-RAG avec des tests séparés pour le frontend (JavaScript) et le backend (Python).

## 🚀 Installation rapide

```bash
# Installation des dépendances JavaScript
npm install

# Installation des dépendances Python pour les tests
pip install -r requirements.txt
```

## 🧪 Exécution des tests

### Tests rapides
```bash
# Tous les tests
npm run test:all

# Tests JavaScript uniquement
npm test

# Tests Python uniquement  
npm run test:backend
```

### Tests avec couverture
```bash
# JavaScript avec couverture
npm run test:coverage

# Python avec couverture
npm run test:backend:coverage

# Utiliser les scripts Windows
scripts\run_tests_coverage.bat
```

### Mode développement
```bash
# Tests JavaScript en mode watch
npm run test:watch

# Tests Python avec détail
python -m pytest tests/backend/ -v -s
```

## 📁 Structure des tests

```
tests/
├── frontend/                 # Tests JavaScript
│   ├── cy_Panel.test.js      # Tests du panneau principal
│   ├── cy_main.test.js       # Tests de l'app principale
│   ├── cy_State.test.js      # Tests du gestionnaire d'état
│   └── utils/
│       └── helpers.test.js   # Tests des utilitaires
├── backend/                  # Tests Python
│   ├── test_cy_mistral.py    # Tests API Mistral
│   ├── test_cy_requests.py   # Tests des requêtes
│   └── fixtures/
│       └── test_fixtures.py  # Fixtures partagées
├── setup.js                  # Configuration Jest
├── coverage/                 # Rapports de couverture
└── README.md                # Ce fichier
```

## 🎯 Couverture de tests

### Frontend JavaScript
- **cy_Panel.js**: Fonctions debounce, cache, gestion UI
- **cy_main.js**: Initialisation, chargement des données
- **cy_State.js**: Gestionnaire d'état réactif
- **Utilitaires**: Validation, manipulation DOM, performance

### Backend Python  
- **cy_mistral.py**: Extraction texte, API Mistral, analyse documents
- **cy_requests.py**: Routes Flask, extraction PDF, réponses IA
- **Fixtures**: Données de test, mocks, utilitaires

## 📊 Rapports de couverture

Après exécution avec couverture:
- **Frontend**: `tests/coverage/lcov-report/index.html`
- **Backend**: `tests/coverage/backend/index.html`

## 🔧 Configuration

### Jest (Frontend)
```javascript
// jest.config.js
{
  testEnvironment: 'jsdom',
  coverageDirectory: 'tests/coverage',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js']
}
```

### Pytest (Backend)
```ini
# pytest.ini
[tool:pytest]
testpaths = tests/backend
addopts = --cov=backend --cov-report=html
```

## 🚨 Résolution de problèmes

### Problèmes courants

1. **"Cannot find module"** (JavaScript)
   ```bash
   npm install
   ```

2. **"Module not found"** (Python)
   ```bash
   pip install -r requirements.txt
   ```

3. **Tests qui échouent**
   - Vérifier que l'environnement virtuel est activé
   - S'assurer que toutes les dépendances sont installées
   - Vérifier les chemins dans `jest.config.js` et `pytest.ini`

### Variables d'environnement pour les tests
```bash
# Pour les tests nécessitant des clés API
export MISTRAL_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
```

## 📝 Écriture de nouveaux tests

### Frontend (JavaScript)
```javascript
describe('MonModule', () => {
  test('devrait faire quelque chose', () => {
    // Arrange
    const input = 'test';
    
    // Act
    const result = myFunction(input);
    
    // Assert
    expect(result).toBe('expected');
  });
});
```

### Backend (Python)
```python
def test_my_function():
    """Test de ma fonction"""
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == "expected"
```

## 🎭 Mocking et fixtures

### Mocks JavaScript
```javascript
// Mock d'une API
global.fetch = jest.fn().mockResolvedValue({
  json: () => Promise.resolve({ data: 'test' })
});
```

### Fixtures Python
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

## 📈 Métriques de qualité

Objectifs de couverture:
- **Frontend**: > 80%
- **Backend**: > 85% 
- **Fonctions critiques**: 100%

## 🤝 Contribution

1. Écrire des tests pour chaque nouvelle fonctionnalité
2. Maintenir la couverture de code au-dessus des seuils
3. Utiliser des noms de tests descriptifs
4. Grouper les tests logiquement avec `describe/context`
5. Nettoyer les mocks dans `beforeEach/afterEach`

## 📚 Ressources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)
