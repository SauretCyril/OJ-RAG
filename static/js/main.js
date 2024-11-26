document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const jobFile = document.getElementById('jobFile').files[0];
    
    if (!jobFile) {
        alert('Veuillez sélectionner les fichiers requis.');
        return;
    }

    formData.append('job_file', jobFile, jobFile.name); // Ensure the file is appended correctly with the correct name
    
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
        const jobTextResponse = await fetch('/get_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ job_path: paths.job_path })
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

document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
});


