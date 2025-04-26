// Add status tooltips


//const { url } = require('inspector');


// Declare the global array
window.conf={};
window.CONSTANTS=[];
window.CurrentRow ="";
window.tabActive = "Campagne";
window.annonces = [];
window.portalLinks=[];
/* window.portalLinks_columns = [
    { key: 'name', editable: false, width: '150px', visible: true,title:'name' },
    { key: 'url', editable: false, width: '200px', visible: false,title:'url' },
    { key: 'date', editable: true, width: '150px', visible: true,title:'Date' },
    { key: 'commentaire', editable: false, width: '200px', visible: false,title:'Commentaire' },
    { key: 'update', editable: true, width: '50px', visible: true,title:'update' },
    { key: 'update_date', editable: true, width: '150px', visible: true,title:'Date update' }
] */

window.columns = [
    { key: 'dossier', editable: false, width: '80px', visible: true, type: 'tb',title:'Dos',
    class: 'description-cell',  
      style: { cursor: 'pointer', color: 'red', textDecoration: 'underline' }, 
      event: 'click',  fixed:true // Store function name as string
    },
    { 
        key: 'description', 
        class: 'description-cell', 
        editable: false, 
        style: { cursor: 'pointer', color: 'blue', textDecoration: 'underline' }, 
        event: 'click', 
        eventHandler: 'openUrlHandler', // Store function name as string
        width: '300px',
        visible: true,
        type: 'tb',
        title:'Description',fixed:false
    },
    { key: 'id', editable: true, width: '200px',"visible":true,"type":"tb",title:'Lot',fixed:false},
    { key: 'entreprise', editable: true, width: '300px',"visible":true ,"type":"tb",title:'Entreprise',fixed:false },
    
    { key: 'role', editable: false, width: '120px',"visible":false,"type":"tb",title:'role',dir:'DIR_ROLE_FILE',fixed:false },   
    { key: 'request', editable: false, width: '120px',"visible":false ,"type":"tb",title:'request',dir:'DIR_RQ_FILE',fixed:false },
    { key: 'isJo', editable: false, width: '50px',"visible":true ,"type":"tb",title:'M.',fixed:false },
  
    
    { key: 'GptSum', editable: false, width: '50px',"visible":true,"type":"tb",title:'Res',fixed:false },
    { key: 'CV', editable: false, width: '70px',"visible":true ,"type":"tb",title:'CV',fixed:false },
    { key: 'CVpdf', editable: false, width: '70px',"visible":true ,"type":"tb",title:'CV.pdf',fixed:false },
    { key: 'BA', editable: false, width: '70px',"visible":true ,"type":"tb",title:'BA',fixed:false },
    { key: 'BApdf', editable: false, width: '70px',"visible":true ,"type":"tb",title:'BA.pdf',fixed:false },
    
    { key: 'categorie', editable: true, class: 'category-badge', prefix: 'category-', width: '100px',"visible":true,"type":"tb",title:'Cat',fixed:false  },
    { key: 'etat', editable: true, width: '100px',"visible":true ,"type":"tb",title:'Etat',fixed:false  },
    { key: 'contact', editable: true, width: '150px',"visible":false ,"type":"tb",title:'Contact',fixed:false },
    { key: 'tel', editable: true, width: '125px',"visible":false ,"type":"tb",title:'Tel.',fixed:false },
    { key: 'mail', editable: true, width: '125px',"visible":false,"type":"tb",title:'mail',fixed:false },
    { key: 'Date', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt pub',fixed:false },
    { key: 'Date_rep', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt Rep',fixed:false },
    { key: 'Date_from', editable: true, default: 'N/A', width: '120px',"visible":true ,"type":"tb",title:'Dt From',fixed:false },
    { key: 'delay', editable: false, default: 'N/A', width: '120px',"visible":false,"type":"tb",title:'Delais',fixed:false },  
    { key: 'Commentaire', editable: true, width: '200px',"visible":true,"type":"tb" ,title:'Commentaire',fixed:false },
    { key: 'todo', editable: true, width: '120px',"visible":true ,"type":"tb" ,title:'ToDo',fixed:false},
    { key: 'Notes', editable: false, width: '50px',"visible":true,"type":"tb" ,title:'Nt',fixed:false },
    { key: 'url', editable: false, width: '100px',"visible":false ,"type":"tb",title:'Url',fixed:false },
    { key: 'type', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Type',fixed:false  },
    { key: 'annonce_pdf', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Annonce (pdf)',fixed:false },
    { key: 'Origine', editable: true, width: '120px',"visible":false ,"type":"tb" ,title:'Origine',fixed:false},
    { key: 'lien_Etape', editable: true, width: '80px',"visible":false ,"type":"tb",title:'Lien Etape',fixed:false },
    
    { key: 'CVfile', editable: true, width: '80px',"visible":false ,"type":"tb",title:'CVfile',fixed:false },
    { key: 'lnk_Youtub', editable: false, width: '80px', visible: false, type: 'lnk', title: 'Youtube',fixed:false },
    { key: 'lnk_Youtub_value', editable: true, width: '80px', visible: false, type: 'tb', title: 'Youtube value',fixed:false },
    { key: 'path_dirpartage', editable: false, width: '80px', visible: false, type: 'dir', title: 'partage',fixed:false },
    { key: 'path_dirpartage_value', editable: true, width: '150px', visible: false, type: 'tb', title: 'dir',fixed:false }

    
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



function  view_results()
{
    fetch('/view_results', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file: 'resultats.json' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('view_results:', data);
    })
    .catch(error => {
        console.error('Error view_results:', error);
    });
}



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



function colisvisible(coltype)
{
    if ((coltype === "tb" || coltype === "lnk" || coltype === "dir"))
    {
        return true;
    }
    return false;
}

// Function to update the global array when a cell is edited



// Function to load filter values from JSON file and update input fields






async function loadCookies() {
        try {
            const response = await fetch('/load_cookies', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const cookies = await response.json();
            // Process the cookies as needed
            console.log('Cookies loaded:', cookies);
        } catch (error) {
            console.error('Error loading cookies:', error);
        }
    }

// Call the function to generate the form when the page loads
//onload
window.addEventListener('load', async function() {
    // Style
    document.head.appendChild(style1);
    document.head.appendChild(style3);
    //document.head.appendChild(style4); RP_CRQ.js
    //document.head.appendChild(style5);
 
    // constant
    await loadConstants();  // Ensure loadConstants is completed


    // load User settings
    await loadCookies();
    window.conf = await conf_loadconf();
    await loadColumnsFromServer();
    //window.columns = window.conf.Columns; // Corrected to use "Columns"
    //await show_current_instruction();  // Ensure get cookie current_instruction is completed
    await show_current_dossier();
    
    // Load data
    
    await loadTableData(function() {
        //console.log('Table data loaded and callback executed.');
        // Add any additional code to execute after loading table data here
        
    });
    setNewTab();  
    //createMenu();
    
  
    // Ensure the element with id 'Excluded' exists before adding the event listener
    const excludedElement = document.getElementById('Excluded');
    if (excludedElement) {
        excludedElement.addEventListener('change', loadTableData);
    } else {
        console.error('Element with id "Excluded" not found.');
    }
});


// ...existing code...


async function show_current_dossier() {
    try {
        const oneCooKie = await get_cookie('current_dossier');
        //alert("oneCookie",oneCooKie);
        if (oneCooKie) {
            document.getElementById('current-dir').textContent = oneCooKie;
        } else {
            document.getElementById('current-dir').textContent = 'No current';
        }
    } catch (error) {
        console.error('Error fetching current dossier:', error);
    }
}
