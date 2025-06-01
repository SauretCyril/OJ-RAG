/**
 * CY2 - State Manager Complet
 * ÉTAPE 2: Gestion d'état centralisée et réactive
 * 
 * Features:
 * - État centralisé pour toute l'application
 * - Système d'abonnements pour la réactivité
 * - Historique undo/redo
 * - Persistance locale
 * - Compatibilité avec l'ancien système
 */

class Cy2StateManager {
    constructor() {
        // État central de l'application
        this.state = {
            // Données de base
            constants: null,
            columns: [],
            annonces: [],
            
            // État de l'interface utilisateur
            ui: {
                activeTab: "Tous",
                filters: {},
                selectedRows: [],
                currentRow: null,
                sortColumn: null,
                sortDirection: 'asc',
                searchQuery: '',
                isLoading: false,
                debugMode: false
            },
            
            // Configuration
            config: {
                excludedFile: ".excluded",
                autoSave: true,
                maxHistorySize: 50
            },
            
            // Métadonnées
            meta: {
                lastUpdated: null,
                totalRows: 0,
                filteredRows: 0,
                loadTime: 0
            }
        };
        
        // Système d'abonnements pour la réactivité
        this.subscribers = new Map();
        
        // Historique pour undo/redo
        this.history = [];
        this.historyIndex = -1;
        
        // Cache pour les performances
        this.cache = new Map();
        
        // Indicateurs d'état
        this.initialized = false;
        this.isUpdating = false;
        
        cy2Logger.log('🏗️ StateManager - Constructeur initialisé');
    }
    
    // ==========================================
    // MÉTHODES PRINCIPALES D'ÉTAT
    // ==========================================
    
    /**
     * Obtenir une valeur de l'état
     */
    getState(key) {
        if (key === undefined) {
            return { ...this.state }; // Copie complète de l'état
        }
        
        // Support pour les clés imbriquées (ex: "ui.activeTab")
        const keys = key.split('.');
        let value = this.state;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return undefined;
            }
        }
        
        return value;
    }
    
    /**
     * Définir une valeur dans l'état avec notifications
     */
    setState(key, value, options = {}) {
        const { 
            silent = false,      // Ne pas notifier les abonnés
            saveHistory = true,  // Sauvegarder dans l'historique
            skipValidation = false // Ignorer la validation
        } = options;
        
        // Validation de base
        if (!skipValidation && !this.validateStateChange(key, value)) {
            cy2Logger.error(`StateManager - Changement d'état invalide: ${key}`, value);
            return false;
        }
        
        // Sauvegarder l'état précédent pour l'historique
        const previousState = saveHistory ? { ...this.state } : null;
        
        // Appliquer le changement
        const keys = key.split('.');
        let target = this.state;
        
        for (let i = 0; i < keys.length - 1; i++) {
            const k = keys[i];
            if (!(k in target) || typeof target[k] !== 'object') {
                target[k] = {};
            }
            target = target[k];
        }
        
        const finalKey = keys[keys.length - 1];
        const oldValue = target[finalKey];
        target[finalKey] = value;
        
        // Mettre à jour les métadonnées
        this.updateMetadata(key, value);
        
        // Sauvegarder dans l'historique
        if (saveHistory && !this.isUpdating) {
            this.addToHistory(previousState, `setState: ${key}`);
        }
        
        // Nettoyer le cache si nécessaire
        this.invalidateCache(key);
        
        // Notifier les abonnés
        if (!silent) {
            this.notifySubscribers(key, value, oldValue);
        }
        
        cy2Logger.log(`📊 StateManager - État mis à jour: ${key}`, { oldValue, newValue: value });
        
        return true;
    }
    
    /**
     * Mettre à jour plusieurs valeurs en une fois
     */
    updateState(updates, options = {}) {
        this.isUpdating = true;
        
        const results = {};
        for (const [key, value] of Object.entries(updates)) {
            results[key] = this.setState(key, value, { ...options, saveHistory: false });
        }
        
        this.isUpdating = false;
        
        // Sauvegarder une seule entrée d'historique pour toutes les mises à jour
        if (options.saveHistory !== false) {
            this.addToHistory(this.state, 'updateState batch');
        }
        
        return results;
    }
    
    // ==========================================
    // SYSTÈME D'ABONNEMENTS
    // ==========================================
    
    /**
     * S'abonner aux changements d'état
     */
    subscribe(key, callback, options = {}) {
        const { 
            immediate = false,   // Appeler immédiatement avec la valeur actuelle
            once = false        // Se désabonner après le premier appel
        } = options;
        
        if (!this.subscribers.has(key)) {
            this.subscribers.set(key, []);
        }
        
        const subscription = {
            callback,
            once,
            id: Date.now() + Math.random()
        };
        
        this.subscribers.get(key).push(subscription);
        
        // Appel immédiat si demandé
        if (immediate) {
            const currentValue = this.getState(key);
            callback(currentValue, undefined, key);
        }
        
        cy2Logger.log(`📡 StateManager - Abonnement créé: ${key}`);
        
        // Retourner une fonction de désabonnement
        return () => this.unsubscribe(key, subscription.id);
    }
    
    /**
     * Se désabonner d'un changement d'état
     */
    unsubscribe(key, subscriptionId) {
        if (!this.subscribers.has(key)) return false;
        
        const subscriptions = this.subscribers.get(key);
        const index = subscriptions.findIndex(sub => sub.id === subscriptionId);
        
        if (index !== -1) {
            subscriptions.splice(index, 1);
            
            // Nettoyer si plus d'abonnés
            if (subscriptions.length === 0) {
                this.subscribers.delete(key);
            }
            
            cy2Logger.log(`📡 StateManager - Désabonnement: ${key}`);
            return true;
        }
        
        return false;
    }
    
    /**
     * Notifier tous les abonnés d'un changement
     */
    notifySubscribers(key, newValue, oldValue) {
        // Notifier les abonnés exacts
        this.notifySubscribersForKey(key, newValue, oldValue);
        
        // Notifier les abonnés de clés parentes (ex: "ui" pour "ui.activeTab")
        const keyParts = key.split('.');
        for (let i = keyParts.length - 1; i > 0; i--) {
            const parentKey = keyParts.slice(0, i).join('.');
            this.notifySubscribersForKey(parentKey, this.getState(parentKey), undefined);
        }
    }
    
    /**
     * Notifier les abonnés d'une clé spécifique
     */
    notifySubscribersForKey(key, newValue, oldValue) {
        if (!this.subscribers.has(key)) return;
        
        const subscriptions = this.subscribers.get(key);
        const toRemove = [];
        
        for (let i = 0; i < subscriptions.length; i++) {
            const subscription = subscriptions[i];
            
            try {
                subscription.callback(newValue, oldValue, key);
                
                // Marquer pour suppression si c'est un abonnement unique
                if (subscription.once) {
                    toRemove.push(i);
                }
            } catch (error) {
                cy2Logger.error(`StateManager - Erreur dans callback d'abonnement ${key}:`, error);
            }
        }
        
        // Supprimer les abonnements uniques utilisés
        for (let i = toRemove.length - 1; i >= 0; i--) {
            subscriptions.splice(toRemove[i], 1);
        }
    }
    
    // ==========================================
    // HISTORIQUE UNDO/REDO
    // ==========================================
    
    /**
     * Ajouter un état à l'historique
     */
    addToHistory(state, action) {
        // Supprimer les états suivants si on n'est pas à la fin
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        
        // Ajouter le nouvel état
        this.history.push({
            state: JSON.parse(JSON.stringify(state)), // Deep copy
            action,
            timestamp: Date.now()
        });
        
        // Limiter la taille de l'historique
        const maxSize = this.getState('config.maxHistorySize') || 50;
        if (this.history.length > maxSize) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }
        
        cy2Logger.log(`⏱️ StateManager - Historique ajouté: ${action}`);
    }
    
    /**
     * Annuler la dernière action (Undo)
     */
    undo() {
        if (this.historyIndex <= 0) {
            cy2Logger.warn('StateManager - Aucune action à annuler');
            return false;
        }
        
        this.historyIndex--;
        const previousState = this.history[this.historyIndex].state;
        
        this.isUpdating = true;
        this.state = JSON.parse(JSON.stringify(previousState));
        this.isUpdating = false;
        
        // Notifier tous les abonnés du changement global
        this.notifySubscribers('*', this.state, undefined);
        
        cy2Logger.log('↶ StateManager - Undo effectué');
        return true;
    }
    
    /**
     * Refaire l'action suivante (Redo)
     */
    redo() {
        if (this.historyIndex >= this.history.length - 1) {
            cy2Logger.warn('StateManager - Aucune action à refaire');
            return false;
        }
        
        this.historyIndex++;
        const nextState = this.history[this.historyIndex].state;
        
        this.isUpdating = true;
        this.state = JSON.parse(JSON.stringify(nextState));
        this.isUpdating = false;
        
        // Notifier tous les abonnés du changement global
        this.notifySubscribers('*', this.state, undefined);
        
        cy2Logger.log('↷ StateManager - Redo effectué');
        return true;
    }
    
    // ==========================================
    // MÉTHODES UTILITAIRES
    // ==========================================
    
    /**
     * Valider un changement d'état
     */
    validateStateChange(key, value) {
        // Validation de base par type de clé
        const validations = {
            'annonces': (val) => Array.isArray(val),
            'columns': (val) => Array.isArray(val),
            'ui.activeTab': (val) => typeof val === 'string',
            'ui.selectedRows': (val) => Array.isArray(val),
            'meta.totalRows': (val) => typeof val === 'number' && val >= 0
        };
        
        if (validations[key]) {
            return validations[key](value);
        }
        
        return true; // Validation par défaut
    }
    
    /**
     * Mettre à jour les métadonnées
     */
    updateMetadata(key, value) {
        this.state.meta.lastUpdated = Date.now();
        
        // Mises à jour spécifiques
        if (key === 'annonces') {
            this.state.meta.totalRows = Array.isArray(value) ? value.length : 0;
        }
    }
    
    /**
     * Invalider le cache pour une clé
     */
    invalidateCache(key) {
        const keysToRemove = [];
        for (const cacheKey of this.cache.keys()) {
            if (cacheKey.startsWith(key)) {
                keysToRemove.push(cacheKey);
            }
        }
        
        keysToRemove.forEach(k => this.cache.delete(k));
    }
    
    /**
     * Obtenir des statistiques du StateManager
     */
    getStats() {
        return {
            stateSize: JSON.stringify(this.state).length,
            subscribersCount: Array.from(this.subscribers.values()).reduce((total, subs) => total + subs.length, 0),
            historySize: this.history.length,
            historyIndex: this.historyIndex,
            cacheSize: this.cache.size,
            lastUpdated: this.state.meta.lastUpdated,
            initialized: this.initialized
        };
    }
    
    /**
     * Réinitialiser le StateManager
     */
    reset() {
        this.state = {
            constants: null,
            columns: [],
            annonces: [],
            ui: {
                activeTab: "Tous",
                filters: {},
                selectedRows: [],
                currentRow: null,
                sortColumn: null,
                sortDirection: 'asc',
                searchQuery: '',
                isLoading: false,
                debugMode: false
            },
            config: {
                excludedFile: ".excluded",
                autoSave: true,
                maxHistorySize: 50
            },
            meta: {
                lastUpdated: null,
                totalRows: 0,
                filteredRows: 0,
                loadTime: 0
            }
        };
        
        this.subscribers.clear();
        this.history = [];
        this.historyIndex = -1;
        this.cache.clear();
        
        cy2Logger.log('🔄 StateManager - Réinitialisé');
    }
    
    // ==========================================
    // INTÉGRATION AVEC L'ANCIEN SYSTÈME
    // ==========================================
    
    /**
     * Synchroniser avec les variables globales existantes
     */
    syncWithGlobals() {
        try {
            // Synchroniser les constantes
            if (window.CONSTANTS) {
                this.setState('constants', window.CONSTANTS, { silent: true });
            }
            
            // Synchroniser les colonnes
            if (window.columns) {
                this.setState('columns', window.columns, { silent: true });
            }
            
            // Synchroniser les annonces
            if (window.annonces) {
                this.setState('annonces', window.annonces, { silent: true });
            }
            
            // Synchroniser l'onglet actif
            if (window.tabActive) {
                this.setState('ui.activeTab', window.tabActive, { silent: true });
            }
            
            // Synchroniser la ligne courante
            if (window.CurrentRow) {
                this.setState('ui.currentRow', window.CurrentRow, { silent: true });
            }
            
            cy2Logger.log('🔄 StateManager - Synchronisation avec globales terminée');
            
        } catch (error) {
            cy2Logger.error('StateManager - Erreur synchronisation globales:', error);
        }
    }
    
    /**
     * Pousser les changements vers les variables globales
     */
    pushToGlobals() {
        try {
            // Mettre à jour les variables globales avec l'état current
            window.CONSTANTS = this.getState('constants');
            window.columns = this.getState('columns');
            window.annonces = this.getState('annonces');
            window.tabActive = this.getState('ui.activeTab');
            window.CurrentRow = this.getState('ui.currentRow');
            
            cy2Logger.log('🔄 StateManager - Push vers globales terminé');
            
        } catch (error) {
            cy2Logger.error('StateManager - Erreur push globales:', error);
        }
    }
}

// ==========================================
// INITIALISATION ET EXPORT
// ==========================================

// Créer l'instance globale du StateManager
if (window.cy2Logger) {
    cy2Logger.log('🏗️ CY2 State Manager - Initialisation...');
} else {
    console.log('🏗️ CY2 State Manager - Initialisation...');
}

window.cy2StateManager = new Cy2StateManager();

// Exposer quelques méthodes globalement pour compatibilité
window.cy2State = {
    get: (key) => window.cy2StateManager.getState(key),
    set: (key, value) => window.cy2StateManager.setState(key, value),
    subscribe: (key, callback) => window.cy2StateManager.subscribe(key, callback),
    undo: () => window.cy2StateManager.undo(),
    redo: () => window.cy2StateManager.redo(),
    stats: () => window.cy2StateManager.getStats()
};

if (window.cy2Logger) {
    cy2Logger.success('✅ CY2 State Manager - Chargé et prêt !');
} else {
    console.log('✅ CY2 State Manager - Chargé et prêt !');
}