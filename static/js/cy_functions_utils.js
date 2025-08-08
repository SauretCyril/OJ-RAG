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
 * Efface le cache de l'explorateur
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function clearExplorerCache() {
    showLoadingOverlay("Effacement du cache en cours...");
    
    try {
        const response = await fetch('/clear_explorer_cache', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === "success") {
            alert(data.message);
            // Rechargement de la page pour appliquer les changements
            window.location.reload();
        } else {
            alert("Erreur lors de l'effacement du cache : " + data.message);
        }
        
        return data;
    } catch (error) {
        console.error('Erreur lors de l\'effacement du cache :', error);
        alert("Erreur lors de l'effacement du cache");
        throw error;
    } finally {
        hideLoadingOverlay();
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
 * Enregistre la valeur d'un cookie
 * @param {string} cookieName - Nom du cookie à enregistrer
 * @param {string} cookieValue - Valeur du cookie à enregistrer
 * @returns {Promise<Object>} - Résultat de l'opération
 */
async function setCookie(cookieName, cookieValue) {
    try {
        const response = await ApiClient.cookies.save(cookieName, cookieValue);
        if (response.message === 'done') {
            console.log(`Cookie '${cookieName}' enregistré avec la valeur : ${cookieValue}`);
        } else {
            console.error('Erreur lors de l\'enregistrement du cookie:', response.error);
        }
        return response;
    } catch (error) {
        console.error(`Erreur lors de l'enregistrement du cookie '${cookieName}':`, error);
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

/**
 * Creates a URL icon that changes appearance based on whether a URL is available
 * and adds click functionality to open the URL when clicked.
 * 
 * @param {string} colKey - The key identifying the column
 * @param {object} item - The data item containing values
 * @returns {HTMLElement} - The created icon element
 */
//colKey = colKey + "_value"
//value=item[colvalue]

function createCell_lnk(colKey,item){
    const icon = document.createElement('span');
    const colvalue = colKey + "_value";
    
    icon.style.position = 'absolute';
    icon.style.alignContent = 'center';
    icon.style.zIndex = '10';
   
    if (item[colvalue] && item[colvalue].trim() !== '') {
        //console.log('#### blanc:');
        icon.textContent = '🔵';
        icon.style.cursor = 'pointer';
        icon.addEventListener('click', () => open_url(item[colvalue]));
    } else {
        //console.log('#### vert:');
        icon.textContent = '⚪'; // White circle icon
    }
    
    return icon;
}

function createCell_PdfView(colkey, item, fichier)
{
    const icon = document.createElement('span');
    icon.style.position = 'absolute';
    icon.style.alignContent='center';
    if (item[colkey] === 'O') {
        //console.log('#### blanc:');
        icon.textContent = '📗'; // Green book icon
                          
        icon.style.cursor = 'pointer';
        icon.addEventListener('click', () => open_url(fichier));
        } else  
        { 
            icon.textContent = '⚪'; // Green book icon
        }                      
    return icon;
}

function createCell_getFile(colkey, item,dir_path)
{
    const icon = document.createElement('span');
    icon.style.position = 'absolute';
    icon.style.alignContent='center';
    icon.style.zIndex = '10'; // Ensure the icon is above the content
    icon.style.cursor = 'pointer';
    if (item[colkey] === 'N' || item[colkey] === '') {
        //console.log('#### blanc:');
        
        icon.textContent = '📤'; // Pick up icon
        //icon.style.color = 'red';
    } else  {
        //console.log('#### vert:');
        icon.textContent = '⬇️'; // Download icon
        //icon.style.color = 'green';
    } 
   
    //icon.style.top = '0px';

    let typeDoc = "";
    if (colkey === 'CV') {typeDoc="CV";}
    if (colkey === 'BA') {typeDoc="BA";}
    icon.addEventListener('click', () => get_cv(item.dossier, dir_path,item[colkey],typeDoc));              
    return icon;
}

function createCell_Notes(file_notes) {
    const Icon = document.createElement('span');
    Icon.textContent = '❤️'; // Heart icon
    Icon.style.cursor = 'pointer';
    Icon.addEventListener('click', () => open_notes(file_notes));
    return Icon;
}



// Enhanced API Client for consistent error handling
class APIClient {
    static async request(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            showLoadingOverlay(options.loadingMessage || 'Processing...');
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'error') {
                throw new Error(data.message || 'API Error');
            }
            
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        } finally {
            hideLoadingOverlay();
        }
    }
    
    static async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }
    
    static async post(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    static async put(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    static async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
}

// Enhanced error handling
class ErrorHandler {
    static show(message, type = 'error') {
        // Create or update error notification
        const existingError = document.getElementById('error-notification');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error-notification';
        errorDiv.className = `notification notification-${type}`;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background-color: ${type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#28a745'};
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    static clear() {
        const errorElement = document.getElementById('error-notification');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

// Exposer les fonctions et objets globalement
window.APIClient = APIClient;
window.ErrorHandler = ErrorHandler;
window.showLoadingOverlay = LoadingOverlay.show.bind(LoadingOverlay);
window.hideLoadingOverlay = LoadingOverlay.hide.bind(LoadingOverlay);
window.isValidURL = isValidURL;

window.setCookie = setCookie;


window.serializeColumns = ColumnUtils.serialize;
window.deserializeColumns = ColumnUtils.deserialize;
window.clearExplorerCache = clearExplorerCache; // Exposer la fonction d'effacement du cache
