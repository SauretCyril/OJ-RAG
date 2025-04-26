/**
 * Module de gestion du tableau
 * Gère toutes les opérations liées au tableau d'annonces
 */

/**
 * Cache pour les éléments DOM fréquemment utilisés
 */
const DOMCache = {
    tableBody: null,
    tableHeader: null,
    tableFilter: null,
    
    /**
     * Initialise le cache des éléments DOM
     */
    init() {
        this.tableBody = document.getElementById('table-body');
        this.tableHeader = document.querySelector('table thead tr:first-child');
        this.tableFilter = document.querySelector('table thead tr:last-child');
    }
};

/**
 * Gestionnaire du tableau
 */
const TableManager = {
    /**
     * Initialise le gestionnaire du tableau
     */
    init() {
        DOMCache.init();
        this.attachEvents();
    },
    
    /**
     * Attache les événements nécessaires
     */
    attachEvents() {
        // S'abonner aux changements d'état des annonces
        subscribeToState('annonces', () => this.renderTable());
        
        // S'abonner aux changements d'état des colonnes
        subscribeToState('columns', () => {
            this.renderTableHeader();
            this.renderTableFilters();
            this.renderTable();
        });
        
        // S'abonner aux changements d'onglet actif
        subscribeToState('tabActive', () => {
            this.loadAnnonces();
            loadFilterValues(getState('tabActive'));
        });
    },
    
    /**
     * Charge les annonces
     * @returns {Promise} - Promise contenant le résultat de l'opération
     */
    async loadAnnonces() {
        showLoadingOverlay('Chargement des données...');
        
        try {
            const excluded = document.getElementById('Excluded').value;
            const tabActive = getState('tabActive');
            
            const data = await ApiClient.annonces.read({ 
                excluded: excluded,
                tabActive: tabActive 
            });
            
            if (data && data.annonces) {
                setState('annonces', data.annonces);
                console.log(`${data.annonces.length} annonces chargées`);
            }
            
            return data;
        } catch (error) {
            console.error('Erreur lors du chargement des annonces:', error);
            throw error;
        } finally {
            hideLoadingOverlay();
        }
    },
    
    /**
     * Affiche le tableau d'annonces
     */
    renderTable() {
        const annonces = getState('annonces');
        const columns = getState('columns');
        const tableBody = DOMCache.tableBody;
        
        // Vider le tableau
        tableBody.innerHTML = '';
        
        if (!annonces || annonces.length === 0) {
            const emptyRow = document.createElement('tr');
            const emptyCell = document.createElement('td');
            emptyCell.textContent = 'Aucune annonce disponible';
            emptyCell.colSpan = columns.filter(col => col.visible).length;
            emptyRow.appendChild(emptyCell);
            tableBody.appendChild(emptyRow);
            return;
        }
        
        // Créer les lignes pour chaque annonce
        annonces.forEach(annonceObj => {
            const id = Object.keys(annonceObj)[0];
            const annonce = annonceObj[id];
            
            const row = document.createElement('tr');
            row.dataset.id = id;
            
            // Ajouter les cellules correspondant aux colonnes
            columns.forEach(column => {
                if (column.visible) {
                    const cell = this.createTableCell(column, annonce);
                    row.appendChild(cell);
                }
            });
            
            // Ajouter des écouteurs d'événements
            row.addEventListener('contextmenu', this.handleContextMenu);
            row.addEventListener('click', () => setState('currentRow', id));
            
            tableBody.appendChild(row);
        });
    },
    
    /**
     * Crée une cellule pour le tableau
     * @param {Object} column - Définition de la colonne
     * @param {Object} annonce - Données de l'annonce
     * @returns {HTMLElement} - Cellule du tableau
     */
    createTableCell(column, annonce) {
        const cell = document.createElement('td');
        cell.dataset.column = column.key;
        
        // Appliquer la classe si définie
        if (column.class) {
            cell.classList.add(column.class);
        }
        
        // Appliquer les styles si définis
        if (column.style) {
            Object.assign(cell.style, column.style);
        }
        
        // Définir la largeur
        if (column.width) {
            cell.style.width = column.width;
        }
        
        // Appliquer la valeur
        let value = annonce[column.key] || '';
        
        // Gérer les types spéciaux
        if (column.key === 'categorie' && column.prefix) {
            cell.classList.add(column.prefix + (value || 'default'));
        }
        
        cell.textContent = value;
        
        // Ajouter l'événement si défini
        if (column.event && column.event === 'click') {
            cell.addEventListener('click', (e) => {
                e.stopPropagation(); // Éviter le déclenchement de l'événement sur la ligne
                
                if (typeof column.eventHandler === 'function') {
                    column.eventHandler(e, annonce);
                } else if (column.key === 'dossier') {
                    // Gestion spéciale pour le clic sur le dossier
                    handleDossierClick(annonce);
                }
            });
        }
        
        return cell;
    },
    
    /**
     * Affiche l'en-tête du tableau
     */
    renderTableHeader() {
        const columns = getState('columns');
        const tableHeader = DOMCache.tableHeader;
        
        // Vider l'en-tête
        tableHeader.innerHTML = '';
        
        // Créer les cellules d'en-tête
        columns.forEach(column => {
            if (column.visible) {
                const headerCell = document.createElement('th');
                headerCell.dataset.column = column.key;
                headerCell.textContent = column.title || column.key;
                
                // Ajouter un événement pour le tri
                headerCell.addEventListener('click', () => {
                    this.sortTable(column.key);
                });
                
                tableHeader.appendChild(headerCell);
            }
        });
    },
    
    /**
     * Affiche les filtres du tableau
     */
    renderTableFilters() {
        const columns = getState('columns');
        const tableFilter = DOMCache.tableFilter;
        
        // Vider les filtres
        tableFilter.innerHTML = '';
        
        // Créer les cellules de filtre
        columns.forEach(column => {
            if (column.visible) {
                const filterCell = document.createElement('th');
                
                // Créer le champ de filtre si applicable
                if (column.key !== 'dossier' && column.key !== 'description' && column.key !== 'Notes') {
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.setAttribute('data-filter', column.key);
                    input.addEventListener('input', () => this.filterTable());
                    filterCell.appendChild(input);
                }
                
                tableFilter.appendChild(filterCell);
            }
        });
    },
    
    /**
     * Gère l'événement de clic droit (menu contextuel)
     * @param {Event} event - Événement de clic
     */
    handleContextMenu(event) {
        event.preventDefault();
        
        const row = event.target.closest('tr');
        const id = row.dataset.id;
        
        // Mettre à jour la ligne courante
        setState('currentRow', id);
        
        // Afficher le menu contextuel
        const contextMenu = document.getElementById('contextMenu');
        contextMenu.style.display = 'block';
        contextMenu.style.left = event.pageX + 'px';
        contextMenu.style.top = event.pageY + 'px';
        
        // Cacher le menu au clic ailleurs
        document.addEventListener('click', function hideMenu() {
            contextMenu.style.display = 'none';
            document.removeEventListener('click', hideMenu);
        });
    },
    
    /**
     * Trie le tableau par une colonne
     * @param {string} key - Clé de la colonne à trier
     */
    sortTable(key) {
        const annonces = [...getState('annonces')];
        
        // Trier les annonces
        annonces.sort((a, b) => {
            const valA = Object.values(a)[0][key] || '';
            const valB = Object.values(b)[0][key] || '';
            
            // Trier par ordre alphabétique
            return valA.toString().localeCompare(valB.toString());
        });
        
        // Mettre à jour l'état
        setState('annonces', annonces);
    },
    
    /**
     * Filtre le tableau selon les valeurs des filtres
     */
    filterTable() {
        const inputs = document.querySelectorAll('input[data-filter]');
        const filters = {};
        
        // Collecter les valeurs des filtres
        inputs.forEach(input => {
            const filterKey = input.dataset.filter;
            const filterValue = input.value.toLowerCase();
            
            if (filterValue) {
                filters[filterKey] = filterValue;
            }
        });
        
        // Appliquer les filtres si nécessaire
        if (Object.keys(filters).length === 0) {
            // Si aucun filtre, recharger toutes les données
            this.loadAnnonces();
            return;
        }
        
        // Filtrer localement les données
        const allAnnonces = getState('annonces');
        const filteredAnnonces = allAnnonces.filter(annonceObj => {
            const annonce = Object.values(annonceObj)[0];
            
            return Object.entries(filters).every(([key, filterValue]) => {
                const value = (annonce[key] || '').toString().toLowerCase();
                return value.includes(filterValue);
            });
        });
        
        // Mettre à jour l'état temporairement sans changer les données d'origine
        setState('annonces', filteredAnnonces);
    }
};

// Sauvegarde des filtres
function saveFilterValues() {
    const inputs = document.querySelectorAll('input[data-filter]');
    const filters = {};
    
    // Collecter les valeurs des filtres
    inputs.forEach(input => {
        const filterKey = input.dataset.filter;
        const filterValue = input.value;
        
        if (filterValue) {
            filters[filterKey] = filterValue;
        }
    });
    
    // Sauvegarder les filtres
    ApiClient.config.saveFilters(filters, getState('tabActive'));
}

// Mise à jour des valeurs des filtres
function updateFilterValues(filters) {
    if (!filters) return;
    
    // Mettre à jour les champs de filtre
    Object.entries(filters).forEach(([key, value]) => {
        const input = document.querySelector(`input[data-filter="${key}"]`);
        
        if (input) {
            input.value = value;
        }
    });
}

// Rechargement des données et rafraîchissement de l'interface
async function refresh() {
    await TableManager.loadAnnonces();
    TableManager.renderTable();
}

// Initialiser le gestionnaire de tableau
window.addEventListener('load', () => {
    TableManager.init();
});

// Exposer les fonctions et objets globalement
window.TableManager = TableManager;
window.refresh = refresh;
window.updateFilterValues = updateFilterValues;
window.saveFilterValues = saveFilterValues;