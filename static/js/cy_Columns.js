

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