/**
 * Module de gestion d'état centralisé pour l'application
 * Permet d'éviter l'utilisation excessive de variables globales
 */

// État de l'application
const AppState = {
    // Configuration
    conf: {},
    CONSTANTS: [],
    
    // Navigation
    currentRow: "",
    tabActive: "Campagne",
    
    // Données
    annonces: [],
    portalLinks: [],
    
    // Configuration des colonnes
    columns: [
        // On garde les colonnes existantes pour l'instant
    ]
};

/**
 * Récupère une valeur de l'état
 * @param {string} key - La clé à récupérer
 * @returns {any} - La valeur associée à la clé
 */
function getState(key) {
    return AppState[key];
}

/**
 * Définit une valeur dans l'état
 * @param {string} key - La clé à définir
 * @param {any} value - La valeur à associer à la clé
 */
function setState(key, value) {
    AppState[key] = value;
    
    // Émettre un événement pour avertir les listeners du changement
    const event = new CustomEvent('state-changed', {
        detail: { key, value }
    });
    document.dispatchEvent(event);
}

/**
 * S'abonne aux changements d'état
 * @param {string} key - La clé à surveiller
 * @param {Function} callback - Fonction à appeler lors du changement
 */
function subscribeToState(key, callback) {
    document.addEventListener('state-changed', (event) => {
        if (event.detail.key === key) {
            callback(event.detail.value);
        }
    });
}

/**
 * Initialise les valeurs par défaut pour les colonnes
 */
function initializeColumns() {
    // Copie les colonnes actuelles de window.columns dans AppState.columns
    // Cela sera appelé au chargement de la page
    if (window.columns && window.columns.length > 0) {
        AppState.columns = [...window.columns];
    }
}

// Exportation des fonctions
window.getState = getState;
window.setState = setState;
window.subscribeToState = subscribeToState;
window.AppState = AppState; // Pour la phase de transition