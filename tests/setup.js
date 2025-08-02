// Configuration globale pour Jest
require('@testing-library/jest-dom');

// Mock des APIs globales
global.fetch = jest.fn();
global.ApiClient = {
  jobs: {
    getAnswer: jest.fn()
  },
  cookies: {
    loadAll: jest.fn()
  },
  data: {
    loadColumns: jest.fn(),
    saveColumns: jest.fn()
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock des fonctions globales de l'application
global.getState = jest.fn();
global.setState = jest.fn();
global.subscribeToState = jest.fn();

// Mock window.annonces
global.window = Object.assign(global.window, {
  annonces: [],
  CONSTANTS: {
    ANNONCE_SUFFIX: '_annonce_.pdf'
  },
  AppState: {
    directories: [],
    currentDossier: null
  }
});

// Réinitialiser les mocks avant chaque test
beforeEach(() => {
  jest.clearAllMocks();
  fetch.mockClear();
  localStorage.clear();
  
  // Réinitialiser window.annonces
  window.annonces = [];
});

// Mock des éléments DOM courants
const mockElement = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  querySelector: jest.fn(),
  querySelectorAll: jest.fn(() => []),
  getElementById: jest.fn(),
  classList: {
    add: jest.fn(),
    remove: jest.fn(),
    contains: jest.fn()
  },
  style: {},
  innerHTML: '',
  value: '',
  onclick: null
};

// Mock des fonctions DOM sans redéfinir document.body
global.document.getElementById = jest.fn(() => mockElement);
global.document.querySelector = jest.fn(() => mockElement);
global.document.querySelectorAll = jest.fn(() => [mockElement]);
global.document.createElement = jest.fn(() => mockElement);
global.document.createTextNode = jest.fn((text) => ({ textContent: text }));

// Mock de document.body avec des méthodes seulement
Object.defineProperty(global.document, 'body', {
  value: {
    appendChild: jest.fn(),
    removeChild: jest.fn(),
    insertAdjacentHTML: jest.fn()
  },
  writable: false
});
