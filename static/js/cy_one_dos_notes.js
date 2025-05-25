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
                                <td contenteditable="true" class="rich-text" style="width: 10%;"onblur="saveNoteChange('${file_notes}', ${index}, 'key', this.innerHTML)">${item.key}</td>
                                <td contenteditable="true" class="rich-text" style="width: 90%;" onblur="saveNoteChange('${file_notes}', ${index}, 'value', this.innerHTML)">${item.value}</td>
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

