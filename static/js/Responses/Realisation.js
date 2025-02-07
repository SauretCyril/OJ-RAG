window.realizations_data = [];

const columns = [
    { id: 'ordre', label: 'Ordre', type: 'number', style: 'width: 50px;' },
    { id: 'titrePoste', label: 'Titre Poste', type: 'text', style: 'width: 150px;' },
    { id: 'etapeSolution', label: 'Etape Solution', type: 'textarea', style: 'width: 200px;' },
    { id: 'resultats', label: 'Résultats', type: 'text', style: 'width: 150px;' },
    { id: 'savoirEtre', label: 'Savoir Être', type: 'select', style: 'width: 150px;', options: ['Option 1', 'Option 2', 'Option 3'] },
    { id: 'savoirFaire', label: 'Savoir-Faire', type: 'select', style: 'width: 150px;', options: ['Option A', 'Option B', 'Option C'] },
    { id: 'deleteRow', label: 'Actions', type: 'deleteRow', style: 'width: 100px;' }
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
        console.log('Data received:', JSON.stringify(data)); // Log the data received
        if (data.status === "success") {
            window.realizations_data = data.realizations;
            updateRealizationsTableBody(); // Update the table body with the new data
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
            <table id="realizationsTable">
                <thead id="realizationsTableHead">
                    <tr>
                        ${columns.map(column => `<th style="${column.style}">${column.label}</th>`).join('')}
                    </tr>
                </thead>
                <tbody id="realizationsTableBody">
                   
                </tbody>
            </table>
            <button onclick="addRealization()">Ajouter</button>
            <button onclick="saveRealizations()">Enregistrer</button>
            <button onclick="closeRealizationsForm()">Retourner à la page d'accueil</button>
        </div>
    `;

    const formContainer = document.createElement('div');
    formContainer.innerHTML = formHtml;
    document.body.appendChild(formContainer);
    updateRealizationsTableBody();
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
    updateRealizationsTableBody();
}

// Fonction pour mettre à jour le corps du tableau des réalisations
function updateRealizationsTableBody() {
    const tableBody = document.getElementById('realizationsTableBody');
    tableBody.innerHTML = window.realizations_data.map((realization, index) => `
        <tr>
            ${columns.map(column => {
                if (column.type === 'select') {
                    return `<td><select onchange="updateRealization(${index}, '${column.id}', this.value)">${column.options.map(option => `<option value="${option}" ${realization[column.id] === option ? 'selected' : ''}>${option}</option>`).join('')}</select></td>`;
                } else if (column.type === 'textarea') {
                    return `<td><textarea style="${column.style}" onchange="updateRealization(${index}, '${column.id}', this.value)">${realization[column.id]}</textarea></td>`;
                } else if (column.type === 'deleteRow') {
                    return `<td><button onclick="removeRealization(this)">${column.label}</button></td>`;
                } else {
                    return `<td><input type="${column.type}" style="${column.style}" value="${realization[column.id]}" onchange="updateRealization(${index}, '${column.id}', this.value)" /></td>`;
                }
            }).join('')}
        </tr>
    `).join('');
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
        sortRealizationsByOrder();
    }
});

function removeRealization(button) {
    const row = button.parentNode.parentNode;
    const index = row.rowIndex - 1; // Adjust for header row
    window.realizations_data.splice(index, 1);
    updateRealizationsTableBody();
}