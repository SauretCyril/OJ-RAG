/**
 * CY2 - Gestion des lignes du tableau
 * ÉTAPE 1: Fichier temporaire vide - sera implémenté dans l'étape suivante
 * 
 * Ce fichier contiendra la version modulaire de loadTableData :
 * - Rendu modulaire des cellules
 * - Gestion des événements optimisée
 * - Integration avec le StateManager
 * - Performance améliorée
 */

cy2Logger.log('🚀 CY2 All Dos All Rows - Chargé (étape 1 - placeholder)');

// Pour l'étape 1, on s'appuie sur l'ancien loadTableData
// qui doit être disponible via l'inclusion des scripts originaux

// TODO ÉTAPE 3: Implémenter la version modulaire
/*
class Cy2TableRenderer {
    constructor(stateManager) {
        this.stateManager = stateManager;
    }
    
    renderSpecialCell(col, item, dir_path, index) {
        // Implémentation modulaire du rendu des cellules
    }
    
    renderRow(itemWrapper, index) {
        // Implémentation modulaire du rendu des lignes
    }
}

function loadTableData(callback) {
    // Version CY2 modernisée de loadTableData
}
*/

// Placeholder pour éviter les erreurs
window.cy2TableRenderer = {
    placeholder: true,
    version: "1.0.0-placeholder"
};

/**
 * CY2 - Rendu modernisé du tableau
 * ÉTAPE 3: Remplacement de loadTableData avec StateManager
 */

if (window.cy2Logger) {
    cy2Logger.log('🚀 CY2 All Dos All Rows - Chargé (étape 3 - complet)');
} else {
    console.log('🚀 CY2 All Dos All Rows - Chargé (étape 3 - complet)');
}

// ==========================================
// RENDU MODERNISÉ CY2
// ==========================================

/**
 * Version CY2 de loadTableData - Utilise le StateManager
 */
function loadTableData(callback) {
    if (!window.cy2StateManager) {
        cy2Logger.error('loadTableData CY2: StateManager non disponible');
        return;
    }
    
    cy2Logger.log('🎨 CY2 loadTableData - Début du rendu modernisé');
    
    try {
        // Obtenir les données depuis le StateManager
        const annonces = window.cy2StateManager.getState('annonces') || [];
        const columns = window.cy2StateManager.getState('columns') || [];
        const constants = window.cy2StateManager.getState('constants') || {};
        
        if (annonces.length === 0) {
            cy2Logger.warn('loadTableData CY2: Aucune annonce à afficher');
            return;
        }
        
        // NOUVEAU: Vérifier et créer la structure du tableau si nécessaire
        ensureTableStructure();
        
        // Marquer le début du chargement
        window.cy2StateManager.setState('ui.isLoading', true);
        
        // Générer les en-têtes avec la nouvelle méthode CY2
        generateTableHeaders();
        
        // Rendu des lignes avec amélirations CY2
        renderTableRows(annonces, columns, constants);
        
        // Marquer la fin du chargement
        window.cy2StateManager.setState('ui.isLoading', false);
        
        // Mettre à jour les métadonnées
        window.cy2StateManager.updateState({
            'meta.totalRows': annonces.length,
            'meta.lastUpdated': Date.now()
        });
        
        cy2Logger.success(`🎨 CY2 loadTableData - ${annonces.length} lignes rendues`);
        
        // Appeler le callback si fourni (compatibilité)
        if (callback && typeof callback === 'function') {
            callback();
        }
        
        // Déclencher un événement pour notifier le rendu terminé
        const event = new CustomEvent('cy2-table-rendered', { 
            detail: { count: annonces.length, timestamp: Date.now() }
        });
        document.dispatchEvent(event);
        
    } catch (error) {
        cy2Logger.error('Erreur loadTableData CY2:', error);
        window.cy2StateManager.setState('ui.isLoading', false);
    }
}

/**
 * NOUVELLE FONCTION: Assurer la structure du tableau
 */
function ensureTableStructure() {
    try {
        // Chercher un tableau existant
        let table = document.querySelector('table');
        
        if (!table) {
            cy2Logger.log('🏗️ CY2: Création automatique de la structure du tableau');
            
            // Trouver un container pour le tableau
            let container = document.querySelector('#table-container') ||
                           document.querySelector('.table-container') ||
                           document.querySelector('#tableContainer') ||
                           document.querySelector('.tableContainer') ||
                           document.querySelector('main') ||
                           document.querySelector('.container') ||
                           document.body;
            
            // Créer la structure HTML du tableau
            const tableHTML = `
                <div id="cy2-table-container" class="cy2-table-wrapper">
                    <table id="cy2-main-table" class="cy2-enhanced-table">
                        <thead id="cy2-table-head">
                            <!-- En-têtes générées dynamiquement -->
                        </thead>
                        <tbody id="cy2-table-body">
                            <!-- Lignes générées dynamiquement -->
                        </tbody>
                    </table>
                </div>
            `;
            
            // Injecter le tableau
            container.insertAdjacentHTML('beforeend', tableHTML);
            
            cy2Logger.success('🏗️ CY2: Structure du tableau créée avec succès');
        } else {
            cy2Logger.log('🏗️ CY2: Tableau existant trouvé, amélioration de la structure');
            
            // Améliorer le tableau existant
            table.classList.add('cy2-enhanced-table');
            
            // Assurer la présence des thead et tbody
            if (!table.querySelector('thead')) {
                const thead = document.createElement('thead');
                thead.id = 'cy2-table-head';
                table.insertBefore(thead, table.firstChild);
            }
            
            if (!table.querySelector('tbody')) {
                const tbody = document.createElement('tbody');
                tbody.id = 'cy2-table-body';
                table.appendChild(tbody);
            }
        }
        
    } catch (error) {
        cy2Logger.error('Erreur création structure tableau:', error);
    }
}

/**
 * Version CY2 de generateTableHeaders - Modernisée avec structure assurée
 */
function generateTableHeaders() {
    if (!window.cy2StateManager) {
        cy2Logger.error('generateTableHeaders CY2: StateManager non disponible');
        return;
    }
    
    try {
        const columns = window.cy2StateManager.getState('columns') || [];
        
        if (columns.length === 0) {
            cy2Logger.warn('generateTableHeaders CY2: Aucune colonne définie');
            return;
        }
        
        cy2Logger.log(`🏗️ CY2 generateTableHeaders - Génération ${columns.length} colonnes`);
        
        // NOUVEAU: Sélecteurs simplifiés car structure assurée
        const headerContainer = document.querySelector('#cy2-table-head') || 
                               document.querySelector('thead') || 
                               document.querySelector('table thead');
        
        if (!headerContainer) {
            cy2Logger.error('generateTableHeaders CY2: Container en-têtes toujours non trouvé');
            return;
        }
        
        // Générer les en-têtes avec améliorations CY2
        let headersHtml = '<tr class="cy2-enhanced-header">';
        
        columns.forEach((col, index) => {
            if (col.visible) {
                const sortClass = getSortClass(col.key);
                const headerClass = `cy2-header-cell ${col.fixed ? 'fixed-column' : ''}`;
                
                headersHtml += `
                    <th class="${headerClass}" 
                        data-column="${col.key}" 
                        data-sortable="true"
                        onclick="cy2SortColumn('${col.key}')"
                        title="Cliquer pour trier par ${col.title}">
                        <div class="cy2-header-content">
                            <span class="header-title">${col.title}</span>
                            <span class="sort-indicator ${sortClass}">
                                <span class="sort-arrow">↕️</span>
                            </span>
                        </div>
                    </th>
                `;
            }
        });
        
        headersHtml += '</tr>';
        
        // Injecter les en-têtes
        headerContainer.innerHTML = headersHtml;
        
        // Ajouter les classes CSS CY2
        headerContainer.classList.add('cy2-enhanced-table');
        
        cy2Logger.success('🏗️ CY2 generateTableHeaders - En-têtes générées avec succès');
        
    } catch (error) {
        cy2Logger.error('Erreur generateTableHeaders CY2:', error);
    }
}

/**
 * Rendu des lignes du tableau - Version CY2 modernisée avec structure assurée
 */
function renderTableRows(annonces, columns, constants) {
    try {
        // NOUVEAU: Sélecteurs simplifiés car structure assurée
        const tableBody = document.querySelector('#cy2-table-body') || 
                         document.querySelector('tbody') || 
                         document.querySelector('table tbody');
        
        if (!tableBody) {
            cy2Logger.error('renderTableRows CY2: Container corps toujours non trouvé');
            return;
        }
        
        cy2Logger.log(`🎨 CY2 renderTableRows - Rendu de ${annonces.length} lignes`);
        
        let rowsHtml = '';
        
        annonces.forEach((item, index) => {
            const rowClass = getRowClass(item, index);
            const rowId = `cy2-row-${index}`;
            
            rowsHtml += `<tr class="${rowClass}" id="${rowId}" data-index="${index}">`;
            
            columns.forEach(col => {
                if (col.visible) {
                    const cellContent = renderSpecialCell(col, item, constants, index);
                    const cellClass = `cy2-enhanced-cell cell-${col.key}`;
                    
                    rowsHtml += `<td class="${cellClass}" data-column="${col.key}">${cellContent}</td>`;
                }
            });
            
            rowsHtml += '</tr>';
        });
        
        // Injecter les lignes avec animation
        tableBody.innerHTML = rowsHtml;
        
        // Ajouter les améliorations CSS CY2
        tableBody.classList.add('cy2-enhanced-body');
        
        // Animation d'apparition
        const rows = tableBody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            row.style.animationDelay = `${index * 10}ms`;
            row.classList.add('cy2-fade-in');
        });
        
        cy2Logger.success(`🎨 CY2 renderTableRows - ${annonces.length} lignes rendues avec animations`);
        
    } catch (error) {
        cy2Logger.error('Erreur renderTableRows CY2:', error);
    }
}

/**
 * Rendu d'une cellule spéciale - Version CY2 OPTIMISÉE
 */
function renderSpecialCell(col, item, constants, index) {
    try {
        // CORRECTION : Extraire les vraies données de l'objet wrapper
        let actualData = item;
        
        // Si l'item a une seule propriété qui est un chemin de fichier, extraire les données
        const itemKeys = Object.keys(item);
        if (itemKeys.length === 1 && itemKeys[0].includes('.data.json')) {
            actualData = item[itemKeys[0]];
            
            // DEBUG uniquement pour la première ligne ET si mode debug activé
            if (index === 0 && window.CY2_CONFIG?.DEBUG) {
                cy2Logger.log('🔍 DEBUG: Données extraites du wrapper:', {
                    wrapperKey: itemKeys[0],
                    actualData: actualData,
                    actualDataKeys: Object.keys(actualData)
                });
            }
        }
        
        // NOUVEAU: Essayer plusieurs façons d'obtenir la valeur depuis les vraies données
        let value = actualData[col.key] || 
                   actualData[col.title] || 
                   actualData[col.title?.toLowerCase()] ||
                   actualData[col.key?.toLowerCase()] ||
                   '';
        
        // NOUVEAU: Si toujours vide, chercher dans toutes les propriétés des vraies données
        if (!value && value !== 0) {
            const dataKeys = Object.keys(actualData);
            const possibleKey = dataKeys.find(key => 
                key.toLowerCase().includes(col.key?.toLowerCase() || '') ||
                key.toLowerCase().includes(col.title?.toLowerCase() || '') ||
                col.key?.toLowerCase().includes(key.toLowerCase()) ||
                col.title?.toLowerCase().includes(key.toLowerCase())
            );
            
            if (possibleKey) {
                value = actualData[possibleKey];
                // DEBUG uniquement si mode debug activé
                if (index === 0 && window.CY2_CONFIG?.DEBUG) {
                    cy2Logger.log(`🔍 Mapping trouvé: ${col.key} → ${possibleKey} = ${value}`);
                }
            }
        }
        
        // Debug pour les premières lignes UNIQUEMENT si mode debug activé
        if (index < 3 && window.CY2_CONFIG?.DEBUG) {
            cy2Logger.log(`🔍 Rendu cellule ${col.title} (${col.key}): "${value}"`);
        }
        
        // Cellules spéciales selon le type
        switch (col.type) {
            case 'date':
                return renderDateCell(value);
            case 'link':
                return renderLinkCell(value, actualData);
            case 'status':
                return renderStatusCell(value);
            case 'number':
                return renderNumberCell(value);
            case 'button':
                return renderButtonCell(col, actualData, index);
            default:
                return renderTextCell(value, col);
        }
        
    } catch (error) {
        cy2Logger.error(`Erreur renderSpecialCell pour ${col.key}:`, error);
        return `<span class="cy2-error">Erreur: ${error.message}</span>`;
    }
}

// ==========================================
// RENDUS SPÉCIALISÉS CY2
// ==========================================

function renderDateCell(value) {
    if (!value) return '<span class="cy2-empty">—</span>';
    
    try {
        const date = new Date(value);
        const formatted = date.toLocaleDateString('fr-FR');
        return `<span class="cy2-date" title="${value}">${formatted}</span>`;
    } catch {
        return `<span class="cy2-text">${value}</span>`;
    }
}

function renderLinkCell(value, item) {
    if (!value) return '<span class="cy2-empty">—</span>';
    
    return `<a href="${value}" class="cy2-link" target="_blank" title="Ouvrir ${value}">
        📎 ${value.length > 30 ? value.substring(0, 30) + '...' : value}
    </a>`;
}

function renderStatusCell(value) {
    if (!value) return '<span class="cy2-empty">—</span>';
    
    const statusClass = `cy2-status status-${value.toLowerCase().replace(/\s+/g, '-')}`;
    return `<span class="${statusClass}">${value}</span>`;
}

function renderNumberCell(value) {
    if (!value && value !== 0) return '<span class="cy2-empty">—</span>';
    
    const formatted = typeof value === 'number' ? value.toLocaleString('fr-FR') : value;
    return `<span class="cy2-number">${formatted}</span>`;
}

function renderButtonCell(col, item, index) {
    const buttonAction = col.action || 'defaultAction';
    const buttonText = col.buttonText || 'Action';
    
    return `<button class="cy2-action-btn" 
                    onclick="cy2CellAction('${buttonAction}', ${index}, '${col.key}')"
                    title="${col.tooltip || buttonText}">
        ${buttonText}
    </button>`;
}

function renderTextCell(value, col) {
    if (!value && value !== 0) return '<span class="cy2-empty">—</span>';
    
    // Limiter la longueur si spécifiée
    let displayValue = value;
    if (col.maxLength && value.length > col.maxLength) {
        displayValue = value.substring(0, col.maxLength) + '...';
    }
    
    return `<span class="cy2-text" title="${value}">${displayValue}</span>`;
}

// ==========================================
// UTILITAIRES CY2
// ==========================================

function getRowClass(item, index) {
    let classes = ['cy2-enhanced-row'];
    
    // Alternance des couleurs
    classes.push(index % 2 === 0 ? 'even-row' : 'odd-row');
    
    // Classes conditionnelles selon les données
    if (item.etat) {
        classes.push(`etat-${item.etat.toLowerCase().replace(/\s+/g, '-')}`);
    }
    
    if (item.priorite) {
        classes.push(`priorite-${item.priorite.toLowerCase()}`);
    }
    
    return classes.join(' ');
}

function getSortClass(columnKey) {
    if (!window.cy2StateManager) return '';
    
    const sortColumn = window.cy2StateManager.getState('ui.sortColumn');
    const sortDirection = window.cy2StateManager.getState('ui.sortDirection');
    
    if (sortColumn === columnKey) {
        return sortDirection === 'asc' ? 'sorted-asc' : 'sorted-desc';
    }
    
    return 'unsorted';
}

/**
 * Tri par colonne - Version CY2
 */
function cy2SortColumn(columnKey) {
    if (!window.cy2StateManager) return;
    
    const currentSort = window.cy2StateManager.getState('ui.sortColumn');
    const currentDirection = window.cy2StateManager.getState('ui.sortDirection');
    
    let newDirection = 'asc';
    if (currentSort === columnKey && currentDirection === 'asc') {
        newDirection = 'desc';
    }
    
    // Mettre à jour l'état
    window.cy2StateManager.updateState({
        'ui.sortColumn': columnKey,
        'ui.sortDirection': newDirection
    });
    
    // Recharger le tableau avec le nouveau tri
    loadTableData();
    
    cy2Logger.log(`🔄 CY2 Tri: ${columnKey} ${newDirection}`);
}

/**
 * Action sur cellule - Version CY2
 */
function cy2CellAction(action, rowIndex, columnKey) {
    if (!window.cy2StateManager) return;
    
    const annonces = window.cy2StateManager.getState('annonces');
    const item = annonces[rowIndex];
    
    cy2Logger.log(`🎯 CY2 Action: ${action} sur ligne ${rowIndex}, colonne ${columnKey}`, item);
    
    // Déclencher un événement pour les actions
    const event = new CustomEvent('cy2-cell-action', {
        detail: { action, rowIndex, columnKey, item }
    });
    document.dispatchEvent(event);
}

// ==========================================
// EXPOSITION GLOBALE
// ==========================================

// Exposer les fonctions pour compatibilité
window.loadTableData = loadTableData;
window.generateTableHeaders = generateTableHeaders;
window.cy2SortColumn = cy2SortColumn;
window.cy2CellAction = cy2CellAction;

// Marquer le module comme chargé
if (window.cy2Logger) {
    cy2Logger.success('✅ CY2 All Dos All Rows - Module de rendu complet chargé !');
} else {
    console.log('✅ CY2 All Dos All Rows - Module de rendu complet chargé !');
}

/**
 * FONCTION DE DEBUG - À retirer après identification
 */
function debugDOMStructure() {
    cy2Logger.log('🔍 DEBUG: Structure DOM du tableau');
    
    // Chercher tous les tableaux
    const tables = document.querySelectorAll('table');
    cy2Logger.log(`Tables trouvées: ${tables.length}`);
    
    tables.forEach((table, index) => {
        cy2Logger.log(`Table ${index}:`, {
            id: table.id,
            classes: table.className,
            thead: !!table.querySelector('thead'),
            tbody: !!table.querySelector('tbody'),
            rows: table.querySelectorAll('tr').length
        });
    });
    
    // Chercher les containers potentiels
    const potentialContainers = [
        '#table-header', 'thead', '.table-headers', 'table thead',
        '#table-body', 'tbody', '.table-body', 'table tbody',
        '#tableContainer', '.tableContainer'
    ];
    
    potentialContainers.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
            cy2Logger.log(`✅ Trouvé: ${selector}`, element);
        }
    });
}

// Exposer temporairement pour debug
window.debugDOMStructure = debugDOMStructure;

/**
 * NOUVELLE FONCTION: Debug des données pour diagnostic
 */
function debugDataStructure() {
    if (!window.cy2StateManager) return;
    
    const annonces = window.cy2StateManager.getState('annonces') || [];
    const columns = window.cy2StateManager.getState('columns') || [];
    
    cy2Logger.log('🔍 DEBUG: Structure des données');
    cy2Logger.log(`Annonces: ${annonces.length}`);
    cy2Logger.log(`Colonnes: ${columns.length}`);
    
    if (annonces.length > 0) {
        cy2Logger.log('Premier élément annonces:', annonces[0]);
        cy2Logger.log('Clés disponibles:', Object.keys(annonces[0]));
    }
    
    if (columns.length > 0) {
        cy2Logger.log('Premières colonnes:', columns.slice(0, 5).map(col => ({
            key: col.key,
            title: col.title,
            visible: col.visible
        })));
    }
    
    // Test de correspondance
    if (annonces.length > 0 && columns.length > 0) {
        const item = annonces[0];
        const itemKeys = Object.keys(item);
        
        cy2Logger.log('🔍 Test correspondances colonnes/données:');
        columns.slice(0, 10).forEach(col => {
            if (col.visible) {
                const directMatch = item[col.key];
                const titleMatch = item[col.title];
                cy2Logger.log(`${col.title} (${col.key}):`, {
                    directMatch: directMatch ? '✅' : '❌',
                    titleMatch: titleMatch ? '✅' : '❌',
                    value: directMatch || titleMatch || 'NON TROUVÉ'
                });
            }
        });
    }
}

// Exposer pour debug
window.debugDataStructure = debugDataStructure;

/**
 * DEBUG AMÉLIORÉ - Analyser la vraie structure
 */
function debugRealDataStructure() {
    cy2Logger.log('🔍 === DEBUG STRUCTURE RÉELLE ===');
    
    const annonces = window.cy2StateManager.getState('annonces') || [];
    const columns = window.cy2StateManager.getState('columns') || [];
    
    if (annonces.length > 0) {
        const firstItem = annonces[0];
        const itemKeys = Object.keys(firstItem);
        
        cy2Logger.log('📋 Premier item wrapper:', firstItem);
        cy2Logger.log('📋 Clés wrapper:', itemKeys);
        
        // Extraire les vraies données
        if (itemKeys.length === 1 && itemKeys[0].includes('.data.json')) {
            const realData = firstItem[itemKeys[0]];
            cy2Logger.log('📋 VRAIES DONNÉES extraites:', realData);
            cy2Logger.log('📋 Clés des vraies données:', Object.keys(realData));
            
            // Analyser chaque propriété des vraies données
            Object.entries(realData).forEach(([key, value]) => {
                cy2Logger.log(`   ${key}: ${typeof value} = ${value}`);
            });
            
            // Test de correspondance avec les vraies données
            cy2Logger.log('🔍 === TEST CORRESPONDANCES RÉELLES ===');
            columns.slice(0, 10).forEach(col => {
                if (col.visible) {
                    const tests = {
                        'col.key directe': realData[col.key],
                        'col.title directe': realData[col.title],
                        'col.key minuscule': realData[col.key?.toLowerCase()],
                        'col.title minuscule': realData[col.title?.toLowerCase()]
                    };
                    
                    cy2Logger.log(`📋 ${col.title} (${col.key}):`, tests);
                    
                    // Correspondances approximatives dans les vraies données
                    const realDataKeys = Object.keys(realData);
                    const fuzzyMatches = realDataKeys.filter(key => 
                        key.toLowerCase().includes(col.key?.toLowerCase() || '') ||
                        key.toLowerCase().includes(col.title?.toLowerCase() || '') ||
                        col.key?.toLowerCase().includes(key.toLowerCase()) ||
                        col.title?.toLowerCase().includes(key.toLowerCase())
                    );
                    
                    if (fuzzyMatches.length > 0) {
                        cy2Logger.log(`   🎯 Correspondances possibles:`, fuzzyMatches.map(k => `${k}=${realData[k]}`));
                    }
                }
            });
        }
    }
}

// Exposer la fonction
window.debugRealDataStructure = debugRealDataStructure;