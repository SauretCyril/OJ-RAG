// ...existing code...
/**
 * Module de fonctions pour la gestion des dossiers
 * Version optimisée utilisant les nouveaux modules
 */

/**
 * Ouvre le répertoire parent d'un fichier
 * @param {string} filepath - Chemin du fichier
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function fix_open_dir(filepath)
{
    currow=getState('currentSelectedRow', null);
    if (currow) {
        open_dir(currow.id);
    }
}
async function open_dir(filepath) {
    try {
        const data = await ApiClient.files.openDirectory(filepath);
        if (data.status === "success") {
            // console.log('Directory opened successfully.');
        } else {
            console.error('Error opening directory:', data.message);
        }
        return data;
    } catch (error) {
        console.error('Error opening directory:', error);
        throw error;
    }
}

/**
 * Obtient une analyse d'une offre d'emploi à partir d'un fichier ou d'une URL
 * @param {string} thepath - Chemin du fichier ou URL
 * @param {string} num_job - Numéro du dossier
 * @param {string} typ - Type d'analyse
 * @param {boolean} isUrl - Indique si thepath est une URL
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function get_job_answer(thepath, num_job, typ, isUrl) {
    if (thepath.length === 0) {
        alert("Veuillez renseigner le chemin du fichier ou l'URL");
        return;
    }
    
    // Question à poser à l'IA
    const q2_job = 
        "peux tu me faire un plan détaillé de l'offre avec les sections en précisant bien ce qui est obligatoire, optionnelle :" +
        "- Titre poste proposé," +
        "- le nom de l'entrerise qui recrute," +
        "- le lieux ou se situe le poste," +
        "- la date de publication ou d'actualisation de l'annonce,"+
        "- Duties (Description du poste décomposée en tache ou responsabilité)," +
        "- requirements (expérience attendues, )," +
        "- skills (languages, outils obligatoires, framework)," +
        "- Savoir-être (soft skill)," +
        "- autres (toutes informations autre utile à connaitre, comme descriptif de l'entreprise, secteur d'activité, pourquoi l'entreprise recrute...)"+
        "- en conclusion : peux tu faire une présentation rapide sur 3 lignes du candidat idéal"+
        "- il faut ajouter la donnée suivante telque : <- "+thepath+" -> afin que je puisse garder la référence";
    
    showLoadingOverlay();

    try {
        let jobTextResponse;
        
        if (!isUrl) {
            console.log("dbg A023a : Traitement du fichier pdf en cours... : " + thepath);
            jobTextResponse = await ApiClient.jobs.getAnswer(thepath, q2_job,num_job,false);
        } else {
            jobTextResponse = await ApiClient.jobs.getAnswerFromUrl(thepath, q2_job,num_job);
        }
        
        const savetext = jobTextResponse.formatted_text;
        
        await ApiClient.jobs.saveAnswer(savetext, num_job, '', q2_job);
        
        // Succès silencieux
        // alert("Résumé de l'offre d'emploi effectué");
    } catch (error) {
        console.error('Error:', error);
        alert("Erreur lors du traitement de l'offre d'emploi");
    } finally {
        hideLoadingOverlay();
        refresh();
    }
}

/**
 * Convertit un CV pour un dossier spécifique
 * @param {string} numDossier - Numéro du dossier
 * @param {string} repertoire_annonces - Répertoire des annonces
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function convert_cv(numDossier, repertoire_annonces) {
    return httpPost('/convert_cv', {
        num_dossier: numDossier,
        repertoire_annonces: repertoire_annonces
    });
}

/**
 * Obtient un CV pour un dossier spécifique
 * @param {string} numDossier - Numéro du dossier
 * @param {string} repertoire_annonces - Répertoire des annonces
 * @param {string} state - État actuel
 * @param {string} prefix - Préfixe
 */
async function get_cv(numDossier, repertoire_annonces, state, prefix) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx';
    input.style.display = 'none';
    
    let ready = true;
    if (state === 'O') {
        if (!confirm("Voulez vous écraser votre CV ?")) {
            ready = false;
        }
    }
    
    if (ready) {
        input.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file_path', file); // Le fichier à uploader
                formData.append('num_dossier', numDossier);
                formData.append('repertoire_annonce', repertoire_annonces);
                formData.append('prefix', prefix || 'CV'); // Optionnel selon votre cas

                showLoadingOverlay();
                
                try {
                    await ApiClient.files.upload(formData);
                    alert("Fichier téléchargé avec succès.");
                    refresh();
                } catch (error) {
                    console.error('Erreur lors du téléchargement du fichier :', error);
                    alert("Erreur lors du téléchargement du fichier.");
                } finally {
                    hideLoadingOverlay();
                }
            }
        });
        
        document.body.appendChild(input);
        input.click();
    }
}

/**
 * Ouvre une URL dans le navigateur par défaut
 * @param {string} theurl - URL à ouvrir
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
function open_url(theurl) {
    if (!theurl || typeof theurl !== 'string') {
        alert(`URL ${theurl} invalide ou non fournie`);
        return Promise.reject(new Error("URL invalide ou non fournie"));
    }
    return ApiClient.files.openUrl(theurl);
}

async function Get_dir_Root() {
    
    try {
        const response = await ApiClient.files.getDirectoryRoot();
        console.log("log3a  Répertoire racine récupéré:", response.root_directory);
        return response.root_directory;
    } catch (error) {
        console.error("Erreur lors de la récupération du répertoire racine:", error);
        throw error;
    }
}

function open_files_Setting() 
{
ApiClient.files.getDirectoryRoot()
  .then(response => {
    // Utilisation de response.root_direc  tory
    alert("Répertoire racine : " + response.root_directory);
    console.log("Répertoire racine:", response.root_directory);

    ask_Local_file_explorer(response.root_directory,"config"); 
  })
  .catch(error => {
    console.error("Erreur lors de la récupération du répertoire racine:", error);
  });
}



/**
 * Ouvre les notes d'un fichier
 * @param {string} file_notes - Chemin du fichier de notes
 * @returns {Promise} - Promise contenant le résultat de l'opération
 */
async function open_notes(file_notes) {
    try {
        const data = await ApiClient.files.readNotes(file_notes);
        
        if (data.status === "success") {
            showNotesPopup(data.content, file_notes);
        } else {
            alert('Erreur lors de la lecture des notes : ' + data.message);
        }
    } catch (error) {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    }
}

/**
 * Remplit le prochain nom de dossier disponible
 */
async function fillNextDossierName() {
    // Get the last used dossier name
    let lastDossier = getState('currentSelectedRow')

    if (!lastDossier) {
        lastDossier = getState('annonces').reduce((last, current) => {
        const currentDossier = Object.values(current)[0].dossier;
        return currentDossier > last ? currentDossier : last;
    }, "A000");
    }
    else {
        lastDossier = get_currentAnnonce().dossier;
        alert("Dernier dossier utilisé : " + lastDossier);
    }

    let letter = lastDossier.charAt(0);
    let number = parseInt(lastDossier.slice(1)) + 1;
    let nextDossier = letter + number.toString().padStart(3, '0');
    
    while (await checkDossierExists(nextDossier)) {
        number += 1;
        nextDossier = letter + number.toString().padStart(3, '0');
    }

    document.getElementById('announcementDossier').value = nextDossier;
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

// Exposer les fonctions globalement
// Note: nous gardons les mêmes noms pour maintenir la compatibilité avec le code existant
window.open_dir = open_dir;
window.get_job_answer = get_job_answer;
window.convert_cv = convert_cv;
window.get_cv = get_cv;
window.open_url = open_url;
window.open_notes = open_notes;
window.fillNextDossierName = fillNextDossierName;
window.checkDossierExists = checkDossierExists;
