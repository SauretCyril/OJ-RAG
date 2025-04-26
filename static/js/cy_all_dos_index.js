function generate_index_html()
{
    fetch('/generate_html_index', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ dossier_list: window.annonces, sufix: window.CONSTANTS['FILE_NAMES']['ANNONCE_SUFFIX'] })

    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            console.log('dbg4757 Data successfully saved.');
        } else {
            console.error('Error saving data:', data.message);
        }
    })
    .catch(error => {
        console.error('Error saving data:', error);
    });
}
