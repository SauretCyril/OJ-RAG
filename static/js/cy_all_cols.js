
async function loadColumnsFromServer() {
    try {
        const response = await fetch('/load-conf-cols', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            console.log (`Erreur lors du chargement des colonnes : ${response.statusText}`);
            return;
        }

        const data = await response.json();

        if (data.error) {
            console.error('Erreur du serveur :', data.error);
            return;
        }

        if (Array.isArray(data)) {
            // Mettre à jour les colonnes globales
            updateColumns(data);
            console.log('Colonnes chargées avec succès depuis le serveur.');
        } else {
            console.error('Le fichier .cols ne contient pas un tableau valide.');
            alert('Le fichier .cols est invalide.');
        }
    } catch (error) {
        console.error('Erreur lors du chargement des colonnes :', error);
        alert('Erreur lors du chargement des colonnes.');
    }
}



function updateColumns(newColumns) {
    if (!Array.isArray(newColumns)) {
        console.error('Le paramètre newColumns doit être un tableau.');
        return;
    }
    oldcols=window.columns;
    // Créer un dictionnaire pour un accès rapide aux colonnes existantes par clé
    const columnsMap = new Map(oldcols.map(col => [col.key, col]));

    // Parcourir les nouvelles colonnes
    newColumns.forEach(newCol => {
        if (!newCol.key) {
            console.warn('Une colonne sans clé a été ignorée:', newCol);
            return;
        }

        if (columnsMap.has(newCol.key)) {
            // Mettre à jour la colonne existante
            const existingCol = columnsMap.get(newCol.key);
            if (existingCol.fixed != true)
            {
                Object.assign(existingCol, newCol); // Fusionner les propriétés
            }
        } 
    });
    console.log('Mise à jour des colonnes:', oldcols, '=>', window.columns);
    // Mettre à jour les colonnes globales
    window.columns = [...oldcols, ...newColumns.filter(col => !columnsMap.has(col.key))];
    console.log('Mise à jour des colonnes terminée:', window.columns);
}