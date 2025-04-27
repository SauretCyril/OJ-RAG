// Example usage
function loadTableData(callback) {
    
 
    generateTableHeaders();
   
    excludedfile = document.getElementById('Excluded').value+".json";
  
    fetch('/read_annonces_json', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
        excluded: excludedfile         
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
            //console.log("<<-1---dir_path--->>",dir_path);
            const isCvRef = item.Commentaire && item.Commentaire.includes('<CV-REF>');
            const isOnDay = item.Commentaire && item.Commentaire.includes('DAY');
            const isrefus = item.todo && item.todo.includes('refus');
           
        
            const row = document.createElement('tr');           
            row.id = filePath;
            row.style.position = 'relative'; // Ajout du positionnement relatif sur la ligne
              if (isrefus) {
                row.classList.add('refus-row');
            } else {
                row.classList.add('normal-row');
            } 
           
 
            window.columns.forEach((col, colIndex) => {
                if (colisvisible(col.type) && col.visible === true) {
                    
                    const cell = document.createElement('td');
                    cell.setAttribute('data-key', col.key);
                   
                    if (col.type === 'lnk')
                    {
                        icon = createCell_lnk(col.key, item);        
                        cell.appendChild(icon); 
                    }                  
                    else if (col.key === 'GptSum' ) 
                    {
                        const fichier = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['GPT_REQUEST_SUFFIX'];
                        icon=createCell_PdfView(col.key, item, fichier);
                        cell.appendChild(icon);
                       
                    }
                    else if (col.key === 'CVpdf'  )
                        {
                            const fichier = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['CV_SUFFIX_NEW']+".pdf";
                            icon=createCell_PdfView(col.key, item, fichier);
                            cell.appendChild(icon);
                        }      
                    else if (col.key === 'BApdf'  )
                        {
                            const fichier = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['BA_SUFFIX_NAME']+".pdf";
                            icon=createCell_PdfView(col.key, item, fichier);
                            cell.appendChild(icon);
                        }                     
                     else if (col.key === 'CV' || col.key === 'BA' ) 
                     {
                        //console.log('#### CV:', item[col.key]);
                       icon=createCell_getFile(col.key, item,dir_path);
                       cell.appendChild(icon);
                    } 
                    
                    else if (col.key === 'isJo')
                    {
                        let fichier = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']+".pdf";
                        icon=createCell_PdfView(col.key, item, fichier);
                        
                        /* const icon = document.createElement('span');
                        icon.style.position = 'absolute';
                        icon.style.alignContent='center';
                        icon.style.zIndex = '10'; // Ensure the icon is above the content
                         if (item[col.key] === 'O') {
                              //console.log('#### blanc:');
                            icon.textContent = '🔵';
                            icon.style.cursor = 'pointer';
                            icon.addEventListener('click', () => open_url(fichier_annonce));
                            
                        } else  {
                            //console.log('#### vert:');
                            icon.textContent = '⚪'; // White circle icon
                        }  */

                        cell.appendChild(icon);
                    }
                else if (col.key === 'Notes' ) 
                        {
                            const file_notes = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['NOTES_FILE'];
                            const heartIcon = document.createElement('span');
                            heartIcon.textContent = '❤️'; // Heart icon
                            heartIcon.style.cursor = 'pointer';
                            heartIcon.addEventListener('click', () => open_notes(file_notes));
                            cell.appendChild(heartIcon);
                        
                        } 
                        
                    else
                    {
                        isDosier=false;
                        isurl=false;
                        if (col.key === 'description' && item.url) {
                            isurl = true;
                        } else if (col.key === 'dossier') {
                            isDosier = true;
                        }

                        if (isurl) {
                            cell.style.cursor = col.style.cursor;
                            cell.style.color = col.style.color;
                            cell.style.textDecoration = col.style.textDecoration;
                            cell.addEventListener(col.event, () => open_url(item.url));
                        } else {
                            if (isDosier) {
                                cell.style.color = col.style.color; // Example color for dossier
                                cell.style.cursor = col.style.cursor;
                                cell.style.textDecoration = col.style.textDecoration;
                              
                                cell.addEventListener('click', function () {
                                    const currentRow = this.parentElement; // Ensure the row is correctly referenced
                                    // Deselect all rows
                                    document.querySelectorAll('.selected-row').forEach(row => {
                                        row.classList.remove('selected-row');
                                    });
                                    // Select the clicked row
                                    currentRow.classList.add('selected-row');
                                });


                            } else {
                                cell.style.color = ''; // Default color
                            }
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
                    

                    scrape_url(item.url,item.dossier);
                  
                    contextMenu.style.display = 'none';
                };
                let resumexist="";
                document.getElementById('Resume').onclick = () => 
                {
                    let thefile="";
                    resuReady=false;
                    if (item.isJo=="O")
                        {thefile=fichier_annonce,resuReady=true;}
                   
                    if (resuReady) 
                    {
                        const rowId = contextMenu.dataset.targetRow;
                        if (confirm("Voulez vous résumer le document ? "+resumexist +"->" +thefile+ " dans le dossier " + item.dossier )) {
                            window.CurrentRow=contextMenu.dataset.targetRow;
                            set_current_row();       
                            // call the function get answers
                          
                            get_job_answer(thefile,item.dossier, item.type,false,item.request);
                            
                            }
                    } else
                    {alert("document à résumer non trouvée")}
                }

                document.getElementById('Delete').onclick = () => {
             
                    if (confirm("Voulez-vous vraiment supprimer ce dossier ?")) {
                           updateAnnonces(index, 'etat', 'DELETED');
                        // Update the 'etat' column in the HTML row
                        const etatCell = row.querySelector('td:nth-child(' + (window.columns.filter(col => col.visible).findIndex(col => col.key === 'etat') + 1) + ')');
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
    //saveTableData();
}
function getStatus(filepath){
    return "Toto";
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
                console.log('dbg445 Data successfully saved.');
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
