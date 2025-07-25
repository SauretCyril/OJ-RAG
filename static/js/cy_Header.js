function generateTableHeaders_new() {
    const theadRow = document.querySelector('thead tr');
    if (!theadRow) return;
    theadRow.innerHTML = '';

    (getState('columns') || []).forEach(col => {
        if (colisvisible(col.type) && col.visible === true) {
            const th = document.createElement('th');
            th.style.width = col.width || '';
            th.classList.add('filter-cell-col');
            th.textContent = col.title || '';
            theadRow.appendChild(th); // ← Correction ici
        }
    });
}
function generateTableHeaders() {
    const thead = document.querySelector('thead');
    if (!thead) return;
    thead.innerHTML = '';

    // Ligne des titres
    const theadRow = document.createElement('tr');
    // Ligne des filtres
    const filterRow = document.createElement('tr');

    (getState('columns') || []).forEach(col => {
        if (colisvisible(col.type) && col.visible === true) {
            // Header cell
            const th = document.createElement('th');
            th.style.width = col.width || '';
            th.classList.add('filter-cell-col');
            th.textContent = col.title || col.key || '';
            theadRow.appendChild(th);

            // Filter cell
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
                input.classList.add('filter-container');
                input.type = 'text';
                input.id = `filter-${col.key}`;
                input.placeholder = 'Filter';
                filterCell.appendChild(input);
                input.addEventListener('input', filterTable);
            }
            filterRow.appendChild(filterCell);
        }
    });

    // Ajout des boutons fixes si besoin
    // (à adapter selon ton besoin, ici exemple)
    // document.getElementById('fix_btn-edit').onclick = () => { fix_openEditModal(); };
    // document.getElementById('fix_btn-open').onclick = () => { fix_open_dir(); };
    // document.getElementById('fix_btn-delete').onclick = () => { updateCurrentAnnonce('etat', 'DELETED'); };

    // Ajout des lignes au thead
    thead.appendChild(theadRow);
    thead.appendChild(filterRow);

    // Ajout du header et filtre status si besoin
    // const statusHeader = document.createElement('th');
    // statusHeader.classList.add('header');
    // theadRow.appendChild(statusHeader);

    // const statusFilterCell = document.createElement('th');
    // filterRow.appendChild(statusFilterCell);
}