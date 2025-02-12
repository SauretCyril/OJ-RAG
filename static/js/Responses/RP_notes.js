

function showNotesPopup(content, file_notes) {
    const popupHtml = `
        <dialog id="notesPopup" class="notes-popup">
            <form method="dialog">
                <h2>Notes</h2>
                <div id="notesContentContainer">
                    <table id="notesTable" class="notes-table">
                        ${content.length === 0 ? `
                            <tr>
                                <td colspan="3">Aucune note disponible.</td>
                            </tr>
                        ` : content.map((item, index) => `
                            <tr>
                                <td contenteditable="true" onblur="saveNoteChange('${file_notes}', ${index}, 'key', this.textContent)">${item.key}</td>
                                <td contenteditable="true" style="width: 300px;" onblur="saveNoteChange('${file_notes}', ${index}, 'value', this.textContent)">${item.value}</td>
                                <td style="width: 50px;"><span class="remove-icon" onclick="removeNoteRow('${file_notes}', ${index})">&times;</span></td>
                               
                            </tr>
                        `).join('')}
                    </table>
                </div>
                <div class="button-group">
                    <button type="button" onclick="addNoteRow('${file_notes}')">Ajouter</button>
                    <button type="button" onclick="closeNotesPopup()">Fermer</button>
                </div>
            </form>
        </dialog>
    `;

    // Remove existing popup if any
    const existingPopup = document.getElementById('notesPopup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Add popup to document
    document.body.insertAdjacentHTML('beforeend', popupHtml);

    // Show popup
    const popup = document.getElementById('notesPopup');
    popup.showModal();
}

function saveNoteChange(file_notes, index, key, value) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            notesContent[index][key] = value;
            saveNotes(file_notes, notesContent);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function saveNotes(file_notes, content) {
    fetch('/save_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes, content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            console.log('Notes enregistrées avec succès.');
        } else {
            alert('Erreur lors de l\'enregistrement des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error saving notes:', error);
        alert('Erreur lors de l\'enregistrement des notes.');
    });
}

function addNoteRow(file_notes) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            notesContent.push({ key: '', value: '' });
            saveNotes(file_notes, notesContent);
            showNotesPopup(notesContent, file_notes);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function removeNoteRow(file_notes, index) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            notesContent.splice(index, 1);
            saveNotes(file_notes, notesContent);
            showNotesPopup(notesContent, file_notes);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function closeNotesPopup() {
    const popup = document.getElementById('notesPopup');
    if (popup) {
        popup.close();
    }
}

// Add styles for notesPopup
const style1 = document.createElement('style');
style1.textContent = `
    .notes-popup {
        width: 800px;
        height: 500px;
        padding: 20px;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .notes-popup .notes-table {
        width: 100%;
        border-collapse: collapse;
    }
    .notes-popup .notes-table td {
        border: 1px solid #ccc;
        padding: 8px;
    }
    .notes-popup .remove-icon {
        cursor: pointer;
        color: red;
        font-size: 20px;
    }
    .notes-popup .select-icon {
        cursor: pointer;
        color: blue;
        font-size: 20px;
    }
    .notes-popup .button-group {
        display: flex;
        justify-content: space-between;
    }
    .notes-popup .button-group button {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .notes-popup .button-group button:first-child {
        background-color: #4CAF50;
        color: white;
    }
    .notes-popup .button-group button:last-child {
        background-color: #f44336;
        color: white;
    }
`;
