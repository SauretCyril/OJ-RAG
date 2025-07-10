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
    document.getElementById('addColumnButton').addEventListener('click', () => {
        addNewColumn();
    });
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
    
    try {
        const response = await fetch('/load_conf_cols');
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            showStatusMessage(`Erreur: ${data.error}`, 'error');
            return;
        }
        
        // Si le serveur renvoie un tableau vide, utiliser window.columns comme valeur par défaut
        if (Array.isArray(data) && data.length === 0 && window.columns && Array.isArray(window.columns)) {
            columnsData = JSON.parse(JSON.stringify(window.columns));
            showStatusMessage('Colonnes par défaut chargées', 'info');
            saveColumns();
        } else {
            columnsData = Array.isArray(data) ? data : [];
            showStatusMessage('Colonnes chargées avec succès!', 'success');
        }
        
        renderColumnsTable();
    } catch (error) {
        console.error('Erreur lors du chargement des colonnes:', error);
        
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
 * Affiche le tableau des colonnes
 */
function renderColumnsTable() {
    const tableBody = document.getElementById('columnsTableBody');
    tableBody.innerHTML = '';
    
    const sortedColumns = [...columnsData].sort((a, b) => (a.order || 0) - (b.order || 0));
    
    sortedColumns.forEach(column => {
        const row = document.createElement('tr');
        row.dataset.key = column.key;
        
        if (column.key === selectedColumnKey) {
            row.classList.add('selected');
        }
        
        row.innerHTML = `
            <td>${column.key}</td>
            <td>${column.label || column.title || ''}</td>
            <td>${column.type || 'text'}</td>
            <td>${column.visible ? 'Oui' : 'Non'}</td>
            <td>${column.order || 0}</td>
        `;
        
        row.addEventListener('click', () => selectColumn(column.key));
        
        tableBody.appendChild(row);
    });
}

/**
 * Sélectionne une colonne et affiche ses détails
 */
function selectColumn(key) {
    selectedColumnKey = key;
    
    const rows = document.querySelectorAll('#columnsTableBody tr');
    rows.forEach(row => {
        if (row.dataset.key === key) {
            row.classList.add('selected');
        } else {
            row.classList.remove('selected');
        }
    });
    
    showColumnDetails(key);
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
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
    statusElement.style.display = 'block';
    
    setTimeout(() => {
        statusElement.style.display = 'none';
    }, 5000);
}