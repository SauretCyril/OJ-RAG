// Ajouter au début de cy_fiche_annonce.js pour ignorer les erreurs d'extension
window.addEventListener('error', function(e) {
    if (e.message.includes('runtime.lastError')) {
        e.preventDefault();
        return true;
    }
});

//let currentSelectedRow = null;

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
    currentrow = getState('currentSelectedRow');
    // Charger le contenu selon l'onglet
    if (currentrow) {
        if (tabId === 'texte-extrait') {
            loadTextExtract(currentrow.id);
        } else if (tabId === 'chatbot') {
            initializeChatbot(currentrow.id);
        }
    }
}

// Nouvelle fonction pour charger le texte extrait
function loadTextExtract(rowId) {
    try {
        const textViewer = document.getElementById('text-viewer');
        const saveBtn = document.getElementById('save-text-btn');
        const annonceData = getAnnonce_byfile(rowId);
        
        console.log('Dbg02-a loadTextExtract - rowId:', rowId);
        console.log('Dbg02-b loadTextExtract - annonceData:', annonceData);
        
        if (annonceData) {
            const numDossier = annonceData.dossier;
            const pdfFilePath = numDossier + "/" + numDossier + "_annonce_.pdf";
            console.log('Dbg02-c loadTextExtract - pdfFilePath:', pdfFilePath);

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
            console.log('DEBUG: Envoi de la requête à /extract_pdf_text');

            fetch('/extract_pdf_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file: pdfFilePath
                })
            })
            .then(response => {
                if (response.status === 404) {
                    // Afficher un message utilisateur, pas d'exception
                    showTextError("Aucun fichier PDF trouvé à extraire.");
                    return null;
                }
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (!data) return;
                console.log('DEBUG: Données reçues:', data);
                if (data.success) {
                    showTextContent(data.text);
                    showSaveButton('save', rowId);
                } else {
                    showTextError(data.error || 'Erreur lors de l\'extraction du texte');
                    showSaveButton('new', rowId);
                }
            })
            .catch(error => {
                console.error('Erreur détaillée lors de l\'extraction du texte:', error);
                showTextError('Erreur de connexion: ' + error.message);
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
    currentrow = getState('currentSelectedRow');
    // Charger le contenu selon l'onglet (seulement texte-extrait)
    if (currentrow && tabId === 'texte-extrait') {
        loadTextExtract(currentrow.id);
    }
}

// Nouvelle fonction pour initialiser le chatbot
function initializeChatbot(rowId) {
    try {
        const chatContainer = document.getElementById('chatbot-container');
        if (!chatContainer) return;

        // Extraire le numéro de dossier
        const annonceData = getAnnonce_byfile(rowId);
        const numDossier = annonceData ? annonceData.dossier : '';

        chatContainer.innerHTML = `
            <div class="chatbot-interface">
                <!-- Zone de rôle IA -->
                <div class="ai-role-section">
                    <div class="ai-role-header">
                        <h4><i class="fas fa-user-cog"></i> Rôle de l'Assistant IA</h4>
                        <button id="save-role-btn-${rowId}" class="btn btn-sm btn-success" onclick="saveAIRole('${rowId}')" style="display: none;">
                            <i class="fas fa-save"></i> Sauvegarder
                        </button>
                    </div>
                    <textarea id="ai-role-text-${rowId}" class="ai-role-textarea" 
                              placeholder="Définissez le rôle de l'assistant IA..."
                              oninput="onRoleTextChange('${rowId}')"></textarea>
                </div>
                
                <!-- Zone de chat -->
                <div class="chat-section">
                    <div class="chat-messages" id="chat-messages-${rowId}">
                        <div class="chat-welcome">
                            <i class="fas fa-robot"></i>
                            <p>Assistant IA prêt à analyser le dossier</p>
                        </div>
                    </div>
                    
                    <div class="chat-input-section">
                        <div class="chat-input-container">
                            <input type="text" id="chat-input-${rowId}" 
                                   placeholder="Posez votre question sur ce dossier..." 
                                   onkeypress="if(event.key==='Enter') sendChatQuestion('${rowId}')">
                            <button id="chat-send-btn-${rowId}" onclick="sendChatQuestion('${rowId}')">
                                <i class="fas fa-paper-plane"></i> Envoyer
                            </button>
                        </div>
                        <button id="chat-save-pdf-btn-${rowId}" class="btn btn-secondary" style="margin-top:10px;" onclick="saveChatToPDF('${rowId}')">
                            <i class="fas fa-file-pdf"></i> Sauvegarder en PDF
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Charger le rôle IA existant
        loadAIRole(rowId, numDossier);

    } catch (error) {
        console.error('Erreur lors de l\'initialisation du chatbot:', error);
    }
}

// Nouvelle fonction pour charger le rôle IA
function loadAIRole(rowId, numDossier) {
    if (!numDossier) return;

    fetch('/get_AI_role', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            NumDos: numDossier
        })
    })
    .then(response => response.json())
    .then(data => {
        const roleTextarea = document.getElementById(`ai-role-text-${rowId}`);
        if (roleTextarea && data.role_text) {
            roleTextarea.value = data.role_text;
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement du rôle IA:', error);
    });
}

// Nouvelle fonction pour détecter les changements dans le texte du rôle
function onRoleTextChange(rowId) {
    const saveBtn = document.getElementById(`save-role-btn-${rowId}`);
    if (saveBtn) {
        saveBtn.style.display = 'inline-block';
    }
}

// Nouvelle fonction pour sauvegarder le rôle IA
function saveAIRole(rowId) {
    const roleTextarea = document.getElementById(`ai-role-text-${rowId}`);
    const saveBtn = document.getElementById(`save-role-btn-${rowId}`);
    
    if (!roleTextarea) return;

    const annonceData = getAnnonce_byfile(rowId);
    const numDossier = annonceData ? annonceData.dossier : '';
    
    if (!numDossier) {
        alert('Erreur: Numéro de dossier non trouvé');
        return;
    }

    // Désactiver le bouton pendant la sauvegarde
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sauvegarde...';
    }

    fetch('/save_AI_role', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            NumDos: numDossier,
            role_text: roleTextarea.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Masquer le bouton de sauvegarde
            if (saveBtn) {
                saveBtn.style.display = 'none';
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save"></i> Sauvegarder';
            }
            
            // Afficher un message de succès temporaire
            const successMsg = document.createElement('div');
            successMsg.className = 'alert alert-success';
            successMsg.style.position = 'absolute';
            successMsg.style.top = '10px';
            successMsg.style.right = '10px';
            successMsg.style.zIndex = '1000';
            successMsg.innerHTML = '<i class="fas fa-check"></i> Rôle sauvegardé';
            document.body.appendChild(successMsg);
            
            setTimeout(() => {
                document.body.removeChild(successMsg);
            }, 3000);
        } else {
            throw new Error(data.message || 'Erreur de sauvegarde');
        }
    })
    .catch(error => {
        console.error('Erreur lors de la sauvegarde du rôle IA:', error);
        alert('Erreur lors de la sauvegarde: ' + error.message);
        
        // Réactiver le bouton en cas d'erreur
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Sauvegarder';
        }
    });
}

// Fonction pour envoyer une question au chatbot
function sendChatQuestion(rowId) {
    try {
        const questionInput = document.getElementById(`chat-input-${rowId}`);
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



//<div id="action-bar"
// Fonction pour gérer la sélection d'une ligne (mise à jour)
function selectRow(row) {
    try {
        document.querySelectorAll('#table-body tr').forEach(tr => {
            tr.classList.remove('selected');
        });
        row.classList.add('selected');
        setState('currentSelectedRow', row, () => {
            showActionBar();
            updatePromptButtonVisibility();
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab) {
                if (activeTab.id === 'texte-extrait') {
                    loadTextExtract(row.id);
                } else if (activeTab.id === 'chatbot') {
                    initializeChatbot(row.id);
                }
            }
            populateDirectorySelect();
        });
    } catch (error) {
        console.error('Erreur lors de la sélection de la ligne:', error);
    }
}

// Fonction pour réinitialiser l'aperçu (mise à jour)
function resetPreview() {
    resetTextPreview();
    resetChatbot();
    //currentSelectedRow = null;
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
                fetch('/save_text_pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        NumDos: numDossier,
                        text: text,
                        Docname:"_annonce_.pdf",    

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

// Fonction pour sauvegarder le chat en PDF
function saveChatToPDF(rowId) {
    const chatMessages = document.getElementById(`chat-messages-${rowId}`);
    if (!chatMessages) {
        alert("Aucun message à sauvegarder.");
        return;
    }

    // Récupérer le texte du chat
    let chatText = "";
    chatMessages.querySelectorAll('.chat-message').forEach(msg => {
        const type = msg.classList.contains('user-message') ? "Question" : "Réponse";
        const content = msg.querySelector('.message-content p')?.textContent || "";
        chatText += `${type}: ${content}\n\n`;
    });

    // Appeler l'API pour générer le PDF côté serveur
    const annonceData = getAnnonce_byfile(rowId);
    const numDossier = annonceData ? annonceData.dossier : '';
    fetch('/save_text_pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            NumDos: numDossier,
            text: chatText,
            Docname:"_chat.pdf"
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Chat sauvegardé avec succès !");
        } else {
            alert("Erreur lors de la sauvegarde du PDF : " + (data.error || "Erreur inconnue"));
        }
    })
    .catch(error => {
        alert("Erreur lors de la sauvegarde du PDF : " + error.message);
    });
}

// Fonction pour afficher la barre d'action
function showActionBar() {
    const bar = document.getElementById('action-bar');
    if (bar) bar.style.display = 'flex';
}

// Fonction pour cacher la barre d'action
function hideActionBar() {
    const bar = document.getElementById('action-bar');
    if (bar) bar.style.display = 'none';
}
 
function populateDirectorySelect() {
    const select = document.getElementById('directory-select');
    if (!window.AppState || !AppState.directories) return;
    select.innerHTML = '';
    AppState.directories.forEach(dir => {
        const option = document.createElement('option');
        option.value = dir.path;
        option.textContent = dir.label;
        // Correction ici : on compare avec currentDossier
        if (dir.path === AppState.currentDossier) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

// Affiche ou cache le bouton selon le type de la ligne sélectionnée
function updatePromptButtonVisibility() {
    const annonce = get_currentAnnonce();
if (!annonce) {
        console.warn('Aucune annonce sélectionnée pour mettre à jour le bouton Prompt.');
        return false;
    }
    const type = annonce.type;
    const btn = document.getElementById('fix_open_prompt_analyse');
    if (!btn) {
        console.error('Bouton fix_open_prompt_analyse non trouvé dans le DOM');
        return false;
    }
    if (type === "Prompt") {
        btn.style.display = "inline-block";
        return true;
    } else {
        btn.style.display = "none";
        return false;
    }
}
