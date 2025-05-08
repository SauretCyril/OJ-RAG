// ...existing code...

async function selectRep() {
    const formHtml = `
        <dialog id="directoryForm" class="directory-form">
            <form method="dialog">
                <h2>Gestion des répertoires</h2>
                <div class="directories-container">
                    <table id="directoriesTable" class="directories-table">
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Chemin</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="directoriesTableBody">
                            <!-- Les lignes des répertoires seront ajoutées ici dynamiquement -->
                        </tbody>
                    </table>
                </div>
                <div class="button-group">
                    <button type="button" onclick="addNewDirectoryRow()">Ajouter un répertoire</button>
                    <button type="button" onclick="saveAllDirectories()">Enregistrer les modifications</button>
                    <button type="button" onclick="closeDirectoryForm()">Fermer</button>
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
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .directories-table {
            width: 100%;
            border-collapse: collapse;
        }
        .directories-table th, .directories-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .directories-table th {
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }
        .directories-table input {
            width: 100%;
            padding: 5px;
            box-sizing: border-box;
        }
        .action-buttons {
            display: flex;
            gap: 5px;
        }
        .action-buttons button {
            padding: 5px 10px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        .select-btn {
            background-color: #28a745;
            color: white;
        }
        .remove-btn {
            background-color: #dc3545;
            color: white;
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
    
    // Bouton Select
    const selectButton = document.createElement('button');
    selectButton.textContent = 'Select';
    selectButton.className = 'select-btn';
    selectButton.addEventListener('click', () => {
        OpenSubdirectory(pathInput.value);
    });
    
    // Bouton Remove
    const removeButton = document.createElement('button');
    removeButton.textContent = 'Supprimer';
    removeButton.className = 'remove-btn';
    removeButton.addEventListener('click', () => {
        row.remove();
    });
    
    actionsCell.appendChild(selectButton);
    actionsCell.appendChild(removeButton);
    
    // Ajouter les cellules à la ligne
    row.appendChild(labelCell);
    row.appendChild(pathCell);
    row.appendChild(actionsCell);
    
    // Ajouter la ligne au tableau
    tableBody.appendChild(row);
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
    }
}

// ...existing code...