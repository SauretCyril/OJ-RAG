/**
 * Fichier principal de l'application
 * Refactorisé pour utiliser le gestionnaire d'état et les modules HTTP
 */

// Initialisation de l'application
async function initializeApp() {
    try {
        // Charger les constantes
        const constants = await ApiClient.config.loadConstants();
        
        // Mettre à jour window.CONSTANTS et l'état centralisé
        window.CONSTANTS = constants;
        setState('CONSTANTS', constants);
        
        // Charger les cookies utilisateur
        await loadCookies();
        
        // Charger la configuration
        const conf = await conf_loadconf();
        setState('conf', conf);
        
        // Charger les colonnes
        await loadColumnsFromServer();
        
        // Afficher le dossier courant
        await showCurrentDossier();
        
        // Charger les données
        await loadTableData(() => {
            console.log('Données chargées avec succès');
        });
        
        // Mettre à jour les onglets
        setNewTab();
        
        // Ajouter des événements
        attachEventListeners();
        
    } catch (error) {
        console.error('Erreur lors de l\'initialisation de l\'application:', error);
    }
}

/**
 * Attache les écouteurs d'événements aux éléments
 */
function attachEventListeners() {
    const excludedElement = document.getElementById('Excluded');
    if (excludedElement) {
        excludedElement.addEventListener('change', loadTableData);
    } else {
        console.error('Element with id "Excluded" not found.');
    }
}

/**
 * Vérifie si une colonne est visible
 * @param {string} coltype - Type de colonne
 * @returns {boolean} - true si la colonne est visible, false sinon
 */
function colIsVisible(coltype) {
    return (coltype === "tb" || coltype === "lnk" || coltype === "dir");
}

/**
 * Charge les cookies du serveur
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function loadCookies() {
    try {
        const cookies = await ApiClient.cookies.loadAll();
        console.log('Cookies chargés:', cookies);
        return cookies;
    } catch (error) {
        console.error('Erreur lors du chargement des cookies:', error);
        throw error;
    }
}

/**
 * Enregistre la configuration des colonnes
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function saveConfigCol() {
    try {
        const columns = getState('columns');
        const tabActive = getState('tabActive');
        const serializedColumns = serializeColumns(columns);
        
        const response = await ApiClient.config.saveColumns(serializedColumns, tabActive);
        
        if (response.status === "success") {
            console.log('Configuration enregistrée avec succès.');
        } else {
            console.error('Erreur lors de l\'enregistrement de la configuration:', response.message);
        }
        
        return response;
    } catch (error) {
        console.error('Erreur lors de l\'enregistrement de la configuration:', error);
        throw error;
    }
}

/**
 * Affiche les résultats
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function viewResults() {
    try {
        const response = await httpPost('/view_results', { file: 'resultats.json' });
        console.log('Résultats:', response);
        return response;
    } catch (error) {
        console.error('Erreur lors de l\'affichage des résultats:', error);
        throw error;
    }
}

/**
 * Charge les valeurs des filtres
 * @param {string} tabActive - Onglet actif
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function loadFilterValues(tabActive) {
    try {
        const filters = await ApiClient.config.loadFilters(tabActive);
        
        if (filters) {
            updateFilterValues(filters);
            filterTable();
        }
        
        return filters;
    } catch (error) {
        console.error('Erreur lors du chargement des valeurs des filtres:', error);
        throw error;
    }
}

/**
 * Affiche le dossier courant
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function showCurrentDossier() {
    try {
        const currentDossier = await getCookie('current_dossier');
        
        if (currentDossier) {
            document.getElementById('current-dir').textContent = currentDossier;
        } else {
            document.getElementById('current-dir').textContent = 'No current';
        }
    } catch (error) {
        console.error('Erreur lors de la récupération du dossier courant:', error);
        throw error;
    }
}

/**
 * Charge les colonnes depuis le serveur
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function loadColumnsFromServer() {
    try {
        const response = await ApiClient.config.loadColumns();
        
        if (response && response.columns) {
            // Désérialiser les colonnes
            const deserializedColumns = deserializeColumns(response.columns);
            setState('columns', deserializedColumns);
            
            // Mettre à jour l'onglet actif si présent
            if (response.tabActive) {
                setState('tabActive', response.tabActive);
            }
        }
        
        return response;
    } catch (error) {
        console.error('Erreur lors du chargement des colonnes:', error);
        throw error;
    }
}

/**
 * Charge la configuration
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function conf_loadconf() {
    try {
        // Pour l'instant, nous retournons un objet vide
        // À implémenter selon les besoins
        return {};
    } catch (error) {
        console.error('Erreur lors du chargement de la configuration:', error);
        throw error;
    }
}

// Initialiser l'application au chargement de la page
window.addEventListener('load', initializeApp);

// Exposer les fonctions globalement
// Note: nous gardons les mêmes noms pour maintenir la compatibilité avec le code existant
window.colisvisible = colIsVisible;
window.save_config_col = saveConfigCol;
window.view_results = viewResults;
window.loadFilterValues = loadFilterValues;
window.show_current_dossier = showCurrentDossier;
