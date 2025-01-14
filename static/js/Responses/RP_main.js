// Add status tooltips
/* document.querySelectorAll('.status-badge').forEach(badge => {
    badge.title = `Dernier changement: ${new Date().toLocaleDateString()}`;
}); */

// Declare the global array
window.CONSTANTS=[];
window.CurrentRow ="";
window.tabActive = "Campagne";
window.annonces = [];
window.portalLinks=[];
window.portalLinks_columns = [
    { key: 'name', editable: false, width: '150px', visible: true,title:'name' },
    { key: 'url', editable: false, width: '200px', visible: false,title:'url' },
    { key: 'date', editable: true, width: '150px', visible: true,title:'Date' },
    { key: 'commentaire', editable: false, width: '200px', visible: false,title:'Commentaire' },
    { key: 'update', editable: true, width: '50px', visible: true,title:'update' },
    { key: 'update_date', editable: true, width: '150px', visible: true,title:'Date update' }
]

window.columns = [
    { key: 'dossier', editable: false, width: '80px', visible: true, type: 'tb',title:'Dos' },
    { 
        key: 'description', 
        class: 'description-cell', 
        editable: false, 
        style: { cursor: 'pointer', color: 'blue', textDecoration: 'underline' }, 
        event: 'click', 
        eventHandler: 'openUrlHandler', // Store function name as string
        width: '200px',
        visible: true,
        type: 'tb',
        title:'Description'
    },
    { key: 'id', editable: true, width: '100px',"visible":true,"type":"tb",title:'ID' },
    { key: 'entreprise', editable: true, width: '150px',"visible":true ,"type":"tb",title:'Entreprise' },
    
    { key: 'isJo', editable: false, width: '70px',"visible":true ,"type":"tb",title:'Manu' },
    { key: 'isSteal', editable: false, width: '70px',"visible":true ,"type":"tb",title:'Steal' },
    { key: 'GptSum', editable: false, width: '70px',"visible":true,"type":"tb",title:'Resum' },
    { key: 'CV', editable: false, width: '70px',"visible":true ,"type":"tb",title:'CV' },
    { key: 'CVpdf', editable: false, width: '70px',"visible":true ,"type":"tb",title:'.pdf' },
    
    { key: 'categorie', editable: true, class: 'category-badge', prefix: 'category-', width: '200px',"visible":false,"type":"tb",title:'Cat'  },
    { key: 'etat', editable: true, width: '95px',"visible":true ,"type":"tb",title:'Etat'  },
    { key: 'contact', editable: true, width: '150px',"visible":true ,"type":"tb",title:'Contact' },
    { key: 'tel', editable: true, width: '125px',"visible":false ,"type":"tb",title:'Tel.' },
    { key: 'mail', editable: true, width: '125px',"visible":false ,"type":"tb",title:'mail' },
    { key: 'Date', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt pub' },
    { key: 'Date_rep', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt Rep' }, 
    { key: 'Commentaire', editable: true, width: '150px',"visible":true,"type":"tb" ,title:'Commentaire' },
    { key: 'Notes', editable: false, width: '50px',"visible":true,"type":"tb" ,title:'Nt' },
    { key: 'todo', editable: true, width: '200px',"visible":true ,"type":"tb" ,title:'ToDo'},
    { key: 'url', editable: false, width: '100px',"visible":false ,"type":"tb",title:'Url' },
    { key: 'type', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Type'  },
    { key: 'annonce_pdf', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Annonce (pdf)' },
    { key: 'type_question', editable: true, width: '80px',"visible":false ,"type":"tb" ,title:'type Question'},
    { key: 'lien_Etape', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Lien Etape' },
    
    { key: 'CVfile', editable: true, width: '80px',"visible":false ,"type":"tb",title:'CVfile' },
    
];
/**
 * Saves the current configuration of columns.
 * Serializes the columns and sends them to the backend for saving.
 */
async function loadConstants() {
    try {
        const response = await fetch('/get_constants');
        window.CONSTANTS = await response.json();
    } catch (error) {
        console.error('Error loading constants:', error);
    }
    console.log('Constants loaded:', window.CONSTANTS);
}
function save_config_col() {
    const serializedColumns = serializeColumns(window.columns);
    
    fetch('/save_config_col', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            columns: serializedColumns,
            tabActive: window.tabActive
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            //console.log('Configuration saved successfully.');
        } else {
            console.error('Error saving configuration:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving configuration:', error);
    });
}
//save_config_col();


function loadFilterValues(tabActive) {
    fetch('/read_filters_json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tabActive: tabActive })
    })
    .then(response => response.json())
    .then(filters => {
        //console.log('Filter values loaded:', filters);
        if (filters)
        {
            updateFilterValues(filters);
            filterTable();
        }
    })
    .catch(error => {
        console.error('Error loading filter values:', error);
    });
}
// Example usage
function loadTableData(callback) {
    
    //reassignEventHandlers(window.columns);
    generateTableHeaders();
    //state = value de la liste box statusFilter
    //const state = document.getElementById('statusFilter').value;
    fetch('/read_annonces_json', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
        state: "En Cours"        
        })
    })
    .then(response => response.json())
    .then(data => {
        // Store the data in the global array
        window.annonces = data;
           
        const tableBody = document.getElementById('table-body');
        if (!tableBody) {
            throw new Error('Element with id "table-body" not found.');
        }

        tableBody.innerHTML = ''; // Clear existing rows

        const categories = new Set();
        const etats = new Set();
        const todos = new Set();
        const types = new Set();
        window.annonces.forEach((itemWrapper, index) => {
            const filePath = Object.keys(itemWrapper)[0];
            const item = itemWrapper[filePath];
            const dir_path = filePath.substring(0, filePath.lastIndexOf('/'));
            const isCvRef = item.Commentaire && item.Commentaire.includes('<CV-REF>');
            
            //let fichier_annonce = dir_path + '/' + item.dossier+"_annonce_.pdf";
            let fichier_annonce = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX'];
            console.log("<<fichier_annonce>>",fichier_annonce);
            let fichier_annonce_steal = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['STEAL_ANNONCE_SUFFIX'];
            //const fichier_annonce_resum = dir_path + '/' + item.dossier+"_gpt_request.pdf";
            const fichier_annonce_resum = dir_path + '/' + window.CONSTANTS['FILE_NAMES']['GPT_REQUEST_SUFFIX'];
             console.log("<<fichier_annonce_resum>>",fichier_annonce_resum);
            //const file_notes = dir_path + '/' + item.dossier+"_notes.txt";
            const file_notes = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['NOTES_FILE'];
            console.log("<<file_notes>>",file_notes);
            const row = document.createElement('tr');
            row.id = filePath;
            row.style.position = 'relative'; // Ajout du positionnement relatif sur la ligne
// forEach((col
            window.columns.forEach((col, colIndex) => {
                if (col.type === "tb" && col.visible === true) {
                    
                    const cell = document.createElement('td');
                    cell.setAttribute('data-key', col.key);
                   
                    
                    if (col.key === 'GptSum' ) 
                    {
                        const icon = document.createElement('span');
                        if (item[col.key] === 'O') {
                            //console.log('#### blanc:');
                            icon.textContent = '📗'; // Red book icon
                        } else  {
                            //console.log('#### vert:');
                            icon.textContent = '📕'; // Green book icon
                            icon.addEventListener(col.event, () => open_url(fichier_annonce_resum));
                        } 
                        icon.style.position = 'absolute';
                        icon.style.alignContent='center';
                        //icon.style.top = '0px';
                        icon.style.zIndex = '10'; // Ensure the icon is above the content
                        cell.appendChild(icon);
                    }
                   
                     else if  (col.key === 'CVpdf' && item['CV']=='O' ) 
                    {
                        //console.log('#### CV:', item[col.key]);
                        const icon = document.createElement('span');
                        if (item[col.key] === 'N') {
                            //console.log('#### blanc:');
                            icon.textContent = '📕'; // Red book icon
                        } else if (item[col.key] === 'O') {
                            //console.log('#### vert:');
                            icon.textContent = '📗'; // Green book icon
                        } 
                        icon.style.position = 'absolute';
                        icon.style.alignContent='center';
                        //icon.style.top = '0px';
                        icon.style.zIndex = '10'; // Ensure the icon is above the content
                        if (item[col.key] === 'O') {
                            icon.style.cursor = 'pointer';
                            icon.addEventListener('click', () => convert_cv(item.dossier, dir_path));
                        }
                        cell.appendChild(icon);
                      } 
                      else  if (col.key === 'CVpdf' && item['CV']=='N' )
                      {
                         
                            const icon = document.createElement('span');
                            icon.textContent = '⚪'; // White circle icon
                            icon.style.position = 'absolute';
                            icon.style.alignContent='center';
                            //icon.style.top = '0px';
                            icon.style.zIndex = '10';
                            cell.appendChild(icon);
                         
                     }                      
                     else if (col.key === 'CV') 
                     {
                        //console.log('#### CV:', item[col.key]);
                        const icon = document.createElement('span');
                        if (item[col.key] === 'N') {
                            //console.log('#### blanc:');
                            
                            icon.textContent = '📕'; // Red book icon
                        } else  {
                            //console.log('#### vert:');
                            icon.textContent = '📗'; // Green book icon
                        } 
                        icon.style.position = 'absolute';
                        icon.style.alignContent='center';
                        //icon.style.top = '0px';
                        icon.style.zIndex = '10'; // Ensure the icon is above the content
                        icon.style.cursor = 'pointer';
                        
                        icon.addEventListener('click', () => get_cv(item.dossier, dir_path,item[col.key],row.id));
                        cell.appendChild(icon);
                        
                    } 
                    else if (col.key === 'isJo')
                    {
                        const icon = document.createElement('span');
                         if (item[col.key] === 'N') {
                            //console.log('#### blanc:');
                            
                            icon.textContent = '📕'; // Red book icon
                        } else  {
                            //console.log('#### vert:');
                            icon.textContent = '📗'; // Green book icon
                           
                            icon.addEventListener(col.event, () => open_url(fichier_annonce));
                        } 
                        icon.style.position = 'absolute';
                        icon.style.alignContent='center';
                        //icon.style.top = '0px';
                        icon.style.zIndex = '10'; // Ensure the icon is above the content
                        icon.style.cursor = 'pointer';
                        cell.appendChild(icon);
                    }
                    else if (col.key === 'isSteal')
                    {
                        const icon = document.createElement('span');
                        if (item[col.key] === 'N') {
                            //console.log('#### blanc:');
                            
                            icon.textContent = '📕'; // Red book icon
                        } else if (item[col.key] === 'O') {
                            //console.log('#### vert:');
                            icon.textContent = '📗'; // Green book icon
                            icon.addEventListener(col.event, () => open_url(fichier_annonce_steal));
                        } 
                        icon.style.position = 'absolute';
                        icon.style.alignContent='center';
                        //icon.style.top = '0px';
                        icon.style.zIndex = '10'; // Ensure the icon is above the content
                        icon.style.cursor = 'pointer';
                        cell.appendChild(icon);
                    } else if (col.key === 'Notes' ) 
                        {
                            const heartIcon = document.createElement('span');
                            heartIcon.textContent = '❤️'; // Heart icon
                            heartIcon.style.cursor = 'pointer';
                            heartIcon.addEventListener('click', () => open_notes(file_notes));
                            cell.appendChild(heartIcon);
                        
                        }
                    else 
                    {
                        isurl=false;
                        if (col.key === 'description' && item.url) {
                            isurl = true;
                        }

                        if (isurl) {
                            cell.style.cursor = col.style.cursor;
                            cell.style.color = col.style.color;
                            cell.style.textDecoration = col.style.textDecoration;
                            cell.addEventListener(col.event, () => open_url(item.url));
                        } else {
                            cell.style.color = ''; // Default color
                            cell.style.textDecoration = ''; // Default text decoration
                        }
                        
                       
                      
                        cell.textContent = item[col.key];
                        if (col.class) cell.classList.add(col.class);
                        if (col.editable) cell.contentEditable = "true";
                        if (col.width) cell.style.width = col.width;
                    
                        cell.onblur = () => updateAnnonces(index, col.key, cell.textContent);
                    }
                    row.appendChild(cell);
                }
            });
            
            if (isCvRef) {
                row.style.backgroundColor = '#8be28b';
            }
            /*   */
            
            
            //tableBody.appendChild(row);

            row.addEventListener('contextmenu', function(e) 
            {
                e.preventDefault();
                const contextMenu = document.getElementById('contextMenu');
                contextMenu.style.display = 'block';
                contextMenu.style.left = `${e.clientX}px`;
                contextMenu.style.top = `${e.clientY}px`;
                contextMenu.dataset.targetRow = row.id;

                document.getElementById('EditRow').onclick = () => {
                    window.CurrentRow=contextMenu.dataset.targetRow;
                    set_current_row();
                    openEditModal(row.id);
                    contextMenu.style.display = 'none';
                };
             
                document.getElementById('SetCurrentRow').onclick = () => {
                    window.CurrentRow=contextMenu.dataset.targetRow;
                    contextMenu.style.display = 'none';
                    set_current_row();
                };
                document.getElementById('Open').onclick = () => {
                    window.CurrentRow=contextMenu.dataset.targetRow;
                    set_current_row();
                    open_dir(filePath);
                  
                    contextMenu.style.display = 'none';
                };

                 document.getElementById('Sscrape_url').onclick = () => {
                    window.CurrentRow=contextMenu.dataset.targetRow;
                    set_current_row();
                    //alert("Scraping de l'annonce en cours...",item.url,item.dossier,fichier_annonce_scrap);

                    scrape_url(item.url,item.dossier);
                  
                    contextMenu.style.display = 'none';
                };
                let resumexist="";
                document.getElementById('Resume').onclick = () => {
                    if (item.GptSum == "True")
                    {
                        let resumexist="Attention cela va écraser le résumé existant...";
                    }
                    const rowId = contextMenu.dataset.targetRow;
                    if (confirm("Voulez vous résumer l'annonce ? "+resumexist +"->" +fichier_annonce+ ": " + item.dossier )) {
                        window.CurrentRow=contextMenu.dataset.targetRow;
                        set_current_row();       
                        // call the function get answers
                        get_job_answer(fichier_annonce,item.dossier);
                        
                        }
                    };

                document.getElementById('Delete').onclick = () => {
             
                    if (confirm("Voulez-vous vraiment supprimer ce dossier ?")) {
                           updateAnnonces(index, 'etat', 'DELETED');
                        // Update the 'etat' column in the HTML row
                        const etatCell = row.querySelector('td:nth-child(' + (window.columns.findIndex(col => col.key === 'etat') + 1) + ')');
                        if (etatCell) {
                            etatCell.textContent = 'DELETED';
                        }
                        }
                    };
                document.getElementById('Repondue').onclick = () => {
                    const rowId = contextMenu.dataset.targetRow;
                    if (confirm("Vous avez répondu :")) {
                               
                        // Update the 'etat' column in the HTML row
                        UpdateState(rowId,'etat','close');
                        UpdateState(rowId,'todo','Répondue');
                       
                        }
                    };

                  
            });


            
            tableBody.appendChild(row);

            categories.add(item.categorie);
            etats.add(item.etat);
            todos.add(item.todo);
            types.add(item.type);
        });
     
        // Populate the filter-categorie dropdown
        const filterCategorie = document.getElementById('select-categorie');
        if (filterCategorie){
            categories.forEach(categorie => {
                const option = document.createElement('option');
                option.value = categorie;
                option.textContent = categorie;
                filterCategorie.appendChild(option);
            });
         }

        // Populate the filter-etat dropdown
        const filterEtat = document.getElementById('select-etat');
        if (filterEtat){
            etats.forEach(etat => {
                const option = document.createElement('option');
                option.value = etat;
                option.textContent = etat;
                filterEtat.appendChild(option);
            });
        }

        // Populate the filter-todo dropdown
        
        const filterTodo = document.getElementById('select-todo');
        if (filterTodo){
            todos.forEach(todo => {
                const option = document.createElement('option');
                option.value = todo;
                option.textContent = todo;
                filterTodo.appendChild(option);
            });
        }   

      
        const filterTypes = document.getElementById('select-type');
        if (filterTypes){
            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                filterTypes.appendChild(option);
            });
        }
        
        loadFilterValues(window.tabActive);
      
        
      
     
    })
    .catch(error => {
        console.error('Error loading table data:', error);
    });
    // Cacher le menu contextuel lors d'un clic ailleurs
    document.addEventListener('click', function() {
        document.getElementById('contextMenu').style.display = 'none';
    });
    saveTableData();
}
function getStatus(filepath){
    return "Toto";
}



// Function to filter table rows based on input values
function filterTable() {
    const filters = {};
    // Collect filter values
    window.columns.forEach(col => {
        if (col.type === "tb" && col.visible === true) {
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
            if (col.type === "tb" && col.visible === true) {
                
              
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
               /*  if (cell) {
                    const cellValue = cell.textContent.toLowerCase();
                    const filterValue = filters[col.key];
                    //console.log(`Cell value for ${col.key}: ${cellValue}, Filter value: ${filterValue}`);
                    if (filterValue && !cellValue.includes(filterValue)) {
                        shouldDisplay = false;
                    }
                } */
            }
        });
        row.style.display = shouldDisplay ? '' : 'none';
    });

    // Save filter values to JSON file
    saveFilterValues(filters);
}

// Function to update the global array when a cell is edited

function updateAnnonces_byfile(root, key, value) {
    try {
        // Assuming this code is running in a Node.js environment
        const fs = require('fs');
        const path = require('path');

        const file_path = path.join(root, ".data.json");

        if (fs.existsSync(file_path)) {
            const data = fs.readFileSync(file_path, 'utf8');
            const jsonData = JSON.parse(data);

            jsonData[key] = value;

            fs.writeFileSync(file_path, JSON.stringify(jsonData, null, 2), 'utf8');
            console.log("File updated successfully:", file_path);
        } else {
            console.error("File not found:", file_path);
        }
    } catch (err) {
        console.error("update annonce", err);
    }
}

function updateAnnonces(index, key, value) {
    const filePath = Object.keys(window.annonces[index])[0];
    window.annonces[index][filePath][key] = value;
    
    
}

function UpdateState(rowId,col,value) {
    const selectedRow = document.getElementById(rowId);
    const Cell = selectedRow.querySelector('td:nth-child(' + (window.columns.findIndex(col => col.key === col) + 1) + ')');
                            if (Cell) {
                                Cell.textContent = value;
                                //updateAnnonces(index, col, value);
                            }
}

function refresh()
{
    saveTableData()
        .then(() => {
            //console.log('Save completed, now loading table data...');
            loadTableData();
            set_current_row();
        })
        .catch(error => {
            console.error('Error during refresh:', error);
        });
}
// Function to save the global array to the JSON file
function saveTableData() {
    return new Promise((resolve, reject) => {
        fetch('/save_annonces_json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(window.annonces)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                //console.log('Data successfully saved.');
                resolve();
            } else {
                console.error('Error saving data:', data.message);
                reject(data.message);
            }
        })
        .catch(error => {
            console.error('Error saving data:', error);
            reject(error);
        });
    });
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
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            //console.log('Filter values successfully saved.');
        } else {
            console.error('Error saving filter values:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving filter values:', error);
    });
}


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

// Function to load filter values from JSON file and update input fields


function openEditModal(rowId) {
    // Find the annonce data
    const index = window.annonces.findIndex(a => Object.keys(a)[0] === rowId);
    if (index === -1) return;
    const annonce = window.annonces[index][rowId];

    // Définir les groupes d'onglets
    const tabGroups = {
        'Informations principales': ['dossier', 'description', 'id', 'entreprise', 'categorie'],
        'Statut': ['etat', 'lien_Etape','annonce_pdf','CV','CVfile'],
        'suivi': [ 'Date','Date_rep','todo','commetaires'],
        'Contact': [ 'contact','tel', 'mail','url'],
        'Détails': ['Commentaire', 'type', 'Lieux'], 
        'GPT': ['GptSum']
    };
//'annonce_pdf'
    // Create modal HTML with tabs
    let modalHtml = `
        <dialog id="editModal" class="edit-modal">
            <form method="dialog">
                <h2>Modifier l'annonce</h2>
                <div class="edit-tabs">
                    ${Object.keys(tabGroups).map((tabName, index) => `
                        <button type="button" class="tab-button ${index === 0 ? 'active' : ''}" 
                                onclick="switchEditTab(event, '${tabName}')">${tabName}</button>
                    `).join('')}
                </div>

                ${Object.entries(tabGroups).map(([tabName, fields], index) => `
                    <div id="${tabName}" class="tab-content ${index === 0 ? 'active' : ''}">
                        ${fields.map(field => `
                            <div class="form-group">
                                <label>${field}:</label>
                                <input type="text" id="edit-${field}" value="${annonce[field] || ''}" 
                                       ${field === 'dossier' ? 'readonly' : ''}>
                            </div>
                        `).join('')}
                    </div>
                `).join('')}

                <div class="button-group">
                    <button type="button" onclick="saveEdit('${rowId}')">Enregistrer</button>
                    <button type="button" onclick="cancelEdit()">Annuler</button>
                </div>
            </form>
        </dialog>
    `;

    // Remove existing modal if any
    const existingModal = document.getElementById('editModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = document.getElementById('editModal');
    modal.showModal();
}

function switchEditTab(event, tabName) {
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let content of tabContents) {
        content.classList.remove('active');
    }

    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let button of tabButtons) {
        button.classList.remove('active');
    }

    // Show the selected tab content and activate the button
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

function saveEdit(rowId) {
    // Ensure the index is correct
    const index = window.annonces.findIndex(a => Object.keys(a)[0] === rowId);
    if (index === -1) return;
    const annonce = window.annonces[index][rowId];

    // Update annonce with new values based on window.columns
    window.columns.forEach(col => {
        const inputElement = document.getElementById(`edit-${col.key}`);
        if (inputElement) {
            annonce[col.key] = inputElement.value;
        }
    });

    // Save changes and refresh table
    refresh();
  

    // Close modal
    document.getElementById('editModal').close();
}

function cancelEdit() {
    document.getElementById('editModal').close();
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

function toggleHeaderVisibility() {
    const header = document.querySelector('thead');
    const toggleButton = document.getElementById('toggle-header-btn');
    if (header.style.display === 'none') {
        header.style.display = '';
        toggleButton.textContent = 'Hide Header';
    } else {
        header.style.display = 'none';
        toggleButton.textContent = 'Show Header';
    }
}

function generateTableHeaders() {
    const thead = document.querySelector('thead tr');
    const filterRow = document.querySelector('thead tr:nth-child(2)');
    // Clear existing headers
    thead.innerHTML = '';
    filterRow.innerHTML = '';
    
    window.columns.forEach(col => {
        if (col.type === "tb" && col.visible === true) {
            // Create header cell
            const th = document.createElement('th');
            th.style.width = col.width;
            th.classList.add('filter-cell');
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

function setNewTab(){
    const activeTab = document.querySelector('.tab.active');
    window.tabActive=activeTab.textContent;
}

function changeTab(tabName) {
    // Remove 'active' class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    // Add 'active' class to the clicked tab
    document.querySelector(`.tab[onclick="changeTab('${tabName}')"]`).classList.add('active');
  
    setNewTab();
    refresh();
}

// Function to generate the column visibility form
function generateColumnVisibilityForm() {
    const formHtml = `
        <dialog id="columnVisibilityModal" class="modal">
            <form id="columnVisibilityForm">
                <h3>Manage Column Visibility</h3>
                ${window.columns.map((col, index) => `
                    <div>
                        <input type="checkbox" id="col-${index}" ${col.visible ? 'checked' : ''}>
                        <label for="col-${index}">${col.key.charAt(0).toUpperCase() + col.key.slice(1)}</label>
                    </div>
                `).join('')}
                <button type="button" onclick="saveColumnVisibility()">Save</button>
                <button type="button" onclick="toggleColumnVisibilityForm()">Close</button>
            </form>
        </dialog>
    `;
    document.body.insertAdjacentHTML('beforeend', formHtml);
}

// Function to save column visibility settings
function saveColumnVisibility() {
    window.columns.forEach((col, index) => {
        const checkbox = document.getElementById(`col-${index}`);
        if (checkbox) {
            col.visible = checkbox.checked;
        }
    });
    save_config_col(window.columns);
    
    toggleColumnVisibilityForm(); // Close the modal after saving
}

// Function to toggle the visibility of the column visibility form
function toggleColumnVisibilityForm() {
    const modal = document.getElementById('columnVisibilityModal');
    if (modal) {
        if (modal.open) {
            modal.close();
        } else {
            modal.showModal();
        }
    }
}

// Call the function to generate the form when the page loads
window.addEventListener('load', function() {
    loadConstants();
    setNewTab();
    //setNewTab();  
    loadTableData(function() {
        //console.log('Table data loaded and callback executed.');
        // Add any additional code to execute after loading table data here
    });
    createMenu();
    loadReseauxLinks();
    

});

// ...existing code...


// Function to serialize columns
function serializeColumns(columns) {
    return columns.map(col => {
        const serializedCol = {};
        for (const key in col) {
            if (col.hasOwnProperty(key)) {
                serializedCol[key] = col[key];
            }
        }
        if (typeof col.eventHandler === 'function') {
            serializedCol.eventHandler = col.eventHandler.name;
        }
        return serializedCol;
    });
}




function loadColumnsFromJson() {
    fetch('/load_config_col', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tabActive: window.tabActive })
    })
    .then(response => response.json())
    .then(data => {
        window.columns = deserializeColumns(data);
        reassignEventHandlers(window.columns);
        generateTableHeaders();
        generateColumnVisibilityForm();
    })
    .catch(error => {
        console.error('Error loading column configuration:', error);
    });
}
// Function to reassign event handlers after deserialization
function reassignEventHandlers(columns) {
    columns.forEach(col => {
        if (col.eventHandler === 'openUrlHandler') {
            col.eventHandler = openUrlHandler;
        }
        // Add more handlers as needed
    });
}


// Function to deserialize columns
function deserializeColumns(columns) {
    return columns.map(col => {
        const deserializedCol = {};
        for (const key in col) {
            if (col.hasOwnProperty(key)) {
                deserializedCol[key] = col[key];
            }
        }
        if (col.eventHandler === 'openUrlHandler') {
            deserializedCol.eventHandler = openUrlHandler;
        }
        // Add more handlers as needed
        return deserializedCol;
    });
}
// ...existing code...
function open_dir(filepath) {
    fetch('/open_parent_directory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: filepath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            //console.log('Directory opened successfully.');
        } else {
            console.error('Error opening directory:', data.message);
        }
    })
    .catch(error => {
        console.error('Error opening directory:', error);
    });
}


function getFilePathFromRowId(rowId) {
    // Implémentez cette fonction pour obtenir le chemin du fichier à partir de l'ID de la ligne
    // Par exemple :
    return document.querySelector(`#row-${rowId}`).dataset.filePath;
}

function AIQ(ispdf, value, oneitem) {
    const params = new URLSearchParams();
    params.append('ispdf', ispdf);
    params.append('value', encodeURIComponent(value));
    params.append('description', encodeURIComponent(oneitem.description));
   
    window.open(`qa.html?${params.toString()}`, '_blank');
}


// ...existing code...

function loadCSVFile(filePath) {
    fetch('/read_csv_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: filePath })
    })
    .then(response => response.json())
    .then(data => {
        displayCSVTable(data);
    })
    .catch(error => {
        console.error('Error reading CSV file:', error);
    });
}

function displayCSVTable(data) {
    const tableContainer = document.getElementById('csv-table-container');
    if (!tableContainer) {
        console.error('Element with id "csv-table-container" not found.');
        return;
    }

    const table = document.createElement('table');
    table.classList.add('csv-table');

    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    if (data.length > 0) {
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');
    data.forEach(row => {
        const tr = document.createElement('tr');
        Object.values(row).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    // Clear existing content and append the new table
    tableContainer.innerHTML = '';
    tableContainer.appendChild(table);
}

function openCSVTable(filePath) {
    const params = new URLSearchParams();
    params.append('file', filePath);
    window.open(`csv_table.html?${params.toString()}`, '_blank');
}

// Add menu
function createMenu() {
    const menu = document.createElement('div');
    menu.id = 'menu';
    menu.innerHTML = `
        <button onclick="openCSVTable('Suivi_annonce_apec.csv')">Load CSV File</button>
    `;
    document.body.insertBefore(menu, document.body.firstChild);
}




async function get_job_answer(path,num_job)
{
 const q2_job = 
        "peux tu me faire un plan détaillé de l'offre avec les sections en précisant bien ce qui est obligatoire, optionnelle :" +
        "- Titre poste proposé," +
        "- Duties (Description du poste décomposée en tache ou responsabilité)," +
        "- requirements (expérience attendues, )," +
        "- skills (languages, outils obligatoires)," +
        "- Savoir-être (soft skill)," +
        "- autres (toutes informations autre utile à connaitre)"
        ;

    showLoadingOverlay();

    try {
        const jobTextResponse = await fetch('/get_job_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: path, RQ: q2_job })
        });

        if (!jobTextResponse.ok) {
            throw new Error('Erreur lors de l\'extraction du texte de l\'offre');
        }

        const jobTextData = await jobTextResponse.json();
        const saved_path = "";
        const saveResponse = await fetch('/save-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text_data: jobTextData.formatted_text, number: num_job, the_path: saved_path })
        });

        if (saveResponse.ok) {
            alert("Résumé de l'offre d'emploi effectué");
        } else {
            alert("Erreur lors de la sauvegarde de l'offre d'emploi");
        }
    } catch (error) {
        console.error('Error:', error);
        alert("Erreur lors du traitement de l'offre d'emploi");
    } finally {
        hideLoadingOverlay();
        refresh();
    }
}

function showLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    overlay.style.zIndex = '1000';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.color = 'white';
    overlay.style.fontSize = '24px';
    overlay.textContent = 'Processing...';
    document.body.appendChild(overlay);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}
async function convert_cv(numDossier, repertoire_annonces) 
{
 fetch('/convert_cv', {
    method: 'POST',
    headers:{
            'Content-Type': 'application/json'
            },
    body: JSON.stringify({ 
        num_dossier: numDossier,
        repertoire_annonces: repertoire_annonces,
        })
    });
}

async function get_cv(numDossier, repertoire_annonces,state,rowId) 
{
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx'; // Acceptable file types
    input.style.display = 'none';
    ready=true;
    if (state==='O')
    {
         if  (! confirm("Voulez vous écraser votre CV ? ")) {
        ready=false;   
        }
    }

    
        input.addEventListener('change', async (event) => 
        {
            const file = event.target.files[0];
            if (file) 
            {
                const formData = new FormData();
                formData.append('file_path', file);
                formData.append('num_dossier', numDossier);
                formData.append('repertoire_annonce', repertoire_annonces);
                fpath=repertoire_annonces + '/' + numDossier +  ".data.json";   
                try 
                {
                    const response = await fetch('/share_cv', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();

                    if (data.status === "success") 
                    {
                        alert('CV selectionné avec succès.');
                        alert(fpath + ",  'CVfile' , "+file.name)
                     
                        //updateAnnonces_byfile(fpath, "CVfile", file.name);
                        refresh();
                    } else 
                    {
                        alert('Erreur lors de la sélection du CV: ' + data.message);
                    }

                } 
                catch (error) 
                {
                    console.error('Error selecting CV:', error);
                    alert('Erreur lors de la sélection du CV.');
                }
            }
        });
    if (ready) 
    {
         document.body.appendChild(input);
        input.click();
    }

   
}



function open_url(theurl) {
      alert(theurl);
            fetch('/open_url', {
                method: 'POST',
                headers: {
                'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: theurl  })
        });
}

// ...existing code...

function createAnnouncementForm() {
    const formHtml = `
        <dialog id="announcementForm" class="announcement-form">
            <form method="dialog">
                <h2>Créer une annonce</h2>
                <div class="form-group">
                    <label for="announcementDossier">Dossier:</label>
                    <input type="text" id="announcementDossier" class="rich-text-field">
                </div>
                <div class="form-group">
                    <label for="announcementURL">URL:</label>
                    <input type="url" id="announcementURL" class="rich-text-field">
                </div>
                <div class="form-group">
                    <label for="announcementContent">Contenu de l'annonce:</label>
                    <textarea id="announcementContent" class="rich-text-field"></textarea>
                </div>
                <div class="button-group">
                    <button type="button" onclick="submitAnnouncement()">Créer</button>
                    <button type="button" onclick="scrapeAndFill()">Scrape URL</button>
                    <button type="button" onclick="closeAnnouncementForm()">Annuler</button>
                </div>
            </form>
        </dialog>
    `;

    // Remove existing form if any
    const existingForm = document.getElementById('announcementForm');
    if (existingForm) {
        existingForm.remove();
    }

    // Add form to document
    document.body.insertAdjacentHTML('beforeend', formHtml);

    // Show form
    const form = document.getElementById('announcementForm');
    form.showModal();
}

// Ajouter cette nouvelle fonction
function scrapeAndFill() {
    const url = document.getElementById('announcementURL').value;
    const dossier = document.getElementById('announcementDossier').value;
    
    if (!url || !isValidURL(url)) {
        alert("Veuillez entrer une URL valide!");
        return;
    }
    
    if (!dossier) {
        alert("Veuillez entrer un numéro de dossier!");
        return;
    }

    showLoadingOverlay();
    fetch('/scrape_url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_url: url,
            num_job: dossier
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            document.getElementById('announcementContent').value = data.content;
            alert('URL scrapée avec succès');
        } else {
            alert('Erreur lors du scraping: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error scraping URL:', error);
        alert('Erreur lors du scraping de l\'URL');
    })
    .finally(() => {
        hideLoadingOverlay();
    });
}

function submitAnnouncement() {
    let content = document.getElementById('announcementContent').value;
    if (content.trim() === '') {
        alert('Le contenu de l\'annonce ne peut pas être vide !!!');
        return;
    }
    const contentNum = document.getElementById('announcementDossier').value;
    if (contentNum.trim() === '') {
        alert('Le numéro du dossier ne peut pas être vide !!!');
        return;
    }

    const contentUrl = document.getElementById('announcementURL').value;
    if (contentUrl.trim() === '' && !isValidURL(contentUrl)) {
        alert("L'URL ne peut pas être null !!!");
        return;
    }
   
    contentUrlembed = "<- " + contentUrl + " ->";

    // Remove all spaces inside content
    content = content.replace(/\s+/g, '');

    globalContent =  content;
    showLoadingOverlay();
    fetch('/save_announcement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            contentNum: contentNum,
            content: content,
            url:contentUrl
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            alert('Annonce créée avec succès.');
            refresh();
        } else {
            alert('Erreur lors de la création de l\'annonce: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error creating announcement:', error);
        alert('Erreur lors de la création de l\'annonce.');
    });
    hideLoadingOverlay();
    // Handle the announcement content (e.g., send it to the server)
    //console.log('Announcement content:', content);

    // Close form
    //closeAnnouncementForm();
}

function isValidURL(url) {
    const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.?)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(url);
}

function closeAnnouncementForm() {
    const form = document.getElementById('announcementForm');
    if (form) {
        form.close();
    }
}

// ...existing code...

function open_notes(file_notes) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            showNotesPopup(notesContent, file_notes);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function showNotesPopup(content, file_notes) {
    const popupHtml = `
        <dialog id="notesPopup" class="notes-popup">
            <form method="dialog">
                <h2>Notes</h2>
                <div id="notesContentContainer">
                    <table id="notesTable" class="notes-table">
                        ${content.map((item, index) => `
                            <tr>
                                <td contenteditable="true" onblur="saveNoteChange('${file_notes}', ${index}, 'key', this.textContent)">${item.key}</td>
                                <td contenteditable="true" style="width: 300px;" onblur="saveNoteChange('${file_notes}', ${index}, 'value', this.textContent)">${item.value}</td>
                                <td style="width: 50px;"><span class="remove-icon" onclick="removeNoteRow('${file_notes}', ${index})">&times;</span></td>
                            </tr>
                        `).join('')}
                    </table>
                </div>
                <div class="button-group">
                    <button type="button" onclick="addNoteRow('${file_notes}')">Ajouter</button>
                    <button type="button" onclick="closeNotesPopup()">Fermer</button>
                </div>
            </form>
        </dialog>
    `;

    // Remove existing popup if any
    const existingPopup = document.getElementById('notesPopup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Add popup to document
    document.body.insertAdjacentHTML('beforeend', popupHtml);

    // Show popup
    const popup = document.getElementById('notesPopup');
    popup.showModal();
}

function saveNoteChange(file_notes, index, key, value) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            notesContent[index][key] = value;
            saveNotes(file_notes, notesContent);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function saveNotes(file_notes, content) {
    fetch('/save_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes, content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            console.log('Notes enregistrées avec succès.');
        } else {
            alert('Erreur lors de l\'enregistrement des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error saving notes:', error);
        alert('Erreur lors de l\'enregistrement des notes.');
    });
}

function addNoteRow(file_notes) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            notesContent.push({ key: '', value: '' });
            saveNotes(file_notes, notesContent);
            showNotesPopup(notesContent, file_notes);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function removeNoteRow(file_notes, index) {
    fetch('/read_notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file_path: file_notes })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            const notesContent = data.content;
            notesContent.splice(index, 1);
            saveNotes(file_notes, notesContent);
            showNotesPopup(notesContent, file_notes);
        } else {
            alert('Erreur lors de la lecture des notes: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error reading notes:', error);
        alert('Erreur lors de la lecture des notes.');
    });
}

function closeNotesPopup() {
    const popup = document.getElementById('notesPopup');
    if (popup) {
        popup.close();
    }
}

// Add styles for notesPopup
const style1 = document.createElement('style');
style1.textContent = `
    .notes-popup {
        width: 800px;
        height: 500px;
        padding: 20px;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    .notes-popup .notes-table {
        width: 100%;
        border-collapse: collapse;
    }
    .notes-popup .notes-table td {
        border: 1px solid #ccc;
        padding: 8px;
    }
    .notes-popup .remove-icon {
        cursor: pointer;
        color: red;
        font-size: 20px;
    }
    .notes-popup .button-group {
        display: flex;
        justify-content: space-between;
    }
    .notes-popup .button-group button {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .notes-popup .button-group button:first-child {
        background-color: #4CAF50;
        color: white;
    }
    .notes-popup .button-group button:last-child {
        background-color: #f44336;
        color: white;
    }
`;
document.head.appendChild(style1);

// ...existing code...

function showReseauxLinks() {
    document.getElementById('reseaux-links-section').style.display = 'block';
    document.getElementById('main-section').style.display = 'none';
}

function hideReseauxLinks() {
    document.getElementById('reseaux-links-section').style.display = 'none';
    document.getElementById('main-section').style.display = 'block';
}

async function loadReseauxLinks() {
    try {
        const response = await fetch('/load_reseaux_link');
        const portalLinks = await response.json();
        window.portalLinks = portalLinks;
        console.log(portalLinks);
        
        const tableBody = document.getElementById('reseaux-links-table-body');
        tableBody.innerHTML = ''; // Clear existing rows

        window.portalLinks.forEach(link => {
            const row = document.createElement('tr');
            window.portalLinks_columns.forEach((col, colIndex) => {

                if (col.visible === true) {
                    let isurl = false;
                    const cell = document.createElement('td');
                    if (col.key === 'name' && link.url) {
                        isurl = true;
                    }

                    if (isurl) {
                        cell.style.cursor = "pointer";
                        cell.style.color = "blue";
                        cell.style.textDecoration = "underline";
                        cell.addEventListener(col.event, () => open_url(link.url));
                    } else {
                        cell.style.color = ''; // Default color
                        cell.style.textDecoration = ''; // Default text decoration
                    }

                    if (col.key === 'update') {
                        const button = document.createElement('button');
                        button.textContent = link[col.key] ? 'OK' : 'No';
                        button.style.backgroundColor = link[col.key] ? 'green' : 'red';
                        button.style.color = 'white';
                        button.onclick = () => {
                            link[col.key] = !link[col.key];
                            button.textContent = link[col.key] ? 'OK' : 'No';
                            button.style.backgroundColor = link[col.key] ? 'green' : 'red';
                            if (link[col.key]) {
                                if (link[col.key]===False) { link.update_date=""; } else 
                                {
                                    if(link[col.key] === true){
                                        const date = new Date();
                                        const dateFr = date.toLocaleDateString('fr-FR'); // Set current date in French format
                                        link.update_date = dateFr;
                                    }
                                    link.update_date = "";
                                   
                                }
                                
                            }
                            console.log('Updated link:', link);
                            saveReseauxLinkUpdate(link);
                           
                        };
                        cell.appendChild(button);
                    } else {
                        cell.contentEditable = col.editable;
                        cell.textContent = link[col.key];
                        cell.onblur = () => {
                            link[col.key] = cell.textContent;
                            saveReseauxLinkUpdate(link);
                        };
                    }

                    if (col.width) cell.style.width = col.width;
                    row.appendChild(cell);
                }
            });

            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading reseaux links:', error);
    }
}

function saveReseauxLinkUpdate(link) {
    fetch('/save_reseaux_link_update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(link)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== "success") {
            console.error('Error saving reseaux link update:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving reseaux link update:', error);
    });
}

// ...existing code...

async function scrape_url(item_url, num_job, the_path) {
   

    try {
        const response = await fetch('/scrape_url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_url: item_url,
                num_job: num_job
            })
        });

        const data = await response.json();

        if (response.status === 200) {
            console.log('Scrape URL successful:', data);
            alert('Scrape URL successful :');
        } else {
            console.error('Error in scrape_url:', data.message);
            alert('Error in scrape_url: ' + data.message);
        }
    } catch (error) {
        console.error('Error in scrape_url:', error);
        alert('Error in scrape_url: ' + error.message);
    }
}
