/**
 * Tests unitaires pour les utilitaires et fonctions communes
 * Tests des fonctions réutilisables dans l'application
 */

describe('Utilitaires - Fonctions de validation', () => {
  
  describe('validateEmail', () => {
    const validateEmail = (email) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    };

    test('devrait valider les emails corrects', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name@company.co.uk')).toBe(true);
      expect(validateEmail('admin+tag@domain.org')).toBe(true);
    });

    test('devrait rejeter les emails incorrects', () => {
      expect(validateEmail('invalid-email')).toBe(false);
      expect(validateEmail('test@')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
      expect(validateEmail('test@.com')).toBe(false);
      expect(validateEmail('')).toBe(false);
      expect(validateEmail(null)).toBe(false);
    });
  });

  describe('validateDossierNumber', () => {
    const validateDossierNumber = (dossier) => {
      if (!dossier || typeof dossier !== 'string') return false;
      // Format: DOSS suivi de 3-6 chiffres
      const dossierRegex = /^DOSS\d{3,6}$/;
      return dossierRegex.test(dossier);
    };

    test('devrait valider les numéros de dossier corrects', () => {
      expect(validateDossierNumber('DOSS001')).toBe(true);
      expect(validateDossierNumber('DOSS123456')).toBe(true);
      expect(validateDossierNumber('DOSS999')).toBe(true);
    });

    test('devrait rejeter les numéros incorrects', () => {
      expect(validateDossierNumber('DOS001')).toBe(false);
      expect(validateDossierNumber('DOSS12')).toBe(false);
      expect(validateDossierNumber('DOSS1234567')).toBe(false);
      expect(validateDossierNumber('doss001')).toBe(false);
      expect(validateDossierNumber('')).toBe(false);
      expect(validateDossierNumber(null)).toBe(false);
    });
  });
});

describe('Utilitaires - Manipulation de données', () => {
  
  describe('formatDate', () => {
    const formatDate = (date, format = 'DD/MM/YYYY') => {
      if (!date) return '';
      
      const d = new Date(date);
      if (isNaN(d.getTime())) return '';
      
      const day = String(d.getDate()).padStart(2, '0');
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const year = d.getFullYear();
      
      switch (format) {
        case 'DD/MM/YYYY':
          return `${day}/${month}/${year}`;
        case 'MM/DD/YYYY':
          return `${month}/${day}/${year}`;
        case 'YYYY-MM-DD':
          return `${year}-${month}-${day}`;
        default:
          return `${day}/${month}/${year}`;
      }
    };

    test('devrait formater les dates correctement', () => {
      const date = new Date('2023-12-25');
      
      expect(formatDate(date)).toBe('25/12/2023');
      expect(formatDate(date, 'DD/MM/YYYY')).toBe('25/12/2023');
      expect(formatDate(date, 'MM/DD/YYYY')).toBe('12/25/2023');
      expect(formatDate(date, 'YYYY-MM-DD')).toBe('2023-12-25');
    });

    test('devrait gérer les cas limites', () => {
      expect(formatDate(null)).toBe('');
      expect(formatDate('')).toBe('');
      expect(formatDate('invalid-date')).toBe('');
    });
  });

  describe('sanitizeHTML', () => {
    const sanitizeHTML = (html) => {
      if (!html || typeof html !== 'string') return '';
      
      // Supprimer les balises script et style
      html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
      html = html.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');
      
      // Échapper les caractères HTML dangereux
      return html
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    };

    test('devrait échapper les caractères HTML', () => {
      expect(sanitizeHTML('<div>Test</div>')).toBe('&lt;div&gt;Test&lt;/div&gt;');
      expect(sanitizeHTML('Test & Company')).toBe('Test &amp; Company');
      expect(sanitizeHTML('"quoted text"')).toBe('&quot;quoted text&quot;');
    });

    test('devrait supprimer les scripts malveillants', () => {
      const maliciousHTML = '<script>alert("XSS")</script><div>Safe content</div>';
      const result = sanitizeHTML(maliciousHTML);
      
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert');
      expect(result).toContain('&lt;div&gt;Safe content&lt;/div&gt;');
    });

    test('devrait gérer les cas limites', () => {
      expect(sanitizeHTML(null)).toBe('');
      expect(sanitizeHTML('')).toBe('');
      expect(sanitizeHTML(123)).toBe('');
    });
  });
});

describe('Utilitaires - Gestion des erreurs', () => {
  
  describe('createErrorHandler', () => {
    const createErrorHandler = (context) => {
      return (error, additionalInfo = {}) => {
        const errorInfo = {
          context,
          message: error.message || 'Unknown error',
          timestamp: new Date().toISOString(),
          ...additionalInfo
        };
        
        console.error('[Error Handler]', errorInfo);
        return errorInfo;
      };
    };

    test('devrait créer un gestionnaire d\'erreur personnalisé', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      const handler = createErrorHandler('TEST_CONTEXT');
      const error = new Error('Test error');
      
      const result = handler(error, { userId: 'test123' });
      
      expect(result.context).toBe('TEST_CONTEXT');
      expect(result.message).toBe('Test error');
      expect(result.userId).toBe('test123');
      expect(result.timestamp).toBeDefined();
      
      expect(consoleSpy).toHaveBeenCalledWith('[Error Handler]', expect.objectContaining({
        context: 'TEST_CONTEXT',
        message: 'Test error'
      }));
      
      consoleSpy.mockRestore();
    });
  });

  describe('retryWithBackoff', () => {
    const retryWithBackoff = async (fn, maxRetries = 3, baseDelay = 100) => {
      let attempt = 0;
      
      while (attempt < maxRetries) {
        try {
          return await fn();
        } catch (error) {
          attempt++;
          
          if (attempt >= maxRetries) {
            throw error;
          }
          
          // Backoff exponentiel
          const delay = baseDelay * Math.pow(2, attempt - 1);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    };

    test('devrait réussir au premier essai', async () => {
      const successFn = jest.fn().mockResolvedValue('success');
      
      const result = await retryWithBackoff(successFn);
      
      expect(result).toBe('success');
      expect(successFn).toHaveBeenCalledTimes(1);
    });

    test('devrait retenter en cas d\'échec puis réussir', async () => {
      const flakeyFn = jest.fn()
        .mockRejectedValueOnce(new Error('First fail'))
        .mockRejectedValueOnce(new Error('Second fail'))
        .mockResolvedValueOnce('success');
      
      const result = await retryWithBackoff(flakeyFn);
      
      expect(result).toBe('success');
      expect(flakeyFn).toHaveBeenCalledTimes(3);
    });

    test('devrait échouer après le nombre maximum de tentatives', async () => {
      const alwaysFailFn = jest.fn().mockRejectedValue(new Error('Always fails'));
      
      await expect(retryWithBackoff(alwaysFailFn, 2)).rejects.toThrow('Always fails');
      expect(alwaysFailFn).toHaveBeenCalledTimes(2);
    });
  });
});

describe('Utilitaires - Performance', () => {
  
  describe('throttle', () => {
    const throttle = (func, limit) => {
      let inThrottle;
      return function(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    };

    test('devrait limiter la fréquence d\'exécution', (done) => {
      const fn = jest.fn();
      const throttledFn = throttle(fn, 100);
      
      // Appeler rapidement plusieurs fois
      throttledFn('call1');
      throttledFn('call2');
      throttledFn('call3');
      
      // Seul le premier appel devrait passer
      expect(fn).toHaveBeenCalledTimes(1);
      expect(fn).toHaveBeenCalledWith('call1');
      
      // Après le délai, un nouvel appel devrait passer
      setTimeout(() => {
        throttledFn('call4');
        expect(fn).toHaveBeenCalledTimes(2);
        expect(fn).toHaveBeenLastCalledWith('call4');
        done();
      }, 150);
    });
  });

  describe('memoize', () => {
    const memoize = (fn) => {
      const cache = new Map();
      return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
          return cache.get(key);
        }
        const result = fn.apply(this, args);
        cache.set(key, result);
        return result;
      };
    };

    test('devrait mettre en cache les résultats', () => {
      const expensiveFn = jest.fn((x) => x * x);
      const memoizedFn = memoize(expensiveFn);
      
      // Premier appel
      expect(memoizedFn(5)).toBe(25);
      expect(expensiveFn).toHaveBeenCalledTimes(1);
      
      // Deuxième appel avec les mêmes arguments
      expect(memoizedFn(5)).toBe(25);
      expect(expensiveFn).toHaveBeenCalledTimes(1); // Pas d'appel supplémentaire
      
      // Appel avec des arguments différents
      expect(memoizedFn(10)).toBe(100);
      expect(expensiveFn).toHaveBeenCalledTimes(2);
    });
  });
});

describe('Utilitaires - Helpers DOM', () => {
  
  describe('createElement', () => {
    const createElement = (tag, attributes = {}, children = []) => {
      const element = document.createElement(tag);
      
      Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'className') {
          element.className = value;
        } else if (key === 'dataset') {
          Object.entries(value).forEach(([dataKey, dataValue]) => {
            element.dataset[dataKey] = dataValue;
          });
        } else {
          element.setAttribute(key, value);
        }
      });
      
      children.forEach(child => {
        if (typeof child === 'string') {
          element.appendChild(document.createTextNode(child));
        } else {
          element.appendChild(child);
        }
      });
      
      return element;
    };

    test('devrait créer un élément avec les attributs', () => {
      const mockElement = {
        setAttribute: jest.fn(),
        appendChild: jest.fn(),
        className: '',
        dataset: {}
      };
      
      document.createElement.mockReturnValue(mockElement);
      document.createTextNode.mockImplementation(text => ({ textContent: text }));
      
      const element = createElement('div', { 
        id: 'test-div', 
        className: 'test-class' 
      }, ['Hello World']);
      
      expect(document.createElement).toHaveBeenCalledWith('div');
      expect(mockElement.setAttribute).toHaveBeenCalledWith('id', 'test-div');
      expect(mockElement.className).toBe('test-class');
      expect(mockElement.appendChild).toHaveBeenCalled();
    });
  });
});
