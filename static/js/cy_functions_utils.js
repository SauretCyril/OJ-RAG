
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



function isValidURL(url) {
    const pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.?)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(url);
}


async function get_cookie(cookieName) {
    try {
        const response = await fetch('/get_cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cookie_name: cookieName })
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data[cookieName];
    } catch (error) {
        console.error('Error fetching cookie:', error);
        throw error;
    }
}



// ...existing code...
function save_cookie(cookieName, value) {
       
    //alert("current_instruction = " + selected);
    fetch('/save_cookie', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'cookie_name':  cookieName, 'cookie_value':value}) // Use CookieName as the key
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.text();  // Changed from response.json() to response.text()
    }).then(data => {
        try {
            const jsonData = JSON.parse(data);
            if (jsonData.message === 'done') {
                console.log(cookieName+ ' saved successfully avec la valeur : ' + value);
            } else {
                alert('Error 2478 setting cookie: ' + jsonData.error);
            }
        } catch (error) {
            console.error('Error 2547 parsing JSON:', error);
            alert('Error 2547 parsing server response.');
        }
    })
    .catch(error => {
        console.error('Error 1244 setting cookie: ', error);
        alert('Error 1244 setting cookie.');
    });


}

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
        if (col.eventHandler === 'SelectHandler') {
            deserializedCol.eventHandler = SelectHandler;
        }
        // Add more handlers as needed
        return deserializedCol;
    });
}
