function open_CRQ() {
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
                <h2>Liste des fichiers</h2>
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
                    <button type="button" onclick="saveSetting()" id="saveButton" style="display: none;">Enregistrer</button>
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
    const selected = document.querySelector('.selected');
    if (selected) {
        selected.classList.remove('selected');
    }
    element.classList.add('selected');
    document.getElementById('saveButton').style.display = 'inline-block';
}

function saveSetting() {
    const selected = document.querySelector('.selected');
    if (selected) {
        const settingValue = selected.querySelector('strong').innerText;
        localStorage.setItem('current_instruction', settingValue);
        document.cookie = `current_instruction=${settingValue}; path=/; max-age=${60 * 60 * 24 * 365}`;
        get_setting_current_instruction();
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


function get_setting_current_instruction() {
    const currentInstruction = getCookie('current_instruction');
    if (currentInstruction) {
        document.getElementById('current-instruction').textContent = currentInstruction;
    } else {
        document.getElementById('current-instruction').textContent = 'No current';
    }
}

function getCookie(name) {
    let cookieArr = document.cookie.split(";");
    for (let i = 0; i < cookieArr.length; i++) {
        let cookiePair = cookieArr[i].split("=");
        if (name == cookiePair[0].trim()) {
            return decodeURIComponent(cookiePair[1]);
        }
    }
    return null;
}