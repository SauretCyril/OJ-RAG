// ...existing code...

async function selectRep() {
    const formHtml = `
        <dialog id="directoryForm" class="directory-form">
            <form method="dialog">
                <h2>Sélectionner une autre racine</h2>
                <div class="button-group" id="directoryButtons">
                    <!-- Les boutons pour configurer les répertoires seront ajoutés ici -->
                </div>
                <div class="form-group">
                    <label for="directoryPath">Répertoire:</label>
                    <input type="text" id="directoryPath" class="rich-text-field">
                </div>
                <div class="button-group">
                    <button type="button" onclick="submitDirectory()">Enregistrer</button>
                    <button type="button" onclick="closeDirectoryForm()">Fermer</button>
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

    // Ajouter les boutons pour configurer les répertoires
    const directories = [
        { path: 'G:/Actions-4a_new', label: 'Annonces' },
        { path: 'G:/Actions-5-reseaux', label: 'Reseaux' },
        { path: 'G:/Actions-6-profiles', label: 'Profiles' },
        { path: 'G:/Actions-7-Publications', label: 'Publications' },
        { path: 'G:/Actions-8-Entretiens', label: 'Entretiens' },
        { path: 'G:/Actions-9-portails', label: 'Portails' },
        { path: 'G:/Actions-10-Perso', label: 'Perso' },
        { path: '', label: 'Répertoire 6' },
        { path: '', label: 'Répertoire 7' },
        { path: '', label: 'Répertoire 8' },
        { path: '', label: 'Répertoire 9' },
        { path: '', label: 'Répertoire 10' }
    ];
    const directoryButtonsContainer = document.getElementById('directoryButtons');
    directories.forEach((directory, index) => {
        if (directory.path !== "") {
            const button = document.createElement('button');
            button.type = 'tab-button';
            button.id = `directoryButton${index + 1}`;
            button.textContent = directory.label;

            button.addEventListener('click', () => {
                OpenSubdirectory(directory.path);
            });

            directoryButtonsContainer.appendChild(button);
        }
    });

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
    // justify-content: space-between;
    //z-index: 1000;
    style6.textContent = `
        .directory-form {
            width: 50%;
            min-width: 50%;
            height: 40%;
            min-height: 40%;
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
       
    `;
    document.head.appendChild(style6);
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