// Ajouter au début de cy_fiche_annonce.js pour ignorer les erreurs d'extension
window.addEventListener('error', function(e) {
    if (e.message.includes('runtime.lastError')) {
        e.preventDefault();
        return true;
    }
});

let currentSelectedRow = null;

// Fonction pour récupérer un enregistrement par nom de fichier
function getAnnonce_byfile(file) {
    try {
        if (!window.annonces || !Array.isArray(window.annonces)) {
            console.error("window.annonces n'est pas disponible ou n'est pas un tableau");
            return null;
        }

        const index = window.annonces.findIndex(a => Object.keys(a)[0] === file);
        console.log("getAnnonce_byfile: " + index + " - " + file);
        
        if (index === -1) {
            console.error("Fichier non trouvé:", file);
            return null;
        }
        
        // Retourner l'enregistrement complet
        return window.annonces[index][file];
        
    } catch (err) {
        console.error("Erreur dans getAnnonce_byfile:", err);
        return null;
    }
}

// Fonction pour récupérer une valeur spécifique par nom de fichier
function getAnnonce_value_byfile(file, key) {
    try {
        const annonce = getAnnonce_byfile(file);
        if (!annonce) {
            return null;
        }
        
        return annonce[key] || null;
        
    } catch (err) {
        console.error("Erreur dans getAnnonce_value_byfile:", err);
        return null;
    }
}

// Fonction pour changer d'onglet (simplifiée pour un seul onglet)
function switchTab(tabId) {
    // Désactiver tous les onglets
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Activer l'onglet sélectionné
    document.querySelector(`[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
    
    // Si on bascule vers l'aperçu PDF, charger le PDF
    if (tabId === 'apercu-pdf' && currentSelectedRow) {
        loadPdfPreview(currentSelectedRow.id);
    }
}

// Fonction pour gérer la sélection d'une ligne
function selectRow(row) {
    try {
        // Désélectionner toutes les lignes
        document.querySelectorAll('#table-body tr').forEach(tr => {
            tr.classList.remove('selected');
        });
        
        // Sélectionner la ligne actuelle
        row.classList.add('selected');
        currentSelectedRow = row;
        
        // Charger directement l'aperçu PDF
        const rowId = row.id;
        
        // Récupérer l'URL du PDF depuis window.annonces
        const annonceData = getAnnonce_byfile(rowId);
        
        if (annonceData) {
            // Chercher le champ URL (peut être 'URL', 'url', 'Url', etc.)
            const numDossier = annonceData.dossier;
            pdffile= numDossier + "/" + numDossier + "_annonce_.pdf";
            console.log('log1 - Ligne sélectionnée:', rowId);
            console.log('log2 - Données annonce:', annonceData);
            console.log('log3 - Fichier PDF:', pdffile);
 
            // Charger l'aperçu PDF
            loadPdfPreview(pdffile);
        } else {
            console.error('Aucune donnée trouvée pour:', rowId);
        }
        
    } catch (error) {
        console.error('Erreur lors de la sélection de la ligne:', error);
    }
}

// Fonction pour charger l'aperçu PDF (version corrigée)
function loadPdfPreview(pdfFilePath) {
    try {
        const pdfViewer = document.getElementById('pdf-viewer');
        const placeholder = document.getElementById('pdf-placeholder');
        
        // Utiliser directement le chemin complet passé (sans ajouter _annonce_.pdf)
        const pdfUrl = `/preview_pdf/${pdfFilePath}`;
        console.log('Chargement du PDF:', pdfUrl);
        
        // Masquer le placeholder et afficher l'iframe
        placeholder.style.display = 'none';
        pdfViewer.style.display = 'block'; 
        pdfViewer.src = pdfUrl;
        
        // Gérer les erreurs de chargement
        pdfViewer.onload = function() {
            console.log('PDF chargé avec succès');
        };
        
        pdfViewer.onerror = function() {
            console.error('Erreur lors du chargement du PDF');
            showPdfError();
        };
        
    } catch (error) {
        console.error('Erreur lors du chargement du PDF:', error);
        showPdfError();
    }
}

// Fonction pour afficher une erreur PDF
function showPdfError() {
    const pdfViewer = document.getElementById('pdf-viewer');
    const placeholder = document.getElementById('pdf-placeholder');
    
    pdfViewer.style.display = 'none';
    placeholder.style.display = 'flex';
    placeholder.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <p>Erreur lors du chargement du PDF</p>
        <small>Vérifiez que le fichier _annonce_.pdf existe</small>
    `;
}

// Fonction pour ouvrir le PDF en plein écran (version corrigée)
function openPdfFullScreen() {
    if (currentSelectedRow) {
        const rowId = currentSelectedRow.id;
        const annonceData = getAnnonce_byfile(rowId);
        
        if (annonceData) {
            const numDossier = annonceData.dossier || annonceData.Dossier || rowId;
            const pdfFilePath = numDossier + "/" + numDossier + "_annonce_.pdf";
            const pdfUrl = `/preview_pdf/${pdfFilePath}`;
            window.open(pdfUrl, '_blank');
        } else {
            alert('Impossible de trouver les données du dossier');
        }
    } else {
        alert('Veuillez d\'abord sélectionner une ligne');
    }
}

// Fonction pour réinitialiser l'aperçu PDF
function resetPdfPreview() {
    const pdfViewer = document.getElementById('pdf-viewer');
    const placeholder = document.getElementById('pdf-placeholder');
    
    pdfViewer.style.display = 'none';
    pdfViewer.src = '';
    placeholder.style.display = 'flex';
    placeholder.innerHTML = `
        <i class="fas fa-file-pdf"></i>
        <p>Sélectionnez une ligne pour voir l'aperçu du PDF</p>
    `;
    
    currentSelectedRow = null;
}

// Fonction de debug pour vérifier window.annonces
function debugWindowAnnonces() {
    console.log('=== DEBUG WINDOW.ANNONCES ===');
    console.log('window.annonces existe:', typeof window.annonces);
    console.log('window.annonces length:', window.annonces ? window.annonces.length : 'N/A');
    
    if (window.annonces && window.annonces.length > 0) {
        console.log('Premier élément:', window.annonces[0]);
        console.log('Clés du premier élément:', Object.keys(window.annonces[0]));
        
        // Afficher les 3 premiers éléments
        window.annonces.slice(0, 3).forEach((item, index) => {
            const key = Object.keys(item)[0];
            console.log(`Element ${index}:`, key, '→', item[key]);
        });
    }
    console.log('=== FIN DEBUG ===');
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Debug pour vérifier window.annonces
    setTimeout(debugWindowAnnonces, 1000);
    
    // Ajouter l'événement de clic sur les lignes du tableau
    const tableBody = document.getElementById('table-body');
    
    if (tableBody) {
        tableBody.addEventListener('click', function(e) {
            const row = e.target.closest('tr');
            if (row && row.id) {
                selectRow(row);
            }
        });
    }
    
    // S'assurer que l'onglet PDF est actif par défaut
    const pdfTab = document.getElementById('apercu-pdf');
    if (pdfTab) {
        pdfTab.classList.add('active');
    }
    
    console.log('Module cy_fiche_annonce initialisé - Mode PDF uniquement');
});