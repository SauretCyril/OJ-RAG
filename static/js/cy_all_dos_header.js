


function generateTableHeaders() {
    const thead = document.querySelector('thead tr');
    const filterRow = document.querySelector('thead tr:nth-child(2)');
    // Clear existing headers
    thead.innerHTML = '';
    filterRow.innerHTML = '';
    
    window.columns.forEach(col => {
        if (colisvisible(col.type) && col.visible === true) {
            // Create header cell
            const th = document.createElement('th');
            th.style.width = col.width;
            th.classList.add('filter-cell-col');
            //th.textContent = col.title.charAt(0).toUpperCase() + col.key.slice(1);
            th.textContent = col.title;
            thead.appendChild(th);

            // Create filter cell
            const filterCell = document.createElement('th');
            
            filterCell.classList.add('filter-cell');
            if (col.key === 'categorie' || col.key === 'etat' || col.key === 'todo' || col.key === 'type') {
                const container = document.createElement('div');
                container.classList.add('filter-container');

                const input = document.createElement('input');
                input.type = 'text';
                input.id = `filter-${col.key}`;
                input.placeholder = 'Filter';
                container.appendChild(input);

                const select = document.createElement('select');
                select.id = `select-${col.key}`;
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'All';
                select.appendChild(option);
                container.appendChild(select);

                filterCell.appendChild(container);

                input.addEventListener('input', filterTable);
                select.addEventListener('change', () => {
                    input.value = select.value;
                    filterTable();
                });
            } else {
                const input = document.createElement('input');
                input.classList.add('filter-container')
                input.type = 'text';
                input.id = `filter-${col.key}`;
                input.placeholder = 'Filter';
                filterCell.appendChild(input);
                input.addEventListener('input', filterTable);
            }
            filterCell.classList.add('filter-cell');
            filterRow.appendChild(filterCell);
        }
    });

    // Add status header and filter cell
    const statusHeader = document.createElement('th');
    statusHeader.classList.add('header');
    // statusHeader.textContent = 'Status';
    thead.appendChild(statusHeader);

    const statusFilterCell = document.createElement('th');
    
}