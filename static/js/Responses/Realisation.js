window.realizations_data = [];

const columns = [
    { id: 'ordre', label: 'Ordre', type: 'number', style: 'min-width: 50px; color: black;' },
    { id: 'titrePoste', label: 'Titre Poste', type: 'text', style: 'min-width: 150px; color: black;' },
    { id: 'etapeSolution', label: 'Etape Solution', type: 'textarea', style: 'min-width: 350px; color: black;' },
    { id: 'resultats', label: 'Résultats', type: 'textarea', style: 'min-width: 150px; color: black;' },
    { id: 'savoirEtre', label: 'Savoir Être', type: 'select_multiple', style: 'min-width: 350px; color: black;', options: ['Option 1', 'Option 2', 'Option 3'] },
    { id: 'savoirFaire', label: 'Savoir-Faire', type: 'select_multiple', style: 'min-width: 350px; color: black;', options: ['Option A', 'Option B', 'Option C'] },
    { id: 'deleteRow', label: 'Remove', type: 'deleteRow', style: 'min-width: 50px; color: black;' }
];

// Fonction pour charger les réalisations
function loadRealizationsData() {
    fetch('/read_realizations', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        //console.log('Data received:', JSON.stringify(data)); // Log the data received
        if (data.status === "success") {
            window.realizations_data = data.realizations;
        } else {
            alert('Erreur-1255 lors de la lecture des réalisations: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error-1488 reading realizations:', error);
    });
}

// Fonction pour afficher le formulaire des réalisations
function showRealizationsForm() {
    const formHtml = `
        <div id="realizationsForm">
            <h2>Gérer les Réalisations</h2>
            <div class="table-responsive">
                <table id="realizationsTable" class="table table-bordered">
                    <thead id="realizationsTableHead">
                        <tr>
                            ${columns.map(column => `<th style="${column.style}">${column.label}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody id="realizationsTableBody">
                        <!-- Table body will be populated by updateRealizationsTableBody() -->
                    </tbody>
                </table>
            </div>
            <button onclick="addRealization()">Ajouter</button>
            <button onclick="saveRealizations()">Enregistrer</button>
            <button onclick="closeRealizationsForm()">Retourner à la page d'accueil</button>
        </div>
    `;

    const formContainer = document.createElement('div');
    formContainer.innerHTML = formHtml;
    document.body.appendChild(formContainer);
    
    // Ensure the form is fully constructed before updating the table body
    setTimeout(() => {
        updateRealizationsTableBody();
    }, 0);
}

function closeRealizationsForm() {

    const formContainer = document.getElementById('realizationsForm');
    if (formContainer) {
        formContainer.remove();
    }
}

// Fonction pour mettre à jour une réalisation
function updateRealization(index, key, value) {
    window.realizations_data[index][key] = value;
}

// Fonction pour ajouter une nouvelle réalisation
function addRealization() {
    const newRealization = {
        ordre: window.realizations_data.length + 1,
        titrePoste: '',
        etapeSolution: '',
        resultats: '',
        savoirEtre: '',
        savoirFaire: ''
    };
    window.realizations_data.push(newRealization);
    //updateRealizationsTableBody();
}

// Fonction pour mettre à jour le corps du tableau des réalisations
function updateRealizationsTableBody() {
    const tableBody = document.getElementById('realizationsTableBody');
    if (tableBody === null) {
        console.error('Table body not found');
        return;
    }
    tableBody.innerHTML = window.realizations_data.map((realization, index) => `
        <tr>
            ${columns.map(column => {
                if (column.type === 'select') {
                    return `<td><input type="text" style="background-color: yellow; ${column.style}" value="${realization[column.id]}" ondblclick="handleDoubleClick('${column.id}')" /></td>`;
                } else if (column.type === 'textarea') {
                    return `<td><textarea style="${column.style}" onchange="updateRealization(${index}, '${column.id}', this.value)">${realization[column.id]}</textarea></td>`;
                } else if (column.type === 'select_multiple') {
                    return `<td><textarea style="${column.style}" ondblclick="handleDoubleClick('${index},${column.id}')" onchange="updateRealization(${index}, '${column.id}', this.value)">${realization[column.id]}</textarea></td>`;
                } else if (column.type === 'deleteRow') {
                    return `<td><span style="cursor: pointer;" onclick="removeRealization(this)">&#10060;</span></td>`;
                } else {
                    return `<td><input type="${column.type}" style="${column.style}" value="${realization[column.id]}" onchange="updateRealization(${index}, '${column.id}', this.value)" /></td>`;
                }
            }).join('')}
        </tr>
    `).join('');
}

function handleDoubleClick(id) {
    //alert("OK "+ id);
    let dirName="";
    let filename="";
    if (id=== 'savoirEtre') {
        dirName= "DIR_SOFT_SK_FILE";
        filename= "SOFT_SK_FILE" ;
        
    }
    else if (id === 'savoirFaire')   {
        dirName= "DIR_HARD_SK_FILE";
        filename= "HARD_SK_FILE";
    } else { 
        alert("Erreur de colonne");
        return;

    }

    
    fetch(`/get_file_path`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ dirName: dirName, filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        //alert('Data received:', JSON.stringify(data)); // Log the data received
        if (data.filePath) {
            const file = data.filePath;
            //alert('Chemin du fichier récupéré avec succès: ' + file);
            // Handle the file path as needed
            open_notes(file,true,index, id);
        } else {
            alert('Erreur 147 : lors de la récupération du chemin du fichier: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error fetching file path:', error);
    });
}

// Fonction pour enregistrer les réalisations
function saveRealizations() {
    const dataToSend = { data: window.realizations_data };
    console.log('Data to be sent:', JSON.stringify(dataToSend)); // Log the data to be sent

    fetch('/save_realizations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataToSend)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === "success") {
            alert('Les réalisations ont été enregistrées avec succès.');
        } else {
            alert('Erreur-1256 lors de l\'enregistrement des réalisations: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error-1489 saving realizations:', error);
    });
}

/* 7 */
// Fonction pour trier le tableau en fonction de la colonne "Ordre"
function sortRealizationsByOrder() {
    window.realizations_data.sort((a, b) => a.ordre - b.ordre);
    updateRealizationsTableBody();
}

// Ajouter un écouteur d'événement pour trier le tableau lorsque la colonne "Ordre" est modifiée
document.addEventListener('change', function(event) {
    if (event.target && event.target.matches('input[type="number"]')) {
        //sortRealizationsByOrder();
    }
});

function removeRealization(button) {
    const row = button.parentNode.parentNode;
    const index = row.rowIndex - 1; // Adjust for header row
    window.realizations_data.splice(index, 1);
    //updateRealizationsTableBody();
}