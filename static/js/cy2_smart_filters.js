/**
 * CY2 - Filtres intelligents avancés
 * ÉTAPE 4: Système de filtrage moderne avec UI
 */

if (window.cy2Logger) {
    cy2Logger.log('🚀 CY2 Smart Filters - Chargé (étape 4)');
} else {
    console.log('🚀 CY2 Smart Filters - Chargé (étape 4)');
}

// ==========================================
// SYSTÈME DE FILTRES INTELLIGENTS CY2
// ==========================================

window.cy2SmartFilters = {
    version: "4.0.0",
    stateManager: null,
    filterPanel: null,
    searchInput: null,
    initialized: false,  // NOUVEAU : Flag d'initialisation
    
    // Initialisation
    init: function(stateManager) {
        // NOUVEAU : Vérifier si déjà initialisé
        if (this.initialized) {
            cy2Logger.warn('⚠️ CY2 Smart Filters déjà initialisé');
            return;
        }
        
        this.stateManager = stateManager;
        this.createFilterUI();
        this.setupEventListeners();
        this.initialized = true;  // NOUVEAU : Marquer comme initialisé
        cy2Logger.log('🔍 CY2 Smart Filters - Initialisé');
    },
    
    // Créer l'interface de filtrage
    createFilterUI: function() {
        // NOUVEAU : Vérifier si le panneau existe déjà
        const existingPanel = document.getElementById('cy2-filter-panel');
        if (existingPanel) {
            cy2Logger.warn('⚠️ Panneau de filtres déjà existant, suppression...');
            existingPanel.remove();
        }
        
        const filterHTML = `
            <div id="cy2-filter-panel" class="cy2-filter-panel">
                <div class="cy2-filter-header">
                    <h3>🔍 Filtres Intelligents CY2</h3>
                    <button id="cy2-toggle-filters" class="cy2-toggle-btn">📊</button>
                </div>
                
                <div class="cy2-filter-content">
                    <!-- Recherche globale -->
                    <div class="cy2-search-section">
                        <div class="cy2-section-header">
                            <h4>🔍 Recherche Globale</h4>
                            <button id="cy2-toggle-global-search" class="cy2-section-toggle" data-target="global-search-content">
                                <span class="cy2-toggle-icon">➖</span>
                            </button>
                        </div>
                        <div id="global-search-content" class="cy2-section-content">
                            <input type="text" 
                                   id="cy2-global-search" 
                                   placeholder="🔍 Recherche globale... (ex: développeur, Lyon, Java)"
                                   class="cy2-search-input">
                            <div id="cy2-search-suggestions" class="cy2-suggestions"></div>
                        </div>
                    </div>
                    
                    <!-- Filtres rapides -->
                    <div class="cy2-quick-filters">
                        <div class="cy2-section-header">
                            <h4>🏷️ Filtres Actifs</h4>
                            <button id="cy2-toggle-quick-filters" class="cy2-section-toggle" data-target="quick-filters-content">
                                <span class="cy2-toggle-icon">➖</span>
                            </button>
                        </div>
                        <div id="quick-filters-content" class="cy2-section-content">
                            <div class="cy2-filter-chips" id="cy2-active-filters"></div>
                            <button id="cy2-clear-all" class="cy2-clear-btn">🗑️ Tout effacer</button>
                        </div>
                    </div>
                    
                    <!-- Filtres par colonne -->
                    <div class="cy2-column-filters-section">
                        <div class="cy2-section-header">
                            <h4>🎯 Filtres par Colonne</h4>
                            <button id="cy2-toggle-column-filters" class="cy2-section-toggle" data-target="column-filters-content">
                                <span class="cy2-toggle-icon">➖</span>
                            </button>
                        </div>
                        <div id="column-filters-content" class="cy2-section-content">
                            <div class="cy2-column-filters" id="cy2-column-filters">
                                <!-- Généré dynamiquement -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Statistiques -->
                    <div class="cy2-filter-stats" id="cy2-filter-stats">
                        <span id="cy2-results-count">153 résultats</span>
                    </div>
                </div>
            </div>
        `;
        
        //
        let container = document.querySelector('#cy2-table-container') || 
                       document.querySelector('.cy2-table-wrapper') ||
                       document.querySelector('#tableContainer') ||
                       document.querySelector('.tableContainer') ||
                       document.querySelector('main') ||
                       document.body;
        
        // NOUVEAU : Injecter au début du container
        container.insertAdjacentHTML('afterbegin', filterHTML);
        
        this.filterPanel = document.getElementById('cy2-filter-panel');
        this.searchInput = document.getElementById('cy2-global-search');
        
        // Vérifier que les éléments sont bien créés
        if (!this.filterPanel) {
            cy2Logger.error('❌ Impossible de créer le panneau de filtres');
            return;
        }
        
        if (!this.searchInput) {
            cy2Logger.error('❌ Impossible de créer l\'input de recherche');
            return;
        }
        
        // CORRECTION : Générer les filtres par colonne avec délai et retry
        setTimeout(() => {
            this.generateColumnFiltersWithRetry();
        }, 500);
        
        cy2Logger.success('🎨 CY2 Smart Filters UI - Créée avec succès');
        
        // NOUVEAU : Log de vérification
        cy2Logger.log('✅ Éléments créés:', {
            panel: !!this.filterPanel,
            searchInput: !!this.searchInput,
            container: container.tagName
        });
    },
    
    // Générer les filtres par colonne
    generateColumnFilters: function() {
        const container = document.getElementById('cy2-column-filters');
        if (!container) {
            cy2Logger.error('❌ Container cy2-column-filters non trouvé');
            return;
        }
        
        // CORRECTION : Utiliser les colonnes VISIBLES du StateManager
        let allColumns = this.stateManager ? this.stateManager.getState('columns') : null;
        
        if (!allColumns || allColumns.length === 0) {
            cy2Logger.warn('⚠️ Aucune colonne dans StateManager');
            container.innerHTML = '<p style="color: red; padding: 10px;">Aucune colonne dans StateManager</p>';
            return;
        }
        
        // NOUVEAU : Filtrer uniquement les colonnes VISIBLES
        const visibleColumns = allColumns.filter(column => column.visible === true);
        
        cy2Logger.log('📊 Colonnes totales dans StateManager:', allColumns.length);
        cy2Logger.log('📊 Colonnes visibles:', visibleColumns.length);
        cy2Logger.log('🔍 Colonnes visibles détectées:', visibleColumns.map(c => c.label || c.key));
        
        if (!visibleColumns || visibleColumns.length === 0) {
            cy2Logger.warn('⚠️ Aucune colonne visible trouvée dans StateManager');
            container.innerHTML = '<p style="color: orange; padding: 10px;">Aucune colonne visible dans StateManager</p>';
            return;
        }
        
        // Générer le HTML des filtres pour les colonnes VISIBLES uniquement
        let filtersHTML = `
            <div style="
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
                <h4 style="
                    margin: 0 0 20px 0; 
                    color: #007bff;
                    font-size: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    🎯 Filtres par colonne (${visibleColumns.length} colonnes)
                </h4>
                
                <div style="
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); 
                    gap: 12px;
                    width: 100%;
                    box-sizing: border-box;
                ">
        `;
        
        visibleColumns.forEach((column, index) => {
            const columnLabel = column.label || column.key || `Colonne ${index + 1}`;
            const columnKey = column.key || columnLabel.toLowerCase().replace(/[^a-z0-9]/g, '_');
            
            filtersHTML += `
                <div class="cy2-column-filter" style="
                    background: #f8f9fa;
                    padding: 12px;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    box-sizing: border-box;
                    min-width: 0;
                    transition: all 0.2s ease;
                " 
                onmouseover="this.style.backgroundColor='#e9ecef'; this.style.borderColor='#007bff';"
                onmouseout="this.style.backgroundColor='#f8f9fa'; this.style.borderColor='#e9ecef';">
                    <label for="cy2-filter-${columnKey}" style="
                        display: block;
                        font-weight: 600;
                        margin-bottom: 6px;
                        color: #495057;
                        font-size: 12px;
                        line-height: 1.2;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    " title="${columnLabel}">${columnLabel}</label>
                    <input type="text" 
                           id="cy2-filter-${columnKey}"
                           class="cy2-column-input" 
                           data-column="${columnKey}"
                           data-column-index="${column.index || index}"
                           data-column-label="${columnLabel}"
                           data-column-original="${column.key}"
                           placeholder="Filtrer..."
                           style="
                               width: 100%;
                               padding: 6px 8px;
                               border: 1px solid #ced4da;
                               border-radius: 4px;
                               font-size: 12px;
                               box-sizing: border-box;
                               transition: border-color 0.2s ease;
                               min-width: 0;
                           "
                           onfocus="this.style.borderColor='#007bff'; this.style.boxShadow='0 0 0 2px rgba(0,123,255,0.25)';"
                           onblur="this.style.borderColor='#ced4da'; this.style.boxShadow='none';">
                </div>
            `;
        });
        
        filtersHTML += `
        </div>
    </div>
`;
        
        // Injecter le HTML
        container.innerHTML = filtersHTML;
        
        // Ajouter les événements pour chaque input
        const inputs = container.querySelectorAll('.cy2-column-input');
        inputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const columnKey = e.target.dataset.columnOriginal || e.target.dataset.column;
                const value = e.target.value;
                
                cy2Logger.log(`🔍 Filtre colonne "${e.target.dataset.columnLabel}" (${columnKey}): "${value}"`);
                
                // Appeler la fonction de filtrage par colonne avec la clé StateManager
                this.performColumnFilterWithStateManager(columnKey, value);
            });
        });
        
        cy2Logger.success(`✅ ${inputs.length} filtres par colonne générés depuis StateManager (colonnes visibles)`);
        
        // Styling pour rendre visible
        container.style.cssText = `
            border: 2px solid #28a745 !important;
            background: linear-gradient(135deg, #f8fff9, #e8f5e8) !important;
            padding: 20px !important;
            margin: 20px 0 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        `;
        
        cy2Logger.log('🎨 Filtres par colonne rendus avec style StateManager');
        
        return inputs.length;
    },
    
    // NOUVEAU : Génération avec retry automatique
    generateColumnFiltersWithRetry: function(attempt = 1, maxAttempts = 3) {
        cy2Logger.log(`🔄 Tentative ${attempt}/${maxAttempts} de génération des filtres par colonne`);
        
        const result = this.generateColumnFilters();
        
        if (result && result > 0) {
            cy2Logger.success(`✅ Filtres par colonne générés avec succès (${result} filtres)`);
            return;
        }
        
        if (attempt < maxAttempts) {
            cy2Logger.warn(`⚠️ Échec tentative ${attempt}, retry dans 1s...`);
            setTimeout(() => {
                this.generateColumnFiltersWithRetry(attempt + 1, maxAttempts);
            }, 1000);
        } else {
            cy2Logger.error('❌ Impossible de générer les filtres par colonne après 3 tentatives');
            
            // FALLBACK : Créer des filtres basiques
            this.createFallbackColumnFilters();
        }
    },
    
    // NOUVEAU : Filtres de secours si StateManager ne fonctionne pas
    createFallbackColumnFilters: function() {
        cy2Logger.warn('🔧 Création de filtres de secours depuis le DOM...');
        
        const container = document.getElementById('cy2-column-filters');
        if (!container) return;
        
        // Extraire les colonnes directement du tableau DOM
        const headers = document.querySelectorAll('thead th, table th');
        
        if (headers.length === 0) {
            container.innerHTML = '<p style="color: red; padding: 10px;">❌ Aucune colonne détectée dans le tableau</p>';
            return;
        }
        
        let filtersHTML = `
            <h4 style="margin: 0 0 15px 0; color: #dc3545;">
                🔧 Filtres de secours (${headers.length} colonnes détectées)
            </h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
        `;
        
        headers.forEach((header, index) => {
            const cleanText = (header.textContent || header.innerText || '')
                .replace(/[\n\r\t]/g, ' ')
                .replace(/\s+/g, ' ')
                .replace(/[↕️⬆️⬇️]/g, '')
                .trim();
            
            if (cleanText) {
                const columnKey = cleanText.toLowerCase().replace(/[^a-z0-9]/g, '_');
                
                filtersHTML += `
                    <div class="cy2-column-filter" style="
                        background: #fff3cd;
                        padding: 12px;
                        border: 1px solid #ffeaa7;
                        border-radius: 6px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                        <label for="fallback-filter-${columnKey}" style="
                            display: block;
                            font-weight: bold;
                            margin-bottom: 6px;
                            color: #856404;
                            font-size: 13px;
                        ">${cleanText}:</label>
                        <input type="text" 
                               id="fallback-filter-${columnKey}"
                               class="cy2-column-input cy2-fallback-input" 
                               data-column="${columnKey}"
                               data-column-index="${index}"
                               data-column-label="${cleanText}"
                               placeholder="Filtrer ${cleanText}..."
                               style="
                                   width: 100%;
                                   padding: 8px 10px;
                                   border: 1px solid #ffeaa7;
                                   border-radius: 4px;
                                   font-size: 13px;
                                   box-sizing: border-box;
                                   background: #fffbf0;
                               ">
                    </div>
                `;
            }
        });
        
        filtersHTML += '</div>';
        
        container.innerHTML = filtersHTML;
        
        // Ajouter les événements pour les filtres de secours
        const inputs = container.querySelectorAll('.cy2-fallback-input');
        inputs.forEach(input => {
            input.addEventListener('input', (e) => {
                const columnIndex = parseInt(e.target.dataset.columnIndex);
                const value = e.target.value.toLowerCase();
                
                cy2Logger.log(`🔍 Filtre secours colonne ${columnIndex} (${e.target.dataset.columnLabel}): "${value}"`);
                
                // Filtrage DOM simple
                const rows = document.querySelectorAll('tbody tr');
                let visibleCount = 0;
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    let showRow = true;
                    
                    // Vérifier tous les filtres actifs
                    inputs.forEach(filterInput => {
                        const filterValue = filterInput.value.toLowerCase().trim();
                        const filterIndex = parseInt(filterInput.dataset.columnIndex);
                        
                        if (filterValue && cells[filterIndex]) {
                            const cellText = cells[filterIndex].textContent.toLowerCase();
                            if (!cellText.includes(filterValue)) {
                                showRow = false;
                            }
                        }
                    });
                    
                    if (showRow) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                });
                
                // Mettre à jour le compteur
                const counter = document.getElementById('cy2-results-count');
                if (counter) {
                    counter.textContent = `${visibleCount}/${rows.length} résultats (mode secours)`;
                }
            });
        });
        
        // Styliser le container
        container.style.cssText = `
            border: 2px solid #ffc107 !important;
            background: linear-gradient(135deg, #fff3cd, #ffeaa7) !important;
            padding: 20px !important;
            margin: 20px 0 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
        `;
        
        cy2Logger.success(`✅ ${inputs.length} filtres de secours créés`);
        
        return inputs.length;
    },
    
    // Configuration des événements
    setupEventListeners: function() {
        // Recherche globale avec debouncing
        let searchTimeout;
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performGlobalSearch(e.target.value);
            }, 300);
        });
        
        // Filtres par colonne
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('cy2-column-input')) {
                const column = e.target.dataset.column;
                const value = e.target.value;
                this.performColumnFilter(column, value);
            }
        });
        
        // Toggle panel principal
        const toggleMainBtn = document.getElementById('cy2-toggle-filters');
        if (toggleMainBtn) {
            toggleMainBtn.addEventListener('click', () => {
                this.toggleFilterPanel();
            });
        }
        
        // Effacer tous les filtres
        const clearAllBtn = document.getElementById('cy2-clear-all');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }
        
        // NOUVEAU : Boutons toggle des sections
        document.querySelectorAll('.cy2-section-toggle').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                cy2Logger.log(`🔄 Toggle section: ${button.dataset.target}`);
                this.toggleSection(button);
            });
        });
        
        // NOUVEAU : Sauvegarder l'état des sections dans localStorage
        setTimeout(() => {
            this.loadSectionStates();
        }, 100);
        
        // Écouter les changements de filtres
        if (this.stateManager && this.stateManager.subscribe) {
            this.stateManager.subscribe('ui.filters', (filters) => {
                this.updateFilterUI(filters);
            });
        }
        
        cy2Logger.success('🎧 Événements configurés avec succès');
    },
    
    // Recherche globale
    performGlobalSearch: function(query) {
        if (!query.trim()) {
            this.clearGlobalSearch();
            return;
        }
        
        cy2Logger.log(`🔍 Recherche globale: "${query}"`);
        
        // Filtrer les données
        const allAnnonces = this.stateManager.getState('annonces') || [];
        const filteredAnnonces = this.filterAnnoncesByGlobalSearch(allAnnonces, query);
        
        // Mettre à jour l'état
        this.stateManager.setState('ui.globalSearch', query);
        this.stateManager.setState('meta.filteredRows', filteredAnnonces.length);
        
        // CORRECTION : Mettre à jour le compteur AVANT le rendu
        this.updateResultsCount(filteredAnnonces.length);
        
        // Recharger le tableau avec les résultats filtrés
        this.renderFilteredResults(filteredAnnonces);
        
        // Highlighting des résultats
        setTimeout(() => {
            this.highlightSearchResults(query);
            // CORRECTION : Remettre à jour le compteur après le rendu
            this.updateResultsCount(filteredAnnonces.length);
        }, 200);
        
        cy2Logger.success(`🔍 Recherche terminée: ${filteredAnnonces.length} résultats`);
    },
    
    // Filtre par colonne
    performColumnFilter: function(column, value) {
        cy2Logger.log(`🔍 Filtrage colonne "${column}": "${value}"`);
        
        // AMÉLIORATION : Obtenir l'index de la colonne avec correspondance intelligente
        const headers = Array.from(document.querySelectorAll('thead th, table th'));
        let columnIndex = -1;
        
        headers.forEach((header, index) => {
            // Nettoyage identique à generateColumnFilters
            const cleanText = (header.textContent || header.innerText || '')
                .replace(/[\n\r\t]/g, ' ')
                .replace(/\s+/g, ' ')
                .replace(/[↕️⬆️⬇️]/g, '')
                .trim();
            
            const headerKey = cleanText.toLowerCase().replace(/[^a-z0-9]/g, '_');
            
            if (headerKey === column) {
                columnIndex = index;
            }
        });
        
        if (columnIndex === -1) {
            cy2Logger.warn(`⚠️ Colonne "${column}" non trouvée (index: ${columnIndex})`);
            // DEBUG : Afficher toutes les clés disponibles
            headers.forEach((header, index) => {
                const cleanText = (header.textContent || header.innerText || '')
                    .replace(/[\n\r\t]/g, ' ')
                    .replace(/\s+/g, ' ')
                    .replace(/[↕️⬆️⬇️]/g, '')
                    .trim();
                const headerKey = cleanText.toLowerCase().replace(/[^a-z0-9]/g, '_');
                cy2Logger.log(`Debug colonne ${index}: "${cleanText}" -> "${headerKey}"`);
            });
            return;
        }
        
        cy2Logger.log(`✅ Colonne trouvée à l'index ${columnIndex}`);
        
        // Filtrer les lignes
        const rows = document.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            let showRow = true;
            
            if (cells[columnIndex]) {
                const cellText = cells[columnIndex].textContent.toLowerCase();
                if (value.trim() && !cellText.includes(value.toLowerCase())) {
                    showRow = false;
                }
            }
            
            // Vérifier aussi les autres filtres actifs
            if (showRow) {
                const allColumnInputs = document.querySelectorAll('.cy2-column-input');
                allColumnInputs.forEach(input => {
                    const otherValue = input.value.toLowerCase().trim();
                    const otherColumnIndex = parseInt(input.dataset.columnIndex) || 0;
                    
                    if (otherValue && cells[otherColumnIndex]) {
                        const otherCellText = cells[otherColumnIndex].textContent.toLowerCase();
                        if (!otherCellText.includes(otherValue)) {
                            showRow = false;
                        }
                    }
                });
            }
            
            if (showRow) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Mettre à jour le compteur
        this.updateResultsCount(visibleCount);
        
        // Mettre à jour l'état des filtres
        const currentFilters = this.stateManager.getState('ui.filters') || {};
        if (value.trim()) {
            currentFilters[column] = value;
        } else {
            delete currentFilters[column];
        }
        this.stateManager.setState('ui.filters', currentFilters);
        
        // Mettre à jour l'UI des filtres actifs
        this.updateActiveFiltersChips(currentFilters);
        
        cy2Logger.success(`✅ Filtrage terminé: ${visibleCount} résultats`);
    },
    
    // NOUVEAU : Filtrage par colonne utilisant le StateManager
    performColumnFilterWithStateManager: function(columnKey, value) {
        cy2Logger.log(`🔍 Filtrage StateManager colonne "${columnKey}": "${value}"`);
        
        // Obtenir toutes les annonces depuis StateManager
        const allAnnonces = this.stateManager.getState('annonces') || [];
        const columns = this.stateManager.getState('columns') || [];
        
        // Trouver la colonne dans StateManager
        const column = columns.find(col => col.key === columnKey);
        if (!column) {
            cy2Logger.warn(`⚠️ Colonne "${columnKey}" non trouvée dans StateManager`);
            return;
        }
        
        cy2Logger.log(`✅ Colonne StateManager trouvée: ${column.label}`);
        
        // Filtrer les annonces
        let filteredAnnonces = allAnnonces;
        
        if (value.trim()) {
            filteredAnnonces = allAnnonces.filter(item => {
                // Extraire les vraies données
                const itemKeys = Object.keys(item);
                let actualData = item;
                
                if (itemKeys.length === 1 && itemKeys[0].includes('.data.json')) {
                    actualData = item[itemKeys[0]];
                }
                
                // Obtenir la valeur de la colonne
                const columnValue = actualData[columnKey];
                if (columnValue === undefined || columnValue === null) {
                    return false;
                }
                
                // Convertir en string et chercher
                const searchText = String(columnValue).toLowerCase();
                return searchText.includes(value.toLowerCase());
            });
        }
        
        // Appliquer aussi les autres filtres actifs
        const currentFilters = this.stateManager.getState('ui.filters') || {};
        
        // Mettre à jour les filtres avec le nouveau filtre
        if (value.trim()) {
            currentFilters[columnKey] = value;
        } else {
            delete currentFilters[columnKey];
        }
        
        // Appliquer tous les filtres de colonnes
        Object.entries(currentFilters).forEach(([filterKey, filterValue]) => {
            if (filterKey !== 'global' && filterKey !== columnKey && filterValue.trim()) {
                filteredAnnonces = filteredAnnonces.filter(item => {
                    const itemKeys = Object.keys(item);
                    let actualData = item;
                    
                    if (itemKeys.length === 1 && itemKeys[0].includes('.data.json')) {
                        actualData = item[itemKeys[0]];
                    }
                    
                    const columnValue = actualData[filterKey];
                    if (columnValue === undefined || columnValue === null) {
                        return false;
                    }
                    
                    const searchText = String(columnValue).toLowerCase();
                    return searchText.includes(filterValue.toLowerCase());
                });
            }
        });
        
        // Appliquer aussi la recherche globale si active
        const globalSearch = this.stateManager.getState('ui.globalSearch') || '';
        if (globalSearch.trim()) {
            filteredAnnonces = this.filterAnnoncesByGlobalSearch(filteredAnnonces, globalSearch);
        }
        
        // Mettre à jour l'état
        this.stateManager.setState('ui.filters', currentFilters);
        this.stateManager.setState('meta.filteredRows', filteredAnnonces.length);
        
        // Recharger le tableau avec les résultats filtrés
        this.renderFilteredResults(filteredAnnonces);
        
        // Mettre à jour le compteur
        this.updateResultsCount(filteredAnnonces.length);
        
        // Mettre à jour l'UI des filtres actifs
        this.updateActiveFiltersChips(currentFilters);
        
        cy2Logger.success(`✅ Filtrage StateManager terminé: ${filteredAnnonces.length} résultats`);
    },
    
    // Mettre à jour l'interface des filtres
    updateFilterUI: function(filters) {
        this.updateActiveFiltersChips(filters);
        this.updateResultsCount();
    },
    
    // Chips des filtres actifs
    updateActiveFiltersChips: function(filters) {
        const container = document.getElementById('cy2-active-filters');
        let chipsHTML = '';
        
        Object.entries(filters).forEach(([key, value]) => {
            if (value && value.trim()) {
                const displayName = key === 'global' ? 'Global' : key;
                chipsHTML += `
                    <div class="cy2-filter-chip" data-filter="${key}">
                        <span>${displayName}: ${value}</span>
                        <button onclick="cy2SmartFilters.removeFilter('${key}')">×</button>
                    </div>
                `;
            }
        });
        
        container.innerHTML = chipsHTML;
    },
    
    // AMÉLIORATION : Mettre à jour le compteur de résultats
    updateResultsCount: function(count = null) {
        const total = this.stateManager.getState('meta.totalRows') || 0;
        const filteredCount = count !== null ? count : total;
        
        const counter = document.getElementById('cy2-results-count');
        
        if (counter) {
            counter.textContent = `${filteredCount}/${total} résultats`;
            counter.className = filteredCount < total ? 'filtered' : 'all';
            
            // NOUVEAU : Log pour debug
            cy2Logger.log(`📊 Compteur mis à jour: ${filteredCount}/${total}`);
        } else {
            // NOUVEAU : Warning si compteur non trouvé
            cy2Logger.warn('⚠️ Compteur de résultats non trouvé dans le DOM');
        }
    },
    
    // Highlighting des résultats
    highlightSearchResults: function(query) {
        if (!query.trim()) {
            this.removeHighlights();
            return;
        }
        
        const tableBody = document.querySelector('#cy2-table-body');
        if (!tableBody) return;
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        
        tableBody.querySelectorAll('.cy2-text').forEach(cell => {
            const originalText = cell.textContent;
            if (originalText.toLowerCase().includes(query.toLowerCase())) {
                cell.innerHTML = originalText.replace(regex, '<mark class="cy2-highlight">$1</mark>');
            }
        });
    },
    
    // Supprimer les highlights
    removeHighlights: function() {
        document.querySelectorAll('.cy2-highlight').forEach(mark => {
            mark.outerHTML = mark.innerHTML;
        });
    },
    
    // Supprimer un filtre spécifique
    removeFilter: function(filterKey) {
        const currentFilters = this.stateManager.getState('ui.filters') || {};
        delete currentFilters[filterKey];
        
        this.stateManager.setState('ui.filters', currentFilters);
        
        // Nettoyer l'input correspondant
        if (filterKey === 'global') {
            this.searchInput.value = '';
        } else {
            const input = document.querySelector(`[data-column="${filterKey}"]`);
            if (input) input.value = '';
        }
        
        // Recharger le tableau
        window.cy2FiltersManager.filterAnnonces();
        loadTableData();
    },
    
    // Effacer tous les filtres
    clearAllFilters: function() {
        this.stateManager.setState('ui.filters', {});
        
        // Nettoyer tous les inputs
        this.searchInput.value = '';
        document.querySelectorAll('.cy2-column-input').forEach(input => {
            input.value = '';
        });
        
        this.removeHighlights();
        
        // Recharger le tableau
        loadTableData();
        
        cy2Logger.log('🔍 Tous les filtres effacés');
    },
    
    // Toggle du panel de filtres
    toggleFilterPanel: function() {
        this.filterPanel.classList.toggle('collapsed');
    },
    
    // Filtrer les annonces par recherche globale
    filterAnnoncesByGlobalSearch: function(annonces, query) {
        const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 0);
        
        return annonces.filter(item => {
            // Extraire les vraies données
            const itemKeys = Object.keys(item);
            let actualData = item;
            
            if (itemKeys.length === 1 && itemKeys[0].includes('.data.json')) {
                actualData = item[itemKeys[0]];
            }
            
            // Chercher dans toutes les propriétés textuelles
            const searchableText = Object.values(actualData)
                .filter(value => typeof value === 'string')
                .join(' ')
                .toLowerCase();
            
            // Tous les termes doivent être trouvés
            return searchTerms.every(term => searchableText.includes(term));
        });
    },
    
    // Rendu des résultats filtrés
    renderFilteredResults: function(filteredAnnonces) {
        // Utiliser le système de rendu existant
        const columns = this.stateManager.getState('columns') || [];
        const constants = this.stateManager.getState('constants') || {};
        
        // Remplacer temporairement les annonces dans le StateManager
        const originalAnnonces = this.stateManager.getState('annonces');
        this.stateManager.setState('annonces', filteredAnnonces);
        
        // Recharger le tableau
        if (window.renderTableRows) {
            window.renderTableRows(filteredAnnonces, columns, constants);
        }
        
        // Note: On ne restaure pas les annonces originales pour garder le filtre
    },
    
    // Effacer la recherche globale
    clearGlobalSearch: function() {
        this.stateManager.setState('ui.globalSearch', '');
        this.removeHighlights();
        
        // Recharger toutes les données
        const allAnnonces = this.stateManager.getState('annonces') || [];
        this.renderFilteredResults(allAnnonces);
        this.updateResultsCount(allAnnonces.length);
    },
    
    // Effacer un filtre de colonne
    clearColumnFilter: function(column) {
        const input = document.querySelector(`[data-column="${column}"]`);
        if (input) input.value = '';
        
        // Recharger avec la recherche globale actuelle
        const globalSearch = this.stateManager.getState('ui.globalSearch') || '';
        if (globalSearch) {
            this.performGlobalSearch(globalSearch);
        } else {
            this.clearGlobalSearch();
        }
    },
    
    // NOUVEAU : Toggle d'une section
    toggleSection: function(button) {
        const targetId = button.dataset.target;
        const content = document.getElementById(targetId);
        const icon = button.querySelector('.cy2-toggle-icon');
        
        if (!content || !icon) {
            cy2Logger.warn(`⚠️ Éléments non trouvés pour ${targetId}`);
            return;
        }
        
        const isHidden = content.classList.contains('hidden');
        
        if (isHidden) {
            // Afficher
            content.classList.remove('hidden');
            content.style.display = '';
            content.style.maxHeight = '2000px';
            content.style.opacity = '1';
            icon.textContent = '➖';
            button.classList.remove('collapsed');
            button.title = 'Cacher cette section';
            cy2Logger.log(`👁️ Section "${targetId}" affichée`);
        } else {
            // Cacher
            content.classList.add('hidden');
            content.style.maxHeight = '0';
            content.style.opacity = '0';
            content.style.overflow = 'hidden';
            icon.textContent = '➕';
            button.classList.add('collapsed');
            button.title = 'Afficher cette section';
            cy2Logger.log(`🙈 Section "${targetId}" cachée`);
        }
        
        // Sauvegarder l'état
        this.saveSectionState(targetId, !isHidden);
    },
    
    // NOUVEAU : Sauvegarder l'état des sections
    saveSectionState: function(sectionId, isVisible) {
        try {
            const states = JSON.parse(localStorage.getItem('cy2-section-states') || '{}');
            states[sectionId] = isVisible;
            localStorage.setItem('cy2-section-states', JSON.stringify(states));
            cy2Logger.log(`💾 État sauvé: ${sectionId} = ${isVisible}`);
        } catch (error) {
            cy2Logger.warn('⚠️ Erreur sauvegarde état:', error);
        }
    },
    
    // NOUVEAU : Charger l'état des sections
    loadSectionStates: function() {
        try {
            const states = JSON.parse(localStorage.getItem('cy2-section-states') || '{}');
            
            // États par défaut (toutes visibles)
            const defaultStates = {
                'global-search-content': true,
                'quick-filters-content': true,
                'column-filters-content': true
            };
            
            // Appliquer les états
            Object.entries(defaultStates).forEach(([sectionId, defaultVisible]) => {
                const isVisible = states.hasOwnProperty(sectionId) ? states[sectionId] : defaultVisible;
                const content = document.getElementById(sectionId);
                const button = document.querySelector(`[data-target="${sectionId}"]`);
                
                if (content && button) {
                    const icon = button.querySelector('.cy2-toggle-icon');
                    
                    if (icon) {
                        if (!isVisible) {
                            content.classList.add('hidden');
                            content.style.maxHeight = '0';
                            content.style.opacity = '0';
                            content.style.overflow = 'hidden';
                            icon.textContent = '➕';
                            button.classList.add('collapsed');
                            button.title = 'Afficher cette section';
                        } else {
                            content.classList.remove('hidden');
                            content.style.display = '';
                            content.style.maxHeight = '2000px';
                            content.style.opacity = '1';
                            icon.textContent = '➖';
                            button.classList.remove('collapsed');
                            button.title = 'Cacher cette section';
                        }
                    }
                }
            });
            
            cy2Logger.log('📂 États des sections chargés');
        } catch (error) {
            cy2Logger.warn('⚠️ Erreur chargement états:', error);
        }
    },
    
    // NOUVEAU : Reset des états des sections
    resetSectionStates: function() {
        localStorage.removeItem('cy2-section-states');
        this.loadSectionStates();
        cy2Logger.log('🔄 États des sections réinitialisés');
    },
};

// Auto-initialisation AMÉLIORÉE
function initCY2SmartFilters() {
    // NOUVEAU : Vérifier si déjà initialisé
    if (window.cy2SmartFilters && window.cy2SmartFilters.initialized) {
        return;
    }
    
    if (window.cy2StateManager && window.cy2SmartFilters) {
        try {
            window.cy2SmartFilters.init(window.cy2StateManager);
            cy2Logger.success('✅ CY2 Smart Filters - Initialisé avec succès !');
        } catch (error) {
            cy2Logger.error('❌ Erreur initialisation Smart Filters:', error);
        }
    } else {
        cy2Logger.warn('⚠️ En attente de cy2StateManager...');
        // Réessayer dans 500ms
        setTimeout(initCY2SmartFilters, 500);
    }
}

// Plusieurs méthodes d'initialisation
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCY2SmartFilters);
} else {
    // DOM déjà chargé, initialiser maintenant
    setTimeout(initCY2SmartFilters, 100);
}

// Backup: initialisation retardée
setTimeout(initCY2SmartFilters, 2000);

// Marquer le module comme chargé
if (window.cy2Logger) {
    cy2Logger.success('✅ CY2 Smart Filters - Module complet chargé !');
} else {
    console.log('✅ CY2 Smart Filters - Module complet chargé !');
}

// Exposer globalement pour debug
window.initCY2SmartFilters = initCY2SmartFilters;