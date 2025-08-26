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


window.runAnalysePrompt = function() {
    alert("Lancement de l'analyse du prompt...");
    fetch('/run_analyse_prompt', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.message || "Lancement demandé !");
        })
        .catch(err => {
            console.log("Erreur lors du lancement analyse prompt: " + err);
        });
};