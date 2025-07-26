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

        await fetchAndSetDirectories();

        // Afficher le dossier courant
        await showCurrentDossier();
        
        // Charger les données
        await loadTableData(() => {
            console.log('Données chargées avec succès');
        });
        
        // Mettre à jour les onglets
        setNewTab();
        // Appel initial au chargement
        updateActionBarVisibility();
        // Ajouter des événements
        //attachEventListeners();
        
    } catch (error) {
        console.error('Erreur lors de l\'initialisation de l\'application:', error);
    }
}

/**
 * Attache les écouteurs d'événements aux éléments
 */
/* function attachEventListeners() {
    const excludedElement = document.getElementById('Excluded');
    if (excludedElement) {
        excludedElement.addEventListener('change', loadTableData);
    } else {
        console.error('Element with id "Excluded" not found.');
    }
} */

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
/* async function saveConfigCol() {
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
} */

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
        //let currentDossier = null;
        ;
        // Tenter de récupérer le cookie current_dossier
        try {
            AppState.currentDossier = await getCookie('current_dossier');
        } catch (cookieError) {
            console.log('Cookie current_dossier non trouvé ou erreur lors de la récupération:', cookieError.message);
            // currentDossier reste null
        }
        
        if (AppState.currentDossier) {
            // Vérifier si le répertoire existe
            const directoryExists = await checkDirectoryExists(AppState.currentDossier);
            
            if (directoryExists) {
                document.getElementById('current-dir').textContent = AppState.currentDossier;
                document.getElementById('current-dir').style.color = ''; // Couleur normale
            } else {
                // Le répertoire n'existe plus
                console.warn(`Le répertoire '${AppState.currentDossier}' n'existe plus.`);
                document.getElementById('current-dir').textContent = `INVALIDE: ${AppState. currentDossier}`;
                document.getElementById('current-dir').style.color = 'red';
                await promptUserForValidDirectory();
            }
        } else {
            // Aucun cookie current_dossier n'existe
            console.log('Aucun répertoire courant défini. Demande de sélection à l\'utilisateur.');
            document.getElementById('current-dir').textContent = 'Aucun répertoire sélectionné';
            document.getElementById('current-dir').style.color = 'orange';
            await promptUserForValidDirectory();
        }
    } catch (error) {   
        console.error('Erreur lors de la récupération du dossier courant:', error);
        // En cas d'erreur, demander quand même à l'utilisateur de sélectionner un répertoire
        document.getElementById('current-dir').textContent = 'Erreur - Sélection requise';
        document.getElementById('current-dir').style.color = 'red';
        await promptUserForValidDirectory();
    }
}

/**
 * Charge les colonnes depuis le serveur
 * @returns {Promise} - Promise contenant le résultat de l'opérationDEBUG:
 */
async function loadColumnsFromServer() {
    try {
        console.log('DBG-2255: Appel à loadColumnsFromServer');
        const response = await ApiClient.config.loadColumns();
        console.log('DBG-2255=Colonnes chargées depuis le serveur:', response);
        if (Array.isArray(response)) {
            const deserializedColumns = deserializeColumns(response);
            setState('columns', deserializedColumns);
            console.log("dbg-0021", getState('columns'));
            // tabActive n'est pas présent ici
        } else if (response && response.columns) {
            const deserializedColumns = deserializeColumns(response.columns);
            setState('columns', deserializedColumns);
            console.log("dbg-0022-A", getState('columns'));
            if (response.tabActive) {
                setState('tabActive', response.tabActive);
            }
        } else {
            console.warn('Réponse sans colonnes:', response);
        }
        return response;
    } catch (error) {
        console.error('err006-Erreur lors du chargement des colonnes:', error);
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

/**
 * Vérifie si un répertoire existe
 * @param {string} directoryPath - Chemin du répertoire à vérifier
 * @returns {Promise<boolean>} - true si le répertoire existe, false sinon
 */
async function checkDirectoryExists(directoryPath) {
    try {
        const response = await httpPost('/check_dossier_exists', { 
            dossier: directoryPath 
        });
        return response.exists === true;
    } catch (error) {
        console.error('Erreur lors de la vérification du répertoire:', error);
        return false;
    }
}

/**
 * Demande à l'utilisateur de sélectionner un répertoire valide
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function promptUserForValidDirectory() {
    try {
        // Afficher une boîte de dialogue pour informer l'utilisateur
        const userChoice = confirm(
            "Aucun répertoire de travail valide n'est défini.\n" +
            "Voulez-vous sélectionner un répertoire de travail maintenant ?\n\n" +
            "Cliquez OK pour ouvrir le sélecteur de fichiers, ou Annuler pour continuer sans répertoire."
        );
        
        if (userChoice) {
            // Ouvrir le sélecteur de répertoire
            await openDirectorySelector();
        } else {
            // L'utilisateur a annulé, afficher un message d'avertissement
            document.getElementById('current-dir').textContent = 'ATTENTION: Aucun répertoire défini';
            document.getElementById('current-dir').style.color = 'red';
            
            // Optionnel : afficher une notification persistante
            console.warn('L\'application fonctionne sans répertoire de travail défini. Certaines fonctionnalités peuvent être limitées.');
        }
    } catch (error) {
        console.error('Erreur lors de la demande de sélection de répertoire:', error);
    }
}

/**
 * Ouvre le sélecteur de répertoire
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function openDirectorySelector() {
    try {
        // Appeler l'API pour ouvrir le sélecteur de répertoire
        const response = await httpPost('/select_directory', {});
        
        if (response && response.success && response.selected_directory) {
            // Mettre à jour le cookie avec le nouveau répertoire
            await setCookie('current_dossier', response.selected_directory);
            
            // Mettre à jour l'affichage
            document.getElementById('current-dir').textContent = response.selected_directory;
            document.getElementById('current-dir').style.color = 'green'; // Couleur verte pour indiquer le succès
            
            console.log(`Nouveau répertoire sélectionné: ${response.selected_directory}`);
            
            // Recharger les données avec le nouveau répertoire
            try {
                await loadTableData(() => {
                    console.log('Données rechargées avec le nouveau répertoire');
                });
            } catch (loadError) {
                console.warn('Erreur lors du rechargement des données:', loadError);
                // Ne pas bloquer l'application si le rechargement échoue
            }
            
        } else if (response && !response.success) {
            console.log('Sélection de répertoire annulée par l\'utilisateur');
            document.getElementById('current-dir').textContent = 'Sélection annulée';
            document.getElementById('current-dir').style.color = 'orange';
        }
    } catch (error) {
        console.error('Erreur lors de l\'ouverture du sélecteur de répertoire:', error);
        document.getElementById('current-dir').textContent = 'Erreur de sélection';
        document.getElementById('current-dir').style.color = 'red';
        
        // Afficher une alerte à l'utilisateur
        alert('Erreur lors de la sélection du répertoire. Veuillez vérifier que l\'application backend fonctionne correctement.');
    }
}

/**
 * Active le bouton de changement de répertoire
 */
function enableDirectoryChangeButton() {
    const dirBtn = document.getElementById('current-dir');
    if (dirBtn) {
        dirBtn.style.pointerEvents = 'auto';
        dirBtn.style.opacity = '1';
        dirBtn.title = "Sélectionner le dossier courant";
    }
}

/**
 * Désactive le bouton de changement de répertoire
 */
function disableDirectoryChangeButton() {
    const dirBtn = document.getElementById('current-dir');
    if (dirBtn) {
        dirBtn.style.pointerEvents = 'none';
        dirBtn.style.opacity = '0.5';
        dirBtn.title = "Veuillez attendre la fin de la sauvegarde";
    }
}

/**
 * Met à jour les informations de l'annonce sélectionnée
 */
function updateSelectedAnnonceInfo() {
    const infoDiv = document.getElementById('selected-annonce-info');
    
    
    const row = getState('currentSelectedRow');
    if (row && row.id) {
        const annonce = getAnnonce_byfile(row.id);
        let infoHtml = `Dossier : ${annonce['dossier']} - ${annonce['description']}`;
        if (annonce['url'] && /^https?:\/\/.+/.test(annonce['url'])) {
            infoHtml += ` <a href="${annonce['url']}" target="_blank" title="Ouvrir le lien">
            <span style="vertical-align:middle; margin-left:5px;">
                <svg width="32" height="32" viewBox="0 0 16 16" fill="none" style="display:inline;">
                <path d="M10.5 2H14v3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M6 10L14 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <rect x="2" y="6" width="8" height="8" rx="2" stroke="currentColor" stroke-width="1.5"/>
                </svg>
            </span>
            </a>`;
        }
        infoDiv.innerHTML = infoHtml;
    } else {
        infoDiv.textContent = '';
    }
}

// Mets à jour à chaque changement de sélection
subscribeToState('currentSelectedRow', updateSelectedAnnonceInfo);

// Mets à jour à l'initialisation (optionnel)
document.addEventListener('DOMContentLoaded', updateSelectedAnnonceInfo);

// Initialiser l'application au chargement de la page
window.addEventListener('load', initializeApp);

// Exposer les fonctions globalement
// Note: nous gardons les mêmes noms pour maintenir la compatibilité avec le code existant
window.colisvisible = colIsVisible;
//window.save_config_col = saveConfigCol;
window.view_results = viewResults;
window.loadFilterValues = loadFilterValues;
window.show_current_dossier = showCurrentDossier;
window.checkDirectoryExists = checkDirectoryExists;
window.promptUserForValidDirectory = promptUserForValidDirectory;
window.openDirectorySelector = openDirectorySelector;
window.enableDirectoryChangeButton = enableDirectoryChangeButton;
window.disableDirectoryChangeButton = disableDirectoryChangeButton;

/**
 * Met à jour la visibilité de la barre d'actions
 */
function updateActionBarVisibility() {
    const actionBar = document.getElementById('action-bar');
    const selected = getState('currentSelectedRow');
    if (actionBar) {
        actionBar.style.display = selected ? '' : 'none';
    }
}

// À appeler après chaque changement de sélection
document.addEventListener('state-changed', (event) => {
    if (event.detail.key === 'currentSelectedRow') {
        updateActionBarVisibility();
    }
});


// Fonction pour récupérer les répertoires et mettre à jour AppState.directories
async function fetchAndSetDirectories() {
    try {
        const response = await fetch('/get_directories');
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des répertoires');
        }
        const directories = await response.json();
        if (window.AppState && typeof window.AppState === 'object') {
            window.AppState.directories = directories;
        } else {
            window.AppState = { directories };
        }
    } catch (error) {
        console.error('Erreur lors de la récupération des répertoires:', error);
    }
}


