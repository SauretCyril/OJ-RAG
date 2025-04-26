function updateAnnonces_byfile(file, key, value) {
    try {
        const index = window.annonces.findIndex(a => Object.keys(a)[0] === file);
        alert("updateAnnonces_byfile" + " - " + index +"- " +file +" - "+key + " - " + value);
        if (index === -1) return;
        
        window.annonces[index][file][key] = value;
        refresh();
    } catch (err) {
        console.error("update annonce", err);
    }
}

function updateAnnonces(index, key, value) {
    const filePath = Object.keys(window.annonces[index])[0];
    
    window.annonces[index][filePath][key] = value;
    //alert("updateAnnonces =" + window.annonces[index][filePath][key]);
    
    
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
