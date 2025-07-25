/**
 * cy_columns_Edit.js
 * Script pour gérer l'édition des colonnes du système
 */

// Structure des colonnes globale
let columnsData = [];
let isColumnsChanged = false;
let autoSaveTimeout = null;
let selectedColumnKey = null;
let currentDirectoryPath = ""; // Pour stocker le chemin du répertoire courant

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    loadColumns();
    getDirectoryPath();
    
    // Gestionnaire pour le bouton d'ajout de colonne
    if (document.getElementById('addColumnButton')) {
        //document.getElementById('addColumnButton').style.display = 'block';
        document.getElementById('addColumnButton').addEventListener('click', () => {
        addNewColumn();
    });
    } 
    
});

/**
 * Récupère le chemin du répertoire courant
 */
async function getDirectoryPath() {
    try {
        const response = await fetch('/get_current_dir');
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        currentDirectoryPath = data.directory || "";
        
        // Afficher le chemin dans l'interface
        const dirElement = document.getElementById('directoryPath');
        if (dirElement) {
            dirElement.textContent = `Répertoire: ${currentDirectoryPath}`;
        }
    } catch (error) {
        console.error('Erreur lors de la récupération du répertoire:', error);
        document.getElementById('directoryPath').textContent = "Répertoire: Non disponible";
    }
}

/**
 * Charge les colonnes depuis le serveur
 */
async function loadColumns() {
    showStatusMessage('Chargement des colonnes...', 'info');
    console.log('dbg-lc000');
    try {
        const response = await fetch('/load_conf_cols');
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        console.log('dbg-lc001');
        const data = await response.json();
        
        if (data.error) {
            showStatusMessage(`Erreur: ${data.error}`, 'error');
            return;
        }
        console.log('dbg-lc002');
        // Si le serveur renvoie un tableau vide, utiliser window.columns comme valeur par défaut
        if (Array.isArray(data) && data.length === 0 && window.columns && Array.isArray(window.columns)) {
            console.log('dbg-lc003');
            columnsData = JSON.parse(JSON.stringify(window.columns));
            showStatusMessage('Colonnes par défaut chargées', 'info');
            saveColumns();
        } else {
            console.log('dbg-lc004');
            columnsData = Array.isArray(data) ? data : [];
            showStatusMessage('Colonnes chargées avec succès!', 'success');
        }
        console.log('dbg-lc005');
        renderColumnsTable();
    } catch (error) {
        console.error('err003-Erreur lors du chargement des colonnes:', error);
        
        if (window.columns && Array.isArray(window.columns)) {
            columnsData = JSON.parse(JSON.stringify(window.columns));
            renderColumnsTable();
            showStatusMessage('Utilisation des colonnes par défaut.', 'warning');
        } else {
            showStatusMessage('Erreur de chargement.', 'error');
        }
    }
}

/**
 * Sauvegarde les colonnes sur le serveur
 */
async function saveColumns() {
    showStatusMessage('Sauvegarde des colonnes...', 'info');
    
    try {
        const response = await fetch('/save_conf_cols', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(columnsData)
        });
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === "success") {
            showStatusMessage('Colonnes sauvegardées avec succès!', 'success');
            isColumnsChanged = false;
        } else {
            showStatusMessage(`Erreur: ${data.message || 'Échec de la sauvegarde'}`, 'error');
        }
    } catch (error) {
        console.error('Erreur lors de la sauvegarde des colonnes:', error);
        showStatusMessage('Erreur de sauvegarde.', 'error');
    }
}

/**
 * Ajoute une nouvelle colonne vide
 */
function addNewColumn() {
    const newColumn = {
        key: `column_${Date.now()}`,
        label: 'Nouvelle colonne',
        type: 'text',
        visible: true,
        sortable: true,
        order: columnsData.length
    };
    
    columnsData.push(newColumn);
    renderColumnsTable();
    selectColumn(newColumn.key);
    markColumnsChanged();
}

/**
 * Supprime une colonne par sa clé
 */
function deleteColumn(key, event) {
    if (event) {
        event.stopPropagation();
    }
    
    if (confirm('Êtes-vous sûr de vouloir supprimer cette colonne ?')) {
        const index = columnsData.findIndex(col => col.key === key);
        if (index !== -1) {
            columnsData.splice(index, 1);
            renderColumnsTable();
            
            if (selectedColumnKey === key) {
                hideColumnDetails();
            }
            
            markColumnsChanged();
        }
    }
}

/**
 * Met à jour une propriété d'une colonne
 */
function updateColumnProperty(key, property, value) {
    const column = columnsData.find(col => col.key === key);
    if (column) {
        if (property === 'visible' || property === 'sortable' || property === 'fixed') {
            column[property] = value === 'true' || value === true;
        } else {
            column[property] = value;
        }
        
        if (['key', 'label', 'title', 'type', 'visible', 'order'].includes(property)) {
            renderColumnsTable();
            selectColumn(key);
        }
        
        markColumnsChanged();
    }
}

/**
 * Signale que les colonnes ont changé et programme une sauvegarde automatique
 */
function markColumnsChanged() {
    isColumnsChanged = true;
    
    if (autoSaveTimeout) {
        clearTimeout(autoSaveTimeout);
    }
    
    autoSaveTimeout = setTimeout(() => {
        if (isColumnsChanged) {
            saveColumns();
        }
    }, 2000);
}

/**
 * Affiche le tableau des colonnes avec gestion d'erreur complète
 */
function renderColumnsTable() {
    console.log('dbg-rct000: Début de renderColumnsTable');
    
    try {
        // Vérifier l'existence de l'élément DOM
        const tableBody = document.getElementById('columnsTableBody');
        console.log('dbg-rct001: tableBody element:', tableBody);
        renderColumnsInElement(tableBody);
        /*  if (!tableBody) {
            console.error('err-rct001: Élément columnsTableBody non trouvé dans le DOM');
            
            // Chercher des éléments alternatifs
            const alternativeElement = document.getElementById('columns-container') || 
                                     document.querySelector('.columns-table tbody') ||
                                     document.querySelector('#columnsTable tbody');
            
            if (alternativeElement) {
                console.warn('warn-rct001: Utilisation d\'un élément alternatif:', alternativeElement.id || alternativeElement.className);
                alternativeElement.innerHTML = '';
                renderColumnsInElement(alternativeElement);
                return;
            } else {
                console.error('err-rct002: Aucun élément conteneur trouvé pour les colonnes');
                showStatusMessage('Erreur: Interface des colonnes non disponible', 'error');
                return;
            }
        } */
        
        // Vérifier les données des colonnes
        console.log('dbg-rct002: columnsData:', columnsData);
        
        if (!Array.isArray(columnsData)) {
            console.error('err-rct003: columnsData n\'est pas un tableau:', typeof columnsData);
            columnsData = [];
        }
        
        if (columnsData.length === 0) {
            console.warn('warn-rct002: Aucune colonne à afficher');
            tableBody.innerHTML = '<tr><td colspan="5" class="no-data">Aucune colonne configurée</td></tr>';
            return;
        }
        
        // Vider le tableau existant
        console.log('dbg-rct003: Vidage du tableau existant');
        tableBody.innerHTML = '';
        
        // Trier les colonnes par ordre
        console.log('dbg-rct004: Tri des colonnes');
        const sortedColumns = [...columnsData].sort((a, b) => {
            const orderA = a.order || 0;
            const orderB = b.order || 0;
            return orderA - orderB;
        });
        
        console.log('dbg-rct005: Colonnes triées:', sortedColumns.length);
        
        // Créer les lignes du tableau
        sortedColumns.forEach((column, index) => {
            try {
                console.log(`dbg-rct006-${index}: Création de la ligne pour la colonne:`, column.key);
                
                if (!column || typeof column !== 'object') {
                    console.error(`err-rct004-${index}: Colonne invalide:`, column);
                    return;
                }
                
                const row = document.createElement('tr');
                row.dataset.key = column.key || `column_${index}`;
                
                // Ajouter la classe selected si nécessaire
                if (column.key === selectedColumnKey) {
                    row.classList.add('selected');
                    console.log(`dbg-rct007-${index}: Ligne sélectionnée pour:`, column.key);
                }
                
                // Construire le contenu HTML de la ligne
                const cellContent = `
                    <td>${escapeHtml(column.key || '')}</td>
                    <td>${escapeHtml(column.label || column.title || '')}</td>
                    <td>${escapeHtml(column.type || 'text')}</td>
                    <td>${column.visible ? 'Oui' : 'Non'}</td>
                    <td>${column.order || 0}</td>
                `;
                
                row.innerHTML = cellContent;
                
                // Ajouter l'événement de clic
                row.addEventListener('click', () => {
                    console.log(`dbg-rct008: Clic sur la colonne:`, column.key);
                    selectColumn(column.key);
                });
                
                // Ajouter la ligne au tableau
                tableBody.appendChild(row);
                console.log(`dbg-rct009-${index}: Ligne ajoutée avec succès pour:`, column.key);
                
            } catch (rowError) {
                console.error(`err-rct005-${index}: Erreur lors de la création de la ligne:`, rowError);
                console.error(`err-rct005-${index}: Données de la colonne:`, column);
            }
        });
        
        console.log('dbg-rct010: renderColumnsTable terminé avec succès');
        
    } catch (error) {
        console.error('err-rct006: Erreur fatale dans renderColumnsTable:', error);
        console.error('err-rct006: Stack trace:', error.stack);
        
        // Afficher un message d'erreur à l'utilisateur
        showStatusMessage('Erreur lors de l\'affichage des colonnes', 'error');
        
        // Essayer de récupérer gracieusement
        try {
            const tableBody = document.getElementById('columnsTableBody');
            if (tableBody) {
                tableBody.innerHTML = '<tr><td colspan="5" class="error-message">Erreur lors de l\'affichage des colonnes</td></tr>';
            }
        } catch (recoveryError) {
            console.error('err-rct007: Impossible de récupérer après erreur:', recoveryError);
        }
    }
}

/**
 * Fonction utilitaire pour échapper le HTML et éviter les injections
 */
function escapeHtml(text) {
    if (typeof text !== 'string') {
        return String(text || '');
    }
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Fonction pour rendre les colonnes dans un élément alternatif
 */
function renderColumnsInElement(element) {
    console.log('dbg-rice000: Rendu dans élément alternatif');
    
    try {
        if (!Array.isArray(columnsData) || columnsData.length === 0) {
            element.innerHTML = '<p class="no-data">Aucune colonne configurée</p>';
            return;
        }
        
        const sortedColumns = [...columnsData].sort((a, b) => (a.order || 0) - (b.order || 0));
        
        let html = '<table class="columns-table"><thead><tr>' +
                   '<th>Clé</th><th>Libellé</th><th>Type</th><th>Visible</th><th>Ordre</th>' +
                   '</tr></thead><tbody>';
        
        sortedColumns.forEach(column => {
            const isSelected = column.key === selectedColumnKey ? 'class="selected"' : '';
            html += `<tr ${isSelected} data-key="${escapeHtml(column.key)}" onclick="selectColumn('${escapeHtml(column.key)}')">
                        <td>${escapeHtml(column.key || '')}</td>
                        <td>${escapeHtml(column.label || column.title || '')}</td>
                        <td>${escapeHtml(column.type || 'text')}</td>
                        <td>${column.visible ? 'Oui' : 'Non'}</td>
                        <td>${column.order || 0}</td>
                     </tr>`;
        });
        
        html += '</tbody></table>';
        element.innerHTML = html;
        
        console.log('dbg-rice001: Rendu alternatif terminé avec succès');
        
    } catch (error) {
        console.error('err-rice001: Erreur dans renderColumnsInElement:', error);
        //element.innerHTML = '<p class="error-message">Erreur lors de l\'affichage des colonnes</p>';
    }
}

/**
 * Affiche les détails d'une colonne
 */
function showColumnDetails(key) {
    const column = columnsData.find(col => col.key === key);
    if (!column) return;
    
    const detailCard = document.getElementById('columnDetailCard');
    const noSelectionMessage = document.getElementById('noSelectionMessage');
    
    detailCard.style.display = 'block';
    noSelectionMessage.style.display = 'none';
    
    detailCard.innerHTML = `
        <h3>${column.label || column.title || 'Sans titre'}
            <button class="delete-button" onclick="deleteColumn('${column.key}', event)">Supprimer</button>
        </h3>
        
        <div class="form-group">
            <label for="key_${column.key}">Clé</label>
            <input type="text" id="key_${column.key}" value="${column.key}" 
                   onchange="updateColumnProperty('${column.key}', 'key', this.value)">
        </div>
        
        <div class="form-group">
            <label for="label_${column.key}">Libellé</label>
            <input type="text" id="label_${column.key}" value="${column.label || column.title || ''}" 
                   onchange="updateColumnProperty('${column.key}', 'label', this.value)">
        </div>
        
        <div class="form-group">
            <label for="type_${column.key}">Type</label>
            <select id="type_${column.key}" 
                    onchange="updateColumnProperty('${column.key}', 'type', this.value)">
                ${generateTypeOptions(column.type)}
            </select>
        </div>
        
        <div class="form-group">
            <label for="order_${column.key}">Ordre</label>
            <input type="number" id="order_${column.key}" value="${column.order || 0}" 
                   onchange="updateColumnProperty('${column.key}', 'order', parseInt(this.value))">
        </div>
        
        <div class="form-group">
            <label for="width_${column.key}">Largeur</label>
            <input type="text" id="width_${column.key}" value="${column.width || ''}" 
                   onchange="updateColumnProperty('${column.key}', 'width', this.value)">
        </div>
        
        <div class="form-group">
            <label class="checkbox-label">
                <input type="checkbox" id="visible_${column.key}" 
                       ${column.visible ? 'checked' : ''} 
                       onchange="updateColumnProperty('${column.key}', 'visible', this.checked)">
                Visible
            </label>
        </div>
        
        <div class="form-group">
            <label class="checkbox-label">
                <input type="checkbox" id="sortable_${column.key}" 
                       ${column.sortable ? 'checked' : ''} 
                       onchange="updateColumnProperty('${column.key}', 'sortable', this.checked)">
                Triable
            </label>
        </div>
        
        <div class="form-group">
            <label class="checkbox-label">
                <input type="checkbox" id="fixed_${column.key}" 
                       ${column.fixed ? 'checked' : ''} 
                       onchange="updateColumnProperty('${column.key}', 'fixed', this.checked)">
                Fixe (non modifiable)
            </label>
        </div>
    `;
}

/**
 * Cache les détails de la colonne
 */
function hideColumnDetails() {
    const detailCard = document.getElementById('columnDetailCard');
    const noSelectionMessage = document.getElementById('noSelectionMessage');
    
    detailCard.style.display = 'none';
    noSelectionMessage.style.display = 'block';
    
    selectedColumnKey = null;
}

/**
 * Génère les options HTML pour le menu déroulant des types
 */
function generateTypeOptions(selectedType) {
    const types = ['text', 'number', 'date', 'boolean', 'link', 'image', 'actions'];
    
    return types.map(type => 
        `<option value="${type}" ${type === selectedType ? 'selected' : ''}>${type}</option>`
    ).join('');
}

/**
 * Affiche un message de statut à l'utilisateur
 */
function showStatusMessage(message, type = 'info') {
    const statusElement = document.getElementById('statusMessage');
    if (statusElement ) {   
        
    
        statusElement.textContent = message;
        statusElement.className = `status-message ${type}`;
        statusElement.style.display = 'block';
        
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 5000);
    }
}

/**
 * Sélectionne une colonne et affiche ses détails
 */
function selectColumn(key) {
    selectedColumnKey = key;
    showColumnDetails(key);
}