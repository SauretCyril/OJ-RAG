/**
 * Module contenant les fonctions utilitaires pour l'application
 */

// Overlay de chargement
const LoadingOverlay = {
    /**
     * Affiche l'overlay de chargement
     * @param {string} message - Message à afficher (optionnel)
     */
    show(message = 'Processing...') {
        // Supprimer l'overlay existant s'il y en a un
        this.hide();
        
        // Créer le nouvel overlay
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        overlay.style.zIndex = '1000';
        overlay.style.display = 'flex';
        overlay.style.justifyContent = 'center';
        overlay.style.alignItems = 'center';
        overlay.style.color = 'white';
        overlay.style.fontSize = '24px';
        overlay.textContent = message;
        
        document.body.appendChild(overlay);
    },
    
    /**
     * Cache l'overlay de chargement
     */
    hide() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
};

/**
 * Vérifie si une URL est valide
 * @param {string} url - L'URL à vérifier
 * @returns {boolean} - true si l'URL est valide, false sinon
 */
function isValidURL(url) {
    if (!url) return false;
    
    const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.?)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return pattern.test(url);
}

/**
 * Récupère un cookie côté client
 * @param {string} cookieName - Nom du cookie à récupérer
 * @returns {Promise<string>} - Valeur du cookie
 */
async function getCookie(cookieName) {
    try {
        const data = await ApiClient.cookies.get(cookieName);
        return data[cookieName];
    } catch (error) {
        console.error('Erreur lors de la récupération du cookie:', error);
        throw error;
    }
}

/**
 * Enregistre un cookie côté serveur
 * @param {string} cookieName - Nom du cookie
 * @param {string} value - Valeur du cookie
 * @returns {Promise} - Résultat de l'opération
 */
async function saveCookie(cookieName, value) {
    try {
        const response = await ApiClient.cookies.save(cookieName, value);
        if (response.message === 'done') {
            console.log(`${cookieName} enregistré avec la valeur : ${value}`);
        } else {
            console.error('Erreur lors de l\'enregistrement du cookie:', response.error);
        }
        return response;
    } catch (error) {
        console.error('Erreur lors de l\'enregistrement du cookie:', error);
        throw error;
    }
}

/**
 * Fonctions pour sérialiser et désérialiser les colonnes
 */
const ColumnUtils = {
    /**
     * Sérialise les colonnes pour l'envoi au serveur
     * @param {Array} columns - Tableau de colonnes
     * @returns {Array} - Tableau de colonnes sérialisées
     */
    serialize(columns) {
        return columns.map(col => {
            const serializedCol = {...col}; // Copie superficielle
            
            // Traitement spécial pour les fonctions
            if (typeof col.eventHandler === 'function') {
                serializedCol.eventHandler = col.eventHandler.name;
            }
            
            return serializedCol;
        });
    },
    
    /**
     * Désérialise les colonnes reçues du serveur
     * @param {Array} columns - Tableau de colonnes sérialisées
     * @returns {Array} - Tableau de colonnes désérialisées
     */
    deserialize(columns) {
        return columns.map(col => {
            const deserializedCol = {...col}; // Copie superficielle
            
            // Réassigner les handlers de fonctions
            if (col.eventHandler === 'openUrlHandler') {
                deserializedCol.eventHandler = window.openUrlHandler || null;
            } else if (col.eventHandler === 'SelectHandler') {
                deserializedCol.eventHandler = window.SelectHandler || null;
            }
            // Ajouter d'autres handlers au besoin
            
            return deserializedCol;
        });
    }
};

// Exposer les fonctions et objets globalement
window.showLoadingOverlay = LoadingOverlay.show.bind(LoadingOverlay);
window.hideLoadingOverlay = LoadingOverlay.hide.bind(LoadingOverlay);
window.isValidURL = isValidURL;
window.get_cookie = getCookie;  // Garder l'ancien nom pour compatibilité
window.save_cookie = saveCookie; // Garder l'ancien nom pour compatibilité
window.serializeColumns = ColumnUtils.serialize;
window.deserializeColumns = ColumnUtils.deserialize;
