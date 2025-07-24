{/* <div class="form-group">
                    <label for="creationMode">Mode de création:</label>
                    <select id="creationMode" class="rich-text-field">
                         <option value="creer_annonce">Contenu</option>
                         <option value="Action">Action</option>
                         <option value="scan_url_annonce">Url</option>
                    </select>
                </div> */}

let currentTab = "Default"; // Ajout de l'indicateur d'onglet

function createAnnouncementForm() {
    const formHtml = `
        <dialog id="announcementForm" class="announcement-form">
            <form method="dialog">
                <h2>Créer un dossier</h2>
                <nav class="tab-nav">
                    <button type="button" class="tab-btn active" id="tabDefaultBtn">Default</button>
                    <button type="button" class="tab-btn" id="tabFilesBtn">Fichiers</button>
                </nav>
                <div class="form-group">
                    <label for="announcementDossier">Dossier:</label>
                    <input type="text" id="announcementDossier" class="rich-text-field">
                </div>
                <div id="tabDefault" class="tab-content active">
                    <div class="form-group">
                        <label for="announcementURL">URL:</label>
                        <input type="url" id="announcementURL" class="rich-text-field">
                    </div>
                    <div class="form-group">
                        <label for="announcementContent">Contenu de l'annonce:</label>
                        <textarea id="announcementContent" class="rich-text-field"></textarea>
                    </div>
                </div>
                <div id="tabFiles" class="tab-content" style="display:none;">
                    <div class="form-group">
                        <label for="directInput">Direct Input:</label>
                        <input type="text" id="directInput" class="rich-text-field">
                    </div>
                </div>
                <div class="form-group">
                    <label for="fldcategorie">Categorie:</label>
                    <input type="text" id="fldcategorie" class="rich-text-field">
                    <label for="flddescription">Description:</label>
                    <input type="text" id="flddescription" class="rich-text-field">
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
    // Remove existing form if any
    const existingForm = document.getElementById('announcementForm');
    if (existingForm) {
        existingForm.remove();
    }

    // Add form to document
    document.body.insertAdjacentHTML('beforeend', formHtml);

    // Onglet switching logic
    document.getElementById('tabDefaultBtn').onclick = function() {
        document.getElementById('tabDefault').style.display = '';
        document.getElementById('tabFiles').style.display = 'none';
        this.classList.add('active');
        document.getElementById('tabFilesBtn').classList.remove('active');
        currentTab = "Default"; // MAJ indicateur
    };
    document.getElementById('tabFilesBtn').onclick = function() {
        document.getElementById('tabDefault').style.display = 'none';
        document.getElementById('tabFiles').style.display = '';
        this.classList.add('active');
        document.getElementById('tabDefaultBtn').classList.remove('active');
        currentTab = "Direct"; // MAJ indicateur
    };

    document.getElementById('pickFilesBtn').onclick = async function() {
        // Appel à la route Python (POST)
        const response = await fetch('/pick_files', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await response.json();
        const files = data.files || [];
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
    fillNextDossierName();
}

function executeCreationMode() {
    // Utilise currentTab pour savoir où tu es
    //if (currentTab === "Default") {
    /*     const creationMode = document.getElementById('creationMode').value;
        if (creationMode === 'scan_url_annonce') {
            scan_url_annonce(); 
        } else if (creationMode === 'creer_annonce') {
            submitAnnouncement(window.CONSTANTS["ANNONCE_SUFFIX"]);
        }
        else if (creationMode === 'Action') {
            submitAnnouncement(window.CONSTANTS["ACTION_SUFFIX"]);
        } */

        submitAnnouncement(window.CONSTANTS["ANNONCE_SUFFIX"]);
    //} 
}



    
function submitAnnouncement(type) {
    const contentNum = document.getElementById('announcementDossier').value;
    if (contentNum.trim() === '') {
        alert('Le numéro du dossier ne peut pas être vide !!!');
        return;
    }

    const contentUrl = document.getElementById('announcementURL').value;
    const flddescription = document.getElementById('flddescription').value;
    const fldcategorie = document.getElementById('fldcategorie').value;
    contentUrlembed = "<- " + contentUrl + " ->";

    // Récupérer la liste des fichiers
    const pickedFilesList = Array.from(document.querySelectorAll('#pickedFilesList li')).map(li => li.textContent);

    const content = document.getElementById('announcementContent').value;

    alert("dbg-1114-a : contentNum :" +  contentNum);

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
            url: contentUrl,
            type: type,
            flddescription: flddescription,
            fldcategorie: fldcategorie,
            currentTab: currentTab,
            sufix: CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX'],
            pickedFilesList: pickedFilesList // Ajout de la liste des fichiers
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert('Annonce créée avec succès.');
            if (pickedFilesList.length > 0) {
                //alert('Fichiers sélectionnés: ' + pickedFilesList.join(', '));
                // Ici, tu peux ajouter d'autres actions à effectuer avec les fichiers sélectionnés
                // Envoie la liste des fichiers et le numéro du dossier à la route Python pour déplacer les fichiers
                alert("dbg-5434-b : dossier :" + contentNum);
                fetch('/move_files_to_dossier', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        files: pickedFilesList,
                        dossier_num: contentNum
                    })
                })
                .then(res => res.json())
                .then(res => {
                    if (res.status === "success") {
                        alert('Fichiers déplacés dans le dossier avec succès.');
                    } else {
                        alert('Erreur lors du déplacement des fichiers: ' + res.message);
                    }
                })
                .catch(err => {
                    console.error('Erreur déplacement fichiers:', err);
                    alert('Erreur lors du déplacement des fichiers.');
                });
            }
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
