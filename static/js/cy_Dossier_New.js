let currentTab = "Default"; // Ajout de l'indicateur d'onglet

async function createAnnouncementForm() {
    // Récupère le numéro de dossier à l'avance
    let nextDossier = "";
    if (window.fillNextDossierName) {
        nextDossier = await window.fillNextDossierName(true); // On passe true pour "juste retourner la valeur"
    }

    const formHtml = `
        <dialog id="announcementForm" class="announcement-form">
            <form method="dialog">
                <h2>Créer un dossier</h2>
                <div class="form-group">
                    <label for="announcementDossier">Numéro de dossier :</label>
                    <input type="text" id="announcementDossier" class="rich-text-field" required value="${nextDossier}">
                </div>
                <div class="form-group">
                    <label for="announcementURL">URL :</label>
                    <input type="url" id="announcementURL" class="rich-text-field">
                </div>
                <div class="form-group">
                    <label for="announcementContent">Contenu de l'annonce :</label>
                    <textarea id="announcementContent" class="rich-text-field"></textarea>
                </div>
                <div class="button-group">
                    <button type="button" onclick="executeCreationMode()">Créer</button>
                    <button type="button" onclick="closeAnnouncementForm()">Fermer</button>
                </div>
            </form>
        </dialog>
    `;
    // Remove existing form if any
    const existingForm = document.getElementById('announcementForm');
    if (existingForm) {
        existingForm.remove();
    }

    // Add form to document
    document.body.insertAdjacentHTML('beforeend', formHtml);

    // Show form
    const form = document.getElementById('announcementForm');
    form.showModal();
}

function executeCreationMode() {
        submitAnnouncement(window.CONSTANTS["ANNONCE_SUFFIX"]);
}



    
function submitAnnouncement(type) {
    const contentNum = document.getElementById('announcementDossier').value;
    if (contentNum.trim() === '') {
        alert('Le numéro du dossier ne peut pas être vide !!!');
        return;
    }

    const contentUrl = document.getElementById('announcementURL').value;
    const content = document.getElementById('announcementContent').value;

    showLoadingOverlay();

    fetch('/save_announcement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contentNum: contentNum,
            content: content,
            url: contentUrl,
            type: type,
            currentTab: currentTab,
            sufix: CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert('Annonce créée avec succès.');
            refresh();
        } else {
            alert('Erreur lors de la création de l\'annonce: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error creating announcement:', error);
        alert('Erreur lors de la création de l\'annonce.');
    });
    hideLoadingOverlay();

}


function closeAnnouncementForm() {
    const form = document.getElementById('announcementForm');
    if (form) {
        form.close();
        form.remove(); // Ensure the form is removed from the DOM
    }
}


/**
 * Remplit le prochain nom de dossier disponible
 */
async function fillNextDossierName(returnValueOnly = false) {
    let lastDossier = getState('currentSelectedRow');

    let annonces = getState('annonces');
    if (!lastDossier) {
        if (Array.isArray(annonces) && annonces.length > 0) {
            lastDossier = annonces.reduce((last, current) => {
                const currentDossier = Object.values(current)[0].dossier;
                return currentDossier > last ? currentDossier : last;
            }, "A000");
        } else {
            lastDossier = "A000";
        }
    } else {
        lastDossier = get_currentAnnonce().dossier;
    }

    let letter = lastDossier.charAt(0);
    let number = parseInt(lastDossier.slice(1)) + 1;
    let nextDossier = letter + number.toString().padStart(3, '0');

    while (await checkDossierExists(nextDossier)) {
        number += 1;
        nextDossier = letter + number.toString().padStart(3, '0');
    }

    if (returnValueOnly) {
        return nextDossier;
    } else {
        document.getElementById('announcementDossier').value = nextDossier;
    }
}

/**
 * Vérifie si un dossier existe déjà
 * @param {string} dossier - Numéro du dossier à vérifier
 * @returns {Promise<boolean>} - true si le dossier existe, false sinon
 */
async function checkDossierExists(dossier) {
    try {
        const response = await httpPost('/check_dossier_exists', { dossier: dossier });
        return response.exists;
    } catch (error) {
        console.error('Error checking dossier existence:', error);
        return false;
    }
}

// Les styles ont été déplacés dans la feuille de style dialogs.css
window.fillNextDossierName = fillNextDossierName;
window.checkDossierExists = checkDossierExists;