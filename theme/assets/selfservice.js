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

            // Focus the button for keyboard accessibility
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
    let categories = []; // Will be populated from server
    let currentWorkDoneReg = null; // Track which job is having work done entered

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
            // Use anvil.server.call for standalone JavaScript (not anvil.call which requires a Form)
            const serverData = await anvil.call(mainContent, 'getCarPartNamesAndCategory');

            if (!Array.isArray(serverData)) {
                throw new Error("Server did not return a list. Check server logs.");
            }

            // Transform server data into parts array
            parts = serverData.map(item => ({
                name: item.Name,
                category: item.Category,
                partNo: item.PartNo || item.Name
            }));

            // Extract unique categories from server data
            const uniqueCategories = [...new Set(serverData.map(item => item.Category))];

            // Build categories array with config
            categories = uniqueCategories.map(catName => {
                const config = categoryConfig[catName] || { icon: '📦', color: 'bg-gray' };
                return {
                    id: catName.toLowerCase().replace(/\s+/g, '-'),
                    name: catName,
                    icon: config.icon,
                    color: config.color
                };
            });

            // **CRITICAL: Load active services from server**
            await loadActiveServices();

            setupListeners();
            render();

            setInterval(async () => { 
                if(currentView === 'home') {
                    await loadActiveServices();
                    render();
                }
            }, 60000); // Refresh every minute (both render AND data)
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

            // Server now returns a flat list, not grouped by status
            activeServices = jobcardsData.map(card => ({
                no: card.id,
                date: card.ReceivedDate,
                tech: card.Technician,
                jobcardref: card.JobCardRef,  // Changed from 'reg' to 'jobcardref'
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
        // Since category comes from server, just return it directly
        return p.category ? p.category.toLowerCase().replace(/\s+/g, '-') : 'other';
    }


    function render() {
        backBtn.classList.toggle('hidden', currentView === 'home' || currentView === 'success' || currentView === 'admin' || currentView === 'workDone');
        cartCount.innerText = cart.length;
        cartCount.classList.toggle('hidden', cart.length === 0 || currentView === 'success' || currentView === 'workDone');
        updateBreadcrumbs();

        if (currentView === 'home') renderHome();
        else if (currentView === 'issueParts') renderIssueParts();
        else if (currentView === 'category') renderCategory();
        else if (currentView === 'search') renderSearch();
        else if (currentView === 'checkout') renderCheckout();
        else if (currentView === 'success') renderSuccess();
        else if (currentView === 'admin') renderAdmin();
        else if (currentView === 'workDone') renderWorkDone();

        window.scrollTo({ top: 0, behavior: 'instant' });
        // Initialize all Lucide icons after any render
        lucide.createIcons();
    }

    function renderHome() {
        const isHistory = currentStatusFilter === 'Completed';
        const filtered = activeServices.filter(s => {
            const matchesStatus = currentStatusFilter === 'all' ? (s.status !== 'Completed') : (s.status === currentStatusFilter);
            const matchesSearch = s.jobcardref.toLowerCase().includes(serviceSearchQuery.toLowerCase()) || s.tech.toLowerCase().includes(serviceSearchQuery.toLowerCase());
            return matchesStatus && matchesSearch;
        });

        mainContent.innerHTML = `
        ${isHistory ? `<div class="summary-card">✅<div><h2>Daily Summary</h2><p>Completed Units Today: ${activeServices.filter(s => s.status === 'Completed').length}</p></div></div>` : ''}
        
        <h1 style="margin-bottom:2rem;">${isHistory ? 'Service History' : 'Service Queue'}</h1>
        
        <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:2rem; flex-wrap:wrap;">
            <div style="display:flex; gap:1rem;">
                <button class="btn-status bg-yellow ${currentStatusFilter === 'Checked-In' ? 'active-filter' : ''}" onclick="filterByStatus('Checked-In')">Checked-In</button>
                <button class="btn-status bg-green ${currentStatusFilter === 'In-Service' ? 'active-filter' : ''}" onclick="filterByStatus('In-Service')">In-Service</button>
                <button class="btn-status bg-gray ${currentStatusFilter === 'Completed' ? 'active-filter' : ''}" onclick="filterByStatus('Completed')">History</button>
            </div>
            
            <div style="position:relative; flex:1; max-width:400px; min-width:300px;">
                <input type="text" id="service-search" class="search-input" placeholder="Search JobCard or Tech..." value="${serviceSearchQuery}" style="font-size:1.5rem; padding:1rem 1rem 1rem 3.5rem; width:100%;">
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
                                    <button onclick="openParts('${s.jobcardref}')" class="btn-issue-parts">Issue Parts</button>
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
            sInput.oninput = (e) => { serviceSearchQuery = e.target.value; renderHome(); };
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
                    <div style="background:#1e293b; padding:3rem; border-radius:2rem; border:4px solid #3b82f6;">
                        <div style="margin-bottom:2rem;">
                            <h2 style="font-size:2.5rem; margin-bottom:1rem;">Work Done Report</h2>
                            <div style="background:#334155; padding:1.5rem; border-radius:1rem; margin-bottom:2rem;">
                                <p style="font-size:1.8rem;"><strong>Registration:</strong> <span style="color:#facc15;">${service.jobcardref}</span></p>
                                <p style="font-size:1.8rem;"><strong>Technician:</strong> ${service.tech}</p>
                                <p style="font-size:1.8rem;"><strong>Instruction:</strong> ${service.instruction}</p>
                            </div>
                        </div>
                        
                        <div style="margin-bottom:2rem;">
                            <label style="display:block; margin-bottom:1rem; font-size:1.8rem; font-weight:bold;">Describe the work completed:</label>
                            <textarea 
                                id="work-done-textarea" 
                                rows="8" 
                                placeholder="Enter detailed description of work performed..."
                                style="width:100%; padding:1.5rem; font-size:1.6rem; border-radius:0.5rem; border:2px solid #475569; background:#0f172a; color:white; resize:vertical;"
                            >${service.workDone || ''}</textarea>
                        </div>

                        <div style="display:flex; gap:1rem; justify-content:flex-end;">
                            <button 
                                onclick="cancelWorkDone()" 
                                style="background:#64748b; color:white; padding:1rem 2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:1.8rem;">
                                Cancel
                            </button>
                            <button 
                                onclick="saveWorkDone()" 
                                style="background:#22c55e; color:white; padding:1rem 2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:1.8rem;">
                                <i data-lucide="save" style="width:20px; height:20px; display:inline-block; vertical-align:middle; margin-right:0.5rem;"></i>
                                Save Work Done
                            </button>
                        </div>
                    </div>
                </div>
            `;
    }

    function renderIssueParts() {
        mainContent.innerHTML = `
                <h2 style="margin-bottom:2rem">Issuing Parts for: <span style="color:#facc15">${activeReg}</span></h2>
                <div class="category-grid">
                    ${categories.map(c => `
                        <button onclick="selectCategory('${c.id}')" class="category-card ${c.color}">
                            <span class="category-icon">${c.icon}</span>
                            <span class="category-name">${c.name}</span>
                            <span style="font-size:2rem;">
                                ${parts.filter(p => categorize(p) === c.id).length} Items
                            </span>
                        </button>
                    `).join('')}
                </div>
            `;
    }

    function renderCategory() {
        const filtered = parts.filter(p => categorize(p) === selectedCategory.id);
        mainContent.innerHTML = `
                <h2 style="font-size:2.5rem; margin-bottom:2rem">${selectedCategory.icon} ${selectedCategory.name}</h2>
                <div class="category-grid">${renderParts(filtered)}</div>
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
        return arr.map(p => `
                <div style="background:#334155; padding:2rem; border-radius:1.5rem; display:flex; flex-direction:column; justify-content:space-between; gap:1.5rem; text-align:center;">
                    <div>
                        <h3 style="font-size:2.4rem;">${p.name}</h3>
                        <p style="color:#94a3b8; margin-top:0.5rem">Category: ${p.category || 'N/A'}</p>
                    </div>
                    <button onclick="addToCart('${p.name}')" class="add-btn-circular">+</button>
                </div>`).join('');
    }

    function renderCheckout() {
        mainContent.innerHTML = `
                <div style="background:#1e293b; padding:3rem; border-radius:2rem; border:4px solid #3b82f6; max-width:800px; margin:2rem auto;">
                    <h2 style="text-align:center; margin-bottom:2rem; font-size:2.5rem;">Your Order</h2>
                    <div style="margin-bottom:2rem;">
                        ${cart.length === 0 ? '<p style="text-align:center; font-size:1.8rem;">Your cart is empty.</p>' : cart.map((item, i) => `<div style="padding:1rem; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center; font-size:1.8rem;"><div><strong>${item.name}</strong><br><small>${item.category}</small></div><button onclick="removeFromCart(${i})" style="color:#ef4444; background:none; border:none; cursor:pointer; font-size:1.5rem;"><i data-lucide="trash-2"></i></button></div>`).join('')}
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="font-size:2rem;">Total: ${cart.length} Parts</h3>
                        <button onclick="confirmOrder()" style="background:#22c55e; color:white; padding:1rem 2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:2.4rem;" ${cart.length === 0 ? 'disabled' : ''}>Confirm Order</button>
                    </div>
                </div>`;
    }

    function renderSuccess() {
        const id = window.lastOrderID;
        const originalTitle = document.title;
        document.title = `Order_Ticket_${id}`;

        mainContent.innerHTML = `
                <div style="text-align:center; padding:4rem 2rem; background:#1e293b; border-radius:2rem; max-width:600px; margin:2rem auto; border:4px solid #22c55e;">
                    <div style="background:#22c55e; width:80px; height:80px; border-radius:50%; margin:0 auto 1.5rem; display:flex; align-items:center; justify-content:center; font-size:3rem;">✓</div>
                    <h2 style="font-size:2.5rem;">Order Confirmed</h2>
                    <div style="font-size:4rem; color:#facc15; margin:1.5rem 0; border:2px dashed #475569; padding:1rem; border-radius:1rem; display:inline-block;">#${id}</div>
                    <div style="margin:2rem 0;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ORDER-${id}"></div>
                    <div style="display:flex; flex-direction:column; gap:1rem;">
                        <button id="print-ticket-btn" class="btn-print">🖨️ Print Ticket</button>
                        <button onclick="goToHome()" style="background:#dc2626; color:white; padding:1.2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:2.4rem;">Finish</button>
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
                    <h2 style="font-size:3rem;">Admin Dashboard</h2>
                    <button onclick="goToHome()" style="background:#dc2626; color:white; border:none; padding:1rem 2rem; border-radius:2rem; cursor:pointer; font-weight:bold; font-size:2.4rem;">Exit Admin</button>
                </div>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1.5rem; margin-bottom:2rem;">
                    <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;"><h4 style="color:#94a3b8; font-size:1.5rem;">Orders Today</h4><p style="font-size:2.5rem; font-weight:bold;">${orderHistory.length}</p></div>
                    <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;"><h4 style="color:#94a3b8; font-size:1.5rem;">Total Items</h4><p style="font-size:2.5rem; font-weight:bold;">${totalItems}</p></div>
                    <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;"><h4 style="color:#94a3b8; font-size:1.5rem;">Session Clock</h4><p style="font-size:2.5rem; font-weight:bold;">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</p></div>
                </div>
                <div style="background:#1e293b; border-radius:1rem; overflow:hidden;">
                    <table style="width:100%; border-collapse:collapse; text-align:center;">
                        <thead style="background:#334155;">
                            <tr style="font-size:2.4rem;"><th style="padding:1rem; font-size:2.4rem; text-align:center;">Time</th><th style="padding:1rem; font-size:2.4rem; text-align:center;">Order ID</th><th style="padding:1rem; font-size:2.4rem; text-align:center;">Items</th></tr>
                        </thead>
                        <tbody>
                            ${orderHistory.map(o => `
                                <tr style="border-bottom:1px solid #334155; font-size:2.4rem;">
                                    <td data-label="Time" style="padding:1rem; text-align:center;">${o.time}</td>
                                    <td data-label="ID" style="padding:1rem; text-align:center;">#${o.id}</td>
                                    <td data-label="Counter" style="padding:1rem; text-align:center;">${o.itemCount} Units</td>
                                </tr>`).reverse().join('')}
                        </tbody>
                    </table>
                </div>
                <button onclick="clearStats()" style="margin-top:2rem; background:none; border:1px solid #ef4444; color:#ef4444; padding:0.8rem 1.5rem; border-radius:0.5rem; cursor:pointer; font-weight:bold; font-size:2.4rem;">Clear Session Data</button>
            </div>`;
    }

    function updateBreadcrumbs() {
        if (currentView === 'home' || currentView === 'success' || currentView === 'workDone') { 
            breadcrumbContainer.classList.add('hidden'); 
            return; 
        }
        breadcrumbContainer.classList.remove('hidden');
        breadcrumbContainer.innerHTML = `<span onclick="goToHome()" style="cursor:pointer; color:#dc2626; font-weight:bold;">Home</span> > ${currentView.charAt(0).toUpperCase() + currentView.slice(1)}`;
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
            orderHistory.push({
                id: id,
                time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
                itemCount: cart.length
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
            currentView = 'issueParts'; 
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
                // 1. Call server to save + complete job
                anvil.call(mainContent, 'save_work_done', currentWorkDoneReg, workDoneText);

                // 2. Update local state immediately (no waiting)
                const service = activeServices.find(
                    s => s.jobcardref === currentWorkDoneReg
                );

                if (service) {
                    service.workDone = workDoneText;
                    service.status = 'Completed';
                }

                // 3. Success feedback
                customAlert(
                    `Work done has been saved successfully for jobcard reference ${currentWorkDoneReg}`,
                    '✅ Success'
                );

                // 4. Reset view + go home
                currentWorkDoneReg = null;
                currentStatusFilter = 'Completed'; // optional: auto-show history
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

        backBtn.onclick = goToHome;
        cartBtn.onclick = () => { currentView = 'checkout'; render(); };
        homeFooterBtn.onclick = goToHome;

        // Admin Secret Trigger - 5 clicks on logo
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

        backToTopBtn.onclick = () => window.scrollTo({top:0, behavior:'smooth'});
    }

    init();
})();