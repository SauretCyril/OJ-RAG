/**
 * Charge les colonnes depuis le serveur
 * Si le fichier n'existe pas, conserve les colonnes par défaut
 */
async function loadColumnsFromServer() {
    try {
        const response = await fetch('/load_conf_cols', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            console.log(`Erreur lors du chargement des colonnes : ${response.statusText}`);
            // En cas d'échec, on s'assure que les colonnes par défaut sont utilisées
            setState('columns', [...window.columns]);
            return;
        }

        const data = await response.json();

        if (data.error) {
            console.error('Erreur du serveur :', data.error);
            // En cas d'erreur, on s'assure que les colonnes par défaut sont utilisées
            setState('columns', [...window.columns]);
            return;
        }

        if (Array.isArray(data)) {
            // Mettre à jour les colonnes globales en conservant la compatibilité
            updateColumns(data);
            console.log('Colonnes chargées avec succès depuis le serveur.');
        } else {
            console.error('Le fichier .cols ne contient pas un tableau valide.');
            //alert('Le fichier .cols est invalide.');
            // En cas de format invalide, on s'assure que les colonnes par défaut sont utilisées
            setState('columns', [...window.columns]);
        }
    } catch (error) {
        console.error('Erreur lors du chargement des colonnes :', error);
        //alert('Erreur lors du chargement des colonnes.');
        // En cas d'exception, on s'assure que les colonnes par défaut sont utilisées
        setState('columns', [...window.columns]);
    }
}

/**
 * Met à jour les colonnes en fusionnant les nouvelles avec les existantes
 * @param {Array} newColumns - Nouvelles colonnes à fusionner
 */
function updateColumns(newColumns) {
    if (!Array.isArray(newColumns)) {
        console.error('Le paramètre newColumns doit être un tableau.');
        return;
    }

    // On utilise les colonnes par défaut comme base
    let currentColumns = [...window.columns];
    
    // Créer un dictionnaire pour un accès rapide aux colonnes existantes par clé
    const columnsMap = new Map(currentColumns.map(col => [col.key, col]));

    // Parcourir les nouvelles colonnes
    newColumns.forEach(newCol => {
        if (!newCol.key) {
            console.warn('Une colonne sans clé a été ignorée:', newCol);
            return;
        }

        if (columnsMap.has(newCol.key)) {
            // Mettre à jour la colonne existante
            const existingCol = columnsMap.get(newCol.key);
            if (existingCol.fixed !== true) {
                Object.assign(existingCol, newCol); // Fusionner les propriétés
            }
        } else {
            // Ajouter une nouvelle colonne qui n'existe pas dans les colonnes par défaut
            currentColumns.push(newCol);
        }
    });

    // Mettre à jour à la fois window.columns (pour compatibilité) et l'état centralisé
    window.columns = currentColumns;
    setState('columns', currentColumns);
    
    console.log('Mise à jour des colonnes terminée:', currentColumns.length, 'colonnes');
}