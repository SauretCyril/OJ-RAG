/**
 * Module client HTTP — IACAS OTA
 * Centralise les requêtes vers le VPS et l'agent local.
 */

// ---------------------------------------------------------------------------
// Gestion du TOKEN agent
// ---------------------------------------------------------------------------
const Auth = {
    getToken: () => sessionStorage.getItem('agent_token') || '',
    getUser:  () => {
        try { return JSON.parse(sessionStorage.getItem('current_user') || 'null'); }
        catch { return null; }
    },
    setToken: (t) => sessionStorage.setItem('agent_token', t),
    setUser:  (u) => sessionStorage.setItem('current_user', JSON.stringify(u)),
    clear:    () => { sessionStorage.removeItem('agent_token'); sessionStorage.removeItem('current_user'); },
    isLoggedIn: () => !!sessionStorage.getItem('agent_token'),
};

window.Auth = Auth;

// ---------------------------------------------------------------------------
// Requête vers le VPS Flask (session cookie)
// ---------------------------------------------------------------------------
async function httpRequest(url, method = 'GET', body = null) {
    try {
        const options = {
            method,
            credentials: 'same-origin',   // envoie le cookie de session
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) options.body = JSON.stringify(body);

        const response = await fetch(url, options);

        // Session expirée → redirect login
        if (response.status === 401) {
            Auth.clear();
            window.location.href = '/login';
            return null;
        }

        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        return await response.text();
    } catch (error) {
        console.error(`Erreur requête VPS (${url}):`, error);
        throw error;
    }
}

// ---------------------------------------------------------------------------
// Requête vers l'agent local (localhost:5005) avec token Bearer
// ---------------------------------------------------------------------------
const AGENT_BASE = 'http://127.0.0.1:5005';

async function agentRequest(path, method = 'GET', body = null) {
    const token = Auth.getToken();
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            }
        };
        if (body) options.body = JSON.stringify(body);

        const response = await fetch(AGENT_BASE + path, options);

        if (response.status === 401) {
            console.warn('[Agent] Token invalide ou expiré.');
            return { error: 'Agent : token invalide', agent_offline: false };
        }
        if (!response.ok) throw new Error(`Agent HTTP: ${response.status}`);

        return await response.json();
    } catch (error) {
        // L'agent n'est pas démarré
        console.warn(`[Agent] Inaccessible (${path}):`, error.message);
        return { error: 'Agent local non disponible', agent_offline: true };
    }
}

window.agentRequest = agentRequest;

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
        saveNotes: (filePath, content) => httpPost('/save_notes', { file_path: filePath, content }),
        getDirectoryRoot: () => httpGet('/get_directory_root'),
        // Fonction centralisée pour upload_doc
        upload: (formData) => {
            // Cette fonction nécessite un FormData pour l'upload de fichiers
            // formData doit contenir : file_path (le fichier), num_dossier, repertoire_annonce, et prefix
            return fetch('/upload_doc', {
                method: 'POST',
                body: formData
            }).then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP: ${response.status}`);
                }
                return response.json();
            });
        }
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
        getAnswer: (path, RQ, NumDos,islibre) => httpPost('/get_AI_answer', { path, RQ, NumDos, libre: islibre }),
        getAnswerFromUrl: (url, RQ,NumDos) => httpPost('/get_AI_answer_from_url', { url, RQ,NumDos }),
        saveAnswer: (textData, number, thePath, RQ) => httpPost('/save-answer', { text_data: textData, number, the_path: thePath, RQ }),
        gettexectFromPdf: (pdfPath) => httpPost('/extract_pdf_text', { pdf_path: pdfPath })
    }
};

// Exposer les fonctions globalement
window.httpGet = httpGet;
window.httpPost = httpPost;
window.ApiClient = ApiClient;