function updateAnnonces_byfile(file, key, value) {
    try {
        const index = window.annonces.findIndex(a => Object.keys(a)[0] === file);
        console.log("updateAnnonces_byfile: " + index + " - " + file + " - " + key + " - " + value);
        if (index === -1) {
            console.error("Fichier non trouvé:", file);
            return;
        }
        
        window.annonces[index][file][key] = value;
        
        // Sauvegarder automatiquement les changements
        saveTableData()
            .then(() => {
                console.log('Modification par fichier sauvegardée automatiquement');
            })
            .catch(error => {
                console.error('Erreur lors de la sauvegarde automatique:', error);
            });
    } catch (err) {
        console.error("Erreur dans updateAnnonces_byfile:", err);
    }
}

function updateAnnonces(index, key, value) {
    try {
        const filePath = Object.keys(window.annonces[index])[0];
        
        // Vérifier si la valeur a réellement changé
        const oldValue = window.annonces[index][filePath][key];
        if (oldValue === value) {
            console.log('JS-002 : Aucun changement détecté pour', key);
            return;
        }
        
        window.annonces[index][filePath][key] = value;
        console.log("JS-001 : updateAnnonces: " + key + " = " + value + " (ancien: " + oldValue + ")");
        
        // Sauvegarder automatiquement les changements
        saveTableData()
            .then(() => {
                console.log('JS-003 : ✓ Modification sauvegardée automatiquement pour ' + key);
            })
            .catch(error => {
                console.error('JS-004 : ✗ Erreur lors de la sauvegarde automatique:', error);
                // Restaurer l'ancienne valeur en cas d'erreur
                window.annonces[index][filePath][key] = oldValue;
            });
    } catch (error) {
        console.error('ER-005 : Erreur dans updateAnnonces:', error);
    }
}

function updateAnnonces_externe(index, key, value) {
    return new Promise((resolve, reject) => {
        try {
            const filePath = Object.keys(window.annonces[index])[0];
            window.annonces[index][filePath][key] = value;
            resolve();
        } catch (error) {
            reject(error);
        }
    });
}



function UpdateState(rowId,col,value) {
    const selectedRow = document.getElementById(rowId);
    const Cell = selectedRow.querySelector('td:nth-child(' + (window.columns.findIndex(col => col.key === col) + 1) + ')');
                            if (Cell) {
                                Cell.textContent = value;
                                //updateAnnonces(index, col, value);
                            }
}


function set_current_row() {
    // Reset the background color of all rows
    
    const ThrowId = window.CurrentRow;
   
    document.querySelectorAll('#table-body tr').forEach(row => {
        row.style.backgroundColor = ''; // Reset to original color
    });

    // Set the backgr/* ound color of the selected row to light blue
    const selectedRow = document.getElementById(ThrowId);
    if (selectedRow) {
        selectedRow.style.backgroundColor = 'lightblue';
    }
}
