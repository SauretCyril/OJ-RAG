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

function createCell_OpenDossier(path) {
    const Icon = document.createElement('span');
    Icon.textContent = '📂'; // Folder icon
    Icon.style.cursor = 'pointer';
    Icon.addEventListener('click', () => open_dossier(path));
    return Icon;
}


// Exposer les fonctions et objets globalement
window.showLoadingOverlay = LoadingOverlay.show.bind(LoadingOverlay);
window.hideLoadingOverlay = LoadingOverlay.hide.bind(LoadingOverlay);
window.isValidURL = isValidURL;
window.get_cookie = getCookie;  // Garder l'ancien nom pour compatibilité
window.save_cookie = saveCookie; // Garder l'ancien nom pour compatibilité
window.serializeColumns = ColumnUtils.serialize;
window.deserializeColumns = ColumnUtils.deserialize;
window.clearExplorerCache = clearExplorerCache; // Exposer la fonction d'effacement du cache
