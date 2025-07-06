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
    
    // Charger le contenu selon l'onglet (seulement texte-extrait)
    if (currentSelectedRow && tabId === 'texte-extrait') {
        loadTextExtract(currentSelectedRow.id);
    }
}

// Nouvelle fonction pour charger le texte extrait
function loadTextExtract(rowId) {
    try {
        const textViewer = document.getElementById('text-viewer');
        const saveBtn = document.getElementById('save-text-btn');
        const annonceData = getAnnonce_byfile(rowId);
        
        console.log('DEBUG loadTextExtract - rowId:', rowId);
        console.log('DEBUG loadTextExtract - annonceData:', annonceData);
        
        if (annonceData) {
            const numDossier = annonceData.dossier;
            const pdfFilePath = numDossier + "/" + numDossier + "_annonce_.pdf";
            
            console.log('DEBUG loadTextExtract - pdfFilePath:', pdfFilePath);
            
            // Afficher un indicateur de chargement
            textViewer.innerHTML = `
                <div class="text-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Extraction du texte en cours...</p>
                </div>
            `;
            
            // Masquer le bouton pendant le chargement
            if (saveBtn) {
                saveBtn.style.display = 'none';
            }
            
            // Appeler l'API pour extraire le texte
            console.log('DEBUG: Envoi de la requête à /extract_text_from_pdf');
            
            fetch('/extract_text_from_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file: pdfFilePath
                })
            })
            .then(response => {
                console.log('DEBUG: Réponse reçue, status:', response.status);
                console.log('DEBUG: Réponse headers:', response.headers);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('DEBUG: Données reçues:', data);
                
                if (data.success) {
                    console.log("DEBUG: loadTextExtract SUCCESS - text length:", data.text ? data.text.length : 0);
                    showTextContent(data.text);
                    // Afficher le bouton "Enregistrer" car le PDF existe
                    showSaveButton('save', rowId);
                } else {
                    console.log("DEBUG: loadTextExtract FAILED:", data.error);
                    showTextError(data.error || 'Erreur lors de l\'extraction du texte');
                    // Afficher le bouton "Nouveau" car le PDF n'existe pas
                    showSaveButton('new', rowId);
                }
            })
            .catch(error => {
                console.error('Erreur détaillée lors de l\'extraction du texte:', error);
                console.error('Error stack:', error.stack);
                showTextError('Erreur de connexion: ' + error.message);
                // Afficher le bouton "Nouveau" en cas d'erreur
                showSaveButton('new', rowId);
            });
            
        } else {
            console.log('DEBUG: Aucune donnée trouvée pour rowId:', rowId);
            showTextError('Aucune donnée trouvée pour ce dossier');
            if (saveBtn) {
                saveBtn.style.display = 'none';
            }
        }
        
    } catch (error) {
        console.error('Erreur lors du chargement du texte:', error);
        showTextError('Erreur lors du chargement du texte: ' + error.message);
        const saveBtn = document.getElementById('save-text-btn');
        if (saveBtn) {
            saveBtn.style.display = 'none';
        }
    }
}

// Fonction pour afficher le texte extrait
function showTextContent(text) {
    const textViewer = document.getElementById('text-viewer');
    
    if (text && text.trim()) {
        textViewer.innerHTML = `
            <div class="text-content-wrapper">
                <textarea id="text-content-area" class="text-content-editable">${text}</textarea>
            </div>
        `;
    } else {
        textViewer.innerHTML = `
            <div class="text-placeholder">
                <i class="fas fa-file-alt"></i>
                <p>Aucun texte trouvé dans le PDF</p>
            </div>
        `;
    }
}

// Fonction pour afficher une erreur texte
function showTextError(errorMessage) {
    const textViewer = document.getElementById('text-viewer');
    
    textViewer.innerHTML = `
        <div class="text-placeholder">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Erreur lors de l'extraction du texte</p>
            <small>${errorMessage}</small>
        </div>
    `;
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
        
        // Charger seulement le contenu texte extrait
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'texte-extrait') {
            loadTextExtract(row.id);
        }
        
    } catch (error) {
        console.error('Erreur lors de la sélection de la ligne:', error);
    }
}

// Fonction pour réinitialiser l'aperçu (version simplifiée)
function resetPreview() {
    resetTextPreview();
    currentSelectedRow = null;
}

// Fonction pour réinitialiser l'aperçu texte
function resetTextPreview() {
    const textViewer = document.getElementById('text-viewer');
    const saveBtn = document.getElementById('save-text-btn');
    
    textViewer.innerHTML = `
        <div class="text-placeholder">
            <i class="fas fa-file-alt"></i>
            <p>Sélectionnez une ligne pour voir le texte extrait</p>
        </div>
    `;
    
    saveBtn.style.display = 'none';
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
    
    // S'assurer que l'onglet texte-extrait est actif par défaut
    const textTab = document.getElementById('texte-extrait');
    if (textTab) {
        textTab.classList.add('active');
    }
    
    console.log('Module cy_fiche_annonce initialisé - Mode texte uniquement');
});

// Fonction pour gérer l'affichage du bouton
function showSaveButton(mode, rowId) {
    console.log('showSaveButton called with mode:', mode, 'rowId:', rowId);
    const saveBtn = document.getElementById('save-text-btn');
    
    if (!saveBtn) {
        console.error('Bouton save-text-btn non trouvé dans le DOM');
        return;
    }
    
    if (mode === 'new') {
        saveBtn.innerHTML = '<i class="fas fa-plus"></i> Nouveau';
        saveBtn.className = 'btn btn-success';
        saveBtn.onclick = () => createNewTextFile(rowId);
    } else {
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Enregistrer';
        saveBtn.className = 'btn btn-primary';
        saveBtn.onclick = () => saveTextContent(rowId);
    }
    
    saveBtn.style.display = 'block';
    console.log('Button should now be visible');
}

// Fonction pour créer un nouveau fichier texte
function createNewTextFile(rowId) {
    try {
        const textViewer = document.getElementById('text-viewer');
        const annonceData = getAnnonce_byfile(rowId);
        
        console.log('createNewTextFile called for rowId:', rowId);
        
        if (annonceData) {
            const numDossier = annonceData.dossier;
            
            // Créer une zone de texte éditable
            textViewer.innerHTML = `
                <div class="text-editor">
                    <h4>Création d'un nouveau fichier texte pour le dossier: ${numDossier}</h4>
                    <textarea id="text-editor-area" class="text-textarea" placeholder="Saisissez le texte de l'annonce..."></textarea>
                    <div class="editor-actions">
                        <button class="btn btn-primary" onclick="saveNewTextContent('${rowId}')">
                            <i class="fas fa-save"></i> Enregistrer
                        </button>
                        <button class="btn btn-secondary" onclick="cancelTextEdit('${rowId}')">
                            <i class="fas fa-times"></i> Annuler
                        </button>
                    </div>
                </div>
            `;
            
            // Modifier le bouton principal
            const saveBtn = document.getElementById('save-text-btn');
            if (saveBtn) {
                saveBtn.style.display = 'none';
            }
            
            // Focus sur la zone de texte
            setTimeout(() => {
                const textArea = document.getElementById('text-editor-area');
                if (textArea) {
                    textArea.focus();
                }
            }, 100);
        }
        
    } catch (error) {
        console.error('Erreur lors de la création du nouveau fichier:', error);
        showTextError('Erreur lors de la création du nouveau fichier: ' + error.message);
    }
}

// Fonction pour sauvegarder le contenu texte existant
function saveTextContent(rowId) {
    try {
        const textContentArea = document.getElementById('text-content-area');
        
        if (textContentArea) {
            const text = textContentArea.value;
            const annonceData = getAnnonce_byfile(rowId);
            
            console.log('saveTextContent called for rowId:', rowId);
            console.log('Text length:', text ? text.length : 0);
            
            if (annonceData) {
                const numDossier = annonceData.dossier;
                
                // Appeler l'API pour sauvegarder le texte
                fetch('/save_text_content', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        folder: numDossier,
                        text: text,
                        action: 'update',
                        annonceData: annonceData
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('PDF sauvegardé avec succès');
                        // Plus besoin de recharger l'onglet PDF
                    } else {
                        alert('Erreur lors de la sauvegarde: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la sauvegarde:', error);
                    alert('Erreur de connexion lors de la sauvegarde');
                });
            }
        } else {
            console.error('Aucune zone de texte trouvée à sauvegarder');
            alert('Aucune zone de texte trouvée à sauvegarder');
        }
        
    } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error);
        alert('Erreur lors de la sauvegarde: ' + error.message);
    }
}

// Fonction pour sauvegarder le nouveau contenu texte
function saveNewTextContent(rowId) {
    try {
        const textArea = document.getElementById('text-editor-area');
        
        if (!textArea) {
            console.error('Zone de texte non trouvée');
            alert('Zone de texte non trouvée');
            return;
        }
        
        const text = textArea.value;
        const annonceData = getAnnonce_byfile(rowId);
        
        console.log('saveNewTextContent called for rowId:', rowId);
        console.log('Text length:', text ? text.length : 0);
        
        if (!text.trim()) {
            alert('Veuillez saisir du texte avant de sauvegarder');
            return;
        }
        
        if (annonceData) {
            const numDossier = annonceData.dossier;
            
            // Appeler l'API pour sauvegarder le nouveau texte
            fetch('/save_text_content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    folder: numDossier,
                    text: text,
                    action: 'create'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Nouveau PDF créé avec succès');
                    // Recharger l'affichage avec le texte éditable
                    showTextContent(text);
                    showSaveButton('save', rowId);
                    // Plus besoin de recharger l'onglet PDF
                } else {
                    alert('Erreur lors de la création: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Erreur lors de la création:', error);
                alert('Erreur de connexion lors de la création');
            });
        }
        
    } catch (error) {
        console.error('Erreur lors de la sauvegarde du nouveau texte:', error);
        alert('Erreur lors de la sauvegarde: ' + error.message);
    }
}

// Fonction pour annuler l'édition
function cancelTextEdit(rowId) {
    console.log('cancelTextEdit called for rowId:', rowId);
    loadTextExtract(rowId);
}