// Example usage
function loadTableData(callback) {
    
 
    generateTableHeaders();
   
    excludedfile = document.getElementById('Excluded').value+".json";
  
    ApiClient.annonces.read({ excluded: excludedfile })
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
            let fichier_annonce = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']+".pdf";
        
            const row = document.createElement('tr');           
            row.id = filePath;
            row.style.position = 'relative'; // Ajout du positionnement relatif sur la ligne
              if (isrefus) {
                row.classList.add('refus-row');
            } else {
                row.classList.add('normal-row');
            } 
           
 
            (getState('columns') || []).forEach((col, colIndex) => {
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
                        //let fichier = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX']+".pdf";
                        icon=createCell_PdfView(col.key, item, fichier_annonce);
                        cell.appendChild(icon);
                    }
                else if (col.key === 'Notes' ) 
                        {
                            const file_notes = dir_path + '/' + item.dossier+window.CONSTANTS['FILE_NAMES']['NOTES_FILE'];
                            icon= createCell_Notes(file_notes);
                            cell.appendChild(icon);                        
                        } 
                        
                    else if (col.key === 'dossier') {
                        // Créer la cellule pour le numéro de dossier avec un icône
                        cell.style.position = 'relative'; // Pour positionner l'icône correctement
                        
                        // Ajouter le numéro de dossier à la cellule
                        cell.textContent = item[col.key];
                        
                        // Appliquer les styles de la colonne
                        if (col.style) {
                            if (col.style.color) cell.style.color = col.style.color;
                            if (col.style.cursor) cell.style.cursor = col.style.cursor;
                            if (col.style.textDecoration) cell.style.textDecoration = col.style.textDecoration;
                        }
                        
                        // Ajouter l'icône de dossier
                        const folderIcon = document.createElement('span');
                        folderIcon.textContent = '📂'; // Icône de dossier
                        folderIcon.style.cursor = 'pointer';
                        folderIcon.style.position = 'absolute';
                        folderIcon.style.right = '5px'; // Changé de -10px à 5px pour être visible dans la cellule
                        folderIcon.style.top = '50%';
                        folderIcon.style.transform = 'translateY(-50%)';
                        folderIcon.style.zIndex = '1000'; // Valeur plus élevée pour être au-dessus
                        folderIcon.style.fontSize = '16px';
                        folderIcon.style.userSelect = 'none';
                        folderIcon.style.pointerEvents = 'auto'; // S'assurer que les événements de pointeur fonctionnent
                        folderIcon.style.display = 'inline-block';
                        folderIcon.style.padding = '2px'; // Un peu de padding pour une zone de clic plus large
                        
                        // Ajouter un attribut pour identifier l'icône
                        folderIcon.setAttribute('data-folder-icon', 'true');
                        
                        // Utilisez la fonction correcte pour ouvrir le dossier
                        folderIcon.addEventListener('click', (e) => {
                            console.log('Folder icon clicked!');
                            e.preventDefault();
                            e.stopPropagation();
                            ask_Local_file_explorer(dir_path, "document"); // ← à adapter selon ta fonction
                        });
                        
                        // Ajout d'un effet hover pour feedback visuel
                        folderIcon.addEventListener('mouseenter', () => {
                            folderIcon.style.backgroundColor = 'rgba(0,0,0,0.1)';
                            folderIcon.style.borderRadius = '3px';
                            console.log('Mouse enter on folder icon'); // Debug
                        });
                        
                        folderIcon.addEventListener('mouseleave', () => {
                            folderIcon.style.backgroundColor = 'transparent';
                        });
                        cell.appendChild(folderIcon);
                        
                        // Assurer que la cellule est assez large pour accommoder le texte et l'icône
                        if (col.width) {
                            cell.style.width = col.width;
                            cell.style.minWidth = col.width;
                        } else {
                            cell.style.minWidth = '120px'; // Largeur minimale augmentée
                        }
                        
                        // Ajouter du padding à droite pour faire de la place à l'icône
                        cell.style.paddingRight = '30px';
                        cell.style.overflow = 'visible';
                
                    }   else if (col.key === 'description') {
                        cell.style.display = 'flex';
                        cell.style.alignItems = 'center';
                        cell.style.justifyContent = 'space-between';

                        const leftPart = document.createElement('span');
                        leftPart.style.display = 'flex';
                        leftPart.style.alignItems = 'center';

                        // Icône lien URL (si url existe)
                        if (item['url'] && item['url'] !== "" && item['url'] !== "N/A") {
                            const urlIcon = document.createElement('span');
                            urlIcon.textContent = '🔗';
                            urlIcon.style.cursor = 'pointer';
                            urlIcon.style.marginRight = '6px';
                            urlIcon.title = 'Ouvrir le lien';
                            urlIcon.addEventListener('click', (e) => {
                                e.stopPropagation();
                                window.open(item['url'], '_blank');
                            });
                            leftPart.appendChild(urlIcon);
                        }

                        // Texte description
                        const descSpan = document.createElement('span');
                        descSpan.textContent = item[col.key];
                        leftPart.appendChild(descSpan);

                        // Icône édition à droite
                        const editIcon = document.createElement('span');
                        editIcon.textContent = '✏️';
                        editIcon.style.cursor = 'pointer';
                        editIcon.style.marginLeft = '8px';
                        editIcon.title = 'Éditer la description';
                        editIcon.style.alignSelf = 'flex-end';
                        editIcon.addEventListener('click', (e) => {
                            e.stopPropagation();
                            const newDesc = prompt('Modifier la description :', item[col.key]);
                            if (newDesc !== null && newDesc !== item[col.key]) {
                                descSpan.textContent = newDesc;
                                updateAnnonces(index, col.key, newDesc);
                            }
                        });

                        cell.appendChild(leftPart);
                        cell.appendChild(editIcon);
                    }

                    else {
                        // Le traitement normal pour les autres cellules
                        cell.style.textDecoration = '';
                        cell.style.color = '';
                        
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
                    //set_current_row();
                    curRow=getState('currentSelectedRow', row);
                    openEditModal(curRow.id);
                    contextMenu.style.display = 'none';
                };
                
                // document.getElementById('SetCurrentRow').onclick = () => {
                //     window.CurrentRow=contextMenu.dataset.targetRow;
                //     contextMenu.style.display = 'none';
                //     set_current_row();
                // };
                document.getElementById('Open').onclick = () => {
                    window.CurrentRow=contextMenu.dataset.targetRow;
                    alert("Open: " + window.CurrentRow);
                    set_current_row();  
                    open_dir(filePath);
                  
                    contextMenu.style.display = 'none';
                };
               

          

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
    disableDirectoryChangeButton();
    return new Promise((resolve, reject) => {
        const data = window.annonces; // ← Correction ici
        console.log('Data envoyé:', data);
        fetch('/save_annonces_json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                console.log('dbg445 Data successfully saved.');
                enableDirectoryChangeButton();
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


