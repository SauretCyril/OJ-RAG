//onfiche
function openEditModal(rowId) {
    // Find the annonce data
    const index = window.annonces.findIndex(a => Object.keys(a)[0] === rowId);
    if (index === -1) return;
    const annonce = window.annonces[index][rowId];

    // Définir les groupes d'onglets
    const tabGroups = {
        'Informations principales': ['dossier', 'description', 'id', 'entreprise', 'categorie'],
        'Statut': ['etat', 'lien_Etape','annonce_pdf','CV','CVfile'],
        'suivi': [ 'Date','Date_rep','todo','commetaires','Origine'],
        'Contact': [ 'contact','tel', 'mail','url'],
        'Détails': ['Commentaire', 'type', 'Lieux'], 
        'GPT': ['GptSum', 'instructions','request'],
        'Publication': ['lnk_Youtub_value','path_dirpartage_value']
    };

    // Create modal HTML with tabs
    let modalHtml = `
        <dialog id="editModal" class="edit-modal">
            <form method="dialog">
                <h2>Modifier l'annonce</h2>
                <div class="edit-tabs">
                    ${Object.keys(tabGroups).map((tabName, index) => `
                        <button type="button" class="tab-button ${index === 0 ? 'active' : ''}" 
                                onclick="switchEditTab(event, '${tabName}')">${tabName}</button>
                    `).join('')}
                </div>

                ${Object.entries(tabGroups).map(([tabName, fields], index) => `
                    <div id="${tabName}" class="tab-content ${index === 0 ? 'active' : ''}">
                        ${fields.map(field => `
                            <div class="form-group">
                                <label>${field}:</label>
                                ${field === 'instructions' ? 
                                    `<textarea id="edit-${field}" class="rich-text-field">${annonce[field] || ''}</textarea>` :
                                    `<input type="text" id="edit-${field}" class="rich-text-field" value="${annonce[field] || ''}" 
                                       ${field === 'dossier' ? 'readonly' : ''}>`
                                }
                            </div>
                        `).join('')}
                    </div>
                `).join('')}

                <div class="button-group">
                    <button type="button" onclick="saveEdit('${rowId}')">Enregistrer</button>
                    <button type="button" onclick="cancelEdit()">Annuler</button>
                </div>
            </form>
        </dialog>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('editModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = document.getElementById('editModal');
    modal.showModal();
}

function switchEditTab(event, tabName) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let content of tabContents) {
        content.classList.remove('active');
    }

    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let button of tabButtons) {
        button.classList.remove('active');
    }

    // Show the selected tab content and activate the button
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

function saveEdit(rowId) {
    // Ensure the index is correct
    const index = window.annonces.findIndex(a => Object.keys(a)[0] === rowId);
    if (index === -1) return;
    const annonce = window.annonces[index][rowId];

    // Update annonce with new values based on window.columns
    window.columns.forEach(col => {
        const inputElement = document.getElementById(`edit-${col.key}`);
        if (inputElement) {
            annonce[col.key] = inputElement.value;
        }
    });

    // Save changes and refresh table
    refresh();
  
    // Close modal
    document.getElementById('editModal').close();
}

function cancelEdit() {
    document.getElementById('editModal').close();
}
