async function conf_loadconf() {
        
        try {
            const response = await fetch('/load-conf-tabs');
        if (!response.ok) {
            print(`dbg 5434 : Erreur lors du chargement des onglets : ${response.statusText}`);
        }
        const confs = await response.json();
        await conf_createTabs(confs.Tabs)
        return confs;
       
       
    } catch (error) {
        console.error('Erreur dans generateTabs:', error);
    }
}

function conf_createTabs(tabs) {

    const tabactiv="New";
    let html = '';
    html += `<button id="New" class="tab active" onclick="changeTab('New')">New</button>\n`;
   
    // Vérifier si le tableau est vide ou non défini
    if (!tabs || tabs.length === 0) {
        console.error('Le tableau des onglets est vide ou non défini.');
        document.getElementById('tabs').innerHTML = '<p>Aucun onglet disponible.</p>';
        
        //return;
    }

    // Générer les boutons si le tableau contient des données
    //.tab.active
    tabs.forEach(tab => {
        if (tab.id==tabactiv) {
            html += `<button id="${tab.id}" class="tab active" onclick="changeTab('${tab.id}')">${tab.label}</button>\n`;
        }
        else
        {
            html += `<button id="${tab.id}" class="tab" onclick="changeTab('${tab.id}')">${tab.label}</button>\n`;
        }
    });
    html += `<button id="All" class="tab" onclick="changeTab('All')">All</button>\n`;
    // Insérer le HTML généré dans l'élément avec l'ID "tabs"
    document.getElementById('tabs').innerHTML = html;   
}