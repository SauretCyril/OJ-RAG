async function conf_loadconf() {
    try {
        const response = await fetch('/load_conf_tabs');
        
        // Vérifier si la réponse est OK
        if (!response.ok) {
            if (response.status === 404) {
                await conf_createTabs([]);

            } else {
                console.error(`Erreur lors du chargement des onglets : ${response.statusText}`);
            }
            return null; // Arrêter l'exécution si le fichier n'existe pas
        }
        else {
            // Lire et traiter la réponse JSON
            const confs = await response.json();
            if (confs && confs.Tabs) {
                await conf_createTabs(confs.Tabs);
                return confs;
            }
        } 
       

       

    } catch (error) {
        console.error('Erreur dans conf_loadconf:', error);
        document.getElementById('tabs').innerHTML = '<p>Une erreur est survenue lors du chargement de la configuration.</p>';
    }
}

function conf_createTabs(tabs) {

    const tabactiv="New";
    let html = '';
    html += `<button id="New" class="tab active" onclick="changeTab('New')">New</button>\n`;
   
    // Vérifier si le tableau est vide ou non défini
    if (!tabs || tabs.length === 0) {
        //console.error('Le tableau des onglets est vide ou non défini.');
        document.getElementById('tabs').innerHTML = '<p>Aucun onglet disponible.</p>';
        
        //return;
    }

    // Générer les boutons si le tableau contient des données
    //.tab.active
    if (tabs.length > 0) {
        console.log('Génération des onglets:', tabs);
    
        tabs.forEach(tab => {
            if (tab.id==tabactiv) {
                html += `<button id="${tab.id}" class="tab active" onclick="changeTab('${tab.id}')">${tab.label}</button>\n`;
            }
            else
            {
                html += `<button id="${tab.id}" class="tab" onclick="changeTab('${tab.id}')">${tab.label}</button>\n`;
            }
        });
    }
    html += `<button id="All" class="tab" onclick="changeTab('All')">All</button>\n`;
    // Insérer le HTML généré dans l'élément avec l'ID "tabs"
    document.getElementById('tabs').innerHTML = html;   
}



function setNewTab(){
    const activeTab = document.querySelector('.tab.active');
    if (activeTab !== null) {
        window.tabActive=activeTab.textContent;
    }
}

function changeTab(tabName) {
    // Remove 'active' class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    // Add 'active' class to the clicked tab
    document.querySelector(`.tab[onclick="changeTab('${tabName}')"]`).classList.add('active');
  
    setNewTab();
    refresh();
}

function ChangeToActiveTab() {
     changeTab(window.tabActive);
}