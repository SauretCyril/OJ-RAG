/**
 * CY2 - Gestion des filtres
 * ÉTAPE 2: Intégration avec StateManager
 */

if (window.cy2Logger) {
    cy2Logger.log('🚀 CY2 All Dos Filters - Chargé (étape 2)');
} else {
    console.log('🚀 CY2 All Dos Filters - Chargé (étape 2)');
}

// Gestionnaire de filtres CY2 avec StateManager
window.cy2FiltersManager = {
    version: "2.0.0",
    stateManager: null,
    
    // Initialisation avec StateManager
    init: function(stateManager) {
        this.stateManager = stateManager;
        cy2Logger.log('🔍 CY2 Filters Manager - Initialisé avec StateManager');
        
        // S'abonner aux changements de filtres
        this.stateManager.subscribe('ui.filters', (filters) => {
            this.onFiltersChanged(filters);
        });
    },
    
    // Appliquer un filtre
    applyFilter: function(filterType, value) {
        if (!this.stateManager) {
            cy2Logger.warn('CY2 Filters - StateManager non initialisé');
            return [];
        }
        
        const currentFilters = this.stateManager.getState('ui.filters') || {};
        const newFilters = { ...currentFilters, [filterType]: value };
        
        this.stateManager.setState('ui.filters', newFilters);
        
        return this.filterAnnonces();
    },
    
    // Effacer tous les filtres
    clearFilters: function() {
        if (!this.stateManager) return;
        
        this.stateManager.setState('ui.filters', {});
        cy2Logger.log('🔍 CY2 Filters - Tous les filtres effacés');
        
        return this.filterAnnonces();
    },
    
    // Filtrer les annonces selon les filtres actifs
    filterAnnonces: function() {
        if (!this.stateManager) return [];
        
        const annonces = this.stateManager.getState('annonces') || [];
        const filters = this.stateManager.getState('ui.filters') || {};
        
        let filteredAnnonces = [...annonces];
        
        // Appliquer chaque filtre
        Object.entries(filters).forEach(([key, value]) => {
            if (value && value.trim() !== '') {
                filteredAnnonces = this.applyFilterToArray(filteredAnnonces, key, value);
            }
        });
        
        // Mettre à jour le count filtré
        this.stateManager.setState('meta.filteredRows', filteredAnnonces.length);
        
        cy2Logger.log(`🔍 CY2 Filters - ${filteredAnnonces.length}/${annonces.length} annonces après filtrage`);
        
        return filteredAnnonces;
    },
    
    // Appliquer un filtre spécifique sur un tableau
    applyFilterToArray: function(items, filterKey, filterValue) {
        const lowerValue = filterValue.toLowerCase();
        
        return items.filter(item => {
            // Filtrage par colonne spécifique
            if (item[filterKey]) {
                return String(item[filterKey]).toLowerCase().includes(lowerValue);
            }
            
            // Filtrage global si pas de colonne spécifique
            if (filterKey === 'global') {
                return Object.values(item).some(val => 
                    String(val).toLowerCase().includes(lowerValue)
                );
            }
            
            return true;
        });
    },
    
    // Callback quand les filtres changent
    onFiltersChanged: function(filters) {
        cy2Logger.log('🔍 CY2 Filters - Filtres mis à jour:', filters);
        
        // Déclencher un événement pour notifier les autres composants
        const event = new CustomEvent('cy2-filters-changed', { 
            detail: { filters, count: Object.keys(filters).length } 
        });
        document.dispatchEvent(event);
    },
    
    // Sauvegarder un préréglage de filtres
    saveFilterPreset: function(name, filters) {
        const presets = JSON.parse(localStorage.getItem('cy2_filter_presets') || '{}');
        presets[name] = filters;
        localStorage.setItem('cy2_filter_presets', JSON.stringify(presets));
        
        cy2Logger.log(`🔍 CY2 Filters - Préréglage "${name}" sauvegardé`);
    },
    
    // Charger un préréglage de filtres
    loadFilterPreset: function(name) {
        const presets = JSON.parse(localStorage.getItem('cy2_filter_presets') || '{}');
        
        if (presets[name]) {
            this.stateManager.setState('ui.filters', presets[name]);
            cy2Logger.log(`🔍 CY2 Filters - Préréglage "${name}" chargé`);
            return presets[name];
        }
        
        cy2Logger.warn(`🔍 CY2 Filters - Préréglage "${name}" non trouvé`);
        return null;
    },
    
    // Obtenir tous les préréglages
    getFilterPresets: function() {
        return JSON.parse(localStorage.getItem('cy2_filter_presets') || '{}');
    }
};

// Auto-initialisation si StateManager est disponible
if (window.cy2StateManager) {
    window.cy2FiltersManager.init(window.cy2StateManager);
} else {
    // Attendre que StateManager soit prêt
    document.addEventListener('DOMContentLoaded', () => {
        if (window.cy2StateManager) {
            window.cy2FiltersManager.init(window.cy2StateManager);
        }
    });
}