/**
 * Module de gestion d'état centralisé pour l'application
 * Permet d'éviter l'utilisation excessive de variables globales
 */

// Définition par défaut des colonnes (comme dans l'original)
window.columns = [
    { key: 'dossier', editable: false, width: '100px', visible: true, type: 'tb',title:'Dos',
    class: 'description-cell',  
      style: { cursor: 'pointer', color: 'red', textDecoration: 'underline' }, 
      event: 'click',  fixed:true // Store function name as string
    },
    { 
        key: 'description', 
        class: 'description-cell', 
        editable: true, 
        style: { cursor: 'pointer', color: 'blue', textDecoration: 'underline' }, 
        event: 'click', 
        eventHandler: 'openUrlHandler', // Store function name as string
        width: '300px',
        visible: true,
        type: 'tb',
        title:'Description',fixed:false
    },
    { key: 'id', editable: true, width: '200px',"visible":true,"type":"tb",title:'Lot',fixed:false},
    { key: 'entreprise', editable: true, width: '300px',"visible":true ,"type":"tb",title:'Entreprise',fixed:false },
    
    { key: 'role', editable: false, width: '120px',"visible":false,"type":"tb",title:'role',dir:'DIR_ROLE_FILE',fixed:false },   
    { key: 'request', editable: false, width: '120px',"visible":false ,"type":"tb",title:'request',dir:'DIR_RQ_FILE',fixed:false },
    { key: 'isJo', editable: false, width: '50px',"visible":true ,"type":"tb",title:'M.',fixed:false },
  
    
    { key: 'GptSum', editable: false, width: '50px',"visible":true,"type":"tb",title:'Res',fixed:false },
    { key: 'CV', editable: false, width: '70px',"visible":true ,"type":"tb",title:'CV',fixed:false },
    { key: 'CVpdf', editable: false, width: '70px',"visible":true ,"type":"tb",title:'CV.pdf',fixed:false },
    { key: 'BA', editable: false, width: '70px',"visible":true ,"type":"tb",title:'BA',fixed:false },
    { key: 'BApdf', editable: false, width: '70px',"visible":true ,"type":"tb",title:'BA.pdf',fixed:false },
    
    { key: 'categorie', editable: true, class: 'category-badge', prefix: 'category-', width: '100px',"visible":true,"type":"tb",title:'Cat',fixed:false  },
    { key: 'etat', editable: true, width: '100px',"visible":true ,"type":"tb",title:'Etat',fixed:false  },
    { key: 'contact', editable: true, width: '150px',"visible":false ,"type":"tb",title:'Contact',fixed:false },
    { key: 'tel', editable: true, width: '125px',"visible":false ,"type":"tb",title:'Tel.',fixed:false },
    { key: 'mail', editable: true, width: '125px',"visible":false,"type":"tb",title:'mail',fixed:false },
    { key: 'Date', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt pub',fixed:false },
    { key: 'Date_rep', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt Rep',fixed:false },
    { key: 'Date_from', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt From',fixed:false },
    { key: 'delay', editable: false, default: 'N/A', width: '120px',"visible":false,"type":"tb",title:'Delais',fixed:false },  
    { key: 'Commentaire', editable: true, width: '200px',"visible":true,"type":"tb" ,title:'Commentaire',fixed:false },
    { key: 'todo', editable: true, width: '120px',"visible":true ,"type":"tb" ,title:'ToDo',fixed:false},
    { key: 'Notes', editable: false, width: '50px',"visible":true,"type":"tb" ,title:'Nt',fixed:false },
    { key: 'url', editable: false, width: '100px',"visible":false ,"type":"tb",title:'Url',fixed:false },
    { key: 'type', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Type',fixed:false  },
    { key: 'annonce_pdf', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Annonce (pdf)',fixed:false },
    { key: 'Origine', editable: true, width: '120px',"visible":false ,"type":"tb" ,title:'Origine',fixed:false},
    { key: 'lien_Etape', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Lien Etape',fixed:false },
    
    { key: 'CVfile', editable: true, width: '80px',"visible":false ,"type":"tb",title:'CVfile',fixed:false },
    { key: 'lnk_Youtub', editable: false, width: '80px', visible: false, type: 'lnk', title: 'Youtube',fixed:false },
    { key: 'lnk_Youtub_value', editable: true, width: '80px', visible: false, type: 'tb', title: 'Youtube value',fixed:false },
    { key: 'path_dirpartage', editable: false, width: '80px', visible: false, type: 'dir', title: 'partage',fixed:false },
    { key: 'path_dirpartage_value', editable: true, width: '150px', visible: false, type: 'tb', title: 'dir',fixed:false }
];

// Initialisation de CONSTANTS par défaut pour éviter les erreurs avant chargement
// Utilisation d'une propriété privée pour éviter les boucles infinies
window._CONSTANTS_INTERNAL = {
    FILE_NAMES: {
        ANNONCE_SUFFIX: "_AN",
        GPT_REQUEST_SUFFIX: "_gpt_request.pdf",
        CV_SUFFIX_NEW: "_CyrilSauret",
        BA_SUFFIX_NAME: "_BriefAnnonce",
        NOTES_FILE: "_notes.json",
        RQ_FILE: "_gpt_request_RQ.txt",
        ACTION_SUFFIX: "_CRQ"
    }
};

// Définir un getter/setter pour window.CONSTANTS
Object.defineProperty(window, 'CONSTANTS', {
    get: function() {
        return this._CONSTANTS_INTERNAL;
    },
    set: function(value) {
        this._CONSTANTS_INTERNAL = value;
        // Ne pas appeler setState ici pour éviter la boucle infinie
    }
});

// État de l'application
const AppState = {
    // Configuration
    conf: {},
    CONSTANTS: window.CONSTANTS, // Initialiser avec la valeur par défaut

    // Navigation
    currentRow: "",
    currentSelectedRow: null, // <-- Ajout ici

    tabActive: "Campagne",

    // Données
    annonces: [],
    portalLinks: [],

    // Configuration des colonnes (initialisé avec les colonnes par défaut)
    columns: [...window.columns]
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
    console.log(`dbg-A022 : State updated: ${key} =`, value);
    // Mise à jour de window.CONSTANTS pour compatibilité si la clé est 'CONSTANTS'
    // uniquement en utilisant l'affectation directe à la propriété interne
    if (key === 'CONSTANTS') {
        window._CONSTANTS_INTERNAL = value;
    }
    
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
    // Pas besoin de copier window.columns car c'est déjà fait à l'initialisation
    // On le conserve pour compatibilité
    if (window.columns && window.columns.length > 0) {
        AppState.columns = [...window.columns];
    }
}

// Exportation des fonctions
window.getState = getState;
window.setState = setState;
window.subscribeToState = subscribeToState;
window.AppState = AppState; // Pour la phase de transition