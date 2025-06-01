/**
 * Configuration globale pour CY2
 */
window.CY2_CONFIG = {
    VERSION: "2.0.0",
    DEBUG: true,
    
    // Compatibilité avec l'ancien système
    COMPATIBILITY_MODE: true,
    
    // APIs partagées avec la version stable
    SHARED_APIS: [
        '/read_annonces_json',
        '/save_annonces_json',
        '/get_constants',
        '/charger_cols_file',
        '/load_conf_tabs',
        '/read_filters_json',
        '/save_filters_json',
        '/open_exploreur'
    ],
    
    // Nouvelles APIs CY2
    CY2_APIS: [
        '/cy2/status',
        '/switch_version',
        '/user_preferences'
    ],
    
    // Configuration UI
    UI: {
        SHOW_VERSION_BADGE: true,
        SHOW_SWITCHER: true,
        ENABLE_DEBUG_CONSOLE: true
    }
};

/**
 * Logger pour CY2
 */
window.cy2Logger = {
    log: function(message, data = null) {
        if (window.CY2_CONFIG.DEBUG) {
            console.log(`🚀 CY2: ${message}`, data || '');
        }
    },
    
    error: function(message, error = null) {
        console.error(`❌ CY2 Error: ${message}`, error || '');
    },
    
    warn: function(message, data = null) {
        if (window.CY2_CONFIG.DEBUG) {
            console.warn(`⚠️ CY2 Warning: ${message}`, data || '');
        }
    },
    
    success: function(message, data = null) {
        if (window.CY2_CONFIG.DEBUG) {
            console.log(`✅ CY2 Success: ${message}`, data || '');
        }
    }
};

// Exposer globalement
window.cy2Config = window.CY2_CONFIG;