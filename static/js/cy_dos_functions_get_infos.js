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


function scan_url_annonce() {
    const contentUrl = document.getElementById('announcementURL').value;
  if (contentUrl )
  {
      if (contentUrl.trim() === '' && !isValidURL(contentUrl)) {
          alert("L'URL ne peut pas être null !!! ou invalide");
          return;
      }
      const contentNum = document.getElementById('announcementDossier').value;
      if (contentNum.trim() === '') {
          alert('Le numéro du dossier ne peut pas être vide !!!');
          return;
      }
      showLoadingOverlay();
      alert("dbg T546 Scanning URL : "+contentUrl);
      get_job_answer(contentUrl,contentNum,"AN",true);
      hideLoadingOverlay();
      refresh();
  } else {
      alert("il y a un problême houston");
  }

} 


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
