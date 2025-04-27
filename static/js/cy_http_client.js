/**
 * Module client HTTP pour centraliser les requêtes réseau
 * Permet d'éviter les duplications de code dans les appels fetch
 */

/**
 * Effectue une requête HTTP générique
 * @param {string} url - URL de la requête
 * @param {string} method - Méthode HTTP (GET, POST, etc.)
 * @param {Object|null} body - Corps de la requête pour POST, PUT, etc.
 * @returns {Promise} - Promise contenant le résultat de la requête
 */
async function httpRequest(url, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        // Vérifier si la réponse est du JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    } catch (error) {
        console.error(`Erreur dans la requête HTTP (${url}):`, error);
        throw error;
    }
}

/**
 * Effectue une requête GET
 * @param {string} url - URL de la requête
 * @returns {Promise} - Promise contenant le résultat de la requête
 */
async function httpGet(url) {
    return httpRequest(url);
}

/**
 * Effectue une requête POST
 * @param {string} url - URL de la requête
 * @param {Object} data - Données à envoyer
 * @returns {Promise} - Promise contenant le résultat de la requête
 */
async function httpPost(url, data) {
    return httpRequest(url, 'POST', data);
}

/**
 * API client abstrait pour les endpoints spécifiques
 */
const ApiClient = {
    // Gestion des annonces
    annonces: {
        read: (data) => httpPost('/read_annonces_json', data),
        save: (data) => httpPost('/save_annonces_json', data),
        saveAnnouncement: (data) => httpPost('/save_announcement', data)
    },
    
    // Gestion des fichiers
    files: {
        openDirectory: (filePath) => httpPost('/open_parent_directory', { file_path: filePath }),
        openUrl: (url) => httpPost('/open_url', { url }),
        readNotes: (filePath) => httpPost('/read_notes', { file_path: filePath }),
        saveNotes: (filePath, content) => httpPost('/save_notes', { file_path: filePath, content })
    },
    
    // Gestion des cookies
    cookies: {
        get: (cookieName) => httpPost('/get_cookie', { cookie_name: cookieName }),
        save: (cookieName, value) => httpPost('/save_cookie', { cookie_name: cookieName, cookie_value: value }),
        loadAll: () => httpGet('/load_cookies')
    },
    
    // Gestion de la configuration
    config: {
        loadConstants: () => httpGet('/get_constants'),
        loadColumns: () => httpGet('/charger_cols_file'),
        saveColumns: (columns, tabActive) => httpPost('/save_config_col', { columns, tabActive }),
        loadTabs: () => httpGet('/load_conf_tabs'),
        loadFilters: (tabActive) => httpPost('/read_filters_json', { tabActive }),
        saveFilters: (filters, tabActive) => httpPost('/save_filters_json', { filters, tabActive })
    },
    
    // Traitement des jobs
    jobs: {
        getAnswer: (path, RQ) => httpPost('/get_job_answer', { path, RQ }),
        getAnswerFromUrl: (url, RQ) => httpPost('/get_job_answer_from_url', { url, RQ }),
        saveAnswer: (textData, number, thePath, RQ) => httpPost('/save-answer', { text_data: textData, number, the_path: thePath, RQ })
    }
};

// Exposer les fonctions globalement
window.httpGet = httpGet;
window.httpPost = httpPost;
window.ApiClient = ApiClient;