window.realizations_data = [];

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
                        <th>Ordre</th>
                        <th>Titre Poste</th>
                        <th>Etape Solution</th>
                        <th>Résultats</th>
                        <th>Savoir Être</th>
                        <th>Savoir-Faire</th>
                        <th>Actions</th>
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
    tableau_fill();
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
            <td><input type="number" value="${realization.ordre}" onchange="updateRealization(${index}, 'ordre', this.value)" /></td>
            
            <td><input type="text" value="${realization.titrePoste}" onchange="updateRealization(${index}, 'titrePoste', this.value)" /></td>
            <td><textarea onchange="updateRealization(${index}, 'etapeSolution', this.value)">${realization.etapeSolution}</textarea></td>
            <td><input type="text" value="${realization.resultats}" onchange="updateRealization(${index}, 'resultats', this.value)" /></td>
            <td><input type="text" value="${realization.savoirEtre}" onchange="updateRealization(${index}, 'savoirEtre', this.value)" /></td>
            <td><input type="text" value="${realization.savoirFaire}" onchange="updateRealization(${index}, 'savoirFaire', this.value)" /></td>
            <td><button onclick="removeRealization(this)">Supprimer</button></td>
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

// Fonction pour remplir le tableau des réalisations
function tableau_fill() {
    const tableBody = document.getElementById('realizationsTableBody');
    tableBody.innerHTML = window.realizations_data.map((realization, index) => `
        <tr>
            <td><input type="number" value="${realization.ordre}" onchange="updateRealization(${index}, 'ordre', this.value)" /></td>
            
            <td><input type="text" value="${realization.titrePoste}" onchange="updateRealization(${index}, 'titrePoste', this.value)" /></td>
            <td><textarea onchange="updateRealization(${index}, 'etapeSolution', this.value)">${realization.etapeSolution}</textarea></td>
            <td><input type="text" value="${realization.resultats}" onchange="updateRealization(${index}, 'resultats', this.value)" /></td>
            <td><input type="text" value="${realization.savoirEtre}" onchange="updateRealization(${index}, 'savoirEtre', this.value)" /></td>
            <td><input type="text" value="${realization.savoirFaire}" onchange="updateRealization(${index}, 'savoirFaire', this.value)" /></td>
            <td><button onclick="removeRealization(this)">Supprimer</button></td>
        </tr>
    `).join('');
}

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