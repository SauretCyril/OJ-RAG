function updateFilterValues(filters) {
    //console.log('Filters object:', typeof(filters), filters); // Vérifier le format de filters
    // Itérer directement sur les clés de l'objet filters

    // forEach((col =W
    for (const key in filters) {
        if (filters.hasOwnProperty(key)) {
            //console.log(`Filter value for ${key}:`, filters[key]); 
            const filterElement = document.getElementById(`filter-${key}`);
            const selectElement = document.getElementById(`select-${key}`);
            if (filterElement) {
                filterElement.value = filters[key] || '';
                //console.log(`Filter value for ${key}:`, filterElement.value); // Add console.log
            }
            if (selectElement) {
                const option = document.createElement('option');
                option.value = filters[key];
                option.textContent = filters[key];
                selectElement.appendChild(option);
                selectElement.value = filters[key];
            }
        }
    }
}

function saveFilterValues(filters) {
    fetch('/save_filters_json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filters: filters,
            tabActive: window.tabActive
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === "success") {
            //console.log('Filter values successfully saved.');
        } else {
            console.error('Error saving filter values:', data.message);
        }
    })
    .catch(error => {
        console.error('An unexpected error occurred while saving filter values:', error);
    });
}

// Function to filter table rows based on input values
function filterTable() {
    const filters = {};
    // Collect filter values
    window.columns.forEach(col => {
        if (colisvisible(col.type) && col.visible === true) {
            const filterElement = document.getElementById(`filter-${col.key}`);
            if (filterElement) {
                filters[col.key] = filterElement.value.toLowerCase();
            }
        }
    });

    const rows = document.querySelectorAll('#table-body tr');
    //console.log(`Filter for ${rows.length} rows...`);
    //console.log("--------Filtering --------------------------------")
    rows.forEach(row => {
        let shouldDisplay = true;
        // Check each cell against the filter
        //filters.forEach(col => {
        let key="";
        let cellIndex=0;
        window.columns.forEach(col => {
            if (colisvisible(col.type) && col.visible === true) {
                
              
                const cell = row.querySelector(`td:nth-child(${cellIndex})`);
                if (cell)
                {
                    if (cell.hasAttributes){ 
                            key=cell.getAttribute('data-key');
                            filterValue=filters[key];
                            //console.log("---cellIndex: key = "+ key + "  |  value =" +filterValue);
                            
                            const cellValue = cell.textContent.toLowerCase();
                            
                            if (filterValue && !cellValue.includes(filters[key])) {
                                shouldDisplay = false;
                                
                            }
                    }
                }
                cellIndex++;
             
            }
        });
        row.style.display = shouldDisplay ? '' : 'none';
    });

    // Save filter values to JSON file
    saveFilterValues(filters);
}
