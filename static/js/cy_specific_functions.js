
async function fix_open_prompt_analyse() {
    const annonce = get_currentAnnonce();
    
    
    if (!annonce) return;
    isDependOn=true;
    const numeroDossier = annonce.dossier;
    const descriptif = annonce.description ;
    file_name = "_Prompt_";
    file_path=AppState.currentDossier = await getCookie('current_dossier');
    const response =  fetch('/open_prompt_table', {
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
