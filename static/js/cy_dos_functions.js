// ...existing code...
function open_dir(filepath) {
    fetch('/open_parent_directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: filepath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            //console.log('Directory opened successfully.');
        } else {
            console.error('Error opening directory:', data.message);
        }
    })
    .catch(error => {
        console.error('Error opening directory:', error);
    });
}

async function get_job_answer(thepath,num_job,typ,isUrl)
{
 if (thepath.length === 0) {
    alert("Veuillez renseigner le chemin du fichier ou l'URL");
    return;
 }
 else {
    //alert("Traitement de l'offre d'emploi en cours... : " + thepath );
 }



 q2_job = 
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
        "- il faut ajouter la donnée suivante telque : <- "+thepath+" -> afin que je puisse garder la référence" ;
 
 
   
    showLoadingOverlay();

    try {
       
        let jobTextResponse = "";
        if (!isUrl) {
            console.log("dbg A023a : Traitement du fichier pdf en cours... : " + thepath );
            jobTextResponse = await fetch('/get_job_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path: thepath, RQ: q2_job })
            });
        } else {
             
            //jobTextResponse = get_job_answer_from_url(thepath,q2_job);
            //alert("dbg T023 : Traitement de l'url en cours... : " + thepath );
            jobTextResponse= await fetch('/get_job_answer_from_url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: thepath, RQ: q2_job }) 
            });
           
        }
        
        if (!jobTextResponse.ok) {
            throw new Error('Erreur lors de l\'extraction du texte de l\'offre');
        }
        
        const jobTextData = await jobTextResponse.json();
        const saved_path = "";
        
        //savetext="[--doc--]\n"+thepath+"\n";
        //savetext+="[--Qestion--]\n"+q2_job+"\n";
        savetext= jobTextData.formatted_text;
      
       
        const saveResponse = await fetch('/save-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text_data: savetext, number: num_job, the_path: saved_path 
                , RQ: q2_job
            })
        });

        if (saveResponse.ok) {
           //alert("Résumé de l'offre d'emploi effectué");
        } else {
            alert("Erreur lors de la sauvegarde de l'offre d'emploi");
        }
    } catch (error) {
        console.error('Error:', error);
        alert("Erreur lors du traitement de l'offre d'emploi");
    } finally {
        hideLoadingOverlay();
        refresh();
    }
}

async function convert_cv(numDossier, repertoire_annonces) 
{
 fetch('/convert_cv', {
    method: 'POST',
    headers:{
            'Content-Type': 'application/json'
            },
    body: JSON.stringify({ 
        num_dossier: numDossier,
        repertoire_annonces: repertoire_annonces,
        })
    });
}


async function get_cv(numDossier, repertoire_annonces,state,prefix) 
{
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx'; // Acceptable file types
    input.style.display = 'none';
    ready=true;
    if (state==='O')
    {
         if  (! confirm("Voulez vous écraser votre CV ? ")) {
        ready=false;   
        }
    }

    
        input.addEventListener('change', async (event) => 
        {
            const file = event.target.files[0];
            if (file) 
            {
                const formData = new FormData();
                formData.append('file_path', file);
                formData.append('num_dossier', numDossier);
                formData.append('repertoire_annonce', repertoire_annonces);
                formData.append('prefix', prefix);
                fpath=repertoire_annonces + '/' + numDossier +  ".data.json";   
                try 
                {
                    const response = await fetch('/share_cv', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();

                    if (data.status === "success") 
                    {
                        alert('CV selectionné avec succès.');
                        alert(fpath + ",  'CVfile' , "+file.name)
                     
                        //updateAnnonces_byfile(fpath, "CVfile", file.name);
                        refresh();
                    } else 
                    {
                        alert('Erreur lors de la sélection du CV: ' + data.message);
                    }

                } 
                catch (error) 
                {
                    console.error('Error selecting CV:', error);
                    alert('Erreur lors de la sélection du CV.');
                }
            }
        });
    if (ready) 
    {
         document.body.appendChild(input);
        input.click();
    }

   
}


function open_url(theurl) {
    //alert(theurl);
           fetch('/open_url', {
               method: 'POST',
               headers: {
               'Content-Type': 'application/json'
               },
               body: JSON.stringify({ url: theurl  })
       });
}

function open_notes(file_notes) {
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



async function fillNextDossierName() {
    let lastDossier = window.annonces.reduce((last, current) => {
        const currentDossier = Object.values(current)[0].dossier;
        return currentDossier > last ? currentDossier : last;
    }, "A000");
   
    let letter = lastDossier.charAt(0);
    let number = parseInt(lastDossier.slice(1)) + 1;
    let nextDossier = letter + number.toString().padStart(3, '0');
    //alert(nextDossier)
    while (await checkDossierExists(nextDossier)) {
        number += 1;
        nextDossier = letter + number.toString().padStart(3, '0');
    }

    document.getElementById('announcementDossier').value = nextDossier;
}

async function checkDossierExists(dossier) {
    try {
        const response = await fetch('/check_dossier_exists', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dossier: dossier })
        });
        const data = await response.json();
        return data.exists;
    } catch (error) {
        console.error('Error checking dossier existence:', error);
        return false;
    }
}
