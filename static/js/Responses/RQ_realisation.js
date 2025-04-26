
function mistral_analyser_experiences()
{
    let question = "Analyse cette réalisation et extrait les informations suivantes sous format JSON structuré:"
    question+="{"
    question+='"contexte": "description du contexte de la mission",'
    question+='"titre": "intitulé du poste ou de la mission",'
    question+='"result": "résultats obtenus",'
    question+='"savoir_faire": ["compétence technique 1", "compétence technique 2"],'
    question+='"savoir_etre": ["qualité comportementale 1", "qualité comportementale 2"]'
    question+="}"
    question+="Respecte strictement ce format pour permettre le parsing JSON."

    const directory = "G:/OneDrive/Entreprendre/Actions-4/M488/RDV.6_Du_28-02-2025/Realisations"
    const role = "En tant qu'expert en recrutement, analyse ce document et réponds au format demandé."
    analyser_experiences(directory,role,question)
}

function analyser_experiences(){
    alert("Analyse des expériences en cours...")
   
  

    showLoadingOverlay();
    fetch('/analyser_documents', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            question: question,
            directory: directory,
            role: role,
            type_doc: "docx",
            subject: "annalyse_realisations"

        })
    })
    .then(response => {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json().then(data => {
                console.log('Données d\'analyse reçues:', data);
                     // Afficher un message de succès
                    alert(`Analyse terminée avec succès!`);

            });
        } 
    })
    .catch(error => {
        console.error('Erreur lors de l\'analyse:', error);
        alert('Erreur lors de l\'analyse des expériences');
    })
    .finally(() => {
        hideLoadingOverlay();
    });
}

