function open_CRQ() {
      // Call the function and wait for it to complete    ;
    fetch('/list-CRQ-files', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(fileList => {
        show_CRQ_Popup(fileList);
    })
    .catch(error => {
        console.error('Error fetching file list:', error);
        alert('Erreur lors de la récupération des fichiers.');
    }); 
} 
function show_CRQ_Popup(fileList) {
    //alert(fileList);
    
    const popupHtml = `
        <dialog id="CRQPopup" class="CRQ-popup">
            <form method="dialog">
                <h2>les instructions de classements</h2>
                <div id="CRQContentContainer">
                    <ul id="fileList">
                        ${fileList.map(file => `
                            <li onclick="selectFile(this)">
                                <strong>${file.name.replace(/\.[^/.]+$/, "")}</strong><br>
                                
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="button-group">
                    <button type="button" onclick="save_current_instruction()" id="saveButton" style="display: none;">Enregistrer</button>
                    <button type="button" onclick="editText()" id="editButton" style="display: none;">Edite</button>
                    <button type="button" onclick="closeCRQPopup()">Fermer</button>
                </div>
            </form>
        </dialog>
    `;
    // ...existing code...
    // Remove existing popup if any
    const existingPopup = document.getElementById('CRQPopup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Add popup to document
    document.body.insertAdjacentHTML('beforeend', popupHtml);

    // Show popup
    const popup = document.getElementById('CRQPopup');
    popup.showModal();
}

function selectFile(element) {
    const selectedElement = document.querySelector('.selected');
    if (selectedElement) {
        selectedElement.classList.remove('selected');
    }
    element.classList.add('selected');
    document.getElementById('saveButton').style.display = 'inline-block';
    document.getElementById('editButton').style.display = 'inline-block';
}

// la fonction EditText doit permettre de modifier le contenu du fichier selectionné
// il faut ouvrir une popup qui contient le contenu du fichier selectionné
// avec un bouton fermer et un bouton enregistrer
// le bouton enregistrer doit permettre de sauvegarder les modifications
function editText(file) {
    const selectedElement = document.querySelector('.selected');
   
    if (selectedElement) {
        const settingValue = selectedElement.querySelector('strong').innerText;
        fetch('/load-CRQ-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_name: settingValue })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Erreur lors de la lecture des instructions : ' + data.error);
            } else {
                showEditTextPopup(data, settingValue);
            }
        })
        .catch(error => {
            console.error('Error reading instructions:', error);
            alert('Erreur lors de la lecture des instructions.');
        });
    }
 }

function showEditTextPopup(content, fileName) {
    const popupHtml = `
        <dialog id="editTextPopup" class="edit-modal">
            <form method="dialog">
                <h2>Edit Text: ${fileName}</h2>
                <div class="form-group">
                    <textarea id="editTextContent" rows="10">${content}</textarea>
                </div>
                <div class="button-group">
                    <button type="button" onclick="saveEditedText('${fileName}')">Enregistrer</button>
                    <button type="button" onclick="closeEditTextPopup()">Fermer</button>
                </div>
            </form>
        </dialog>
    `;

    // Remove existing popup if any
    const existingPopup = document.getElementById('editTextPopup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Add popup to document
    document.body.insertAdjacentHTML('beforeend', popupHtml);

    // Show popup
    const popup = document.getElementById('editTextPopup');
    popup.showModal();
}

function saveEditedText(fileName) {
    const editedContent = document.getElementById('editTextContent').value;
    fetch('/save-CRQ-text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_name: fileName, text_data: editedContent })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Text saved successfully') {
            alert('Text saved successfully.');
            closeEditTextPopup();
        } else {
            alert('Error saving text: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving text:', error);
        alert('Error saving text.');
    });
}

function closeEditTextPopup() {
    const popup = document.getElementById('editTextPopup');
    if (popup) {
        popup.close();
        popup.remove();
    }
}



function closeCRQPopup() {
    const popup = document.getElementById('CRQPopup');
    if (popup) {
        popup.close();
    }
}

// Add styles for CRQPopup
const style4 = document.createElement('style');
style4.textContent = `
    .CRQ-popup {
        width: 400px;
        height: 300px;
        padding: 20px;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .CRQ-popup #fileList {
        list-style-type: none;
        padding: 0;
    }
    .CRQ-popup #fileList li {
        padding: 8px;
        border-bottom: 1px solid #ccc;
        cursor: pointer;
    }
    .CRQ-popup #fileList li.selected {
        background-color: #007bff;
        color: white;
    }
    .CRQ-popup .button-group {
        display: flex;
        justify-content: flex-end;
    }
    .CRQ-popup .button-group button {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        background-color: #f44336;
        color: white;
    }
`;
function save_current_instruction() {
    value=document.querySelector('.selected').innerText;
    CookieName='current_instruction';
    const selectedElement = document.querySelector('.selected');
    if (selectedElement) {
        const selected = selectedElement.innerText;
        save_cookie(CookieName,selected);

     }
}



