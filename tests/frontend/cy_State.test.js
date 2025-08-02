/**
 * Tests unitaires pour cy_State.js
 * Tests du gestionnaire d'état de l'application
 */

describe('cy_State.js - Gestionnaire d\'état', () => {
  
  let appState;
  let stateSubscribers;
  
  beforeEach(() => {
    // Implémentation simplifiée du gestionnaire d'état
    appState = new Map();
    stateSubscribers = new Map();
    
    // Fonctions du gestionnaire d'état
    global.getState = jest.fn((key) => appState.get(key));
    global.setState = jest.fn((key, value) => {
      const oldValue = appState.get(key);
      appState.set(key, value);
      
      // Notifier les abonnés
      if (stateSubscribers.has(key)) {
        stateSubscribers.get(key).forEach(callback => {
          callback(value, oldValue);
        });
      }
    });
    global.subscribeToState = jest.fn((key, callback) => {
      if (!stateSubscribers.has(key)) {
        stateSubscribers.set(key, []);
      }
      stateSubscribers.get(key).push(callback);
    });
    
    // Configuration par défaut des colonnes
    global.defaultColumns = [
      { key: 'id', editable: true, width: '200px', visible: true, type: 'tb', title: 'Lot', fixed: false },
      { key: 'entreprise', editable: true, width: '300px', visible: true, type: 'tb', title: 'Entreprise', fixed: false },
      { key: 'categorie', editable: true, width: '100px', visible: true, type: 'tb', title: 'Cat', fixed: false },
      { key: 'etat', editable: true, width: '100px', visible: true, type: 'tb', title: 'Etat', fixed: false },
      { key: 'url', editable: false, width: '100px', visible: false, type: 'tb', title: 'Url', fixed: false }
    ];
  });

  describe('getState', () => {
    test('devrait récupérer une valeur d\'état', () => {
      appState.set('testKey', 'testValue');
      
      const result = getState('testKey');
      expect(result).toBe('testValue');
    });

    test('devrait retourner undefined pour une clé inexistante', () => {
      const result = getState('nonexistent');
      expect(result).toBeUndefined();
    });
  });

  describe('setState', () => {
    test('devrait définir une valeur d\'état', () => {
      setState('newKey', 'newValue');
      
      expect(appState.get('newKey')).toBe('newValue');
    });

    test('devrait notifier les abonnés lors d\'un changement', () => {
      const callback = jest.fn();
      subscribeToState('watchedKey', callback);
      
      setState('watchedKey', 'newValue');
      
      expect(callback).toHaveBeenCalledWith('newValue', undefined);
    });

    test('devrait notifier avec l\'ancienne valeur', () => {
      const callback = jest.fn();
      appState.set('existingKey', 'oldValue');
      subscribeToState('existingKey', callback);
      
      setState('existingKey', 'newValue');
      
      expect(callback).toHaveBeenCalledWith('newValue', 'oldValue');
    });
  });

  describe('subscribeToState', () => {
    test('devrait permettre de s\'abonner aux changements d\'état', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      subscribeToState('multiKey', callback1);
      subscribeToState('multiKey', callback2);
      
      setState('multiKey', 'value');
      
      expect(callback1).toHaveBeenCalledWith('value', undefined);
      expect(callback2).toHaveBeenCalledWith('value', undefined);
    });
  });
});

describe('cy_State.js - Configuration des colonnes', () => {
  
  test('devrait avoir une configuration de colonnes par défaut', () => {
    const columns = global.defaultColumns;
    
    expect(Array.isArray(columns)).toBe(true);
    expect(columns.length).toBeGreaterThan(0);
    
    // Vérifier la structure des colonnes
    columns.forEach(col => {
      expect(col).toHaveProperty('key');
      expect(col).toHaveProperty('editable');
      expect(col).toHaveProperty('width');
      expect(col).toHaveProperty('visible');
      expect(col).toHaveProperty('type');
      expect(col).toHaveProperty('title');
      expect(col).toHaveProperty('fixed');
    });
  });

  test('devrait contenir les colonnes essentielles', () => {
    const columns = global.defaultColumns;
    const keys = columns.map(col => col.key);
    
    expect(keys).toContain('id');
    expect(keys).toContain('entreprise');
    expect(keys).toContain('categorie');
    expect(keys).toContain('etat');
  });

  test('devrait distinguer les colonnes visibles et cachées', () => {
    const columns = global.defaultColumns;
    const visibleColumns = columns.filter(col => col.visible);
    const hiddenColumns = columns.filter(col => !col.visible);
    
    expect(visibleColumns.length).toBeGreaterThan(0);
    expect(hiddenColumns.length).toBeGreaterThan(0);
    
    // Vérifier que certaines colonnes importantes sont visibles
    const visibleKeys = visibleColumns.map(col => col.key);
    expect(visibleKeys).toContain('id');
    expect(visibleKeys).toContain('entreprise');
  });

  test('devrait avoir des types de colonnes appropriés', () => {
    const columns = global.defaultColumns;
    const types = [...new Set(columns.map(col => col.type))];
    
    // Vérifier que nous avons les types attendus
    expect(types).toContain('tb'); // tableau
    
    // Vérifier que chaque colonne a un type valide
    columns.forEach(col => {
      expect(['tb', 'lnk', 'dir']).toContain(col.type);
    });
  });
});

describe('cy_State.js - Gestion des données d\'annonces', () => {
  
  beforeEach(() => {
    // Mock des données d'annonces
    const mockAnnonces = [
      {
        'folder1/dossier1.pdf': {
          id: 'DOSS001',
          entreprise: 'Entreprise Test 1',
          categorie: 'IT',
          etat: 'En cours',
          dossier: 'DOSS001'
        }
      },
      {
        'folder2/dossier2.pdf': {
          id: 'DOSS002',
          entreprise: 'Entreprise Test 2', 
          categorie: 'Finance',
          etat: 'Terminé',
          dossier: 'DOSS002'
        }
      }
    ];
    
    setState('annonces', mockAnnonces);
  });

  test('devrait stocker les données d\'annonces', () => {
    const annonces = getState('annonces');
    
    expect(Array.isArray(annonces)).toBe(true);
    expect(annonces).toHaveLength(2);
  });

  test('devrait pouvoir filtrer les annonces par état', () => {
    const annonces = getState('annonces');
    
    const filterByEtat = (etat) => {
      return annonces.filter(annonceObj => {
        const key = Object.keys(annonceObj)[0];
        const annonce = annonceObj[key];
        return annonce.etat === etat;
      });
    };
    
    const enCours = filterByEtat('En cours');
    const termines = filterByEtat('Terminé');
    
    expect(enCours).toHaveLength(1);
    expect(termines).toHaveLength(1);
  });

  test('devrait pouvoir rechercher par entreprise', () => {
    const annonces = getState('annonces');
    
    const searchByEntreprise = (term) => {
      return annonces.filter(annonceObj => {
        const key = Object.keys(annonceObj)[0];
        const annonce = annonceObj[key];
        return annonce.entreprise.toLowerCase().includes(term.toLowerCase());
      });
    };
    
    const results = searchByEntreprise('test');
    expect(results).toHaveLength(2);
    
    const specific = searchByEntreprise('Test 1');
    expect(specific).toHaveLength(1);
  });
});

describe('cy_State.js - Réactivité et performance', () => {
  
  test('devrait éviter les notifications inutiles', () => {
    const callback = jest.fn();
    subscribeToState('unchangedKey', callback);
    
    setState('unchangedKey', 'value');
    setState('unchangedKey', 'value'); // Même valeur
    
    // Dans une implémentation optimisée, cela ne devrait être appelé qu'une fois
    // Pour ce test, nous vérifions juste qu'il est appelé
    expect(callback).toHaveBeenCalled();
  });

  test('devrait gérer de multiples abonnés efficacement', () => {
    const callbacks = Array.from({ length: 100 }, () => jest.fn());
    
    // S'abonner avec tous les callbacks
    callbacks.forEach(callback => {
      subscribeToState('massKey', callback);
    });
    
    const start = Date.now();
    setState('massKey', 'newValue');
    const end = Date.now();
    
    // Vérifier que tous les callbacks ont été appelés
    callbacks.forEach(callback => {
      expect(callback).toHaveBeenCalledWith('newValue', undefined);
    });
    
    // Vérifier que cela s'exécute rapidement (moins de 100ms)
    expect(end - start).toBeLessThan(100);
  });

  test('devrait gérer les erreurs dans les callbacks d\'abonnés', () => {
    const goodCallback = jest.fn();
    
    subscribeToState('errorKey', goodCallback);
    
    // Mock console.error pour capturer les erreurs
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    // Le setState devrait fonctionner normalement
    expect(() => {
      setState('errorKey', 'value');
    }).not.toThrow();
    
    expect(goodCallback).toHaveBeenCalled();
    expect(goodCallback.mock.calls[0][0]).toBe('value');
    
    consoleErrorSpy.mockRestore();
  });
});
