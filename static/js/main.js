document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const jobFile = document.getElementById('jobFile').files[0];
    
    if (!jobFile) {
        alert('Veuillez sélectionner les fichiers requis.');
        return;
    }

    const q2_job = 
        "peux tu me faire un plan détaillé de l'offre avec les sections en précisant bien ce qui est obligatoire, optionnelle :" +
        "- Titre poste proposé," +
        "- Duties (Description du poste décomposée en tache ou responsabilité)," +
        "- requirements (expérience attendues, )," +
        "- skills (languages, outils obligatoires)," +
        "- Savoir-être (soft skill)," +
        "- autres (toutes informations autre utile à connaitre)";
    console.log("q2_job", q2_job);
    formData.append('job_file', jobFile, jobFile.name);
    formData.append('q2_job', q2_job);

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
        const num_job = paths.job_file_dir;
        document.getElementById('NUM').textContent = num_job;
        console.log('num_job', num_job);

        // Extraction rapide du texte de l'offre
        const jobTextResponse = await fetch('/get_job_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ job_path: paths.job_path, q2_job: q2_job })
        });

        if (!jobTextResponse.ok) {
            throw new Error('Erreur lors de l\'extraction du texte de l\'offre');
        }

        const jobTextData = await jobTextResponse.json();

        // Log the data being sent to /save-job-text for debugging
        console.log('Saving job text data:', {
            job_text_data: jobTextData.formatted_text,
            job_number: num_job
        });

        // sauvegarder la réponse au niveau du répertoire de l'annonce
        const saveResponse = await fetch('/save-job-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ job_text_data: jobTextData.formatted_text, job_number: num_job })
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

    formData.append('cv_file', cvFile, cvFile.name); // Ensure the file is appended correctly with the correct name
    
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
        const num_cv = paths.cv_file_dir;
        document.getElementById('CV_NUM').textContent = num_cv;
        console.log('num_cv', num_cv);

        // Extraction rapide du texte du CV
        const cvTextResponse = await fetch('/get_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cv_path: paths.cv_path })
        });

        if (!cvTextResponse.ok) {
            throw new Error('Erreur lors de l\'extraction du texte du CV');
        }

        const cvTextData = await cvTextResponse.json();

        // Log the data being sent to /save-cv-text for debugging
        console.log('Saving CV text data:', {
            cv_text_data: cvTextData.formatted_text,
            cv_number: num_cv
        });

        // sauvegarder la réponse au niveau du répertoire du CV
        const saveResponse = await fetch('/save-cv-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cv_text_data: cvTextData.formatted_text, cv_number: num_cv })
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

document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
});


