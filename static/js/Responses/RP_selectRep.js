// ...existing code...

function selectRep() {
    const formHtml = `
        <dialog id="directoryForm" class="directory-form">
            <form method="dialog">
                <h2>Créer un nouveau dossier</h2>
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

    // Remove existing form if any
    const existingForm = document.getElementById('directoryForm');
    if (existingForm) {
        existingForm.remove();
    }

    // Add form to document
    document.body.insertAdjacentHTML('beforeend', formHtml);

    // Show form
    const form = document.getElementById('directoryForm');
    form.showModal();
   
    // Add styles for directoryForm
    let style6 = document.createElement('style');
    style6.textContent = `
        .directory-form {
            width: 50%;
            min-width: 50%;
            height: 30%;
            min-height: 30%;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            index: 1000;
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
            justify-content: space-between;
        }
        .directory-form .button-group button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .directory-form .button-group button:first-child {
            background-color: #4CAF50;
            color: white;
        }
        .directory-form .button-group button:last-child {
            background-color: #f44336;
            color: white;
        }
    `;
    document.head.appendChild(style6);
}

function submitDirectory() {
    const directoryPath = document.getElementById('directoryPath').value;
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
            alert('Répertoire enregistré avec succès.');
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

function closeDirectoryForm() {
    const form = document.getElementById('directoryForm');
    if (form) {
        form.close();
        form.remove(); // Ensure the form is removed from the DOM
    }
}

// ...existing code...