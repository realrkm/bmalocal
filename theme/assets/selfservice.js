(() => {
    const mainContent = document.getElementById('main-content');
    const backBtn = document.getElementById('back-btn');
    const cartBtn = document.getElementById('cart-btn');
    const cartCount = document.getElementById('cart-count');
    const breadcrumbContainer = document.getElementById('breadcrumb-container');
    const homeFooterBtn = document.getElementById('home-footer-btn');
    const adminTrigger = document.getElementById('admin-trigger');

    // State Management
    let parts = [], cart = [], currentView = 'home';
    let selectedCategory = null, activeReg = null;
    let serviceSearchQuery = '', currentStatusFilter = 'all';
    let orderHistory = [], adminClicks = 0, adminTimeout;

    const categories = [
        { id: 'body', name: 'Body & Exterior', icon: '🚗', color: 'bg-indigo', keywords: ['bumper', 'fender', 'door', 'hood'] },
        { id: 'brakes', name: 'Brake System', icon: '🛑', color: 'bg-orange', keywords: ['brake', 'rotor', 'caliper', 'pad'] },
        { id: 'cooling', name: 'Cooling System', icon: '❄️', color: 'bg-cyan', keywords: ['radiator', 'fan', 'coolant', 'thermostat'] },
        { id: 'electrical', name: 'Electrical & Lighting', icon: '💡', color: 'bg-yellow', keywords: ['battery', 'alternator', 'starter', 'light'] },
        { id: 'engine', name: 'Engine Components', icon: '⚙️', color: 'bg-red', keywords: ['engine', 'piston', 'cylinder', 'valve', 'gasket'] },
        { id: 'exhaust', name: 'Exhaust System', icon: '💨', color: 'bg-gray', keywords: ['exhaust', 'muffler', 'catalytic'] },
        { id: 'filters', name: 'Filters & Fluids', icon: '🔍', color: 'bg-green', keywords: ['filter', 'air filter', 'oil filter'] },
        { id: 'suspension', name: 'Suspension & Steering', icon: '🔧', color: 'bg-blue', keywords: ['suspension', 'shock', 'strut', 'spring'] },
        { id: 'transmission', name: 'Transmission', icon: '⚡', color: 'bg-purple', keywords: ['transmission', 'clutch', 'gearbox'] }
    ];

    let activeServices = [
        { date: '2026-01-24', tech: 'John Doe', reg: 'KBA 123X', instruction: 'Oil Change', status: 'In-Service', statusChangedAt: new Date(Date.now() - 5400000) },
        { date: '2026-01-24', tech: 'Sarah Smith', reg: 'KCC 789Z', instruction: 'Brake Check', status: 'Checked-In', statusChangedAt: new Date(Date.now() - 1800000) }
    ];

    async function init() {
        // Simulate loading parts data
        parts = [
            { name: "Oil Filter - Synthetic", partNo: "OF-1001" },
            { name: "Brake Pads - Front", partNo: "BP-5522" },
            { name: "Radiator Fan", partNo: "RF-990" }
        ];
        setupListeners();
        render();
        setInterval(() => { if(currentView === 'home') render(); }, 60000);
    }

    function getTimeElapsed(startTime) {
        const diffMs = new Date() - new Date(startTime);
        const diffMins = Math.floor(diffMs / 60000);
        const hours = Math.floor(diffMins / 60);
        return hours > 0 ? `${hours}h ${diffMins % 60}m` : `${diffMins}m`;
    }

    function render() {
        backBtn.classList.toggle('hidden', currentView === 'home' || currentView === 'admin');
        cartCount.innerText = cart.length;
        cartCount.classList.toggle('hidden', cart.length === 0);
        updateBreadcrumbs();

        if (currentView === 'home') renderHome();
        else if (currentView === 'issueParts') renderIssueParts();
        else if (currentView === 'category') renderCategory();
        else if (currentView === 'checkout') renderCheckout();
        else if (currentView === 'admin') renderAdmin();

        if (window.lucide) lucide.createIcons();
    }

    function renderHome() {
        const isHistory = currentStatusFilter === 'Completed';
        const filtered = activeServices.filter(s => {
            const matchesStatus = currentStatusFilter === 'all' ? (s.status !== 'Completed') : (s.status === currentStatusFilter);
            const matchesSearch = s.reg.toLowerCase().includes(serviceSearchQuery.toLowerCase()) || s.tech.toLowerCase().includes(serviceSearchQuery.toLowerCase());
            return matchesStatus && matchesSearch;
        });

        mainContent.innerHTML = `
            ${isHistory ? `<div class="summary-card"><i data-lucide="check-circle" style="width:40px; height:40px;"></i><div><h2>Daily Summary</h2><p>Completed Units Today: ${activeServices.filter(s => s.status === 'Completed').length}</p></div></div>` : ''}
            
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                <h1>${isHistory ? 'Service History' : 'Service Queue'}</h1>
                <div style="position:relative; width:400px;">
                    <input type="text" id="service-search" class="search-input" placeholder="Search Reg or Tech..." value="${serviceSearchQuery}" style="font-size:1.5rem; padding:1rem 1rem 1rem 3.5rem;">
                    <i data-lucide="search" style="position:absolute; left:1rem; top:1.2rem; color:#94a3b8; width:20px;"></i>
                </div>
            </div>

            <div style="display:flex; gap:1rem; margin-bottom:2rem;">
                <button class="btn-status bg-yellow ${currentStatusFilter === 'Checked-In' ? 'active-filter' : ''}" onclick="filterByStatus('Checked-In')">Checked-In</button>
                <button class="btn-status bg-green ${currentStatusFilter === 'In-Service' ? 'active-filter' : ''}" onclick="filterByStatus('In-Service')">In-Service</button>
                <button class="btn-status bg-gray ${currentStatusFilter === 'Completed' ? 'active-filter' : ''}" onclick="filterByStatus('Completed')">History</button>
            </div>

            <div class="service-table-container">
                <table class="kiosk-table">
                    <thead><tr><th>Received</th><th>Technician</th><th>Reg No</th><th>Elapsed</th><th>Status</th><th>Action</th></tr></thead>
                    <tbody>
                        ${filtered.map(s => `
                            <tr>
                                <td>${s.date}</td>
                                <td><strong>${s.tech}</strong></td>
                                <td style="color:#facc15; font-weight:bold;">${s.reg}</td>
                                <td><i data-lucide="clock" style="width:16px;"></i> ${getTimeElapsed(s.statusChangedAt)}</td>
                                <td><span class="status-badge ${s.status === 'In-Service' ? 'status-in-service' : s.status === 'Completed' ? 'status-completed' : 'status-checked-in'}">${s.status}</span></td>
                                <td>
                                    ${s.status === 'Completed' ? '✅ Finished' : `
                                        <button onclick="openParts('${s.reg}')" class="btn-issue-parts">Issue Parts</button>
                                        <button onclick="completeJob('${s.reg}')" style="background:#22c55e; border:none; color:white; padding:0.8rem; border-radius:0.5rem; cursor:pointer;"><i data-lucide="check"></i></button>
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

    function renderIssueParts() {
        mainContent.innerHTML = `
            <h2 style="margin-bottom:2rem">Issuing Parts for: <span style="color:#facc15">${activeReg}</span></h2>
            <div class="category-grid">
                ${categories.map(c => `
                    <button onclick="selectCat('${c.id}')" class="category-card ${c.color}">
                        <span class="category-icon">${c.icon}</span>
                        <span style="font-size:2rem; font-weight:bold;">${c.name}</span>
                    </button>
                `).join('')}
            </div>
        `;
    }

    function renderCategory() {
        const filtered = parts; // In real app, filter by category keywords
        mainContent.innerHTML = `
            <h2 style="margin-bottom:2rem">${selectedCategory.icon} ${selectedCategory.name}</h2>
            <div class="category-grid">
                ${filtered.map(p => `
                    <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;">
                        <h3>${p.name}</h3><p>#${p.partNo}</p>
                        <button onclick="addToCart('${p.partNo}')" style="background:#dc2626; border:none; color:white; width:50px; height:50px; border-radius:50%; margin-top:1rem; cursor:pointer;"><i data-lucide="plus"></i></button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function renderCheckout() {

        mainContent.innerHTML = `

            <div style="background:#1e293b; padding:3rem; border-radius:2rem; border:4px solid #3b82f6; max-width:800px; margin:2rem auto;">

                <h2 style="text-align:center; margin-bottom:2rem;">Your Order</h2>

                <div style="margin-bottom:2rem;">

                    ${cart.length === 0 ? '<p style="text-align:center;">Your cart is empty.</p>' : cart.map((item, i) => `<div style="padding:1rem; border-bottom:1px solid #334155; display:flex; justify-content:space-between; align-items:center;"><div><strong>${item.name}</strong><br><small>#${item.partNo}</small></div><button onclick="removeFromCart(${i})" style="color:#ef4444; background:none; border:none; cursor:pointer;"><i data-lucide="trash-2"></i></button></div>`).join('')}

                </div>

                <div style="display:flex; justify-content:space-between; align-items:center;">

                    <h3 >Total: ${cart.length} Parts</h3>

                    <button onclick="confirmOrder()" style="background:#22c55e; color:white; padding:1rem 2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:2.4rem;" ${cart.length === 0 ? 'disabled' : ''}>Confirm Order</button>

                </div>

            </div>`;

    }





    // Actions
    window.filterByStatus = (s) => { currentStatusFilter = (currentStatusFilter === s) ? 'all' : s; render(); };
    window.openParts = (reg) => { activeReg = reg; currentView = 'issueParts'; render(); };
    window.selectCat = (id) => { selectedCategory = categories.find(c => c.id === id); currentView = 'category'; render(); };
    window.addToCart = (no) => { cart.push(parts.find(p => p.partNo === no)); render(); };
    window.completeJob = (reg) => { activeServices.find(s => s.reg === reg).status = 'Completed'; render(); };
    window.processOrder = () => { cart = []; currentView = 'home'; alert("Order Processed Successfully!"); render(); };
    
    function updateBreadcrumbs() {
        breadcrumbContainer.classList.toggle('hidden', currentView === 'home');
        breadcrumbContainer.innerHTML = `<span onclick="location.reload()" style="cursor:pointer; color:#dc2626">Home</span> > ${currentView}`;
    }

    function renderAdmin() {
        const totalItems = orderHistory.reduce((sum, order) => sum + order.itemCount, 0);
        mainContent.innerHTML = `
        <div class="view-animate">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                <h2 style="font-size:3rem;">Admin Dashboard</h2>
                <button onclick="goToService()" style="background:#dc2626; color:white; border:none; padding:1rem 2rem; border-radius:2rem; cursor:pointer; font-weight:bold; font-size:2.4rem;">Exit Admin</button>
            </div>
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1.5rem; margin-bottom:2rem;">
                <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;"><h4 style="color:#94a3b8">Orders Today</h4><p style="font-size:2.5rem; font-weight:bold;">${orderHistory.length}</p></div>
                <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;"><h4 style="color:#94a3b8">Total Items</h4><p style="font-size:2.5rem; font-weight:bold;">${totalItems}</p></div>
                <div style="background:#334155; padding:2rem; border-radius:1rem; text-align:center;"><h4 style="color:#94a3b8">Session Clock</h4><p style="font-size:2.5rem; font-weight:bold;">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</p></div>
            </div>
            <div style="background:#1e293b; border-radius:1rem; overflow:hidden;">
                <table style="width:100%; border-collapse:collapse; text-align:center;">
                    <thead style="background:#334155;">
                        <tr style="font-size:2.4rem;"><th style="padding:1rem; font-size:2.4rem; text-align:center;">Time</th><th style="padding:1rem; font-size:2.4rem; text-align:center;">Order ID</th><th style="padding:1rem; font-size:2.4rem; text-align:center;">Items</th></tr>
                    </thead>
                    <tbody>
                        ${orderHistory.map(o => `
                            <tr style="border-bottom:1px solid #334155; font-size:2.4rem;">
                                <td style="padding:1rem; text-align:center;">${o.time}</td>
                                <td style="padding:1rem; text-align:center;">#${o.id}</td>
                                <td style="padding:1rem; text-align:center;">${o.itemCount} Units</td>
                            </tr>`).reverse().join('')}
                    </tbody>
                </table>
            </div>
            <button onclick="clearStats()" style="margin-top:2rem; background:none; border:1px solid #ef4444; color:#ef4444; padding:0.8rem 1.5rem; border-radius:0.5rem; cursor:pointer; font-weight:bold; font-size:2.4rem;" >Clear Session Data</button>
        </div>`;
    }


    function setupListeners() {
        backBtn.onclick = () => { currentView = 'home'; render(); };
        homeFooterBtn.onclick = () => { currentView = 'home'; render(); };
        cartBtn.onclick = () => { currentView = 'checkout'; render(); };
        window.clearStats = () => { if(confirm("Clear session history?")) { orderHistory = []; renderAdmin(); } };
        window.goToService = () => { currentView = 'home'; render(); };
        window.removeFromCart = (i) => { cart.splice(i,1); render(); };
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
        adminTrigger.onclick = () => {
            adminClicks++;
            clearTimeout(adminTimeout);
            if (adminClicks === 5) { currentView = 'admin'; render(); }
            adminTimeout = setTimeout(() => adminClicks = 0, 2000);
        };
    }

    init();
})();