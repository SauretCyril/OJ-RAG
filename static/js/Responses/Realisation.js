window.realizations_data = {}

function loadRealizationsData() {
    fetch('/read_realizations', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            window.realizations_data = data.realizations;
            //showRealizationsForm(window.realizations_data);
        } else {
            alert('Erreur lors de la lecture des réalisations: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading realizations:', error);
    });
}

function showRealizationsForm(realizations) {
    const formHtml = `
        <div id="realizationsForm">
            <h2>Gérer les Réalisations</h2>
            <table id="realizationsTable">
                <thead>
                    <tr>
                        <th>Num</th>
                        <th>Titre Poste</th>
                        <th>Etape Solution</th>
                        <th>Résultats</th>
                        <th>Savoir Être</th>
                        <th>Savoir-Faire</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${realizations.map((realization, index) => `
                        <tr>
                            <td>${index + 1}</td>
                            <td><input type="text" value="${realization.titrePoste}" /></td>
                            <td><textarea>${realization.etapeSolution}</textarea></td>
                            <td><input type="text" value="${realization.resultats}" /></td>
                            <td><input type="text" value="${realization.savoirEtre}" /></td>
                            <td><input type="text" value="${realization.savoirFaire}" /></td>
                            <td><button onclick="removeRealization(this)">Supprimer</button></td>
                        </tr>
                    `).join('')}
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
}

function addRealization() {
    const table = document.getElementById('realizationsTable').getElementsByTagName('tbody')[0];
    const newRow = table.insertRow();
    newRow.innerHTML = `
        <tr>
            <td>${table.rows.length}</td>
            <td><input type="text" /></td>
            <td><textarea></textarea></td>
            <td><input type="text" /></td>
            <td><input type="text" /></td>
            <td><input type="text" /></td>
            <td><button onclick="removeRealization(this)">Supprimer</button></td>
        </tr>
    `;
}

function removeRealization(button) {
    const row = button.parentNode.parentNode;
    row.parentNode.removeChild(row);
}

function saveRealizations() {
    const table = document.getElementById('realizationsTable').getElementsByTagName('tbody')[0];
    const realizations = [];
    for (let i = 0; i < table.rows.length; i++) {
        const row = table.rows[i];
        const realization = {
            num: i + 1,
            titrePoste: row.cells[1].getElementsByTagName('input')[0].value,
            etapeSolution: row.cells[2].getElementsByTagName('textarea')[0].value,
            resultats: row.cells[3].getElementsByTagName('input')[0].value,
            savoirEtre: row.cells[4].getElementsByTagName('input')[0].value,
            savoirFaire: row.cells[5].getElementsByTagName('input')[0].value
        };
        realizations.push(realization);
    }

    fetch('/save_realizations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ realizations: realizations })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert('Réalisations enregistrées avec succès');
        } else {
            alert('Erreur lors de l\'enregistrement des réalisations: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error saving realizations:', error);
    });
}

function closeRealizationsForm() {
    const form = document.getElementById('realizationsForm');
    if (form) {
        form.remove();
    }
    window.location.href = 'RP_index.html';
}