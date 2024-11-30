document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const jobFile = document.getElementById('jobFile').files[0];
    
    if (!jobFile) {
        alert('Veuillez sélectionner les fichiers requis.');
        return;
    }

    

    
    formData.append('file', jobFile, jobFile.name);
    ///formData.append('q2_job', q2_job);

    // Log the FormData content for debugging
    for (let pair of formData.entries()) {
        console.log(pair[0]+ ': ' + pair[1]);
    }
    
    try {
        // Afficher le spinner
        document.getElementById('loading').style.display = 'block';
        
        // Upload des fichiers
        const uploadResponse = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('Upload response error:', errorText);
            throw new Error('Erreur lors du téléchargement des fichiers');
        }

        const paths = await uploadResponse.json();
        const num_job = paths.file_dir;
        document.getElementById('NUM').textContent = num_job;
        document.getElementById('formattedJobDescription').innerHTML="";
        console.log('num_job', num_job);

        // Extraction rapide du texte de l'offre
        const q2_job = 
        "peux tu me faire un plan détaillé de l'offre avec les sections en précisant bien ce qui est obligatoire, optionnelle :" +
        "- Titre poste proposé," +
        "- Duties (Description du poste décomposée en tache ou responsabilité)," +
        "- requirements (expérience attendues, )," +
        "- skills (languages, outils obligatoires)," +
        "- Savoir-être (soft skill)," +
        "- autres (toutes informations autre utile à connaitre)";
        
        const jobTextResponse = await fetch('/get_job_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: paths.path, RQ: q2_job })
        });
        
        if (!jobTextResponse.ok) {
            throw new Error('Erreur lors de l\'extraction du texte de l\'offre');
        }

        const jobTextData = await jobTextResponse.json();

        // Log the data being sent to /save-job-text for debugging
       /*  console.log('Saving job text data:', {
            job_text_data: jobTextData.formatted_text,
            job_number: num_job
        }); */

        // sauvegarder la réponse au niveau du répertoire de l'annonce
        const saved_path="G:/OneDrive/Entreprendre/Actions-4";
        const saveResponse = await fetch('/save-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            //
            body: JSON.stringify({ text_data: jobTextData.formatted_text, number: num_job, the_path: saved_path })
        });

        if (!saveResponse.ok) {
            const errorText = await saveResponse.text();
            console.error('Save response error:', errorText);
            throw new Error('Erreur lors de la sauvegarde du texte de l\'offre');
        }

        // Display job details directly
        displayJobDetails(jobTextData);


        
    } catch (error) {
        console.error('Error:', error);
        alert('Une erreur est survenue lors de l\'analyse');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

document.getElementById('uploadCVForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const cvFile = document.getElementById('cvFile').files[0];
    
    if (!cvFile) {
        alert('Veuillez sélectionner les fichiers requis.');
        return;
    }

    formData.append('file', cvFile, cvFile.name); // Ensure the file is appended correctly with the correct name
    
    // Log the FormData content for debugging
    /* for (let pair of formData.entries()) {
        console.log(pair[0]+ ': ' + pair[1]);
    } */
    
    try {
        // Afficher le spinner
        document.getElementById('loading').style.display = 'block';
        
        // Upload des fichiers
        const uploadResponse = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('Upload response error:', errorText);
            throw new Error('Erreur lors du téléchargement des fichiers');
        }

        const paths = await uploadResponse.json();

        const num_cv = paths.file_dir;
        document.getElementById('CV_NUM').textContent = num_cv;
        console.log('num_cv', num_cv);
   

        q1_cv="peux tu me faire un plan détaillé du cv avec les rubriques : ";
        q1_cv+="-le Titre CV,";
        q1_cv+="- les Expériences Professionnelles :";
        q1_cv+="  - pour chaque expérience la liste des tâches";
        q1_cv+="- les méthodologies,";
        q1_cv+="- les outils (logiciels),";
        q1_cv+="- les Langages informatiques,";
        q1_cv+="- les framworks,";
        q1_cv+="- les savoir-être," ;
        q1_cv+="- les base de données,";
        q1_cv+="- les Formations.";
   
        /* console.log('q1_cv-----------', q1_cv);
        console.log('path------------', paths.path); */

        // Extraction rapide du texte du CV
        const cvTextResponse = await fetch('/get_job_answer', {  // Changé de /get_answer à /get_job_answer
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: paths.path, RQ: q1_cv })
        });
        
        if (!cvTextResponse.ok) {
            throw new Error('Erreur lors de l\'extraction du texte du CV');
        }
        
        
        /* const getsavePath = await fetch('/save-path', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        }); */

        const cvTextData = await cvTextResponse.json();
        const saved_path="G:/OneDrive/Entreprendre/Actions-4";
        
        // sauvegarder la réponse au niveau du répertoire du CV
         const saveResponse = await fetch('/save-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text_data: cvTextData.formatted_text, number: num_cv, the_path: saved_path })
        });

        if (!saveResponse.ok) {
            const errorText = await saveResponse.text();
            console.error('Save response error:', errorText);
            throw new Error('Erreur lors de la sauvegarde du texte du CV');
        }
        // Display CV details directly
        displayCVDetails(cvTextData); 
        
    } catch (error) {
        console.error('Error:', error);
        alert('Une erreur est survenue lors de l\'analyse');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

function displayCVDetails(cvTextData) {
    const cvDetailsContainer = document.getElementById('formattedCvDescription');
    if (cvDetailsContainer) {
        cvDetailsContainer.innerHTML = ``;
        cvDetailsContainer.innerHTML=`<pre>${cvTextData.formatted_text}</pre>`;
       console.log(cvTextData) ;
    }
    else {
        console.error('CVcontent not found');
    }
  
}

document.addEventListener('DOMContentLoaded', function() {
    showSection("File_choose");
});



    function showSection(sectionId) {
        if (sectionId === "File_choose") {
            document.getElementById("CV_choose").style.display = "none";
            document.getElementById("File_choose").style.display = "block";
        }
        if (sectionId === "CV_choose") {
            document.getElementById("CV_choose").style.display = "block";
            document.getElementById("File_choose").style.display = "none";
        }
       
    }