(() => {
    const mainContent = document.getElementById('main-content');
    const backBtn = document.getElementById('back-btn');
    const cartBtn = document.getElementById('cart-btn');
    const cartCount = document.getElementById('cart-count');
    const breadcrumbContainer = document.getElementById('breadcrumb-container');
    const backToTopBtn = document.getElementById('back-to-top');
    const homeFooterBtn = document.getElementById('home-footer-btn');
    const adminTrigger = document.getElementById('admin-trigger');

    // Custom Alert Function
    function customAlert(message, title = 'BMA Parts Express') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'custom-alert-overlay';

            overlay.innerHTML = `
                <div class="custom-alert-box">
                    <div class="custom-alert-title">
                        ${title}
                    </div>
                    <div class="custom-alert-message">${message}</div>
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

    // Custom Confirm Function
    function customConfirm(message, title = 'Confirm Action') {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'custom-alert-overlay';

            overlay.innerHTML = `
                <div class="custom-alert-box">
                    <div class="custom-alert-title">
                        ❓ ${title}
                    </div>
                    <div class="custom-alert-message">${message}</div>
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

    // State Management
    let parts = [], cart = [], currentView = 'home', selectedCategory = null;
    let searchResults = [], activeSearchFilter = 'all', orderHistory = [];
    let adminClicks = 0, adminTimeout;
    let activeReg = null, serviceSearchQuery = '', currentStatusFilter = 'all';
    let categories = [];
    let currentWorkDoneReg = null;
    let partsSearchQuery = '';
    let techNotes = ''; 
    let defectList = ''; 

    // Category display configuration (icons and colors)
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

    let activeServices = [];

    async function init() {
        try {
            const serverData = await anvil.call(mainContent, 'getCarPartNamesAndCategory');
            console.log("The server data is", serverData)
            if (!Array.isArray(serverData)) {
                throw new Error("Server did not return a list. Check server logs.");
            }

            parts = serverData.map(item => ({
                name: item.Name,
                category: item.Category,
                partNo: item.PartNo || item.Name
            }));

            const uniqueCategories = [...new Set(serverData.map(item => item.Category))];

            categories = uniqueCategories.map(catName => {
                const config = categoryConfig[catName] || { icon: '📦', color: 'bg-gray' };
                return {
                    id: catName.toLowerCase().replace(/\s+/g, '-'),
                    name: catName,
                    icon: config.icon,
                    color: config.color
                };
            });

            await loadActiveServices();

            setupListeners();
            render();

            setInterval(async () => { 
                if(currentView === 'home') {
                    await loadActiveServices();
                    render();
                }
            }, 60000);
        } catch (e) { 
            console.error("Initialization Error (raw):", e);
            if (e && e.args) {
                console.error("Python args:", e.args);
            }
        }
    }

    async function loadActiveServices() {
        try {
            const jobcardsData = await anvil.call(mainContent, 'get_technician_jobcards_by_status');

            activeServices = jobcardsData.map(card => ({
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

            console.log('Loaded active services:', activeServices.length);
        } catch (error) {
            console.error('Error loading active services:', error);
            activeServices = [];
        }
    }

    function categorize(p) {
        return p.category ? p.category.toLowerCase().replace(/\s+/g, '-') : 'other';
    }

    function render() {
        const showBackBtn = currentView === 'category' || 
            (currentView !== 'home' && currentView !== 'success' && 
             currentView !== 'admin' && currentView !== 'workDone' && 
             currentView !== 'Request Parts');

        backBtn.classList.toggle('hidden', !showBackBtn);

        const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.innerText = Math.round(totalQuantity);
        cartCount.classList.toggle('hidden', cart.length === 0 || currentView === 'success' || currentView === 'workDone');

        updateBreadcrumbs();

        if (currentView === 'home') renderHome();
        else if (currentView === 'Request Parts') renderRequestParts();
        else if (currentView === 'category') renderCategory();
        else if (currentView === 'search') renderSearch();
        else if (currentView === 'checkout') renderCheckout();
        else if (currentView === 'success') renderSuccess();
        else if (currentView === 'admin') renderAdmin();
        else if (currentView === 'workDone') renderWorkDone();

        window.scrollTo({ top: 0, behavior: 'instant' });
        lucide.createIcons();
    }

    function renderHome() {
        const isHistory = currentStatusFilter === 'Completed';
        const filtered = activeServices.filter(s => {
            const matchesStatus = currentStatusFilter === 'all' ? (s.status !== 'Completed') : (s.status === currentStatusFilter);
            const matchesSearch = s.jobcardref.toLowerCase().includes(serviceSearchQuery.toLowerCase()) || s.tech.toLowerCase().includes(serviceSearchQuery.toLowerCase());
            return matchesStatus && matchesSearch;
        });

        // Calculate statistics
        const totalServices = activeServices.length;
        const checkedInCount = activeServices.filter(s => s.status === 'Checked-In').length;
        const inServiceCount = activeServices.filter(s => s.status === 'In-Service').length;
        const completedCount = activeServices.filter(s => s.status === 'Completed').length;

        mainContent.innerHTML = `
        <!-- Hero Section -->
        <div class="hero-section">
            <h1 class="hero-title">Modern Garage System</h1>
            <p class="hero-subtitle">${isHistory ? 'Service History' : 'Service & Parts Management'}</p>
            
            <div class="status-badges">
                <span class="badge badge-premium">Premium UI</span>
                <span class="badge badge-fast">Fast Delivery</span>
                <span class="badge badge-service">Developing Service</span>
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
            
            <div class="service-card">
                <div class="service-icon" style="background: linear-gradient(135deg, #64748b 0%, #475569 100%);">✅</div>
                <div>
                    <div class="service-card-title">Completed</div>
                    <div class="service-card-subtitle">Finished today</div>
                    <div class="service-stat">${completedCount}</div>
                </div>
            </div>
        </div>
        
        <!-- Filter and Search -->
        <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:2rem; flex-wrap:wrap;">
            <div style="display:flex; gap:1rem;">
                <button class="btn-status ${currentStatusFilter === 'Checked-In' ? 'active-filter' : ''}" onclick="filterByStatus('Checked-In')">Checked-In</button>
                <button class="btn-status ${currentStatusFilter === 'In-Service' ? 'active-filter' : ''}" onclick="filterByStatus('In-Service')">In-Service</button>
                <button class="btn-status ${currentStatusFilter === 'Completed' ? 'active-filter' : ''}" onclick="filterByStatus('Completed')">History</button>
            </div>
            
            <div style="position:relative; flex:1; max-width:400px; min-width:300px;">
                <input type="text" id="service-search" class="search-input" placeholder="Search JobCard or Technician..." value="${serviceSearchQuery}" style="font-size:1.5rem; padding:1rem 1rem 1rem 3.5rem; width:100%;">
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
                            <td data-label="Received">${s.date}</td>
                            <td data-label="Technician"><strong>${s.tech}</strong></td>
                            <td data-label="JobCard Ref" style="color:#facc15; font-weight:bold;">${s.jobcardref}</td>
                            <td data-label="Instruction">${s.instruction}</td>
                            <td data-label="Status"><span class="status-badge ${s.status === 'In-Service' ? 'status-in-service' : s.status === 'Completed' ? 'status-completed' : 'status-checked-in'}">${s.status}</span></td>
                            <td data-label="Action">
                                ${s.status === 'Completed' ? '✅ Finished' : s.status === 'In-Service' ? `
                                    <button onclick="openWorkDone('${s.jobcardref}')" style="background:#3b82f6; border:none; color:white; padding:0.8rem 1.2rem; border-radius:0.5rem; cursor:pointer; font-weight:bold;">Work Done</button>
                                ` : `
                                    <button onclick="openParts('${s.jobcardref}')" class="btn-issue-parts">Request Parts</button>
                                `}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

        const sInput = document.getElementById('service-search');
        if(sInput) {
            sInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    serviceSearchQuery = e.target.value;
                    renderHome();
                }
            };

            sInput.onclick = (e) => e.target.focus();
        }
    }

    function renderWorkDone() {
        const service = activeServices.find(s => s.jobcardref === currentWorkDoneReg);
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
                                <p style="font-size:1.8rem;"><strong>Registration:</strong> <span style="color:#facc15;">${service.jobcardref}</span></p>
                                <p style="font-size:1.8rem;"><strong>Technician:</strong> ${service.tech}</p>
                                <p style="font-size:1.8rem;"><strong>Instruction:</strong> ${service.instruction}</p>
                            </div>
                        </div>
                        
                        <div style="margin-bottom:2rem;">
                            <label style="display:block; margin-bottom:1rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">Describe the work completed:</label>
                            <textarea 
                                id="work-done-textarea" 
                                rows="8" 
                                placeholder="Enter detailed description of work performed..."
                                style="width:100%; padding:1.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical;"
                            >${service.workDone || ''}</textarea>
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
        const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);

        mainContent.innerHTML = `
        <h2 style="margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Requesting Parts for: <span style="color:#facc15">${activeReg}</span></h2>
        
        ${cart.length > 0 ? `
            <div style="background:linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(22, 163, 74, 0.2) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; margin-bottom:2rem; border:3px solid rgba(34, 197, 94, 0.5); box-shadow: 0 10px 30px rgba(34, 197, 94, 0.2);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                    <div>
                        <h3 style="font-size:2rem; margin-bottom:0.5rem;">Cart Summary</h3>
                        <p style="color:#94a3b8; font-size:1.6rem;">${cart.length} item(s) • ${totalQuantity.toFixed(2)} total units</p>
                    </div>
                    <button onclick="viewCart()" style="background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color:white; padding:0.8rem 1.5rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem; transition:all 0.3s ease;">
                        View Cart
                    </button>
                </div>
                <div style="display:flex; gap:1rem; justify-content:flex-end;">
                    <button onclick="cancelOrder()" style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease;">
                        Cancel Order
                    </button>
                    <button onclick="confirmPartsOrder()" style="background:linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(34, 197, 94, 0.3); font-weight:bold; cursor:pointer; font-size:1.8rem; transition:all 0.3s ease;">
                        Confirm Order
                    </button>
                </div>
            </div>
        ` : ''}
        
        <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); border-radius:1rem; margin-bottom:2rem; border:2px solid rgba(59, 130, 246, 0.2); overflow:hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);">
            <button 
                id="collapse-toggle" 
                onclick="toggleCollapse()"
                style="width:100%; padding:1.5rem 2rem; background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); border:none; color:white; font-size:1.8rem; font-weight:bold; cursor:pointer; display:flex; justify-content:space-between; align-items:center; transition:all 0.3s ease;">
                <span>📋 Add Tech Notes / List Of Defects</span>
                <i id="collapse-icon" data-lucide="chevron-down" style="width:24px; height:24px; transition:transform 0.3s;"></i>
            </button>
            
            <div id="collapse-content" style="display:none; padding:2rem;">
                <div style="margin-bottom:2rem;">
                    <label style="display:block; margin-bottom:0.5rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">Tech Notes</label>
                    <textarea 
                        id="tech-notes-textarea" 
                        rows="4" 
                        placeholder="Enter any technical notes or observations..."
                        style="width:100%; padding:1rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical;"
                    >${techNotes}</textarea>
                </div>
                
                <div>
                    <label style="display:block; margin-bottom:0.5rem; font-size:1.8rem; font-weight:bold; color:#06b6d4;">List of Defects</label>
                    <textarea 
                        id="defects-textarea" 
                        rows="4" 
                        placeholder="List any defects found during inspection..."
                        style="width:100%; padding:1rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; resize:vertical;"
                    >${defectList}</textarea>
                </div>
            </div>
        </div>
        
        <div style="position:relative; max-width:600px; margin:0 auto 2rem;">
            <input 
                type="text" 
                id="parts-search" 
                class="search-input" 
                placeholder="Search parts by name..." 
                value="${partsSearchQuery}" 
                style="font-size:1.8rem; padding:1.2rem 1.2rem 1.2rem 4rem; width:100%;">
            <span style="position:absolute; left:1.2rem; top:1.4rem; color:#94a3b8; font-size:1.8rem;">🔍</span>
        </div>
        
        <div id="parts-results-container">
            ${partsSearchQuery ? renderPartsSearchResults() : renderCategoryGrid()}
        </div>
    `;

        const techNotesTextarea = document.getElementById('tech-notes-textarea');
        const defectsTextarea = document.getElementById('defects-textarea');

        if (techNotesTextarea) {
            techNotesTextarea.oninput = (e) => {
                techNotes = e.target.value;
            };
        }

        if (defectsTextarea) {
            defectsTextarea.oninput = (e) => {
                defectList = e.target.value;
            };
        }

        const partsInput = document.getElementById('parts-search');
        if(partsInput) {
            partsInput.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    partsSearchQuery = e.target.value.trim();
                    renderRequestParts();
                }
            };
            partsInput.onclick = (e) => e.target.focus();
        }
    }

    function renderCategory() {
        const filtered = parts.filter(p => categorize(p) === selectedCategory.id);

        const uniquePartsMap = new Map();
        filtered.forEach(part => {
            if (!uniquePartsMap.has(part.name)) {
                uniquePartsMap.set(part.name, part);
            }
        });

        const uniqueParts = Array.from(uniquePartsMap.values());

        mainContent.innerHTML = `
        <h2 style="font-size:2.5rem; margin-bottom:2rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${selectedCategory.icon} ${selectedCategory.name}</h2>
        <div class="category-grid">${renderParts(uniqueParts)}</div>
    `;
    }

    function renderCategoryGrid() {
        return `
        <div class="category-grid">
            ${categories.map(c => {
                const categoryParts = parts.filter(p => categorize(p) === c.id);
                const uniqueNames = new Set(categoryParts.map(p => p.name));
                return `
                    <button onclick="selectCategory('${c.id}')" class="category-card ${c.color}">
                        <span class="category-icon">${c.icon}</span>
                        <span class="category-name">${c.name}</span>
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
        if (!partsSearchQuery) return '';

        const searchTerm = partsSearchQuery.toLowerCase();
        const matchedParts = parts.filter(p => 
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
                <p style="font-size:2rem; color:#94a3b8;">No parts found matching "${partsSearchQuery}"</p>
                <button onclick="clearPartsSearch()" style="margin-top:1rem; background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; padding:1rem 2rem; border-radius:0.8rem; border:2px solid rgba(220, 38, 38, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem;">Clear Search</button>
            </div>
        `;
        }

        return `
        <div style="margin-bottom:2rem; display:flex; justify-content:space-between; align-items:center;">
            <h3 style="font-size:2rem; color:#06b6d4;">Found ${uniqueMatchedParts.length} part(s) matching "${partsSearchQuery}"</h3>
            <button onclick="clearPartsSearch()" style="background:linear-gradient(135deg, #64748b 0%, #475569 100%); color:white; padding:0.8rem 1.5rem; border-radius:0.8rem; border:2px solid rgba(100, 116, 139, 0.3); font-weight:bold; cursor:pointer; font-size:1.6rem;">Clear Search</button>
        </div>
        <div class="category-grid">${renderParts(uniqueMatchedParts)}</div>
    `;
    }
    
    function renderSearch() {
        const resultCats = [...new Set(searchResults.map(p => categorize(p)))].filter(c => c !== 'other');
        const filtered = activeSearchFilter === 'all' ? searchResults : searchResults.filter(p => categorize(p) === activeSearchFilter);
        mainContent.innerHTML = `
                <h2 style="font-size:2.5rem; margin-bottom:1.5rem;">Results (${filtered.length})</h2>
                <div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:2rem;">
                    <button onclick="setSearchFilter('all')" style="padding:0.75rem 1.5rem; border-radius:2rem; border:none; cursor:pointer; font-weight:bold; font-size:1.5rem; ${activeSearchFilter === 'all' ? 'background:#dc2626; color:white;' : 'background:#334155; color:#94a3b8;'}">All</button>
                    ${resultCats.map(cid => `<button onclick="setSearchFilter('${cid}')" style="padding:0.75rem 1.5rem; border-radius:2rem; border:none; cursor:pointer; font-weight:bold; font-size:1.5rem; ${activeSearchFilter === cid ? 'background:#dc2626; color:white;' : 'background:#334155; color:#94a3b8;'}">${categories.find(c => c.id === cid).name}</button>`).join('')}
                </div>
                <div class="category-grid">${renderParts(filtered)}</div>
            `;
    }

    function renderParts(arr) {
        return arr.map((p, index) => `
        <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1.5rem; display:flex; flex-direction:column; justify-content:space-between; gap:1.5rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2); transition:all 0.3s ease; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);" onmouseover="this.style.transform='translateY(-5px)'; this.style.borderColor='rgba(59, 130, 246, 0.5)'; this.style.boxShadow='0 15px 30px rgba(59, 130, 246, 0.3)';" onmouseout="this.style.transform=''; this.style.borderColor='rgba(59, 130, 246, 0.2)'; this.style.boxShadow='0 10px 20px rgba(0, 0, 0, 0.3)';">
            <div>
                <h3 style="font-size:2rem; color:#06b6d4;">${p.name}</h3>
                <p style="color:#94a3b8; margin-top:0.5rem">Category: ${p.category || 'N/A'}</p>
            </div>
            <div style="display:flex; flex-direction:column; gap:1rem; align-items:center;">
                <div style="width:100%;">
                    <label style="display:block; color:#94a3b8; font-size:1.4rem; margin-bottom:0.5rem;">Quantity</label>
                    <input 
                        type="number" 
                        id="qty-${index}" 
                        min="0" 
                        step="0.01" 
                        value="1" 
                        placeholder="0.00"
                        style="width:100%; padding:0.8rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; text-align:center;"
                    >
                </div>
                <button onclick="addToCart('${p.name.replace(/'/g, "\\'")}', '${index}')" class="add-btn-circular">+</button>
            </div>
        </div>`).join('');
    }

    function renderCheckout() {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);

        mainContent.innerHTML = `
        <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); padding:3rem; border-radius:2rem; border:4px solid rgba(59, 130, 246, 0.5); max-width:800px; margin:2rem auto; box-shadow: 0 20px 60px rgba(59, 130, 246, 0.3);">
            <h2 style="text-align:center; margin-bottom:2rem; font-size:2.5rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Your Order</h2>
            <div style="margin-bottom:2rem;">
                ${cart.length === 0 ? '<p style="text-align:center; font-size:1.8rem;">Your cart is empty.</p>' : cart.map((item, i) => `
                    <div style="padding:1rem; border-bottom:1px solid rgba(59, 130, 246, 0.2); display:flex; justify-content:space-between; align-items:center; font-size:1.8rem; gap:1rem;">
                        <div style="min-width:40px; font-size:2rem; font-weight:bold; color:#06b6d4;">${i + 1}.</div>
                        <div style="flex:1;">
                            <strong>${item.name}</strong><br>
                            <small style="color:#94a3b8;">${item.category}</small>
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
                                    style="width:80px; padding:0.5rem; font-size:1.6rem; border-radius:0.8rem; border:2px solid rgba(59, 130, 246, 0.3); background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); color:white; text-align:center;"
                                >
                            </div>
                            <button onclick="removeFromCart(${i})" style="color:#ef4444; background:none; border:none; cursor:pointer; font-size:1.5rem;">
                                <i data-lucide="trash-2"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
            ${cart.length > 0 ? `
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
                    <div style="margin:2rem 0;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ORDER-${id}"></div>
                    <div style="display:flex; flex-direction:column; gap:1rem;">
                        <button id="print-ticket-btn" class="btn-print">🖨️ Print Ticket</button>
                        <button onclick="goToHome()" style="background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; padding:1.2rem; border-radius:0.8rem; border:2px solid rgba(220, 38, 38, 0.3); font-weight:bold; cursor:pointer; font-size:2.4rem; transition:all 0.3s ease;">Finish</button>
                    </div>
                </div>`;

        document.getElementById('print-ticket-btn').onclick = () => window.print();

        setTimeout(() => { 
            if(currentView === 'success') { 
                document.title = originalTitle; 
                goToHome(); 
            } 
        }, 20000);
    }

    function renderAdmin() {
        const totalItems = orderHistory.reduce((sum, order) => sum + order.itemCount, 0);
        mainContent.innerHTML = `
            <div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                    <h2 style="font-size:3rem; background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Admin Dashboard</h2>
                    <button onclick="goToHome()" style="background:linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color:white; border:2px solid rgba(220, 38, 38, 0.3); padding:1rem 2rem; border-radius:1rem; cursor:pointer; font-weight:bold; font-size:2.4rem; transition:all 0.3s ease;">Exit Admin</button>
                </div>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1.5rem; margin-bottom:2rem;">
                    <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2);"><h4 style="color:#06b6d4; font-size:1.5rem;">Orders Today</h4><p style="font-size:2.5rem; font-weight:bold;">${orderHistory.length}</p></div>
                    <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2);"><h4 style="color:#06b6d4; font-size:1.5rem;">Total Items</h4><p style="font-size:2.5rem; font-weight:bold;">${totalItems}</p></div>
                    <div style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%); backdrop-filter:blur(10px); padding:2rem; border-radius:1rem; text-align:center; border:2px solid rgba(59, 130, 246, 0.2);"><h4 style="color:#06b6d4; font-size:1.5rem;">Session Clock</h4><p style="font-size:2.5rem; font-weight:bold;">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</p></div>
                </div>
                <div style="background:linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); backdrop-filter:blur(10px); border-radius:1rem; overflow:hidden; border:2px solid rgba(59, 130, 246, 0.2);">
                    <table style="width:100%; border-collapse:collapse; text-align:center;">
                        <thead style="background:linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);">
                            <tr style="font-size:2.4rem;"><th style="padding:1rem; font-size:2.4rem; text-align:center; color:#06b6d4;">Time</th><th style="padding:1rem; font-size:2.4rem; text-align:center; color:#06b6d4;">Order ID</th><th style="padding:1rem; font-size:2.4rem; text-align:center; color:#06b6d4;">Items</th></tr>
                        </thead>
                        <tbody>
                            ${orderHistory.map(o => `
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
        if (currentView === 'home' || currentView === 'success' || currentView === 'workDone') { 
            breadcrumbContainer.classList.add('hidden'); 
            return; 
        }
        breadcrumbContainer.classList.remove('hidden');

        let breadcrumb = `<span onclick="goToHome()" style="cursor:pointer; color:#06b6d4; font-weight:bold;">Home</span>`;

        if (currentView === 'Request Parts') {
            breadcrumb += ` > Request Parts`;
        } else if (currentView === 'category' || currentView === 'checkout') {
            breadcrumb += ` > <span onclick="backToPartsRequest()" style="cursor:pointer; color:#06b6d4; font-weight:bold;">Request Parts</span>`;
        }

        if (currentView === 'category') {
            breadcrumb += ` > Category`;
        } else if (currentView === 'checkout') {
            breadcrumb += ` > Checkout`;
        } else if (currentView !== 'Request Parts' && currentView !== 'home') {
            breadcrumb += ` > ${currentView.charAt(0).toUpperCase() + currentView.slice(1)}`;
        }

        breadcrumbContainer.innerHTML = breadcrumb;
    }

    function setupListeners() {
        window.selectCategory = (id) => { 
            selectedCategory = categories.find(c => c.id === id); 
            currentView = 'category'; 
            render(); 
        };

        window.addToCart = (name) => { 
            const item = parts.find(p => p.name === name); 
            if(item) cart.push(item); 
            render(); 
        };

        window.removeFromCart = (i) => { 
            cart.splice(i,1); 
            render(); 
        };

        window.goToHome = () => { 
            currentView = 'home'; 
            serviceSearchQuery = '';
            currentStatusFilter = 'all';
            currentWorkDoneReg = null;
            partsSearchQuery = '';
            techNotes = '';
            defectList = '';
            render(); 
        };

        window.backToPartsRequest = () => {
            currentView = 'Request Parts';
            selectedCategory = null;
            partsSearchQuery = '';
            render();
        };
        
        window.setSearchFilter = (f) => { 
            activeSearchFilter = f; 
            render(); 
        };

        window.clearStats = async () => {
            const confirmed = await customConfirm('Are you sure you want to clear all session data? This cannot be undone.', 'Clear Session Data');
            if(confirmed) {
                orderHistory = [];
                renderAdmin();
            }
        };

        window.confirmOrder = () => {
            const id = Math.floor(1000 + Math.random() * 9000);
            const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);

            orderHistory.push({
                id: id,
                time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                itemCount: totalQuantity.toFixed(2)
            });

            window.lastOrderID = id;
            cart = []; 
            currentView = 'success'; 
            render(); 
        };

        window.filterByStatus = (s) => { 
            currentStatusFilter = (currentStatusFilter === s) ? 'all' : s; 
            render(); 
        };

        window.openParts = (reg) => { 
            activeReg = reg; 
            currentView = 'Request Parts'; 
            render(); 
        };

        window.openWorkDone = (reg) => {
            currentWorkDoneReg = reg;
            currentView = 'workDone';
            render();
        };

        window.cancelWorkDone = () => {
            currentWorkDoneReg = null;
            currentView = 'home';
            render();
        };

        window.saveWorkDone = async () => {
            const textarea = document.getElementById('work-done-textarea');
            const workDoneText = textarea.value.trim();

            if (!workDoneText) {
                customAlert('Please enter the work done details before saving.', 'Work Done Required');
                return;
            }

            try {
                anvil.call(mainContent, 'save_work_done', currentWorkDoneReg, workDoneText);

                const service = activeServices.find(
                    s => s.jobcardref === currentWorkDoneReg
                );

                if (service) {
                    service.workDone = workDoneText;
                    service.status = 'Completed';
                }

                customAlert(
                    `Work done has been saved successfully for jobcard reference ${currentWorkDoneReg}`,
                    '✅ Success'
                );

                currentWorkDoneReg = null;
                currentStatusFilter = 'Completed';
                currentView = 'home';
                render();

            } catch (err) {
                console.error(err);
                await customAlert(
                    'Failed to save work done. Please try again.',
                    '❌ Error'
                );
            }
        };

        window.completeJob = (jobcardref) => { 
            const service = activeServices.find(s => s.jobcardref === jobcardref);
            if(service) {
                service.status = 'Completed';
                service.statusChangedAt = new Date();
            }
            render(); 
        };
        
        window.addToCart = (name, index) => {
            const qtyInput = document.getElementById(`qty-${index}`);
            const quantity = parseFloat(qtyInput?.value) || 1;

            if (quantity <= 0) {
                customAlert('Please enter a valid quantity greater than 0.', 'Invalid Quantity');
                return;
            }

            const item = parts.find(p => p.name === name);
            if (!item) return;

            const existingItemIndex = cart.findIndex(c => c.name === item.name);

            if (existingItemIndex > -1) {
                cart[existingItemIndex].quantity += quantity;
            } else {
                cart.push({
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
                document.getElementById(`cart-qty-${index}`).value = cart[index].quantity;
                return;
            }

            cart[index].quantity = qty;
            render();
        };
        
        backBtn.onclick = () => {
            if (currentView === 'category') {
                backToPartsRequest();
            } else {
                goToHome();
            }
        };
        cartBtn.onclick = () => { currentView = 'checkout'; render(); };
        homeFooterBtn.onclick = goToHome;

        adminTrigger.onclick = () => {
            adminClicks++;
            clearTimeout(adminTimeout);
            if (adminClicks === 5) {
                adminClicks = 0;
                currentView = 'admin';
                render();
            } else {
                adminTimeout = setTimeout(() => { adminClicks = 0; }, 2000);
            }
        };

        window.onscroll = () => {
            backToTopBtn.className = window.scrollY > 300 ? 'visible-fade' : 'hidden-fade';
        };

        window.clearPartsSearch = () => {
            partsSearchQuery = '';
            renderRequestParts();
        };

        window.confirmPartsOrder = async () => {
            if (cart.length === 0) {
                await customAlert('Your cart is empty. Please add parts before confirming.', 'Empty Cart');
                return;
            }

            const confirmed = await customConfirm(
                `You are about to submit an order with ${cart.length} item(s). Do you want to proceed?`,
                'Confirm Order Submission'
            );

            if (!confirmed) return;

            let partsAndQuantities = cart.map((item, i) => 
                `${i + 1}. ${item.name} (${item.category}) - Qty: ${item.quantity}`
            ).join('\n');

            const techNotesValue = techNotes.trim() || null;
            const defectListValue = defectList.trim() || null;
            const partsValue = partsAndQuantities || null;

            try {
                await anvil.call(
                    mainContent, 
                    'storeTechDetails', 
                    activeReg,
                    techNotesValue, 
                    defectListValue, 
                    partsValue
                );

                const id = Math.floor(1000 + Math.random() * 9000);
                const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);

                orderHistory.push({
                    id: id,
                    time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                    itemCount: totalQuantity.toFixed(2)
                });

                window.lastOrderID = id;

                cart = [];
                techNotes = '';
                defectList = '';
                partsSearchQuery = '';

                currentView = 'success';
                render();

            } catch (error) {
                console.error('Error storing tech details:', error);
                await customAlert(
                    'Failed to submit order. Please try again.',
                    '❌ Error'
                );
            }
        };

        window.toggleCollapse = () => {
            const content = document.getElementById('collapse-content');
            const icon = document.getElementById('collapse-icon');
            const button = document.getElementById('collapse-toggle');

            if (content.style.display === 'none') {
                content.style.display = 'block';
                button.style.background = 'linear-gradient(135deg, rgba(71, 85, 105, 0.8) 0%, rgba(51, 65, 85, 0.8) 100%)';
                if (icon) {
                    icon.style.transform = 'rotate(180deg)';
                }
            } else {
                content.style.display = 'none';
                button.style.background = 'linear-gradient(135deg, rgba(51, 65, 85, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)';
                if (icon) {
                    icon.style.transform = 'rotate(0deg)';
                }
            }

            lucide.createIcons();
        };

        window.viewCart = () => {
            currentView = 'checkout';
            render();
        };

        window.cancelOrder = async () => {
            const confirmed = await customConfirm(
                'Are you sure you want to cancel this order? All items in the cart and entered notes will be cleared.',
                'Cancel Order'
            );

            if (confirmed) {
                cart = [];
                techNotes = '';
                defectList = '';
                partsSearchQuery = '';

                await customAlert(
                    'Order has been cancelled successfully.',
                    'Order Cancelled'
                );

                currentView = 'home';
                render();
            }
        };
        
        backToTopBtn.onclick = () => window.scrollTo({top:0, behavior:'smooth'});
    }

    init();
})();
