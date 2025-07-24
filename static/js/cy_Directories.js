// ...existing code...

// Variable pour suivre la ligne sélectionnée actuellement
let selectedDirectoryRow = null;

// Fonction pour ouvrir une boîte de dialogue de sélection de répertoire
async function selectDirectoryDialog(pathInput) {
    try {
        // Essayer d'utiliser l'API moderne showDirectoryPicker si disponible
        if ('showDirectoryPicker' in window) {
            const directoryHandle = await window.showDirectoryPicker();
            const path = directoryHandle.name;
            
            // Récupérer le chemin complet en parcourant la hiérarchie des handles
            let pathParts = [path];
            let currentHandle = directoryHandle;
            
            try {
                while (currentHandle.parent) {
                    currentHandle = await currentHandle.parent;
                    if (currentHandle.name) {
                        pathParts.unshift(currentHandle.name);
                    }
                }
            } catch (error) {
                console.warn("Impossible de récupérer le chemin complet:", error);
            }
            
            // Construire le chemin avec des slashes/backslashes selon l'OS
            const fullPath = pathParts.join('\\');
            pathInput.value = fullPath;
        } else {
            // Solution de secours: Créer un input de type file masqué avec l'attribut webkitdirectory
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.style.display = 'none';
            fileInput.setAttribute('webkitdirectory', '');
            fileInput.setAttribute('directory', '');
            
            document.body.appendChild(fileInput);
            
            // Ouvrir la boîte de dialogue de sélection de fichier
            fileInput.click();
            
            // Attendre que l'utilisateur sélectionne un dossier
            fileInput.onchange = function() {
                if (this.files && this.files.length > 0) {
                    // Extraire le chemin du dossier sélectionné
                    const filePath = this.files[0].webkitRelativePath || this.files[0].path;
                    const folderPath = filePath.split('/')[0];
                    
                    pathInput.value = folderPath;
                }
                
                // Nettoyer
                document.body.removeChild(fileInput);
            };
        }
    } catch (error) {
        console.error("Erreur lors de la sélection du répertoire:", error);
        alert("Impossible de sélectionner le répertoire: " + error.message);
    }
}

async function selectRep() {
    const currentDossier = await get_cookie('current_dossier') || 'Non défini';
    
    const formHtml = `
        <dialog id="directoryForm" class="directory-form">
            <form method="dialog">
                <div class="current-directory-header">
                    <h3>Répertoire courant :</h3>
                    <div class="current-directory-path">${currentDossier}</div>
                </div>
                <h2>Gestion des répertoires</h2>
                <div class="directories-container">
                    <table id="directoriesTable" class="directories-table">
                        <thead>
                            <tr>
                                <th class="action-column">Sel.</th>
                                <th>Nom</th>
                                <th>Chemin</th>
                                <th class="action-column">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="directoriesTableBody">
                            <!-- Les lignes des répertoires seront ajoutées ici dynamiquement -->
                        </tbody>
                    </table>
                </div>
                <div class="button-group">
                    <button type="button" onclick="addNewDirectoryRow()" title="Ajouter un répertoire">➕</button>
                    <button type="button" onclick="saveAllDirectories()" title="Enregistrer les modifications">💾</button>
                    <button type="button" onclick="closeDirectoryForm()" title="Fermer">❌</button>
                </div>
                <div class="form-group" style="display: none;">
                    <label for="directoryPath">Répertoire actuel:</label>
                    <input type="text" id="directoryPath" class="rich-text-field">
                </div>
            </form>
        </dialog>
    `;

    // Supprimer le formulaire existant s'il est déjà présent
    const existingForm = document.getElementById('directoryForm');
    if (existingForm) {
        existingForm.remove();
    }

    // Ajouter le formulaire au DOM
    document.body.insertAdjacentHTML('beforeend', formHtml);

    // Charger les répertoires depuis le serveur
    await loadDirectories();

    // Pré-remplir le champ input avec la valeur actuelle du cookie
    const inputField = document.getElementById('directoryPath');
    if (inputField) {
        const curdossier = await get_cookie('current_dossier');
        if (curdossier) {
            inputField.value = curdossier;
        }
    }

    // Afficher le formulaire
    const form = document.getElementById('directoryForm');
    form.showModal();

    // Ajouter les styles pour le formulaire
    let style6 = document.createElement('style');
    style6.textContent = `
        .directory-form {
            width: 60%;
            min-width: 60%;
            height: 60%;
            min-height: 60%;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }
        .current-directory-header {
            background-color: #f0f8ff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            border: 1px solid #b8daff;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }
        .current-directory-header h3 {
            margin: 0;
            margin-right: 10px;
            color: #0056b3;
        }
        .current-directory-path {
            font-family: monospace;
            font-weight: bold;
            color: #003366;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
        }
        .directory-form .form-group {
            margin-bottom: 15px;
        }
        .directory-form .form-group label {
            display: block;
            margin-bottom: 5px;
        }
        .directory-form .form-group input {
            width: 100%;
            padding: 8px;
            box-sizing: border-box;
        }
        .directory-form .button-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: space-between;
            margin-top: 15px;
        }
        .directory-form .button-group button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background-color: #007bff;
            color: white;
        }
        .directory-form .button-group button:hover {
            background-color: #0056b3;
        }
        .directories-container {
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .directories-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        .directories-table th, .directories-table td {
            padding: 10px 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .directories-table th {
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }
        .action-column {
            width: 70px;
            min-width: 70px;
        }
        .directories-table input {
            width: 100%;
            padding: 5px;
            box-sizing: border-box;
        }
        .selected-row {
            background-color: #042c52ff;
        }
        .action-buttons {
            display: flex;
            gap: 5px;
            width: 70px;
            min-width: 70px;
            justify-content: space-between;
        }
        .browse-btn {
            background-color: #6c757d;
            color: white;
            width: 30px;
            padding: 4px;
            margin-right: 2px;
        }
        .browse-btn:hover {
            background-color: #5a6268;
        }
        .select-btn {
            background-color: #28a745;
            color: white;
            width: 30px;
            min-width: 30px;
            padding: 4px;
            height: 30px;
            min-height: 30px;
        }
        .select-btn:hover {
            background-color: #218838;
        }
        .remove-btn {
            background-color: #dc3545;
            color: white;
            width: 30px;
            min-width: 30px;
            padding: 4px;
            height: 30px;
            min-height: 30px;
        }
        .remove-btn:hover {
            background-color: #c82333;
        }
        tr {
            height: 40px;
            min-height: 40px;
        }
    `;
    document.head.appendChild(style6);
}

// Charger les répertoires depuis le serveur
async function loadDirectories() {
    try {
        const response = await fetch('/get_directories');
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des répertoires');
        }
        
        let directories = await response.json();
        
        // Si aucun répertoire n'est défini, utiliser les valeurs par défaut
        if (!directories || directories.length === 0) {
            directories = [
                { label: 'Annonces', path: 'G:/Actions-4a_new' },
                { label: 'Reseaux', path: 'G:/Actions-5-reseaux' },
                { label: 'Profiles', path: 'G:/Actions-6-profiles' },
                { label: 'Publications', path: 'G:/Actions-7-Publications' },
                { label: 'Entretiens', path: 'G:/Actions-8-Entretiens' },
                { label: 'Portails', path: 'G:/Actions-9-portails' },
                { label: 'Perso', path: 'G:/Actions-10-Perso' }
            ];
        }
        
        // Ajouter les répertoires au tableau
        const tableBody = document.getElementById('directoriesTableBody');
        tableBody.innerHTML = '';
        
        directories.forEach((dir, index) => {
            addDirectoryToTable(dir.label, dir.path);
        });
        
    } catch (error) {
        console.error('Erreur lors du chargement des répertoires:', error);
        alert('Erreur lors du chargement des répertoires. Veuillez réessayer plus tard.');
    }
}

// Ajouter une ligne de répertoire au tableau
function addDirectoryToTable(label = '', path = '') {
    const tableBody = document.getElementById('directoriesTableBody');
    const row = document.createElement('tr');
    
  // Bouton Select avec icône
  const selectButton = document.createElement('button');
  selectButton.innerHTML = '👆'; // Icône de dossier ouvert
  selectButton.title = 'Sélectionner ce répertoire';
  selectButton.className = 'select-btn';
  selectButton.addEventListener('click', (event) => {
      event.stopPropagation();
      OpenSubdirectory(pathInput.value);
  });
  
    // Cellule pour le nom
    const labelCell = document.createElement('td');
    const labelInput = document.createElement('input');
    labelInput.type = 'text';
    labelInput.value = label;
    labelInput.className = 'directory-label';
    labelCell.appendChild(labelInput);
    
    // Cellule pour le chemin
    const pathCell = document.createElement('td');
    const pathInput = document.createElement('input');
    pathInput.type = 'text';
    pathInput.value = path;
    pathInput.className = 'directory-path';
    pathCell.appendChild(pathInput);
    
    // Cellule pour les actions
    const actionsCell = document.createElement('td');
    actionsCell.className = 'action-buttons';
    actionsCell.style.visibility = 'hidden'; // Cacher par défaut
    
    // Bouton Browse avec icône de curseur
    const browseButton = document.createElement('button');
    browseButton.innerHTML = '📂'; // Icône de curseur/pointer
    browseButton.title = 'Parcourir les répertoires';
    browseButton.className = 'browse-btn';
    browseButton.addEventListener('click', (event) => {
        event.stopPropagation();
        selectDirectoryDialog(pathInput);
    });
    
  

    // Bouton Remove avec icône
    const removeButton = document.createElement('button');
    removeButton.innerHTML = '🗑️'; // Icône de corbeille
    removeButton.title = 'Supprimer ce répertoire';
    removeButton.className = 'remove-btn';
    removeButton.addEventListener('click', (event) => {
        event.stopPropagation();
        row.remove();
        // Si la ligne supprimée était sélectionnée, réinitialiser la sélection
        if (selectedDirectoryRow === row) {
            selectedDirectoryRow = null;
        }
    });
   
    actionsCell.appendChild(browseButton);
    actionsCell.appendChild(removeButton);
    
    // Ajouter les cellules à la ligne
    
    row.appendChild(selectButton);
    row.appendChild(labelCell);
    row.appendChild(pathCell);
    row.appendChild(actionsCell);
    
    // Ajouter un événement de clic pour sélectionner la ligne
    row.addEventListener('click', (event) => {
        // Ne pas déclencher si on clique sur un bouton
        if (event.target.tagName !== 'BUTTON') {
            selectDirectoryRow(row);
        }
    });
    
    // Ajouter la ligne au tableau
    tableBody.appendChild(row);
}

// Fonction pour sélectionner une ligne et afficher ses boutons d'action
function selectDirectoryRow(row) {
    // Désélectionner la ligne précédemment sélectionnée
    if (selectedDirectoryRow) {
        selectedDirectoryRow.classList.remove('selected-row');
        const prevActionsCell = selectedDirectoryRow.querySelector('.action-buttons');
        if (prevActionsCell) {
            prevActionsCell.style.visibility = 'hidden';
        }
    }
    
    // Sélectionner la nouvelle ligne
    row.classList.add('selected-row');
    const actionsCell = row.querySelector('.action-buttons');
    if (actionsCell) {
        actionsCell.style.visibility = 'visible';
    }
    
    // Mettre à jour la référence à la ligne sélectionnée
    selectedDirectoryRow = row;
}

// Ajouter une nouvelle ligne de répertoire
function addNewDirectoryRow() {
    addDirectoryToTable('', '');
}

// Sauvegarder tous les répertoires
async function saveAllDirectories() {
    const tableBody = document.getElementById('directoriesTableBody');
    const rows = tableBody.querySelectorAll('tr');
    
    const directories = [];
    
    rows.forEach(row => {
        const labelInput = row.querySelector('.directory-label');
        const pathInput = row.querySelector('.directory-path');
        
        if (labelInput && pathInput && pathInput.value.trim() !== '') {
            directories.push({
                label: labelInput.value.trim(),
                path: pathInput.value.trim()
            });
        }
    });
    
    try {
        const response = await fetch('/save_directories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(directories)
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la sauvegarde des répertoires');
        }
        
        const data = await response.json();
        
        if (data.message === 'done') {
            alert('Répertoires enregistrés avec succès.');
        } else {
            alert('Erreur lors de l\'enregistrement des répertoires: ' + (data.message || 'Erreur inconnue'));
        }
        
    } catch (error) {
        console.error('Erreur lors de la sauvegarde des répertoires:', error);
        alert('Erreur lors de la sauvegarde des répertoires. Veuillez réessayer plus tard.');
    }
}

function submitDirectory() {
    const directoryPath = document.getElementById('directoryPath').value;
    OpenSubdirectory(directoryPath);
}

function OpenSubdirectory(directoryPath) {
    
    if (directoryPath.trim() === '') {
        alert('Le répertoire ne peut pas être vide !!!');
        return;
    }

    fetch('/save_cookie', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'cookie_name': 'current_dossier' , 'cookie_value': directoryPath})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.message === "done") {
            //alert('Répertoire enregistré avec succès.');
            save_cookie('current_dossier', directoryPath);
            show_current_dossier();
            refresh();
           
        } else {
            alert('Err 4532 - lors de l\'enregistrement du répertoire: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error saving directory:', error);
        alert('Err 4523 lors de l\'enregistrement du répertoire.');
    });

    // Close form
    closeDirectoryForm();
    
}

async function closeDirectoryForm() {
    const form = document.getElementById('directoryForm');
    if (form) {
        form.close();
        form.remove(); // Ensure the form is removed from the DOM
        window.conf = conf_loadconf();
        await loadColumnsFromServer();
        refresh();
        // Vérifier si la fonction loadColumnsFromServer existe et si l'élément DOM nécessaire est présent
       /*  if (typeof loadColumnsFromServer === 'function') {
            try {
                // Vérifier si l'élément DOM requis pour les colonnes existe
                const columnsContainer = document.getElementById('columnsTableBody') || 
                                       document.getElementById('columns-container') || 
                                       document.querySelector('.columns-table');
                
                if (columnsContainer) {
                    await loadColumnsFromServer();
                } else {
                    console.warn('Container pour les colonnes non trouvé, skip loadColumnsFromServer');
                }
            } catch (error) {
                console.error('err005-Erreur lors du chargement des colonnes:', error);
                // Ne pas bloquer le refresh même si loadColumnsFromServer échoue
                console.warn('Continuing with refresh despite column loading error');
            }
        } else {
            console.warn('loadColumnsFromServer function not found, skipping column loading');
        } */
        
        // S'assurer que refresh existe avant de l'appeler
       /*  if (typeof refresh === 'function') {
            refresh();
        } else {
            console.warn('refresh function not found');
            // Solution alternative : recharger la page
            window.location.reload();
        } */
    }
}

// ...existing code...