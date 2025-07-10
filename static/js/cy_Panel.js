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

// Fonction pour changer d'onglet (mise à jour pour inclure chatbot)
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
    
    // Charger le contenu selon l'onglet
    if (currentSelectedRow) {
        if (tabId === 'texte-extrait') {
            loadTextExtract(currentSelectedRow.id);
        } else if (tabId === 'chatbot') {
            initializeChatbot(currentSelectedRow.id);
        }
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

// Nouvelle fonction pour initialiser le chatbot
function initializeChatbot(rowId) {
    try {
        const chatContainer = document.getElementById('chatbot-container');
        const annonceData = getAnnonce_byfile(rowId);
        
        console.log('initializeChatbot called for rowId:', rowId);
        
        if (annonceData) {
            const numDossier = annonceData.dossier;
            
            chatContainer.innerHTML = `
                <div class="chatbot-header">
                    <h4><i class="fas fa-robot"></i> Assistant IA - Dossier: ${numDossier}</h4>
                </div>
                <div class="chat-messages" id="chat-messages-${rowId}">
                    <div class="welcome-message">
                        <i class="fas fa-robot"></i>
                        <p>Bonjour ! Je peux analyser ce dossier d'annonce et répondre à vos questions. Que souhaitez-vous savoir ?</p>
                    </div>
                </div>
                <div class="chat-input-container">
                    <div class="input-group">
                        <textarea 
                            id="chat-question-${rowId}" 
                            class="chat-input" 
                            placeholder="Posez votre question sur ce dossier..."
                            rows="2"
                        ></textarea>
                        <button 
                            id="chat-send-btn-${rowId}" 
                            class="btn btn-primary chat-send-btn"
                            onclick="sendChatQuestion('${rowId}')"
                        >
                            <i class="fas fa-paper-plane"></i> Envoyer
                        </button>
                    </div>
                </div>
            `;
            
            // Ajouter l'événement Enter pour envoyer la question
            const questionInput = document.getElementById(`chat-question-${rowId}`);
            questionInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatQuestion(rowId);
                }
            });
            
        } else {
            chatContainer.innerHTML = `
                <div class="chatbot-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Aucune donnée trouvée pour ce dossier</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'initialisation du chatbot:', error);
        const chatContainer = document.getElementById('chatbot-container');
        chatContainer.innerHTML = `
            <div class="chatbot-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Erreur lors de l'initialisation du chatbot</p>
            </div>
        `;
    }
}

// Fonction pour envoyer une question au chatbot
function sendChatQuestion(rowId) {
    try {
        const questionInput = document.getElementById(`chat-question-${rowId}`);
        const chatMessages = document.getElementById(`chat-messages-${rowId}`);
        const sendBtn = document.getElementById(`chat-send-btn-${rowId}`);
        
        if (!questionInput || !chatMessages) {
            console.error('Éléments du chat non trouvés');
            return;
        }
        
        const question = questionInput.value.trim();
        
        if (!question) {
            alert('Veuillez saisir une question');
            return;
        }
        
        // Ajouter la question de l'utilisateur
        addChatMessage(chatMessages, question, 'user');
        
        // Vider le champ de saisie
        questionInput.value = '';
        
        // Désactiver le bouton et afficher un indicateur de chargement
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyse...';
        
        // Ajouter un message de chargement
        const loadingId = addChatMessage(chatMessages, 'Analyse du document en cours...', 'bot', true);
        
        // Récupérer les données de l'annonce
        const annonceData = getAnnonce_byfile(rowId);
        const numDossier = annonceData.dossier;
        
        // Extraire le chemin complet du fichier PDF à partir de l'objet annonceData
        let pdfFilePath = rowId.substring(0, rowId.lastIndexOf('/'));
        if (annonceData && annonceData.dossier) {
            pdfFilePath = pdfFilePath + "/" + annonceData.dossier + "_annonce_.pdf";
        } else {
            console.error("Impossible de déterminer le chemin du fichier PDF pour rowId:", rowId);
            removeChatMessage(chatMessages, loadingId);
            addChatMessage(chatMessages, "Erreur: chemin du fichier PDF introuvable.", "bot error");
            // Réactiver le bouton et sortir
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Envoyer';
            return;
        }
        
        console.log("DEBUG: Envoi de la question à l'API pour le PDF:", pdfFilePath, "- Question:", question, "- Numéro de dossier:", numDossier);
        
        // Fonction pour réactiver le bouton
        function reactivateButton() {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Envoyer';
        }
        
        // Utiliser soit ApiClient soit fetch selon ce qui est disponible
        if (typeof ApiClient !== 'undefined' && ApiClient.jobs && typeof ApiClient.jobs.getAnswer === 'function' && question != "") {
            // Utiliser ApiClient avec gestion de Promise
            try {
                console.log("DEBUG: Utilisation d'ApiClient avec Promise");

                ApiClient.jobs.getAnswer(pdfFilePath, question, numDossier, true)
                    .then(jobTextResponse => {
                        console.log("DEBUG: Réponse ApiClient Promise résolue:", jobTextResponse);
                        console.log("DEBUG: Type de la réponse:", typeof jobTextResponse);
                        console.log("DEBUG: Propriétés de la réponse:", Object.keys(jobTextResponse || {}));
                        
                        // Supprimer le message de chargement
                        removeChatMessage(chatMessages, loadingId);
                        
                        // Traiter la réponse selon sa structure
                        if (jobTextResponse) {
                            if (jobTextResponse.formatted_text) {
                                addChatMessage(chatMessages, jobTextResponse.formatted_text, 'bot');
                            } else if (jobTextResponse.raw_text) {
                                addChatMessage(chatMessages, jobTextResponse.raw_text, 'bot');
                            } else if (typeof jobTextResponse === 'string') {
                                addChatMessage(chatMessages, jobTextResponse, 'bot');
                            } else if (jobTextResponse.Er005 || jobTextResponse.Er006 || jobTextResponse.Er007) {
                                const errorMsg = jobTextResponse.Er005 || jobTextResponse.Er006 || jobTextResponse.Er007 || 'Erreur inconnue';
                                addChatMessage(chatMessages, `Erreur: ${errorMsg}`, 'bot error');
                            } else {
                                console.warn("Structure de réponse inattendue:", jobTextResponse);
                                addChatMessage(chatMessages, 'Réponse reçue mais format inattendu. Vérifiez la console pour plus de détails.', 'bot error');
                            }
                        } else {
                            addChatMessage(chatMessages, 'Aucune réponse reçue du serveur', 'bot error');
                        }
                        
                        // Réactiver le bouton
                        reactivateButton();
                    })
                    .catch(apiError => {
                        console.error('Erreur avec ApiClient Promise:', apiError);
                        removeChatMessage(chatMessages, loadingId);
                        addChatMessage(chatMessages, 'Erreur lors de l\'appel API: ' + apiError.message, 'bot error');
                        reactivateButton();
                    });
                
            } catch (apiError) {
                console.error('Erreur avec ApiClient:', apiError);
                removeChatMessage(chatMessages, loadingId);
                addChatMessage(chatMessages, 'Erreur lors de l\'appel API: ' + apiError.message, 'bot error');
                reactivateButton();
            }
            
        } else {
            // Fallback vers fetch si ApiClient n'est pas disponible
            console.log("DEBUG: ApiClient non disponible, utilisation de fetch");
            
            fetch('/get_AI_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    path: pdfFilePath,
                    RQ: question,
                    NumDos: numDossier,
                    libre: true
                })
            })
            .then(response => {
                console.log("DEBUG: Réponse fetch reçue, status:", response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("DEBUG: Données fetch reçues:", data);
                console.log("DEBUG: Type des données:", typeof data);
                console.log("DEBUG: Propriétés des données:", Object.keys(data || {}));
                
                // Supprimer le message de chargement
                removeChatMessage(chatMessages, loadingId);
                
                if (data.formatted_text) {
                    addChatMessage(chatMessages, data.formatted_text, 'bot');
                } else if (data.raw_text) {
                    addChatMessage(chatMessages, data.raw_text, 'bot');
                } else if (data.Er005 || data.Er006 || data.Er007) {
                    const errorMsg = data.Er005 || data.Er006 || data.Er007 || 'Erreur inconnue';
                    addChatMessage(chatMessages, `Erreur: ${errorMsg}`, 'bot error');
                } else {
                    console.warn("Structure de données inattendue:", data);
                    addChatMessage(chatMessages, 'Réponse invalide reçue du serveur. Vérifiez la console pour plus de détails.', 'bot error');
                }
                
                // Réactiver le bouton
                reactivateButton();
            })
            .catch(error => {
                console.error('Erreur lors de l\'envoi de la question avec fetch:', error);
                removeChatMessage(chatMessages, loadingId);
                addChatMessage(chatMessages, 'Erreur de connexion: ' + error.message, 'bot error');
                reactivateButton();
            });
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'envoi de la question:', error);
        
        // Nettoyer l'interface en cas d'erreur
        const chatMessages = document.getElementById(`chat-messages-${rowId}`);
        const sendBtn = document.getElementById(`chat-send-btn-${rowId}`);
        
        if (chatMessages) {
            const loadingElement = chatMessages.querySelector('.chat-message:last-child');
            if (loadingElement && loadingElement.textContent.includes('Analyse du document')) {
                loadingElement.remove();
            }
            addChatMessage(chatMessages, 'Erreur technique: ' + error.message, 'bot error');
        }
        
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Envoyer';
        }
    }
}

// Fonction pour ajouter un message dans le chat
function addChatMessage(chatContainer, message, type, isLoading = false) {
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const messageClass = type === 'user' ? 'user-message' : type === 'bot error' ? 'bot-message error' : 'bot-message';
    const icon = type === 'user' ? 'fas fa-user' : type === 'bot error' ? 'fas fa-exclamation-triangle' : 'fas fa-robot';
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${messageClass}`;
    messageDiv.innerHTML = `
        <div class="message-icon">
            <i class="${icon}"></i>
        </div>
        <div class="message-content">
            <p>${message}</p>
            <small class="message-time">${new Date().toLocaleTimeString()}</small>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    
    // Faire défiler vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageId;
}

// Fonction pour supprimer un message du chat
function removeChatMessage(chatContainer, messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.remove();
    }
}

// Fonction pour gérer la sélection d'une ligne (mise à jour)
function selectRow(row) {
    try {
        // Désélectionner toutes les lignes
        document.querySelectorAll('#table-body tr').forEach(tr => {
            tr.classList.remove('selected');
        });
        
        // Sélectionner la ligne actuelle
        row.classList.add('selected');
        currentSelectedRow = row;
        
        // Charger le contenu selon l'onglet actif
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab) {
            if (activeTab.id === 'texte-extrait') {
                loadTextExtract(row.id);
            } else if (activeTab.id === 'chatbot') {
                initializeChatbot(row.id);
            }
        }
        
    } catch (error) {
        console.error('Erreur lors de la sélection de la ligne:', error);
    }
}

// Fonction pour réinitialiser l'aperçu (mise à jour)
function resetPreview() {
    resetTextPreview();
    resetChatbot();
    currentSelectedRow = null;
}

// Fonction pour réinitialiser le chatbot
function resetChatbot() {
    const chatContainer = document.getElementById('chatbot-container');
    if (chatContainer) {
        chatContainer.innerHTML = `
            <div class="chatbot-placeholder">
                <i class="fas fa-robot"></i>
                <p>Sélectionnez une ligne pour analyser le dossier avec l'IA</p>
            </div>
        `;
    }
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

// Initialisation au chargement de la page (mise à jour)
document.addEventListener('DOMContentLoaded', function() {
    // Debug pour vérifier window.annonces
    //setTimeout(debugWindowAnnonces, 1000);
    
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
    
    // Initialiser le chatbot vide
    resetChatbot();
    
    console.log('Module cy_fiche_annonce initialisé - Mode texte et chatbot');
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
                        //alert('PDF sauvegardé avec succès');
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
                    //alert('Nouveau PDF créé avec succès');
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

// Fonction pour basculer la taille du panneau
function togglePanelSize() {
    const splitContainer = document.querySelector('.split-container');
    const toggleButton = document.getElementById('toggle-panel-size');
    const icon = toggleButton.querySelector('i');
    
    if (splitContainer.classList.contains('panel-maximized')) {
        // Restaurer la taille normale
        splitContainer.classList.remove('panel-maximized');
        icon.className = 'fas fa-expand';
        toggleButton.title = 'Agrandir le panneau';
    } else {
        // Maximiser le panneau
        splitContainer.classList.add('panel-maximized');
        icon.className = 'fas fa-compress';
        toggleButton.title = 'Restaurer la taille';
    }
}