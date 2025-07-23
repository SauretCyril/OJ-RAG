function createAnnouncementForm() {
    const formHtml = `
        <dialog id="announcementForm" class="announcement-form">
            <form method="dialog">
                <h2>Créer un dossier</h2>
                <div class="form-group">
                    <label for="announcementDossier">Dossier:</label>
                    <input type="text" id="announcementDossier" class="rich-text-field">
                </div>
                <div class="form-group">
                    <label for="announcementURL">URL:</label>
                    <input type="url" id="announcementURL" class="rich-text-field">
                </div>
                <div class="form-group">
                    <label for="announcementContent">Contenu de l'annonce:</label>
                    <textarea id="announcementContent" class="rich-text-field"></textarea>
                </div>
                <div class="form-group">
                    <label for="creationMode">Mode de création:</label>
                    <select id="creationMode" class="rich-text-field">
                         <option value="creer_annonce">Contenu</option>
                         <option value="Action">Action</option>
                         <option value="scan_url_annonce">Url</option>
                    </select>
                </div>
                <div class="form-group">
                    <button type="button" id="pickFilesBtn">Sélectionner des fichiers (serveur)</button>
                    <ul id="pickedFilesList"></ul>
                </div>
                <div class="button-group">
                    <button type="button" onclick="executeCreationMode()">Exécuter</button>
                    <button type="button" onclick="closeAnnouncementForm()">Fermer</button>
                </div>
            </form>
        </dialog>
    `;
   /*  <option value="creer_annonce">Ajouter Annonce à partir de contenu</option>
    <option value="creer_reponse">Ajouter Réponse à partir de contenu</option>
   
    <option value="scrapeAndFill">Scrape URL</option>
    <option value="NewAteller">New Atelier</option> */
    // Remove existing form if any
    const existingForm = document.getElementById('announcementForm');
    if (existingForm) {
        existingForm.remove();
    }

    // Add form to document
    document.body.insertAdjacentHTML('beforeend', formHtml);

    document.getElementById('pickFilesBtn').onclick = async function() {
        // Appel à la route Python (POST)
        const response = await fetch('/pick_files', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // ou {initial_dir: "chemin"} si besoin
        });
        const data = await response.json();
        const files = data.files || [];
        // Affichage dans la liste
        const ul = document.getElementById('pickedFilesList');
        ul.innerHTML = '';
        files.forEach(f => {
            const li = document.createElement('li');
            li.textContent = f;
            ul.appendChild(li);
        });
    };

    // Show form
    const form = document.getElementById('announcementForm');
    form.showModal();
    fillNextDossierName(); // Call the function to fill the next dossier name
}

function executeCreationMode() {
    const creationMode = document.getElementById('creationMode').value;
    if (creationMode === 'scan_url_annonce') {
        scan_url_annonce(); 
    } else if (creationMode === 'creer_annonce') {
        submitAnnouncement(window.CONSTANTS["ANNONCE_SUFFIX"]);
    }
    else if (creationMode === 'Action') {
        submitAnnouncement(window.CONSTANTS["ACTION_SUFFIX"]);

    }
}



    
function submitAnnouncement(type) {
    // let content = document.getElementById('announcementContent').value;
    // if (content.trim() === '') {
    //     alert('Le contenu de l\'action ne peut pas être vide !!!');
    //     return;
    // }
    const contentNum = document.getElementById('announcementDossier').value;
    if (contentNum.trim() === '') {
        alert('Le numéro du dossier ne peut pas être vide !!!');
        return;
    }

    const contentUrl = document.getElementById('announcementURL').value;
  
    contentUrlembed = "<- " + contentUrl + " ->";

    // Remove all spaces inside content
    
    //content = content.replace(/\s+/g, '');

    globalContent =  content;
    showLoadingOverlay();
    alert(CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX'])
    fetch('/save_announcement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contentNum: contentNum,
            content: content,
            url:contentUrl,
            type: type,
            sufix:CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']
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
    // Handle the announcement content (e.g., send it to the server)
    //console.log('Announcement content:', content);

    // Close form
    //closeAnnouncementForm();
}


function closeAnnouncementForm() {
    const form = document.getElementById('announcementForm');
    if (form) {
        form.close();
        form.remove(); // Ensure the form is removed from the DOM
    }
}

// Les styles ont été déplacés dans la feuille de style dialogs.css
