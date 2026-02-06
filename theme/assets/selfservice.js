(() => {
    'use strict';

    // ===========================
    // DOM ELEMENT REFERENCES
    // ===========================
    const mainContent = document.getElementById('main-content');
    const backBtn = document.getElementById('back-btn');
    const cartBtn = document.getElementById('cart-btn');
    const cartCount = document.getElementById('cart-count');
    const breadcrumbContainer = document.getElementById('breadcrumb-container');
    const backToTopBtn = document.getElementById('back-to-top');
    const homeFooterBtn = document.getElementById('home-footer-btn');
    const adminTrigger = document.getElementById('admin-trigger');

    // ===========================
    // STATE MANAGEMENT
    // ===========================
    const state = {
        parts: [],
        cart: [],
        currentView: 'home',
        selectedCategory: null,
        searchResults: [],
        activeSearchFilter: 'all',
        orderHistory: [],
        activeServices: [],
        categories: [],
        navigationHistory: [],
        technicians: [],

        // Service-specific state
        activeReg: null,
        serviceSearchQuery: '',
        currentStatusFilter: 'all',
        currentWorkDoneReg: null,

        // Parts request state
        partsSearchQuery: '',
        techNotes: '',
        defectList: '',
        activePartsTab: 'request',
        customerResponse: '',
        approvedParts: '',
        selectedTechnician: '',
        signatureData: '',
        collapseOpen: false,

        // Admin state
        adminClicks: 0,
        adminTimeout: null,

        // Auto-refresh
        autoRefreshInterval: null
    };

    // Category display configuration
    const categoryConfig = {
        'Body & Exterior': { icon: '🚗', color: 'bg-indigo' },
        'Brake System': { icon: '🛑', color: 'bg-orange' },
        'Cooling System': { icon: '❄️', color: 'bg-cyan' },
        'Electrical & Lighting': { icon: '💡', color: 'bg-yellow' },
        'Engine Components': { icon: '⚙️', color: 'bg-red' },
        'Exhaust System': { icon: '💨', color: 'bg-gray' },
        'Filters & Fluids': { icon: '🔍', color: 'bg-green' },
        'Suspension & Steering': { icon: '🔧', color: 'bg-blue' },
        'Transmission': { icon: '⚡', color: 'bg-purple' }
    };

    // ===========================
    // UTILITY FUNCTIONS
    // ===========================

    function sanitizeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function categorize(part) {
        return part.category ? part.category.toLowerCase().replace(/\s+/g, '-') : 'other';
    }

    // ===========================
    // CUSTOM ALERT/CONFIRM
    // ===========================

    function customAlert(message, title = 'BMA Parts Express') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'custom-alert-overlay';

            overlay.innerHTML = `
                <div class="custom-alert-box">
                    <div class="custom-alert-title">
                        ${sanitizeHTML(title)}
                    </div>
                    <div class="custom-alert-message">${sanitizeHTML(message)}</div>
                    <button class="custom-alert-button">OK</button>
                </div>
            `;

            document.body.appendChild(overlay);

            const button = overlay.querySelector('.custom-alert-button');
            const closeAlert = () => {
                overlay.remove();
                resolve();
            };

            button.onclick = closeAlert;
            overlay.onclick = (e) => {
                if (e.target === overlay) closeAlert();
            };

            setTimeout(() => button.focus(), 100);
        });
    }

    function customConfirm(message, title = 'Confirm Action') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'custom-alert-overlay';

            overlay.innerHTML = `
                <div class="custom-alert-box">
                    <div class="custom-alert-title">
                        ❓ ${sanitizeHTML(title)}
                    </div>
                    <div class="custom-alert-message">${sanitizeHTML(message)}</div>
                    <div style="display:flex; gap:1rem;">
                        <button class="custom-alert-button" style="background:#64748b;" data-action="cancel">Cancel</button>
                        <button class="custom-alert-button" data-action="confirm">Confirm</button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const handleClick = (confirmed) => {
                overlay.remove();
                resolve(confirmed);
            };

            overlay.querySelector('[data-action="confirm"]').onclick = () => handleClick(true);
            overlay.querySelector('[data-action="cancel"]').onclick = () => handleClick(false);
            overlay.onclick = (e) => {
                if (e.target === overlay) handleClick(false);
            };
        });
    }

    // ===========================
    // SIGNATURE PAD CLASS
    // ===========================

    class SignaturePad {
        constructor(canvasId) {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) {
                console.error('Canvas not found:', canvasId);
                return;
            }
            this.ctx = this.canvas.getContext('2d');
            this.isSigned = false;
            this.isDrawing = false;
            this.lastX = 0;
            this.lastY = 0;

            this.resize();

            this.init();
        }

        resize() {
            const rect = this.canvas.getBoundingClientRect();
            if (!rect.width) return;
            this.canvas.width = rect.width;
            this.canvas.height = 200;

            // Fill canvas with white background
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

            if (this.isSigned && state.signatureData) {
                const img = new Image();
                img.onload = () => {
                    this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
                };
                img.src = state.signatureData;
            }
        }

        init() {
            console.log('Initializing signature pad...');

            // Mouse events
            this.canvas.addEventListener('mousedown', (e) => {
                e.preventDefault();
                console.log('Mouse down detected');
                this.startDrawing(e);
            });
            this.canvas.addEventListener('mousemove', (e) => {
                e.preventDefault();
                this.draw(e);
            });
            this.canvas.addEventListener('mouseup', (e) => {
                e.preventDefault();
                console.log('Mouse up detected');
                this.stopDrawing();
            });
            this.canvas.addEventListener('mouseout', (e) => {
                e.preventDefault();
                this.stopDrawing();
            });

            // Touch events - FIXED
            this.canvas.addEventListener('touchstart', (e) => {
                e.preventDefault();
                console.log('Touch start detected');
                this.startDrawing(e);
            }, { passive: false });

            this.canvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
                console.log('Touch move detected'); // Added logging
                this.draw(e);
            }, { passive: false });

            this.canvas.addEventListener('touchend', (e) => {
                e.preventDefault();
                console.log('Touch end detected');
                this.stopDrawing();
            }, { passive: false });

            this.canvas.addEventListener('touchcancel', (e) => {
                e.preventDefault();
                console.log('Touch cancel detected');
                this.stopDrawing();
            }, { passive: false });

            console.log('Signature pad initialized successfully');
        }

        startDrawing(event) {
            this.isDrawing = true;
            const pos = this.getMousePos(event);
            this.lastX = pos.x;
            this.lastY = pos.y;

            // Draw a small dot at the starting point
            this.ctx.beginPath();
            this.ctx.arc(pos.x, pos.y, 1, 0, Math.PI * 2);
            this.ctx.fillStyle = '#06b6d4';
            this.ctx.fill();

            console.log('Started drawing at:', pos);
        }

        draw(event) {
            if (!this.isDrawing) return;

            event.preventDefault();
            const pos = this.getMousePos(event);

            this.ctx.beginPath();
            this.ctx.moveTo(this.lastX, this.lastY);
            this.ctx.lineTo(pos.x, pos.y);
            this.ctx.strokeStyle = '#06b6d4';
            this.ctx.lineWidth = 2;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            this.ctx.stroke();

            this.lastX = pos.x;
            this.lastY = pos.y;
            this.isSigned = true;

            console.log('Drawing to:', pos); // Added logging
        }

        stopDrawing() {
            if (this.isDrawing) {
                this.isDrawing = false;
                if (this.isSigned) {
                    state.signatureData = this.getSignatureData();
                }
                console.log('Stopped drawing');
            }
        }

        getMousePos(event) {
            const rect = this.canvas.getBoundingClientRect();
            let x, y;

            if (event.touches && event.touches.length > 0) {
                x = event.touches[0].clientX - rect.left;
                y = event.touches[0].clientY - rect.top;
            } else {
                x = event.clientX - rect.left;
                y = event.clientY - rect.top;
            }

            return { x, y };
        }

        clear() {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            // Refill with white background
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.isSigned = false;
            console.log('Signature cleared');
        }

        getSignatureData() {
            if (this.isSigned) {
                return this.canvas.toDataURL('image/png');
            }
            return '';
        }
    }

    let signaturePadInstance = null;

    function initSignaturePad() {
        // Use requestAnimationFrame for better timing
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                const canvas = document.getElementById('signature-canvas');
                if (!canvas) {
                    console.error('Signature canvas not found');
                    return;
                }

                if (!signaturePadInstance || signaturePadInstance.canvas !== canvas) {
                    signaturePadInstance = new SignaturePad('signature-canvas');
                } else {
                    signaturePadInstance.resize();
                }

                if (state.signatureData && signaturePadInstance) {
                    const img = new Image();
                    img.onload = () => {
                        signaturePadInstance.ctx.drawImage(
                            img,
                            0,
                            0,
                            signaturePadInstance.canvas.width,
                            signaturePadInstance.canvas.height
                        );
                        signaturePadInstance.isSigned = true;
                    };
                    img.src = state.signatureData;
                }

                console.log('Signature pad setup complete');
            });
        });
    }

    function clearSignature() {
        if (signaturePadInstance) {
            signaturePadInstance.clear();
            state.signatureData = '';
        } else {
            console.warn('Signature pad instance not found');
        }
    }

    function getSignatureData() {
        if (signaturePadInstance && signaturePadInstance.isSigned) {
            state.signatureData = signaturePadInstance.getSignatureData();
            return state.signatureData;
        }
        return '';
    }

    // ===========================
    // NAVIGATION MANAGEMENT
    // ===========================

    function pushNavigation(view, newState = {}) {
        if (state.currentView === view) return;

        // Persist signature before leaving the request parts view
        getSignatureData();

        state.navigationHistory.push({
            view: state.currentView,
            state: {
                selectedCategory: state.selectedCategory,
                activeReg: state.activeReg,
                activePartsTab: state.activePartsTab,
                partsSearchQuery: state.partsSearchQuery
            }
        });

        state.currentView = view;
        if (newState.selectedCategory !== undefined) state.selectedCategory = newState.selectedCategory;
        if (newState.activeReg !== undefined) state.activeReg = newState.activeReg;
        if (newState.activePartsTab !== undefined) state.activePartsTab = newState.activePartsTab;
        if (newState.partsSearchQuery !== undefined) state.partsSearchQuery = newState.partsSearchQuery;

        render();
    }

    function popNavigation() {
        if (state.navigationHistory.length === 0) {
            goToHome();
            return;
        }

        const previous = state.navigationHistory.pop();
        state.currentView = previous.view;
        state.selectedCategory = previous.state.selectedCategory;
        state.activeReg = previous.state.activeReg;
        state.activePartsTab = previous.state.activePartsTab;
        state.partsSearchQuery = previous.state.partsSearchQuery;
        render();
    }

    function clearNavigationHistory() {
        state.navigationHistory = [];
    }

    // ===========================
    // DATA LOADING
    // ===========================

    async function init() {
        try {
            const serverData = await anvil.call(mainContent, 'getCarPartNamesAndCategory');
            console.log("Server data received:", serverData);

            if (!Array.isArray(serverData)) {
                throw new Error("Server did not return a list. Check server logs.");
            }

            state.parts = serverData.map(item => ({
                name: item.Name,
                category: item.Category,
                partNo: item.PartNo || item.Name
            }));

            const uniqueCategories = [...new Set(serverData.map(item => item.Category))];

            state.categories = uniqueCategories.map(catName => {
                const config = categoryConfig[catName] || { icon: '📦', color: 'bg-gray' };
                return {
                    id: catName.toLowerCase().replace(/\s+/g, '-'),
                    name: catName,
                    icon: config.icon,
                    color: config.color
                };
            });

            await loadActiveServices();
            await loadTechnicians();

            setupListeners();
            render();

            // Clear any existing interval
            if (state.autoRefreshInterval) {
                clearInterval(state.autoRefreshInterval);
            }

            // Auto-refresh every minute
            state.autoRefreshInterval = setInterval(async () => { 
                if (state.currentView === 'home') {
                    await loadActiveServices();
                    render();
                }
            }, 60000);

        } catch (e) { 
            console.error("Initialization Error:", e);
            if (e && e.args) {
                console.error("Python args:", e.args);
            }
            await customAlert(
                'Failed to initialize application. Please refresh the page.',
                'Initialization Error'
            );
        }
    }

    async function loadActiveServices() {
        try {
            const jobcardsData = await anvil.call(mainContent, 'get_technician_jobcards_by_status');

            if (!Array.isArray(jobcardsData)) {
                throw new Error('Invalid data format received');
            }

            state.activeServices = jobcardsData.map(card => ({
                no: card.id,
                date: card.ReceivedDate,
                tech: card.Technician,
                jobcardref: card.JobCardRef,
                instruction: card.Instruction,
                workDone: card.workDone || '',
                status: card.status === 'Checked In' ? 'Checked-In' : 
                    card.status === 'In Service' ? 'In-Service' : 
                    card.status
            }));

            console.log('Loaded active services:', state.activeServices.length);
        } catch (error) {
            console.error('Error loading active services:', error);
            state.activeServices = [];

            if (state.currentView === 'home') {
                await customAlert(
                    'Failed to load services. Please refresh the page.',
                    'Connection Error'
                );
            }
        }
    }

    async function loadTechnicians() {
        try {
            const techData = await anvil.call(mainContent, 'get_technicians_list');
            state.technicians = techData || [];
            console.log('Loaded technicians:', state.technicians.length);
        } catch (error) {
            console.error('Error loading technicians:', error);
            state.technicians = [];
        }
    }

    // ===========================
    // RENDER FUNCTIONS
    // ===========================

    function render() {
        const showBackBtn = state.navigationHistory.length > 0 && 
            state.currentView !== 'home' && 
            state.currentView !== 'success' && 
            state.currentView !== 'admin';

        backBtn.classList.toggle('hidden', !showBackBtn);

        const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.innerText = Math.round(totalQuantity);
        cartCount.classList.toggle('hidden', state.cart.length === 0 || 
                                   state.currentView === 'success' || 
                                   state.currentView === 'workDone');

        updateBreadcrumbs();

        switch (state.currentView) {
            case 'home':
                renderHome();
                break;
            case 'Request Parts':
                renderRequestParts();
                break;
            case 'category':
                renderCategory();
                break;
            case 'search':
                renderSearch();
                break;
            case 'checkout':
                renderCheckout();
                break;
            case 'success':
                renderSuccess();
                break;
            case 'admin':
                renderAdmin();
                break;
            case 'workDone':
                renderWorkDone();
                break;
            default:
                renderHome();
        }

        window.scrollTo({ top: 0, behavior: 'instant' });
        lucide.createIcons();
    }

    function renderHome() {
        const filtered = state.activeServices.filter(s => {
            const matchesStatus = state.currentStatusFilter === 'all' ? 
                (s.status !== 'Completed') : 
                (s.status === state.currentStatusFilter);
            
            // Enhanced search - similar to modal parts search
            if (!state.serviceSearchQuery.trim()) {
                return matchesStatus;
            }
            
            const searchTerm = state.serviceSearchQuery.toLowerCase();
            const matchesSearch = 
                s.jobcardref.toLowerCase().includes(searchTerm) || 
                s.tech.toLowerCase().includes(searchTerm) ||
                (s.instruction && s.instruction.toLowerCase().includes(searchTerm)) ||
                (s.date && s.date.toLowerCase().includes(searchTerm)) ||
                (s.status && s.status.toLowerCase().includes(searchTerm));
            
            return matchesStatus && matchesSearch;
        });

        const totalServices = state.activeServices.length;
        const checkedInCount = state.activeServices.filter(s => s.status === 'Checked-In').length;
        const inServiceCount = state.activeServices.filter(s => s.status === 'In-Service').length;

        mainContent.innerHTML = `
        <!-- Hero Section -->
        <div class="hero-section">
            <h1 class="hero-title">BMA PARTS EXPRESS</h1>
            <p class="hero-subtitle">A comprehensive, operational, and centralized hub for technical excellence.</p>
            
            <div class="status-badges">
                <span class="badge badge-premium">Comprehensive</span>
                <span class="badge badge-fast">Operational</span>
                <span class="badge badge-service">Centralized</span>
            </div>
        </div>

        <!-- Stats Cards -->
        <div class="service-card-grid">
            <div class="service-card">
                <div class="service-icon">🔧</div>
                <div>
                    <div class="service-card-title">Total Services</div>
                    <div class="service-card-subtitle">All active services</div>
                    <div class="service-stat">${totalServices}</div>
                </div>
            </div>
            
            <div class="service-card">
                <div class="service-icon" style="background: linear-gradient(135deg, #facc15 0%, #eab308 100%);">⏳</div>
                <div>
                    <div class="service-card-title">Checked In</div>
                    <div class="service-card-subtitle">Awaiting service</div>
                    <div class="service-stat">${checkedInCount}</div>
                </div>
            </div>
            
            <div class="service-card">
                <div class="service-icon" style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);">🔨</div>
                <div>
                    <div class="service-card-title">In Service</div>
                    <div class="service-card-subtitle">Currently working</div>
                    <div class="service-stat">${inServiceCount}</div>
                </div>
            </div>
            
        </div>
        
        <!-- Filter and Search -->
        <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:2rem; flex-wrap:wrap;">
            <div style="display:flex; gap:1rem;">
                <button class="btn-status ${state.currentStatusFilter === 'Checked-In' ? 'active-filter' : ''}" onclick="filterByStatus('Checked-In')">Checked-In</button>
                <button class="btn-status ${state.currentStatusFilter === 'In-Service' ? 'active-filter' : ''}" onclick="filterByStatus('In-Service')">In-Service</button>
            </div>
            
            <div style="position:relative; flex:1; max-width:400px; min-width:300px;">
                <input type="text" id="service-search" class="search-input" placeholder="Search by JobCard, Technician, Status..." value="${sanitizeHTML(state.serviceSearchQuery)}" style="font-size:1.5rem; padding:1rem 1rem 1rem 3.5rem; width:100%;">
                <span style="position:absolute; left:1rem; top:1.2rem; color:#94a3b8;">🔍</span>
            </div>
        </div>

        <div class="service-table-container">
            <table class="kiosk-table">
                <thead><tr><th>No</th><th>Received</th><th>Technician</th><th>JobCard Ref</th><th>Instruction</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                    ${filtered.map(s => `
                        <tr>
                            <td data-label="No">${s.no}</td>
                            <td data-label="Received">${sanitizeHTML(s.date)}</td>
                            <td data-label="Technician"><strong>${sanitizeHTML(s.tech)}</strong></td>
                            <td data-label="JobCard Ref" style="color:#facc15; font-weight:bold;">${sanitizeHTML(s.jobcardref)}</td>
                            <td data-label="Instruction">${sanitizeHTML(s.instruction)}</td>
                            <td data-label="Status"><span class="status-badge ${s.status === 'In-Service' ? 'status-in-service' : s.status === 'Completed' ? 'status-completed' : 'status-checked-in'}">${s.status}</span></td>
                            <td data-label="Action">
                                ${s.status === 'Completed' ? '✅ Finished' : s.status === 'In-Service' ? `
                                    <button onclick="openWorkDone('${sanitizeHTML(s.jobcardref)}')" style="background:#3b82f6; border:none; color:white; padding:0.8rem 1.2rem; border-radius:0.5rem; cursor:pointer; font-weight:bold;">Work Done</button>
                                ` : `
                                    <button onclick="openParts('${sanitizeHTML(s.jobcardref)}')" class="btn-issue-parts">Request Parts</button>
                                `}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

        const sInput = document.getElementById('service-search');
        if (sInput) {
            const debouncedSearch = debounce((value) => {
                state.serviceSearchQuery = value;
                updateServiceTable();
            }, 300);

            sInput.oninput = (e) => {
                debouncedSearch(e.target.value);
            };

            sInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    state.serviceSearchQuery = e.target.value;
                    updateServiceTable();
                }
            };

            sInput.onclick = (e) => e.target.focus();
        }
    }

    function updateServiceTable() {
        const filtered = state.activeServices.filter(s => {
            const matchesStatus = state.currentStatusFilter === 'all' ? 
                (s.status !== 'Completed') : 
                (s.status === state.currentStatusFilter);
            
            // Enhanced search - similar to modal parts search
            if (!state.serviceSearchQuery.trim()) {
                return matchesStatus;
            }
            
            const searchTerm = state.serviceSearchQuery.toLowerCase();
            const matchesSearch = 
                s.jobcardref.toLowerCase().includes(searchTerm) || 
                s.tech.toLowerCase().includes(searchTerm) ||
                (s.instruction && s.instruction.toLowerCase().includes(searchTerm)) ||
                (s.date && s.date.toLowerCase().includes(searchTerm)) ||
                (s.status && s.status.toLowerCase().includes(searchTerm));
            
            return matchesStatus && matchesSearch;
        });

        const tbody = document.querySelector('.kiosk-table tbody');
        if (tbody) {
            tbody.innerHTML = filtered.map(s => `
                <tr>
                    <td data-label="No">${s.no}</td>
                    <td data-label="Received">${sanitizeHTML(s.date)}</td>
                    <td data-label="Technician"><strong>${sanitizeHTML(s.tech)}</strong></td>
                    <td data-label="JobCard Ref" style="color:#facc15; font-weight:bold;">${sanitizeHTML(s.jobcardref)}</td>
                    <td data-label="Instruction">${sanitizeHTML(s.instruction)}</td>
                    <td data-label="Status"><span class="status-badge ${s.status === 'In-Service' ? 'status-in-service' : s.status === 'Completed' ? 'status-completed' : 'status-checked-in'}">${s.status}</span></td>
                    <td data-label="Action">
                        ${s.status === 'Completed' ? '✅ Finished' : s.status === 'In-Service' ? `
                            <button onclick="openWorkDone('${sanitizeHTML(s.jobcardref)}')" style="background:#3b82f6; border:none; color:white; padding:0.8rem 1.2rem; border-radius:0.5rem; cursor:pointer; font-weight:bold;">Work Done</button>
                        ` : `
                            <button onclick="openParts('${sanitizeHTML(s.jobcardref)}')" class="btn-issue-parts">Request Parts</button>
                        `}
                    </td>
                </tr>
            `).join('');
        }
    }

    function renderWorkDone() {
        const service = state.activeServices.find(s => s.jobcardref === state.currentWorkDoneReg);
        if (!service) {
            goToHome();
            return;
        }

        mainContent.innerHTML = `
            <div style="max-width:800px; margin:2rem auto;">
                <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); padding:3rem; border-radius:2rem; border:4px solid rgba(59, 130, 246, 0.5); box-shadow: 0 20px 60px rgba(59, 130, 246, 0.3);">
                    <div style="margin-bottom:2rem;">
                        <h2 style="font-size:2.5rem; margin-bottom:1rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Work Done Report</h2>
                        <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); padding:1.5rem; border-radius:1rem; margin-bottom:2rem; border:2px solid rgba(59, 130, 246, 0.2);">
                            <p style="font-size:1.8rem;"><strong>Registration:</strong> <span style="color:#facc15;">${sanitizeHTML(service.jobcardref)}</span></p>
                            <p style="font-size:1.8rem;"><strong>Technician:</strong> ${sanitizeHTML(service.tech)}</p>
                            <p style="font-size:1.8rem;"><strong>Instruction:</strong> ${sanitizeHTML(service.instruction)}</p>
                        </div>
                    </div>
                    
                    <div style="margin-bottom:2rem;">
                        <label style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">
                            <span>Describe the work completed:</span>
                            <div style="display:flex; gap:0.5rem;">
                                <span id="work-done-voice-indicator" class="voice-indicator" aria-hidden="true"></span>
                                <button id="work-done-voice-start" type="button" style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem;"><i data-lucide="mic"></i>  </button>
                                <button id="work-done-voice-stop" type="button" disabled style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem; opacity:0.6;"><i data-lucide="mic-off"></i>  </button>
                            </div>
                        </label>
                        <textarea 
                            id="work-done-textarea" 
                            rows="8" 
                            placeholder="Enter detailed description of work performed..."
                            style="width:100%; padding:1.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical;"
                        >${sanitizeHTML(service.workDone || '')}</textarea>
                    </div>

                    <div style="display:flex; gap:1rem; justify-content:flex-end;">
                        <button 
                            onclick="cancelWorkDone()" 
                            style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease;">
                            Cancel
                        </button>
                        <button 
                            onclick="saveWorkDone()" 
                            style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease;">
                            <i data-lucide="save" style="width:20px; height:20px; display:inline-block; vertical-align:middle; margin-right:0.5rem;"></i>
                            Save Work Done
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderRequestParts() {
        const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);

        mainContent.innerHTML = `
        <h2 style="margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Requesting Parts for: <span style="color:#facc15">${sanitizeHTML(state.activeReg)}</span></h2>
        
        <!-- Tab Navigation -->
        <div style="display:flex; gap:1rem; margin-bottom:2rem; background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); padding:1rem; border-radius:1.5rem; border:2px solid rgba(59, 130, 246, 0.2); overflow-x:auto;">
            <button 
                onclick="switchPartsTab('request')" 
                class="parts-tab-btn ${state.activePartsTab === 'request' ? 'active' : ''}"
                style="flex:1; min-width:180px; padding:1.2rem 2rem; border-radius:1rem; font-size:1.8rem; font-weight:bold; cursor:pointer; transition:all 0.3s ease; border:2px solid ${state.activePartsTab === 'request' ? 'rgba(59, 130, 246, 0.5)' : 'transparent'}; background:${state.activePartsTab === 'request' ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' : 'transparent'}; color:white;">
                📦 Parts Request
            </button>
            <button 
                onclick="switchPartsTab('feedback')" 
                class="parts-tab-btn ${state.activePartsTab === 'feedback' ? 'active' : ''}"
                style="flex:1; min-width:180px; padding:1.2rem 2rem; border-radius:1rem; font-size:1.8rem; font-weight:bold; cursor:pointer; transition:all 0.3s ease; border:2px solid ${state.activePartsTab === 'feedback' ? 'rgba(59, 130, 246, 0.5)' : 'transparent'}; background:${state.activePartsTab === 'feedback' ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' : 'transparent'}; color:white;">
                💬 Customer Feedback
            </button>
            <button 
                onclick="switchPartsTab('workdone')" 
                class="parts-tab-btn ${state.activePartsTab === 'workdone' ? 'active' : ''}"
                style="flex:1; min-width:180px; padding:1.2rem 2rem; border-radius:1rem; font-size:1.8rem; font-weight:bold; cursor:pointer; transition:all 0.3s ease; border:2px solid ${state.activePartsTab === 'workdone' ? 'rgba(59, 130, 246, 0.5)' : 'transparent'}; background:${state.activePartsTab === 'workdone' ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' : 'transparent'}; color:white;">
                ✅ Work Done
            </button>
        </div>
        
        <!-- Tab Content -->
        <div id="parts-tab-content">
            ${renderPartsTabContent()}
        </div>
    `;

        if (state.activePartsTab === 'request') {
            attachPartsRequestListeners();
        } else if (state.activePartsTab === 'feedback') {
            attachFeedbackListeners();
        } else if (state.activePartsTab === 'workdone') {
            attachWorkDoneListeners();
        }

        if (state.activePartsTab === 'request' && (state.collapseOpen || state.signatureData)) {
            initSignaturePad();
        }
    }

    function renderPartsTabContent() {
        switch (state.activePartsTab) {
            case 'request':
                return renderPartsRequestTab();
            case 'feedback':
                return renderCustomerFeedbackTab();
            case 'workdone':
                return renderWorkDoneTab();
            default:
                return '';
        }
    }

    function renderPartsRequestTab() {
        const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);
        const shouldShowCollapse = state.collapseOpen || !!state.signatureData;

        return `
        <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); border-radius:1rem; margin-bottom:2rem; border:2px solid rgba(59, 130, 246, 0.2); overflow:hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);">
            <button 
                id="collapse-toggle" 
                onclick="toggleCollapse()"
                style="width:100%; padding:1.5rem 2rem; background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); border:none; color:white; font-size:1.8rem; font-weight:bold; cursor:pointer; display:flex; justify-content:space-between; align-items:center; transition:all 0.3s ease;">
                <span>📋 Add Tech Notes / List Of Defects</span>
                <i id="collapse-icon" data-lucide="chevron-down" style="width:24px; height:24px; transition:transform 0.3s;" aria-hidden="true"></i>
            </button>
            
            <div id="collapse-content" style="display:${shouldShowCollapse ? 'block' : 'none'}; padding:2rem;">
                <div style="margin-bottom:2rem;">
                    <label for="tech-notes-textarea" style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">
                        <span>Tech Notes</span>
                        <div style="display:flex; gap:0.5rem;">
                            <span id="tech-notes-voice-indicator" class="voice-indicator" aria-hidden="true"></span>
                            <button id="tech-notes-voice-start" type="button" style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem;"><i data-lucide="mic"></i>  </button>
                            <button id="tech-notes-voice-stop" type="button" disabled style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem; opacity:0.6;"><i data-lucide="mic-off"></i>  </button>
                        </div>
                    </label>
                    <textarea 
                        id="tech-notes-textarea" 
                        rows="4" 
                        placeholder="Enter any technical notes or observations..."
                        style="width:100%; padding:1rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical;"
                    >${sanitizeHTML(state.techNotes)}</textarea>
                </div>
                
                <div>
                    <label for="defects-textarea" style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">
                        <span>List of Defects</span>
                        <div style="display:flex; gap:0.5rem;">
                            <span id="defects-voice-indicator" class="voice-indicator" aria-hidden="true"></span>
                            <button id="defects-voice-start" type="button" style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem;"><i data-lucide="mic"></i>  </button>
                            <button id="defects-voice-stop" type="button" disabled style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem; opacity:0.6;"><i data-lucide="mic-off"></i>  </button>
                        </div>
                    </label>
                    <textarea 
                        id="defects-textarea" 
                        rows="4" 
                        placeholder="List any defects found during inspection..."
                        style="width:100%; padding:1rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical;"
                    >${sanitizeHTML(state.defectList)}</textarea>
                </div>

                <!-- Technician Dropdown -->
                <div style="margin-top:2rem;">
                    <label for="technician-dropdown" style="display:block; margin-bottom:0.5rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">Select Technician</label>
                    <select 
                        id="technician-dropdown" 
                        style="width:100%; padding:1rem; font-size:1.8rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; cursor:pointer; appearance:none; -webkit-appearance:none; -moz-appearance:none; background-image:url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2724%27 height=%2724%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%2306b6d4%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3e%3cpolyline points=%276 9 12 15 18 9%27/%3e%3c/svg%3e'); background-repeat:no-repeat; background-position:right 1rem center; background-size:20px; padding-right:3rem;">
                        <option value="" style="background:#1e293b; color:#94a3b8;">-- Select Technician --</option>
                        ${state.technicians.map(tech => `<option value="${sanitizeHTML(tech)}" ${state.selectedTechnician === tech ? 'selected' : ''} style="background:#1e293b; color:white; padding:1rem;">${sanitizeHTML(tech)}</option>`).join('')}
                    </select>
                </div>

                <!-- Signature Pad -->
                <div style="margin-top:2rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <label style="font-size:1.8rem; font-weight:bold; color:#06b6d4;">Technician Signature</label>
                        <button 
                            onclick="clearSignaturePad()" 
                            style="background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; padding:0.5rem 1rem; border-radius:0.5rem; border:2px solid rgba(220, 38, 38, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease;">
                            Clear Signature
                        </button>
                    </div>
                    <canvas 
                        id="signature-canvas"
                        style="display:block; width:100%; height:200px; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); touch-action:none; cursor:crosshair; background:#ffffff;">
                    </canvas>
                    <p style="font-size:1.3rem; color:#94a3b8; margin-top:0.5rem;">Sign above using your mouse or touch screen</p>
                </div>
            </div>
        </div>
        
        <!-- Requested Parts Section -->
        <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); border-radius:1rem; margin-bottom:2rem; border:2px solid rgba(59, 130, 246, 0.2); overflow:hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3); padding:2rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                <h3 style="font-size:2rem; color:#06b6d4; display:flex; align-items:center; gap:0.5rem;">
                    <span>📦</span> Requested Parts
                </h3>
                <button 
                    onclick="openPartsModal()"
                    style="background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3); display:flex; align-items:center; gap:0.5rem;">
                    Add Parts
                </button>
            </div>
            ${state.cart.length > 0 ? `
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius:0.8rem; padding:1.5rem;">
                    ${state.cart.map((item, i) => `
                        <div style="padding:1rem; border-bottom:${i < state.cart.length - 1 ? '1px solid rgba(59, 130, 246, 0.2)' : 'none'}; display:flex; justify-content:space-between; align-items:center; font-size:1.6rem;">
                            <div style="flex:1;">
                                <div style="font-weight:bold; color:#06b6d4; margin-bottom:0.3rem;">${i + 1}. ${sanitizeHTML(item.name)}</div>
                            </div>
                            <div style="color:#facc15; font-weight:bold; font-size:1.8rem;">
                                Qty: ${item.quantity}
                            </div>
                        </div>
                    `).join('')}
                    <div style="margin-top:1rem; padding-top:1rem; border-top:2px solid rgba(59, 130, 246, 0.3); display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.8rem; font-weight:bold; color:#06b6d4;">Total Items:</span>
                        <span style="font-size:2rem; font-weight:bold; color:#facc15;">${state.cart.length}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.8rem; font-weight:bold; color:#06b6d4;">Total Quantity:</span>
                        <span style="font-size:2rem; font-weight:bold; color:#facc15;">${totalQuantity.toFixed(2)}</span>
                    </div>
                </div>
            ` : `
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); border-radius:0.8rem; padding:2rem; text-align:center;">
                    <p style="color:#94a3b8; font-size:1.6rem;">No parts added yet. Click "Add Parts" to add parts to your request.</p>
                </div>
            `}
        </div>
        
        <!-- Clear and Save Details Buttons -->
        <div style="display:flex; gap:1rem; justify-content:flex-end; margin-bottom:2rem;">
            <button 
                onclick="clearPartsDetails()" 
                style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:1.2rem 2.5rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease;">
                Clear Details
            </button>
            <button 
                onclick="savePartsDetails()" 
                style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:1.2rem 2.5rem; border-radius:0.8rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);">
                Save Details
            </button>
        </div>
        `;
    }

    // Add these new functions after your existing functions

    function openPartsModal() {
        // Create modal overlay
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        modalOverlay.id = 'parts-modal-overlay';

        const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);

        modalOverlay.innerHTML = `
        <div class="modal-container">
            <div class="modal-header">
                <h2 class="modal-title">Add Parts to Request</h2>
                <button class="modal-close-btn" onclick="closePartsModal()" aria-label="Close modal">
                    ✕
                </button>
            </div>
            <div class="modal-body">
                <div style="position:relative; max-width:600px; margin:0 auto 2rem;">
                    <input 
                        type="text" 
                        id="modal-parts-search" 
                        class="search-input" 
                        placeholder="Search parts by name..." 
                        value="${sanitizeHTML(state.partsSearchQuery)}" 
                        style="font-size:1.8rem; padding:1.2rem 1.2rem 1.2rem 4rem; width:100%;">
                    <span style="position:absolute; left:1.2rem; top:1.4rem; color:#94a3b8; font-size:1.8rem;">🔍</span>
                </div>
                
                <div id="modal-parts-results">
                    ${state.partsSearchQuery ? renderModalPartsSearchResults() : renderModalCategoryGrid()}
                </div>
            </div>
            <div class="modal-cart-summary">
                <div class="modal-cart-info">
                    Items in Cart: <span class="modal-cart-count">${state.cart.length}</span>
                    <span style="margin-left:2rem;">Total Quantity: <span class="modal-cart-count">${totalQuantity.toFixed(2)}</span></span>
                </div>
                <button 
                    onclick="closePartsModal()"
                    style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem; transition:all 0.3s ease;">
                    Done
                </button>
            </div>
        </div>
    `;

        document.body.appendChild(modalOverlay);

        // Trigger animation
        setTimeout(() => {
            modalOverlay.classList.add('active');
        }, 10);

        // Attach search listener
        const modalSearchInput = document.getElementById('modal-parts-search');
        if (modalSearchInput) {
            const debouncedSearch = debounce((value) => {
                state.partsSearchQuery = value.trim();
                updateModalPartsResults();
            }, 300);

            modalSearchInput.oninput = (e) => {
                debouncedSearch(e.target.value);
            };

            modalSearchInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    state.partsSearchQuery = e.target.value.trim();
                    updateModalPartsResults();
                }
            };

            modalSearchInput.focus();
        }

        // Close on overlay click
        modalOverlay.onclick = (e) => {
            if (e.target === modalOverlay) {
                closePartsModal();
            }
        };

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        lucide.createIcons();
    }

    function closePartsModal() {
        const modalOverlay = document.getElementById('parts-modal-overlay');
        if (modalOverlay) {
            modalOverlay.classList.remove('active');
            setTimeout(() => {
                modalOverlay.remove();
                document.body.style.overflow = '';
            }, 300);
        }

        // Update the main view to show updated cart
        renderRequestParts();
    }

    function updateModalPartsResults() {
        const resultsContainer = document.getElementById('modal-parts-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = state.partsSearchQuery ? 
                renderModalPartsSearchResults() : 
                renderModalCategoryGrid();
            lucide.createIcons();
        }
    }

    function updateModalCartSummary() {
        const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);
        const cartCounts = document.querySelectorAll('.modal-cart-count');
        if (cartCounts.length >= 2) {
            cartCounts[0].textContent = state.cart.length;
            cartCounts[1].textContent = totalQuantity.toFixed(2);
        }
    }

    function renderModalCategoryGrid() {
        return `
        <div class="category-grid">
            ${state.categories.map(c => {
                const categoryParts = state.parts.filter(p => categorize(p) === c.id);
                const uniqueNames = new Set(categoryParts.map(p => p.name));
                return `
                    <button onclick="selectModalCategory('${c.id}')" class="category-card ${c.color}" aria-label="View ${sanitizeHTML(c.name)} category">
                        <span class="category-icon">${c.icon}</span>
                        <span class="category-name">${sanitizeHTML(c.name)}</span>
                        <span style="font-size:1.6rem; color:#94a3b8;">
                            ${uniqueNames.size} Items
                        </span>
                    </button>
                `;
            }).join('')}
        </div>
    `;
    }

    function renderModalPartsSearchResults() {
        if (!state.partsSearchQuery) return '';

        const searchTerm = state.partsSearchQuery.toLowerCase();
        const matchedParts = state.parts.filter(p => 
            p.name.toLowerCase().includes(searchTerm) ||
            (p.category && p.category.toLowerCase().includes(searchTerm)) ||
            (p.partNo && p.partNo.toLowerCase().includes(searchTerm))
                                               );

        const uniquePartsMap = new Map();
        matchedParts.forEach(part => {
            const normalizedName = part.name.trim().toLowerCase();
        if (!uniquePartsMap.has(normalizedName)) {
            uniquePartsMap.set(normalizedName, part);
        }
    });

    const uniqueMatchedParts = Array.from(uniquePartsMap.values());

    if (uniqueMatchedParts.length === 0) {
        return `
            <div style="text-align:center; padding:3rem;">
                <p style="font-size:2rem; color:#94a3b8;">No parts found matching "${sanitizeHTML(state.partsSearchQuery)}"</p>
                <button onclick="clearModalPartsSearch()" style="margin-top:1rem; background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(220, 38, 38, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem;">Clear Search</button>
            </div>
        `;
    }

    return `
        <div style="margin-bottom:2rem; display:flex; justify-content:space-between; align-items:center;">
            <h3 style="font-size:2rem; color:#06b6d4;">Found ${uniqueMatchedParts.length} part(s) matching "${sanitizeHTML(state.partsSearchQuery)}"</h3>
            <button onclick="clearModalPartsSearch()" style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.8rem 1.5rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem;">Clear Search</button>
        </div>
        <div class="category-grid">${renderModalParts(uniqueMatchedParts)}</div>
        `;
    }

    function renderModalCategoryParts(categoryId) {
        const filtered = state.parts.filter(p => categorize(p) === categoryId);
    
        const uniquePartsMap = new Map();
        filtered.forEach(part => {
            if (!uniquePartsMap.has(part.name)) {
                uniquePartsMap.set(part.name, part);
            }
        });
    
        const uniqueParts = Array.from(uniquePartsMap.values());
        const category = state.categories.find(c => c.id === categoryId);
    
        return `
            <div style="margin-bottom:2rem;">
                <button 
                    onclick="backToModalCategories()" 
                    style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.8rem 1.5rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem; display:flex; align-items:center; gap:0.5rem;">
                    <i data-lucide="arrow-left" style="width:18px; height:18px;"></i>
                    Back to Categories
                </button>
            </div>
            <h3 style="font-size:2.5rem; margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                ${category ? category.icon : '📦'} ${category ? sanitizeHTML(category.name) : 'Parts'}
            </h3>
            <div class="category-grid">${renderModalParts(uniqueParts)}</div>
        `;
    }
    
    function renderModalParts(arr) {
        return arr.map((p, index) => `
            <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1.5rem; display:flex; flex-direction:column; justify-content:space-between; gap:1.5rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2); transition:all 0.3s ease; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);" onmouseover="this.style.transform='translateY(-5px)'; this.style.borderColor='rgba(59, 130, 246, 0.5)'; this.style.boxShadow='0 15px 30px rgba(59, 130, 246, 0.3)';" onmouseout="this.style.transform=''; this.style.borderColor='rgba(59, 130, 246, 0.2)'; this.style.boxShadow='0 10px 20px rgba(0, 0, 0, 0.3)';">
                <div>
                    <h3 style="font-size:2rem; color:#06b6d4;">${sanitizeHTML(p.name)}</h3>
                    <p style="color:#94a3b8; margin-top:0.5rem">Category: ${sanitizeHTML(p.category || 'N/A')}</p>
                </div>
                <div style="display:flex; flex-direction:column; gap:1rem; align-items:center;">
                    <div style="width:100%;">
                        <label for="modal-qty-${index}" style="display:block; color:#94a3b8; font-size:1.4rem; margin-bottom:0.5rem;">Quantity</label>
                        <input 
                            type="number" 
                            id="modal-qty-${index}" 
                            min="0" 
                            step="0.01" 
                            value="1" 
                            placeholder="0.00"
                            aria-label="Quantity for ${sanitizeHTML(p.name)}"
                            style="width:100%; padding:0.8rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; text-align:center;"
                        >
                    </div>
                    <button onclick="addToCartFromModal('${p.name.replace(/'/g, "\\'")}', 'modal-qty-${index}')" class="add-btn-circular" aria-label="Add ${sanitizeHTML(p.name)} to cart">+</button>
                </div>
            </div>
        `).join('');
    }


    function renderCustomerFeedbackTab() {
        return `
        <div style="max-width:900px; margin:0 auto;">
            <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); padding:3rem; border-radius:2rem; border:2px solid rgba(59, 130, 246, 0.3); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                <h3 style="font-size:2.5rem; margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Customer Feedback</h3>
                
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); padding:2rem; border-radius:1rem; margin-bottom:2rem; border:2px solid rgba(59, 130, 246, 0.2);">
                    <p style="font-size:1.6rem; color:#94a3b8; margin-bottom:1rem;">
                        <strong style="color:#facc15;">JobCard Reference:</strong> ${sanitizeHTML(state.activeReg)}
                    </p>
                </div>
                
                <!-- Response Section -->
                <div style="margin-bottom:2rem;">
                    <label for="customer-response-textarea" style="display:block; margin-bottom:1rem; font-size:2rem; font-weight:bold; color:#06b6d4;">
                        📝 Response
                    </label>
                    <textarea 
                        id="customer-response-textarea" 
                        rows="6" 
                        placeholder="Enter customer's response or feedback regarding the service..."
                        style="width:100%; padding:1.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical; line-height:1.6;"
                    >${sanitizeHTML(state.customerResponse)}</textarea>
                    <p style="font-size:1.3rem; color:#94a3b8; margin-top:0.5rem;">Document any customer concerns, requests, or approvals here.</p>
                </div>
                
                <!-- Approved Parts Section -->
                <div style="margin-bottom:2rem;">
                    <label for="approved-parts-textarea" style="display:block; margin-bottom:1rem; font-size:2rem; font-weight:bold; color:#06b6d4;">
                        ✅ Approved Parts
                    </label>
                    <textarea 
                        id="approved-parts-textarea" 
                        rows="6" 
                        placeholder="List the parts approved by the customer for installation/replacement..."
                        style="width:100%; padding:1.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical; line-height:1.6;"
                    >${sanitizeHTML(state.approvedParts)}</textarea>
                    <p style="font-size:1.3rem; color:#94a3b8; margin-top:0.5rem;">Enter each approved part on a new line or separate with commas.</p>
                </div>
            </div>
        </div>
        `;
    }

    function renderWorkDoneTab() {
        const service = state.activeServices.find(s => s.jobcardref === state.activeReg);
        
        if (!service) {
            return `
            <div style="text-align:center; padding:3rem;">
                <p style="font-size:2rem; color:#94a3b8;">Service information not found for ${sanitizeHTML(state.activeReg)}</p>
            </div>
            `;
        }

        return `
        <div style="max-width:900px; margin:0 auto;">
            <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); padding:3rem; border-radius:2rem; border:2px solid rgba(59, 130, 246, 0.3); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
                <h3 style="font-size:2.5rem; margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Work Done Report</h3>
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); padding:2rem; border-radius:1rem; margin-bottom:2rem; border:2px solid rgba(59, 130, 246, 0.2);">
                    <p style="font-size:1.6rem; color:#94a3b8; margin-bottom:0.8rem;">
                        <strong style="color:#facc15;">JobCard Reference:</strong> ${sanitizeHTML(service.jobcardref)}
                    </p>
                    <p style="font-size:1.6rem; color:#94a3b8; margin-bottom:0.8rem;">
                        <strong style="color:#06b6d4;">Technician:</strong> ${sanitizeHTML(service.tech)}
                    </p>
                    <p style="font-size:1.6rem; color:#94a3b8;">
                        <strong style="color:#06b6d4;">Instruction:</strong> ${sanitizeHTML(service.instruction)}
                    </p>
                </div>
                <div style="margin-bottom:2rem;">
                <label for="workdone-textarea" style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; font-size:2rem; font-weight:bold; color:#06b6d4;">
                    <span>📋 Work Completed Description</span>
                    <div style="display:flex; gap:0.5rem;">
                        <span id="workdone-voice-indicator" class="voice-indicator" aria-hidden="true"></span>
                        <button id="workdone-voice-start" type="button" style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem;"><i data-lucide="mic"></i></i>Start</button>
                        <button id="workdone-voice-stop" type="button" disabled style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.4rem 0.8rem; border-radius:0.5rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:2.2rem; opacity:0.6;"><i data-lucide="mic-off"></i>Stop Voice</button>
                    </div>
                </label>
                <textarea 
                    id="workdone-textarea" 
                    rows="8" 
                    placeholder="Enter detailed description of all work performed on this vehicle..."
                    style="width:100%; padding:1.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical; line-height:1.6;"
                >${sanitizeHTML(service.workDone || '')}</textarea>
                <p style="font-size:1.3rem; color:#94a3b8; margin-top:0.5rem;">Include all repairs, replacements, adjustments, and services performed.</p>
            </div>

            <div style="display:flex; gap:1rem; justify-content:flex-end; margin-top:3rem;">
                <button 
                    onclick="saveWorkDoneFromTab()" 
                    style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:1.2rem 2.5rem; border-radius:0.8rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease; box-shadow: 0 4px 15px rgba(34, 197, 94, 0.3);">
                    <i data-lucide="save" style="width:20px; height:20px; display:inline-block; vertical-align:middle; margin-right:0.5rem;" aria-hidden="true"></i>
                    Save Work Done
                </button>
            </div>
        </div>
    </div>
    `;
    }

    function attachPartsRequestListeners() {
        const techNotesTextarea = document.getElementById('tech-notes-textarea');
        const defectsTextarea = document.getElementById('defects-textarea');
        const technicianDropdown = document.getElementById('technician-dropdown');
        const techNotesVoiceStart = document.getElementById('tech-notes-voice-start');
        const techNotesVoiceStop = document.getElementById('tech-notes-voice-stop');
        const techNotesVoiceIndicator = document.getElementById('tech-notes-voice-indicator');
        const defectsVoiceStart = document.getElementById('defects-voice-start');
        const defectsVoiceStop = document.getElementById('defects-voice-stop');
        const defectsVoiceIndicator = document.getElementById('defects-voice-indicator');

        if (techNotesTextarea) {
            techNotesTextarea.oninput = (e) => {
                state.techNotes = e.target.value;
            };
        }

        if (defectsTextarea) {
            defectsTextarea.oninput = (e) => {
                state.defectList = e.target.value;
            };
        }

        if (technicianDropdown) {
            technicianDropdown.onchange = (e) => {
                state.selectedTechnician = e.target.value;
            };
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const supportsSpeech = !!SpeechRecognition;

        function bindSpeechToTextarea(textarea, startBtn, stopBtn, indicator, onText) {
            if (!textarea || !startBtn || !stopBtn) return;
            if (!supportsSpeech) {
                startBtn.disabled = true;
                stopBtn.disabled = true;
                startBtn.textContent = 'Voice Unsupported';
                return;
            }

            let recognition = null;
            let isListening = false;
            let indicatorTimeout = null;
            let lastFinalTranscript = '';
            let pendingLine = '';
            let pendingTimer = null;
            const PAUSE_MS = 800;

            const setButtons = (listening) => {
                isListening = listening;
                startBtn.disabled = listening;
                stopBtn.disabled = !listening;
                stopBtn.style.opacity = listening ? '1' : '0.6';
                stopBtn.style.color = listening ? '#ef4444' : 'white';
            };

            const showIndicator = () => {
                if (!indicator) return;
                indicator.classList.add('voice-indicator--active');
                if (indicatorTimeout) clearTimeout(indicatorTimeout);
                indicatorTimeout = setTimeout(() => {
                    indicator.classList.remove('voice-indicator--active');
                }, 1200);
            };

            const flushPendingLine = () => {
                if (!pendingLine.trim()) return;
                const needsNewLine = textarea.value && !textarea.value.endsWith('\n');
                textarea.value += (needsNewLine ? '\n' : '') + pendingLine.trim();
                textarea.scrollTop = textarea.scrollHeight;
                if (onText) onText(textarea.value);
                pendingLine = '';
            };

            const startListening = () => {
                if (isListening) return;
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    lastFinalTranscript = '';
                    pendingLine = '';
                    if (pendingTimer) {
                        clearTimeout(pendingTimer);
                        pendingTimer = null;
                    }
                };

                recognition.onresult = (event) => {
                    let transcript = '';
                    let hasSpeech = false;
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        const chunk = event.results[i][0].transcript || '';
                        if (chunk.trim()) hasSpeech = true;
                        if (event.results[i].isFinal) {
                            const finalChunk = event.results[i][0].transcript || '';
                            if (finalChunk) {
                                if (finalChunk.startsWith(lastFinalTranscript)) {
                                    transcript += finalChunk.slice(lastFinalTranscript.length);
                                } else {
                                    transcript += finalChunk;
                                }
                                lastFinalTranscript = finalChunk;
                            }
                        }
                    }
                    if (hasSpeech) {
                        showIndicator();
                    }
                    if (transcript) {
                        const cleaned = transcript.trim();
                        if (cleaned) {
                            pendingLine = pendingLine ? `${pendingLine} ${cleaned}` : cleaned;
                            if (pendingTimer) clearTimeout(pendingTimer);
                            pendingTimer = setTimeout(() => {
                                flushPendingLine();
                                pendingTimer = null;
                            }, PAUSE_MS);
                        }
                    }
                };

                recognition.onend = () => {
                    setButtons(false);
                    if (indicatorTimeout) clearTimeout(indicatorTimeout);
                    if (indicator) indicator.classList.remove('voice-indicator--active');
                    lastFinalTranscript = '';
                    if (pendingTimer) {
                        clearTimeout(pendingTimer);
                        pendingTimer = null;
                    }
                    flushPendingLine();
                };

                recognition.onerror = () => {
                    setButtons(false);
                    if (indicatorTimeout) clearTimeout(indicatorTimeout);
                    if (indicator) indicator.classList.remove('voice-indicator--active');
                    lastFinalTranscript = '';
                    if (pendingTimer) {
                        clearTimeout(pendingTimer);
                        pendingTimer = null;
                    }
                    flushPendingLine();
                };

                recognition.start();
                setButtons(true);
            };

            const stopListening = () => {
                if (!recognition) return;
                recognition.stop();
                setButtons(false);
            };

            startBtn.onclick = startListening;
            stopBtn.onclick = stopListening;
        }

        bindSpeechToTextarea(
            techNotesTextarea,
            techNotesVoiceStart,
            techNotesVoiceStop,
            techNotesVoiceIndicator,
            (value) => { state.techNotes = value; }
        );

        bindSpeechToTextarea(
            defectsTextarea,
            defectsVoiceStart,
            defectsVoiceStop,
            defectsVoiceIndicator,
            (value) => { state.defectList = value; }
        );

        console.log('Scheduling signature pad initialization...');
        if (state.collapseOpen || state.signatureData) {
            initSignaturePad();
        }

        const partsInput = document.getElementById('parts-search');
        if (partsInput) {
            const debouncedSearch = debounce((value) => {
                state.partsSearchQuery = value.trim();
                renderRequestParts();
            }, 300);

            partsInput.oninput = (e) => {
                debouncedSearch(e.target.value);
            };

            partsInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    state.partsSearchQuery = e.target.value.trim();
                    renderRequestParts();
                }
            };

            partsInput.onclick = (e) => e.target.focus();
        }
    }

    function attachFeedbackListeners() {
        const responseTextarea = document.getElementById('customer-response-textarea');
        const approvedPartsTextarea = document.getElementById('approved-parts-textarea');

        if (responseTextarea) {
            responseTextarea.oninput = (e) => {
                state.customerResponse = e.target.value;
            };
        }

        if (approvedPartsTextarea) {
            approvedPartsTextarea.oninput = (e) => {
                state.approvedParts = e.target.value;
            };
        }

        lucide.createIcons();
    }

    function attachWorkDoneListeners() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const supportsSpeech = !!SpeechRecognition;

        function bindSpeechToTextarea(textarea, startBtn, stopBtn, indicator, onText) {
            if (!textarea || !startBtn || !stopBtn) return;
            if (!supportsSpeech) {
                startBtn.disabled = true;
                stopBtn.disabled = true;
                startBtn.textContent = 'Voice Unsupported';
                return;
            }

            let recognition = null;
            let isListening = false;
            let indicatorTimeout = null;
            let lastFinalTranscript = '';
            let pendingLine = '';
            let pendingTimer = null;
            const PAUSE_MS = 800;

            const setButtons = (listening) => {
                isListening = listening;
                startBtn.disabled = listening;
                stopBtn.disabled = !listening;
                stopBtn.style.opacity = listening ? '1' : '0.6';
                stopBtn.style.color = listening ? '#ef4444' : 'white';
            };

            const showIndicator = () => {
                if (!indicator) return;
                indicator.classList.add('voice-indicator--active');
                if (indicatorTimeout) clearTimeout(indicatorTimeout);
                indicatorTimeout = setTimeout(() => {
                    indicator.classList.remove('voice-indicator--active');
                }, 1200);
            };

            const flushPendingLine = () => {
                if (!pendingLine.trim()) return;
                const needsNewLine = textarea.value && !textarea.value.endsWith('\n');
                textarea.value += (needsNewLine ? '\n' : '') + pendingLine.trim();
                textarea.scrollTop = textarea.scrollHeight;
                if (onText) onText(textarea.value);
                pendingLine = '';
            };

            const startListening = () => {
                if (isListening) return;
                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    lastFinalTranscript = '';
                    pendingLine = '';
                    if (pendingTimer) {
                        clearTimeout(pendingTimer);
                        pendingTimer = null;
                    }
                };

                recognition.onresult = (event) => {
                    let transcript = '';
                    let hasSpeech = false;
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        const chunk = event.results[i][0].transcript || '';
                        if (chunk.trim()) hasSpeech = true;
                        if (event.results[i].isFinal) {
                            const finalChunk = event.results[i][0].transcript || '';
                            if (finalChunk) {
                                if (finalChunk.startsWith(lastFinalTranscript)) {
                                    transcript += finalChunk.slice(lastFinalTranscript.length);
                                } else {
                                    transcript += finalChunk;
                                }
                                lastFinalTranscript = finalChunk;
                            }
                        }
                    }
                    if (hasSpeech) {
                        showIndicator();
                    }
                    if (transcript) {
                        const cleaned = transcript.trim();
                        if (cleaned) {
                            pendingLine = pendingLine ? `${pendingLine} ${cleaned}` : cleaned;
                            if (pendingTimer) clearTimeout(pendingTimer);
                            pendingTimer = setTimeout(() => {
                                flushPendingLine();
                                pendingTimer = null;
                            }, PAUSE_MS);
                        }
                    }
                };

                recognition.onend = () => {
                    setButtons(false);
                    if (indicatorTimeout) clearTimeout(indicatorTimeout);
                    if (indicator) indicator.classList.remove('voice-indicator--active');
                    lastFinalTranscript = '';
                    if (pendingTimer) {
                        clearTimeout(pendingTimer);
                        pendingTimer = null;
                    }
                    flushPendingLine();
                };

                recognition.onerror = () => {
                    setButtons(false);
                    if (indicatorTimeout) clearTimeout(indicatorTimeout);
                    if (indicator) indicator.classList.remove('voice-indicator--active');
                    lastFinalTranscript = '';
                    if (pendingTimer) {
                        clearTimeout(pendingTimer);
                        pendingTimer = null;
                    }
                    flushPendingLine();
                };

                recognition.start();
                setButtons(true);
            };

            const stopListening = () => {
                if (!recognition) return;
                recognition.stop();
                setButtons(false);
            };

            startBtn.onclick = startListening;
            stopBtn.onclick = stopListening;
        }

        const workDoneTextarea = document.getElementById('work-done-textarea');
        const workDoneStart = document.getElementById('work-done-voice-start');
        const workDoneStop = document.getElementById('work-done-voice-stop');
        const workDoneIndicator = document.getElementById('work-done-voice-indicator');

        const workdoneTextarea = document.getElementById('workdone-textarea');
        const workdoneStart = document.getElementById('workdone-voice-start');
        const workdoneStop = document.getElementById('workdone-voice-stop');
        const workdoneIndicator = document.getElementById('workdone-voice-indicator');

        bindSpeechToTextarea(
            workDoneTextarea,
            workDoneStart,
            workDoneStop,
            workDoneIndicator,
            (value) => {
                const service = state.activeServices.find(s => s.jobcardref === state.currentWorkDoneReg);
                if (service) service.workDone = value;
            }
        );

        bindSpeechToTextarea(
            workdoneTextarea,
            workdoneStart,
            workdoneStop,
            workdoneIndicator,
            (value) => {
                const service = state.activeServices.find(s => s.jobcardref === state.activeReg);
                if (service) service.workDone = value;
            }
        );

        lucide.createIcons();
    }

    function renderCategory() {
        const filtered = state.parts.filter(p => categorize(p) === state.selectedCategory.id);

        const uniquePartsMap = new Map();
        filtered.forEach(part => {
            if (!uniquePartsMap.has(part.name)) {
                uniquePartsMap.set(part.name, part);
            }
        });

        const uniqueParts = Array.from(uniquePartsMap.values());

        mainContent.innerHTML = `
    <h2 style="font-size:2.5rem; margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${state.selectedCategory.icon} ${sanitizeHTML(state.selectedCategory.name)}</h2>
    <div class="category-grid">${renderParts(uniqueParts)}</div>
`;
    }

    function renderCategoryGrid() {
        return `
    <div class="category-grid">
        ${state.categories.map(c => {
            const categoryParts = state.parts.filter(p => categorize(p) === c.id);
            const uniqueNames = new Set(categoryParts.map(p => p.name));
            return `
                <button onclick="selectCategory('${c.id}')" class="category-card ${c.color}" aria-label="View ${sanitizeHTML(c.name)} category">
                    <span class="category-icon">${c.icon}</span>
                    <span class="category-name">${sanitizeHTML(c.name)}</span>
                    <span style="font-size:1.6rem; color:#94a3b8;">
                        ${uniqueNames.size} Items
                    </span>
                </button>
            `;
        }).join('')}
    </div>
`;
    }

    function renderPartsSearchResults() {
        if (!state.partsSearchQuery) return '';

        const searchTerm = state.partsSearchQuery.toLowerCase();
        const matchedParts = state.parts.filter(p => 
            p.name.toLowerCase().includes(searchTerm) ||
            (p.category && p.category.toLowerCase().includes(searchTerm)) ||
            (p.partNo && p.partNo.toLowerCase().includes(searchTerm))
                                               );

        const uniquePartsMap = new Map();
        matchedParts.forEach(part => {
            const normalizedName = part.name.trim().toLowerCase();
            if (!uniquePartsMap.has(normalizedName)) {
                uniquePartsMap.set(normalizedName, part);
            }
        });

        const uniqueMatchedParts = Array.from(uniquePartsMap.values());

        if (uniqueMatchedParts.length === 0) {
            return `
        <div style="text-align:center; padding:3rem;">
            <p style="font-size:2rem; color:#94a3b8;">No parts found matching "${sanitizeHTML(state.partsSearchQuery)}"</p>
            <button onclick="clearPartsSearch()" style="margin-top:1rem; background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(220, 38, 38, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem;">Clear Search</button>
        </div>
    `;
        }

        return `
    <div style="margin-bottom:2rem; display:flex; justify-content:space-between; align-items:center;">
        <h3 style="font-size:2rem; color:#06b6d4;">Found ${uniqueMatchedParts.length} part(s) matching "${sanitizeHTML(state.partsSearchQuery)}"</h3>
        <button onclick="clearPartsSearch()" style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.8rem 1.5rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem;">Clear Search</button>
    </div>
    <div class="category-grid">${renderParts(uniqueMatchedParts)}</div>
`;
}

function renderSearch() {
    const resultCats = [...new Set(state.searchResults.map(p => categorize(p)))].filter(c => c !== 'other');
    const filtered = state.activeSearchFilter === 'all' ? 
        state.searchResults : 
        state.searchResults.filter(p => categorize(p) === state.activeSearchFilter);
        
    mainContent.innerHTML = `
        <h2 style="font-size:2.5rem; margin-bottom:1.5rem;">Results (${filtered.length})</h2>
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:2rem;">
            <button onclick="setSearchFilter('all')" style="padding:0.75rem 1.5rem; border-radius:2rem; border:none; cursor:pointer; font-weight:bold; font-size:1.5rem; ${state.activeSearchFilter === 'all' ? 'background:#dc2626; color:white;' : 'background:#334155; color:#94a3b8;'}">All</button>
            ${resultCats.map(cid => {
                const cat = state.categories.find(c => c.id === cid);
                return `<button onclick="setSearchFilter('${cid}')" style="padding:0.75rem 1.5rem; border-radius:2rem; border:none; cursor:pointer; font-weight:bold; font-size:1.5rem; ${state.activeSearchFilter === cid ? 'background:#dc2626; color:white;' : 'background:#334155; color:#94a3b8;'}">${sanitizeHTML(cat ? cat.name : cid)}</button>`;
            }).join('')}
        </div>
        <div class="category-grid">${renderParts(filtered)}</div>
    `;
}

function renderParts(arr) {
    return arr.map((p, index) => `
    <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1.5rem; display:flex; flex-direction:column; justify-content:space-between; gap:1.5rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2); transition:all 0.3s ease; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);" onmouseover="this.style.transform='translateY(-5px)'; this.style.borderColor='rgba(59, 130, 246, 0.5)'; this.style.boxShadow='0 15px 30px rgba(59, 130, 246, 0.3)';" onmouseout="this.style.transform=''; this.style.borderColor='rgba(59, 130, 246, 0.2)'; this.style.boxShadow='0 10px 20px rgba(0, 0, 0, 0.3)';">
        <div>
            <h3 style="font-size:2rem; color:#06b6d4;">${sanitizeHTML(p.name)}</h3>
            <p style="color:#94a3b8; margin-top:0.5rem">Category: ${sanitizeHTML(p.category || 'N/A')}</p>
        </div>
        <div style="display:flex; flex-direction:column; gap:1rem; align-items:center;">
            <div style="width:100%;">
                <label for="qty-${index}" style="display:block; color:#94a3b8; font-size:1.4rem; margin-bottom:0.5rem;">Quantity</label>
                <input 
                    type="number" 
                    id="qty-${index}" 
                    min="0" 
                    step="0.01" 
                    value="1" 
                    placeholder="0.00"
                    aria-label="Quantity for ${sanitizeHTML(p.name)}"
                    style="width:100%; padding:0.8rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; text-align:center;"
                >
            </div>
            <button onclick="addToCart('${p.name.replace(/'/g, "\\'")}', '${index}')" class="add-btn-circular" aria-label="Add ${sanitizeHTML(p.name)} to cart">+</button>
        </div>
    </div>`).join('');
}

function renderCheckout() {
    const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);

    mainContent.innerHTML = `
    <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); padding:3rem; border-radius:2rem; border:4px solid rgba(59, 130, 246, 0.5); max-width:800px; margin:2rem auto; box-shadow: 0 20px 60px rgba(59, 130, 246, 0.3);">
        <h2 style="text-align:center; margin-bottom:2rem; font-size:2.5rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Your Order</h2>
        <div style="margin-bottom:2rem;">
            ${state.cart.length === 0 ? '<p style="text-align:center; font-size:1.8rem;">Your cart is empty.</p>' : state.cart.map((item, i) => `
                <div style="padding:1rem; border-bottom:1px solid rgba(59, 130, 246, 0.2); display:flex; justify-content:space-between; align-items:center; font-size:1.8rem; gap:1rem;">
                    <div style="min-width:40px; font-size:2rem; font-weight:bold; color:#06b6d4;">${i + 1}.</div>
                    <div style="flex:1;">
                        <strong>${sanitizeHTML(item.name)}</strong><br>
                        <small style="color:#94a3b8;">${sanitizeHTML(item.category)}</small>
                    </div>
                    <div style="display:flex; align-items:center; gap:1rem;">
                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <span style="color:#94a3b8; font-size:1.2rem;">QTY</span>
                            <input 
                                type="number" 
                                id="cart-qty-${i}"
                                value="${item.quantity}" 
                                min="0.01"
                                step="0.01"
                                onchange="updateCartQuantity(${i}, this.value)"
                                aria-label="Quantity for ${sanitizeHTML(item.name)}"
                                style="width:80px; padding:0.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; text-align:center;"
                            >
                        </div>
                        <button onclick="removeFromCart(${i})" aria-label="Remove ${sanitizeHTML(item.name)} from cart" style="color:#ef4444; background:none; border:none; cursor:pointer; font-size:1.5rem;">
                            <i data-lucide="trash-2" aria-hidden="true"></i>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
        ${state.cart.length > 0 ? `
            <div style="text-align:center; padding:2rem 0;">
                <h3 style="font-size:2rem; margin-bottom:1rem; color:#06b6d4;">Total: ${totalItems.toFixed(2)} Units</h3>
                <p style="color:#94a3b8; font-size:1.6rem;">Return to Request Parts to confirm your order</p>
            </div>
        ` : ''}
    </div>`;
}

function renderSuccess() {
    const id = window.lastOrderID;
    const originalTitle = document.title;
    document.title = `Order_Ticket_${id}`;

    mainContent.innerHTML = `
        <div style="text-align:center; padding:4rem 2rem; background:linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%); backdrop-filter:blur(20px); border-radius:2rem; max-width:600px; margin:2rem auto; border:4px solid rgba(34, 197, 94, 0.5); box-shadow: 0 20px 60px rgba(34, 197, 94, 0.3);">
            <div style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); width:80px; height:80px; border-radius:50%; margin:0 auto 1.5rem; display:flex; align-items:center; justify-content:center; font-size:3rem; box-shadow: 0 10px 30px rgba(34, 197, 94, 0.5);">✓</div>
            <h2 style="font-size:2.5rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Order Confirmed</h2>
            <div style="font-size:4rem; color:#facc15; margin:1.5rem 0; border:2px dashed rgba(59, 130, 246, 0.3); padding:1rem; border-radius:1rem; display:inline-block;">#${id}</div>
            <div style="margin:2rem 0;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ORDER-${id}" alt="QR Code for order ${id}"></div>
            <div style="display:flex; flex-direction:column; gap:1rem;">
                <button id="print-ticket-btn" class="btn-print">🖨️ Print Ticket</button>
                <button onclick="goToHome()" style="background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; padding:1.2rem; border-radius:0.8rem; border:2px solid rgba(220, 38, 38, 0.3); font-weight:bold; cursor:pointer; font-size:2.4rem; transition:all 0.3s ease;">Finish</button>
            </div>
        </div>`;

    document.getElementById('print-ticket-btn').onclick = () => window.print();

    setTimeout(() => { 
        if (state.currentView === 'success') { 
            document.title = originalTitle; 
            goToHome(); 
        } 
    }, 20000);
}

function renderAdmin() {
    const totalItems = state.orderHistory.reduce((sum, order) => sum + order.itemCount, 0);
    
    mainContent.innerHTML = `
        <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                <h2 style="font-size:3rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Admin Dashboard</h2>
                <button onclick="goToHome()" style="background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; border:2px solid rgba(220, 38, 38, 0.3); padding:1rem 2rem; border-radius:1rem; cursor:pointer; font-weight:bold; font-size:2.4rem; transition:all 0.3s ease;">Exit Admin</button>
            </div>
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1.5rem; margin-bottom:2rem;">
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2);"><h4 style="color:#06b6d4; font-size:1.5rem;">Orders Today</h4><p style="font-size:2.5rem; font-weight:bold;">${state.orderHistory.length}</p></div>
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2);"><h4 style="color:#06b6d4; font-size:1.5rem;">Total Items</h4><p style="font-size:2.5rem; font-weight:bold;">${totalItems}</p></div>
                <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2);"><h4 style="color:#06b6d4; font-size:1.5rem;">Session Clock</h4><p style="font-size:2.5rem; font-weight:bold;">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</p></div>
            </div>
            <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); border-radius:1rem; overflow:hidden; border:2px solid rgba(59, 130, 246, 0.2);">
                <table style="width:100%; border-collapse:collapse; text-align:center;">
                    <thead style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);">
                        <tr style="font-size:2.4rem;"><th style="padding:1rem; font-size:2.4rem; text-align:center; color:#06b6d4;">Time</th><th style="padding:1rem; font-size:2.4rem; text-align:center; color:#06b6d4;">Order ID</th><th style="padding:1rem; font-size:2.4rem; text-align:center; color:#06b6d4;">Items</th></tr>
                    </thead>
                    <tbody>
                        ${state.orderHistory.map(o => `
                            <tr style="border-bottom:1px solid rgba(59, 130, 246, 0.2); font-size:2.4rem;">
                                <td data-label="Time" style="padding:1rem; text-align:center;">${o.time}</td>
                                <td data-label="ID" style="padding:1rem; text-align:center;">#${o.id}</td>
                                <td data-label="Counter" style="padding:1rem; text-align:center;">${o.itemCount} Units</td>
                            </tr>`).reverse().join('')}
                    </tbody>
                </table>
            </div>
            <button onclick="clearStats()" style="margin-top:2rem; background:none; border:2px solid #ef4444; color:#ef4444; padding:0.8rem 1.5rem; border-radius:0.8rem; cursor:pointer; font-weight:bold; font-size:2.4rem; transition:all 0.3s ease;">Clear Session Data</button>
        </div>`;
}

function updateBreadcrumbs() {
    if (state.currentView === 'home' || state.currentView === 'success' || state.currentView === 'workDone') { 
        breadcrumbContainer.classList.add('hidden'); 
        return; 
    }
    breadcrumbContainer.classList.remove('hidden');

    let breadcrumb = `<span onclick="goToHome()" style="cursor:pointer; color:#06b6d4; font-weight:bold;">Home</span>`;

    if (state.currentView === 'Request Parts') {
        breadcrumb += ` > Request Parts`;
    } else if (state.currentView === 'category' || state.currentView === 'checkout') {
        breadcrumb += ` > <span style="color:#06b6d4; font-weight:bold;">Request Parts</span>`;
    }

    if (state.currentView === 'category') {
        breadcrumb += ` > Category`;
    } else if (state.currentView === 'checkout') {
        breadcrumb += ` > Checkout`;
    } else if (state.currentView !== 'Request Parts' && state.currentView !== 'home') {
        breadcrumb += ` > ${state.currentView.charAt(0).toUpperCase() + state.currentView.slice(1)}`;
    }

    breadcrumbContainer.innerHTML = breadcrumb;
}

// ===========================
// EVENT HANDLERS
// ===========================

function goToHome() {
    state.currentView = 'home';
    state.serviceSearchQuery = '';
    state.currentStatusFilter = 'all';
    state.currentWorkDoneReg = null;
    state.activeReg = null;
    state.partsSearchQuery = '';
    state.techNotes = '';
    state.defectList = '';
    state.activePartsTab = 'request';
    state.customerResponse = '';
    state.approvedParts = '';
    state.cart = [];
    state.selectedTechnician = '';
    state.signatureData = '';
    
    clearNavigationHistory();
    
    cartCount.innerText = 0;
    cartCount.classList.add('hidden');
    
    render();
}

function setupListeners() {
    // Global window functions for onclick handlers
    window.selectCategory = (id) => { 
        pushNavigation('category', { 
            selectedCategory: state.categories.find(c => c.id === id) 
        });
    };

    window.switchPartsTab = (tabName) => {
        state.activePartsTab = tabName;
        renderRequestParts();
    };

    window.clearPartsDetails = async () => {
        const confirmed = await customConfirm(
            'Are you sure you want to clear Tech Notes, List of Defects, Requested Parts, Technician, and Signature?',
            'Clear All Details'
        );

        if (confirmed) {
            state.techNotes = '';
            state.defectList = '';
            state.cart = [];
            state.partsSearchQuery = '';
            state.selectedTechnician = '';
            state.signatureData = '';
            state.collapseOpen = false;
            
            const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);
            cartCount.innerText = Math.round(totalQuantity);
            cartCount.classList.toggle('hidden', state.cart.length === 0);
            
            renderRequestParts();
            await customAlert('All details have been cleared.', 'Cleared');
        }
    };

    window.savePartsDetails = async () => {
        // Validation
        const errors = [];
        
        if (state.cart.length === 0 && !state.techNotes.trim() && !state.defectList.trim()) {
            errors.push('No details to save. Please add tech notes,defects or parts first.');
        }
        
        if (!state.selectedTechnician) {
            errors.push('Please select a technician before saving.');
        }
        
        const signature = getSignatureData();
        console.log('Signature check:', { hasSignature: !!signature, signatureLength: signature ? signature.length : 0 });
        
        if (!signature || signature.length === 0) {
            errors.push('Please provide your signature before saving.');
        }
        
        if (errors.length > 0) {
            await customAlert(errors.join('\n'), 'Validation Error');
            return;
        }

        let partsAndQuantities = null;
        if (state.cart.length > 0) {
            partsAndQuantities = state.cart.map((item, i) => 
                `${i + 1}. ${item.name} (${item.category}) - Qty: ${item.quantity}`
            ).join('\n');
        }

        const techNotesValue = state.techNotes.trim() || null;
        const defectListValue = state.defectList.trim() || null;

        console.log('Saving parts details with:', {
            activeReg: state.activeReg,
            techNotes: techNotesValue,
            defectList: defectListValue,
            partsAndQuantities,
            technician: state.selectedTechnician,
            hasSignature: !!signature
        });

        try {
            await anvil.call(
                mainContent, 
                'storeTechDetails', 
                state.activeReg,
                techNotesValue, 
                defectListValue, 
                partsAndQuantities,
                state.selectedTechnician,
                signature
            );

            await customAlert(
                `Details have been saved successfully for JobCard ${state.activeReg}`,
                '✅ Success'
            );

            // Clear state
            state.activeReg = null;
            state.cart = [];
            state.techNotes = '';
            state.defectList = '';
            state.partsSearchQuery = '';
            state.customerResponse = '';
            state.approvedParts = '';
            state.selectedTechnician = '';
            state.signatureData = '';
            state.collapseOpen = false;
            
            // Update cart display
            cartCount.innerText = 0;
            cartCount.classList.add('hidden');
            
            // Reload active services to get updated data
            await loadActiveServices();
            
            // Clear navigation history and go home
            clearNavigationHistory();

            // Clear signature pad
            clearSignature();
            state.currentView = 'home';
            render();

        } catch (error) {
            console.error('Error saving parts details:', error);
            
            // Extract meaningful error message
            let errorMessage = 'Failed to save details. Please try again.';
            if (error && error.message) {
                errorMessage = error.message;
            } else if (error && error.args && error.args.length > 0) {
                errorMessage = error.args.join(' ');
            } else if (typeof error === 'string') {
                errorMessage = error;
            }
            
            await customAlert(
                errorMessage,
                '❌ Error'
            );
        }
    };

    window.saveWorkDoneFromTab = async () => {
        const textarea = document.getElementById('workdone-textarea');
        const workDoneText = textarea ? textarea.value.trim() : '';

        if (!workDoneText) {
            await customAlert('Please enter the work done details before saving.', 'Work Done Required');
            return;
        }

        try {
            await anvil.call(mainContent, 'save_work_done', state.activeReg, workDoneText);

            const service = state.activeServices.find(s => s.jobcardref === state.activeReg);
            if (service) {
                service.workDone = workDoneText;
                service.status = 'Completed';
            }

            await customAlert(
                `Work done has been saved successfully for JobCard ${state.activeReg}`,
                '✅ Success'
            );

        } catch (err) {
            console.error(err);
            await customAlert(
                'Failed to save work done. Please try again.',
                '❌ Error'
            );
        }
    };

    window.addToCart = (name, index) => {
        const qtyInput = document.getElementById(`qty-${index}`);
        const quantity = parseFloat(qtyInput?.value) || 1;

        if (quantity <= 0) {
            customAlert('Please enter a valid quantity greater than 0.', 'Invalid Quantity');
            return;
        }

        const item = state.parts.find(p => p.name === name);
        if (!item) return;

        const existingItemIndex = state.cart.findIndex(c => c.name === item.name);

        if (existingItemIndex > -1) {
            state.cart[existingItemIndex].quantity += quantity;
        } else {
            state.cart.push({
                name: item.name,
                category: item.category,
                partNo: item.partNo,
                quantity: quantity
            });
        }

        if (qtyInput) qtyInput.value = '1';

        render();
    };

    window.updateCartQuantity = (index, newQuantity) => {
        const qty = parseFloat(newQuantity);

        if (isNaN(qty) || qty <= 0) {
            customAlert('Please enter a valid quantity greater than 0.', 'Invalid Quantity');
            document.getElementById(`cart-qty-${index}`).value = state.cart[index].quantity;
            return;
        }

        state.cart[index].quantity = qty;
        render();
    };

    window.removeFromCart = (i) => { 
        state.cart.splice(i, 1); 
        render(); 
    };

    window.goToHome = goToHome;

    window.setSearchFilter = (f) => { 
        state.activeSearchFilter = f; 
        render(); 
    };

    window.clearStats = async () => {
        const confirmed = await customConfirm(
            'Are you sure you want to clear all session data? This cannot be undone.',
            'Clear Session Data'
        );
        if (confirmed) {
            state.orderHistory = [];
            renderAdmin();
        }
    };

    window.filterByStatus = (s) => { 
        state.currentStatusFilter = (state.currentStatusFilter === s) ? 'all' : s; 
        
        // Update button states
        const buttons = document.querySelectorAll('.btn-status');
        buttons.forEach(btn => {
            const btnText = btn.textContent.trim();
            if (btnText === s) {
                btn.classList.toggle('active-filter');
            } else {
                btn.classList.remove('active-filter');
            }
        });
        
        // Update the table
        updateServiceTable();
    };

    window.openParts = (reg) => { 
        if (state.activeReg !== reg) {
            state.cart = [];
            state.techNotes = '';
            state.defectList = '';
            state.partsSearchQuery = '';
            state.customerResponse = '';
            state.approvedParts = '';
            state.selectedTechnician = '';
            state.signatureData = '';
            
            cartCount.innerText = 0;
            cartCount.classList.add('hidden');
        }
        
        pushNavigation('Request Parts', { activeReg: reg, activePartsTab: 'request' });
    };

    window.openWorkDone = (reg) => {
        if (state.activeReg !== reg) {
            state.cart = [];
            state.techNotes = '';
            state.defectList = '';
            state.partsSearchQuery = '';
            state.customerResponse = '';
            state.approvedParts = '';
            state.selectedTechnician = '';
            state.signatureData = '';
            
            cartCount.innerText = 0;
            cartCount.classList.add('hidden');
        }
        
        pushNavigation('Request Parts', { activeReg: reg, activePartsTab: 'workdone' });
    };

    window.cancelWorkDone = () => {
        state.currentWorkDoneReg = null;
        state.currentView = 'home';
        render();
    };

    window.saveWorkDone = async () => {
        const textarea = document.getElementById('work-done-textarea');
        const workDoneText = textarea.value.trim();

        if (!workDoneText) {
            await customAlert('Please enter the work done details before saving.', 'Work Done Required');
            return;
        }

        try {
            await anvil.call(mainContent, 'save_work_done', state.currentWorkDoneReg, workDoneText);

            const service = state.activeServices.find(s => s.jobcardref === state.currentWorkDoneReg);
            if (service) {
                service.workDone = workDoneText;
                service.status = 'Completed';
            }

            await customAlert(
                `Work done has been saved successfully for jobcard reference ${state.currentWorkDoneReg}`,
                '✅ Success'
            );

            state.currentWorkDoneReg = null;
            
            // Reload active services to get updated data
            await loadActiveServices();
            
            clearNavigationHistory();
            state.currentView = 'home';
            render();

        } catch (err) {
            console.error(err);
            await customAlert(
                'Failed to save work done. Please try again.',
                '❌ Error'
            );
        }
    };

    window.clearPartsSearch = () => {
        state.partsSearchQuery = '';
        renderRequestParts();
    };

    window.clearSignaturePad = () => {
        clearSignature();
    };

    window.toggleCollapse = () => {
        const content = document.getElementById('collapse-content');
        const icon = document.getElementById('collapse-icon');
        const button = document.getElementById('collapse-toggle');

        if (content.style.display === 'none') {
            content.style.display = 'block';
            state.collapseOpen = true;
            button.style.background = 'linear-gradient(135deg, rgba(71, 85, 105, 0.8) 0%, rgba(51, 65, 85, 0.8) 100%)';
            if (icon) {
                icon.style.transform = 'rotate(180deg)';
            }
            initSignaturePad();
        } else {
            getSignatureData();
            content.style.display = 'none';
            state.collapseOpen = false;
            button.style.background = 'linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)';
            if (icon) {
                icon.style.transform = 'rotate(0deg)';
            }
        }

        lucide.createIcons();
    };

    // Button listeners
    backBtn.onclick = () => {
        popNavigation();
    };
    
    cartBtn.onclick = () => { 
        pushNavigation('checkout');
    };
    
    homeFooterBtn.onclick = goToHome;

    adminTrigger.onclick = () => {
        state.adminClicks++;
        clearTimeout(state.adminTimeout);
        if (state.adminClicks === 5) {
            state.adminClicks = 0;
            state.currentView = 'admin';
            render();
        } else {
            state.adminTimeout = setTimeout(() => { 
                state.adminClicks = 0; 
            }, 2000);
        }
    };

    window.onscroll = () => {
        backToTopBtn.className = window.scrollY > 300 ? 'visible-fade' : 'hidden-fade';
    };

    backToTopBtn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });

    window.addEventListener('resize', () => {
        if (signaturePadInstance) {
            signaturePadInstance.resize();
        }
    });

    window.openPartsModal = openPartsModal;
    window.closePartsModal = closePartsModal;

    window.selectModalCategory = (id) => {
        const resultsContainer = document.getElementById('modal-parts-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = renderModalCategoryParts(id);
            lucide.createIcons();
        }
    };

    window.backToModalCategories = () => {
        state.partsSearchQuery = '';
        const searchInput = document.getElementById('modal-parts-search');
        if (searchInput) searchInput.value = '';
        updateModalPartsResults();
    };

    window.clearModalPartsSearch = () => {
        state.partsSearchQuery = '';
        const searchInput = document.getElementById('modal-parts-search');
        if (searchInput) searchInput.value = '';
        updateModalPartsResults();
    };

    window.addToCartFromModal = (name, inputId) => {
        const qtyInput = document.getElementById(inputId);
        const quantity = parseFloat(qtyInput?.value) || 1;

        if (quantity <= 0) {
            customAlert('Please enter a valid quantity greater than 0.', 'Invalid Quantity');
            return;
        }

        const item = state.parts.find(p => p.name === name);
        if (!item) return;

        const existingItemIndex = state.cart.findIndex(c => c.name === item.name);

        if (existingItemIndex > -1) {
            state.cart[existingItemIndex].quantity += quantity;
        } else {
            state.cart.push({
                name: item.name,
                category: item.category,
                partNo: item.partNo,
                quantity: quantity
            });
        }

        if (qtyInput) qtyInput.value = '1';

        // Update cart count display
        const totalQuantity = state.cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.innerText = Math.round(totalQuantity);
        cartCount.classList.remove('hidden');

        // Update modal cart summary
        updateModalCartSummary();
    };
}

// ===========================
// INITIALIZATION
// ===========================

init();
})();