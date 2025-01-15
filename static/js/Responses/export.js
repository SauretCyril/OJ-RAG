async function loadNotesData(filePath) {
    const response = await fetch('/read_csv_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: filePath })
    });
    return response.json();
}

async function mergeNotesData(annonces) {
    for (const itemWrapper of annonces) {
        const filePath = Object.keys(itemWrapper)[0];
        const item = itemWrapper[filePath];
        const dirPath = filePath.substring(0, filePath.lastIndexOf('/'));
        const notesFilePath = `${dirPath}/${item.dossier}_notes.csv`;

        try {
            const notesData = await loadNotesData(notesFilePath);
            item.notes = notesData.map(note => `${note.key}: ${note.value}`).join('; ');
        } catch (error) {
            console.error(`Error loading notes for ${filePath}:`, error);
            item.notes = '';
        }
    }
}

function generateCSV(columns, data) {
    const csvRows = [];

    // Add header row
    const headers = columns.map(col => col.title);
    csvRows.push(headers.join(','));

    // Add data rows
    data.forEach(itemWrapper => {
        const filePath = Object.keys(itemWrapper)[0];
        const item = itemWrapper[filePath];
        const row = columns.map(col => item[col.key] || '');
        csvRows.push(row.join(','));
    });

    return csvRows.join('\n');
}

function downloadCSV(csvContent, fileName) {
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', fileName);
    a.click();
}

async function exportToCSV() {
    await mergeNotesData(window.annonces);
    const csvContent = generateCSV(window.columns, window.annonces);
    downloadCSV(csvContent, 'annonces.csv');
}

// Call the function to export data to CSV
