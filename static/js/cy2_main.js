/**
 * Point d'entrée principal de l'application CY2
 */
class Cy2Main {
    constructor() {
        this.version = window.CY2_CONFIG.VERSION;
        this.initialized = false;
        this.startTime = Date.now();
        
        cy2Logger.log('Constructor CY2Main créé');
    }
    
    async init() {
        try {
            cy2Logger.log('🔄 Début initialisation CY2...');
            
            // 1. Charger la configuration d'abord
            await this.loadSharedConfiguration();
            
            // 2. Charger les données
            await this.loadInitialData();
            
            // 3. Initialiser les modules APRÈS le chargement des données
            this.initializeModules();
            
            // 4. Configurer les événements
            this.setupEventListeners();
            
            const endTime = Date.now();
            cy2Logger.success(`CY2 initialisé en ${endTime - this.startTime}ms`);
            
        } catch (error) {
            cy2Logger.error('Erreur initialisation CY2:', error);
            throw error;
        }
    }
    
    async checkCompatibility() {
        try {
            const response = await fetch('/cy2/status');
            if (response.ok) {
                const status = await response.json();
                cy2Logger.log('Statut CY2:', status);
                return true;
            } else {
                throw new Error('CY2 status non disponible');
            }
        } catch (error) {
            cy2Logger.warn('Vérification compatibilité échouée, mode dégradé:', error);
            return false;
        }
    }
    
    async loadSharedConfiguration() {
        try {
            // Charger les constantes (API partagée)
            const constantsResponse = await fetch('/get_constants');
            if (constantsResponse.ok) {
                window.CONSTANTS = await constantsResponse.json();
                cy2Logger.log('Constantes chargées:', window.CONSTANTS);
            }
            
            // Charger les colonnes (API partagée)
            const columnsResponse = await fetch('/charger_cols_file');
            if (columnsResponse.ok) {
                const savedColumns = await columnsResponse.json();
                
                // Si le fichier .cols existe et contient des données
                if (savedColumns && Object.keys(savedColumns).length > 0) {
                    window.columns = savedColumns;
                    cy2Logger.log('Colonnes chargées depuis .cols:', savedColumns.length);
                } else {
                    // Fallback vers les colonnes par défaut du state_manager
                    cy2Logger.warn('Fichier .cols vide ou invalide, utilisation colonnes par défaut');
                    // window.columns sera défini par cy_state_manager.js
                    // Si cy_state_manager.js n'est pas chargé, définir des colonnes minimales
                    if (!window.columns) {
                        window.columns = this.getDefaultColumns();
                        cy2Logger.warn('Colonnes par défaut CY2 utilisées');
                    }
                }
            } else {
                cy2Logger.warn('Erreur chargement .cols, utilisation colonnes par défaut');
                if (!window.columns) {
                    window.columns = this.getDefaultColumns();
                }
            }
            
        } catch (error) {
            cy2Logger.error('Erreur chargement configuration:', error);
            // En cas d'erreur, utiliser des colonnes minimales
            if (!window.columns) {
                window.columns = this.getDefaultColumns();
            }
            throw error;
        }
    }
    
    getDefaultColumns() {
        // Colonnes minimales pour CY2 en cas d'échec de chargement
        return [
            { key: 'dossier', fixed: true, title: 'Dos', visible: true, type: 'tb' },
            { key: 'description', title: 'Description', visible: true, type: 'tb' },
            { key: 'entreprise', title: 'Entreprise', visible: true, type: 'tb' },
            { key: 'etat', title: 'État', visible: true, type: 'tb' },
            { key: 'Date', title: 'Date', visible: true, type: 'tb' },
            { key: 'todo', title: 'Todo', visible: true, type: 'tb' }
        ];
    }
    
    async initializeModules() {
        try {
            // Pour l'instant, on utilise les modules existants
            // Les modules CY2 seront créés dans les prochaines étapes
            
            // Charger l'ancien système en mode compatibilité
            if (typeof loadTableData === 'function') {
                cy2Logger.log('Module loadTableData détecté (compatibilité)');
            } else {
                cy2Logger.warn('Module loadTableData non trouvé');
            }
            
            if (typeof generateTableHeaders === 'function') {
                cy2Logger.log('Module generateTableHeaders détecté (compatibilité)');
            } else {
                cy2Logger.warn('Module generateTableHeaders non trouvé');
            }
            
            // Marquer les modules comme chargés
            this.modulesLoaded = true;
            
        } catch (error) {
            cy2Logger.error('Erreur initialisation modules:', error);
            throw error;
        }
    }
    
    setupEventListeners() {
        // Raccourcis clavier pour CY2
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.altKey) {
                if (e.key === '1') {
                    e.preventDefault();
                    this.switchToStable();
                } else if (e.key === 'd') {
                    e.preventDefault();
                    this.toggleDebugMode();
                } else if (e.key === 's') {
                    e.preventDefault();
                    this.showStatus();
                }
            }
        });
        
        cy2Logger.log('Event listeners configurés (Ctrl+Alt+1=Stable, Ctrl+Alt+D=Debug, Ctrl+Alt+S=Status)');
    }
    
    async loadInitialData() {
        // Essayer d'utiliser loadTableData si disponible, sinon chargement direct
        if (typeof loadTableData === 'function') {
            cy2Logger.log('Chargement données avec loadTableData (compatibilité)');
            
            // Attendre que les données soient chargées avant d'appeler loadTableData
            await this.loadDataDirectly();
            
            // Maintenant appeler loadTableData pour le rendu
            loadTableData();
        } else {
            cy2Logger.warn('loadTableData non disponible, tentative de chargement direct');
            await this.loadDataDirectly();
        }
    }
    
    async loadDataDirectly() {
        try {
            // Chargement direct des données si loadTableData n'est pas disponible
            const response = await fetch('/read_annonces_json', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ excluded: ".excluded" })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // NOUVEAU: Utiliser le StateManager
                window.cy2StateManager.setState('annonces', data);
                window.annonces = data; // Rétrocompatibilité
                
                // NOUVEAU: Synchroniser avec les variables globales après chargement
                window.cy2StateManager.syncWithGlobals();
                
                cy2Logger.success(`Données chargées via StateManager: ${data.length} annonces`);
                
                // Déclencher un événement pour notifier le chargement
                const event = new CustomEvent('cy2-data-loaded', { detail: data });
                document.dispatchEvent(event);
            } else {
                throw new Error('Erreur chargement données');
            }
        } catch (error) {
            cy2Logger.error('Erreur chargement direct:', error);
        }
    }
    
    switchToStable() {
        if (confirm('Basculer vers la version stable ?')) {
            localStorage.setItem('cy_last_version', 'stable');
            window.location.href = '/';
        }
    }
    
    toggleDebugMode() {
        window.CY2_CONFIG.DEBUG = !window.CY2_CONFIG.DEBUG;
        cy2Logger.log(`Mode debug: ${window.CY2_CONFIG.DEBUG ? 'ON' : 'OFF'}`);
        
        // Mettre à jour l'affichage debug
        this.updateDebugDisplay();
    }
    
    showStatus() {
        const status = this.getStatus();
        const statusText = `
CY2 Status:
- Version: ${status.version}
- Initialisé: ${status.initialized}
- Temps de chargement: ${status.loadTime}ms
- Modules chargés: ${status.modulesLoaded}
- Données: ${window.annonces ? window.annonces.length : 0} annonces
- Colonnes: ${window.columns ? window.columns.length : 0} colonnes
        `;
        
        alert(statusText);
        cy2Logger.log('Status affiché:', status);
    }
    
    updateDebugDisplay() {
        let debugDiv = document.getElementById('cy2-debug-info');
        
        if (window.CY2_CONFIG.DEBUG) {
            if (!debugDiv) {
                debugDiv = document.createElement('div');
                debugDiv.id = 'cy2-debug-info';
                debugDiv.className = 'cy2-debug-info active';
                document.body.appendChild(debugDiv);
            }
            
            const status = this.getStatus();
            debugDiv.innerHTML = `
                CY2 v${status.version} | 
                ${status.initialized ? '✅' : '❌'} | 
                ${status.loadTime}ms | 
                ${window.annonces ? window.annonces.length : 0} items
            `;
            debugDiv.style.display = 'block';
        } else {
            if (debugDiv) {
                debugDiv.style.display = 'none';
            }
        }
    }
    
    handleInitializationError(error) {
        console.error('❌ CY2 - Erreur critique:', error);
        
        // Afficher un message d'erreur à l'utilisateur
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff4757;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        errorDiv.innerHTML = `
            ❌ Erreur CY2: ${error.message}
            <button onclick="window.location.href='/'" style="margin-left: 10px; background: white; color: #ff4757; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                Retour version stable
            </button>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Proposer le retour automatique vers stable après 5 secondes
        setTimeout(() => {
            if (confirm('CY2 a rencontré une erreur. Retourner à la version stable ?')) {
                window.location.href = '/';
            }
        }, 5000);
    }
    
    // Méthodes utilitaires
    getStatus() {
        return {
            version: this.version,
            initialized: this.initialized,
            loadTime: Date.now() - this.startTime,
            modulesLoaded: this.modulesLoaded || false,
            dataCount: window.annonces ? window.annonces.length : 0,
            columnsCount: window.columns ? window.columns.length : 0
        };
    }
}

// Créer l'instance globale
window.cy2Main = new Cy2Main();

// Auto-initialisation si DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.cy2Main.init();
    });
} else {
    // DOM déjà prêt
    window.cy2Main.init();
}