window.runAnnoncesGui = function() {
    fetch('/run_annonces_gui', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.message || "Lancement demandé !");
        })
        .catch(err => {
            console.log("Erreur lors du lancement liste annonce: " + err);
        });
};


window.runAnalysePromptImage = function() {
    //alert("Lancement de l'analyse du prompt...");
    fetch('/run_analyse_prompt', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.message || "Lancement demandé !");
        })
        .catch(err => {
            console.log("Erreur lors du lancement analyse prompt: " + err);
        });
};

window.runImagesProduction = function() {
    //alert("Lancement de la production d'images...");
    fetch('/run_images_production', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.message || "Lancement demandé !");
        })
        .catch(err => {
            console.log("Erreur lors du lancement production images: " + err);
        });
};

window.fix_open_analyse = function(numDossier) {
    //alert("Lancement de l'analyse générale pour le dossier " + numDossier + "...");
    fetch('/run_general_analyse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ numdos: numDossier })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message || "Lancement demandé !");
    })
    .catch(err => {
        console.log("Erreur lors du lancement de l'analyse générale: " + err);
    });
}; 