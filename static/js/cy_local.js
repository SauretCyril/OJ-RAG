function ask_Local_file_explorer(chemin, TypeExploreur="document") {
    const path = chemin.replace(/\\/g, '/');
    //alert("dgb-loc-001 : Opening explorer for path:", path);
    fetch('/get_local_FileExplorer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            path: path,
            explorer_type: TypeExploreur
        })
    })
    .then(response => response.json())
    .then(response => {
        if (response.status === "success") {
            console.log("Directory explorer opened successfully.");
        } else {
            console.error("Error opening directory explorer:", response.message);
        }
    })
    .catch(error => {
        console.error("Error opening directory explorer:", error);
    });
}

async function ask_local_PromptTable() {
    const annonce = get_currentAnnonce();
    
    if (!annonce) return;
    isDependOn=true;
    const numeroDossier = annonce.dossier;
    const descriptif = annonce.description ;
    file_name = "_Prompt_";
    file_path=AppState.currentDossier = await getCookie('current_dossier');
    const response =  fetch('/get_local_PromptTable', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path:file_path,
                file_name:file_name,
                isDependOn: isDependOn,
                num_dossier: numeroDossier,
                descriptif: descriptif
            })
        });
}