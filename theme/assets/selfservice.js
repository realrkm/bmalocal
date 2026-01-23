(() => {

    // -------------------------------
    // DOM REFERENCES
    // -------------------------------
    const mainContent = document.getElementById('main-content');
    const backBtn = document.getElementById('back-btn');
    const cartBtn = document.getElementById('cart-btn');
    const cartCount = document.getElementById('cart-count');
    const breadcrumbContainer = document.getElementById('breadcrumb-container');
    const homeFooterBtn = document.getElementById('home-footer-btn');
    const adminTrigger = document.getElementById('admin-trigger');
    const backToTopBtn = document.getElementById('back-to-top');

    // -------------------------------
    // STATE
    // -------------------------------
    let currentView = 'home';          // home | issueParts | category | checkout | success | admin
    let selectedCategory = null;
    let activeReg = null;

    let parts = [];
    let cart = [];

    let serviceSearchQuery = '';
    let currentStatusFilter = 'all';

    let orderHistory = [];
    let lastOrderID = null;

    let adminClicks = 0;
    let adminTimeout = null;

    // -------------------------------
    // STATIC DATA
    // -------------------------------

    const categories = [
        { id: 'body', name: 'Body & Exterior', icon: '🚗', color: 'bg-indigo', keywords: ['bumper','fender','door','hood'] },
        { id: 'brakes', name: 'Brake System', icon: '🛑', color: 'bg-orange', keywords: ['brake','rotor','caliper','pad'] },
        { id: 'cooling', name: 'Cooling System', icon: '❄️', color: 'bg-cyan', keywords: ['radiator','fan','coolant','thermostat'] },
        { id: 'electrical', name: 'Electrical & Lighting', icon: '💡', color: 'bg-yellow', keywords: ['battery','alternator','starter','light'] },
        { id: 'engine', name: 'Engine Components', icon: '⚙️', color: 'bg-red', keywords: ['engine','piston','cylinder','valve','gasket'] },
        { id: 'exhaust', name: 'Exhaust System', icon: '💨', color: 'bg-gray', keywords: ['exhaust','muffler','catalytic'] },
        { id: 'filters', name: 'Filters & Fluids', icon: '🔍', color: 'bg-green', keywords: ['filter','oil filter','air filter'] },
        { id: 'suspension', name: 'Suspension & Steering', icon: '🔧', color: 'bg-blue', keywords: ['suspension','shock','strut','spring'] },
        { id: 'transmission', name: 'Transmission', icon: '⚡', color: 'bg-purple', keywords: ['transmission','clutch','gearbox'] }
    ];

    let activeServices = [
        { date: '2026-01-24', tech: 'John Doe', reg: 'KBA 123X', instruction: 'Oil Change', status: 'In-Service', statusChangedAt: new Date(Date.now() - 5400000) },
        { date: '2026-01-24', tech: 'Sarah Smith', reg: 'KCC 789Z', instruction: 'Brake Check', status: 'Checked-In', statusChangedAt: new Date(Date.now() - 1800000) }
    ];

    // -------------------------------
    // INIT
    // -------------------------------
    function init() {
        // Simulate CSV-loaded parts (replace with fetch later)
        parts = [
            { name: "Oil Filter - Synthetic", partNo: "OF-1001" },
            { name: "Brake Pads - Front", partNo: "BP-5522" },
            { name: "Radiator Fan", partNo: "RF-0990" },
            { name: "Alternator Assembly", partNo: "ALT-8831" },
            { name: "Shock Absorber", partNo: "SH-2201" }
        ];

        setupListeners();
        render();
        lucide.createIcons();

        setInterval(() => {
            if (currentView === 'home') render();
        }, 60000);
    }

    // -------------------------------
    // HELPERS
    // -------------------------------
    function categorize(part) {
        const text = (part.name + part.partNo).toLowerCase();
        for (const c of categories) {
            if (c.keywords.some(k => text.includes(k))) return c.id;
        }
        return 'other';
    }

    function getTimeElapsed(startTime) {
        const diffMs = new Date() - new Date(startTime);
        const mins = Math.floor(diffMs / 60000);
        const hrs = Math.floor(mins / 60);
        return hrs > 0 ? `${hrs}h ${mins % 60}m` : `${mins}m`;
    }

    function generateOrderID() {
        return Math.floor(1000 + Math.random() * 9000);
    }

    // -------------------------------
    // RENDER ROUTER
    // -------------------------------
    function render() {
        backBtn.classList.toggle('hidden', currentView === 'home' || currentView === 'admin');
        cartCount.innerText = cart.length;
        cartCount.classList.toggle('hidden', cart.length === 0);

        updateBreadcrumbs();

        if (currentView === 'home') renderHome();
        else if (currentView === 'issueParts') renderIssueParts();
        else if (currentView === 'category') renderCategory();
        else if (currentView === 'checkout') renderCheckout();
        else if (currentView === 'success') renderSuccess();
        else if (currentView === 'admin') renderAdmin();

        lucide.createIcons();
        window.scrollTo({ top: 0, behavior: 'instant' });
    }

    // -------------------------------
    // VIEWS
    // -------------------------------

    function renderHome() {
        const isHistory = currentStatusFilter === 'Completed';

        const filtered = activeServices.filter(s => {
            const matchesStatus =
                currentStatusFilter === 'all'
                    ? s.status !== 'Completed'
                    : s.status === currentStatusFilter;

            const matchesSearch =
                s.reg.toLowerCase().includes(serviceSearchQuery.toLowerCase()) ||
                s.tech.toLowerCase().includes(serviceSearchQuery.toLowerCase());

            return matchesStatus && matchesSearch;
        });

        mainContent.innerHTML = `
            ${isHistory ? `
                <div class="summary-card">
                    <i data-lucide="check-circle"></i>
                    <div>
                        <h2>Daily Summary</h2>
                        <p>Completed Units Today: ${activeServices.filter(s => s.status === 'Completed').length}</p>
                    </div>
                </div>` : ''}

            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                <h1>${isHistory ? 'Service History' : 'Service Queue'}</h1>
                <div style="position:relative; width:400px;">
                    <input type="text" id="service-search" class="search-input"
                        placeholder="Search Reg or Tech..." value="${serviceSearchQuery}">
                    <i data-lucide="search" style="position:absolute; left:1rem; top:1.2rem;"></i>
                </div>
            </div>

            <div style="display:flex; gap:1rem; margin-bottom:2rem;">
                <button class="btn-status bg-yellow ${currentStatusFilter === 'Checked-In' ? 'active-filter' : ''}" onclick="filterByStatus('Checked-In')">Checked-In</button>
                <button class="btn-status bg-green ${currentStatusFilter === 'In-Service' ? 'active-filter' : ''}" onclick="filterByStatus('In-Service')">In-Service</button>
                <button class="btn-status bg-gray ${currentStatusFilter === 'Completed' ? 'active-filter' : ''}" onclick="filterByStatus('Completed')">History</button>
            </div>

            <div class="service-table-container">
                <table class="kiosk-table">
                    <thead>
                        <tr>
                            <th>Received</th>
                            <th>Technician</th>
                            <th>Reg No</th>
                            <th>Elapsed</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${filtered.map(s => `
                            <tr>
                                <td>${s.date}</td>
                                <td><strong>${s.tech}</strong></td>
                                <td style="color:#facc15; font-weight:bold;">${s.reg}</td>
                                <td><i data-lucide="clock"></i> ${getTimeElapsed(s.statusChangedAt)}</td>
                                <td>
                                    <span class="status-badge ${
                                        s.status === 'In-Service' ? 'status-in-service' :
                                        s.status === 'Completed' ? 'status-completed' :
                                        'status-checked-in'
                                    }">${s.status}</span>
                                </td>
                                <td>
                                    ${s.status === 'Completed' ? '✅ Finished' : `
                                        <button onclick="openParts('${s.reg}')" class="btn-issue-parts">Issue Parts</button>
                                        <button onclick="completeJob('${s.reg}')" class="btn-complete"><i data-lucide="check"></i></button>
                                    `}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        const sInput = document.getElementById('service-search');
        sInput.oninput = e => {
            serviceSearchQuery = e.target.value;
            renderHome();
        };
    }

    function renderIssueParts() {
        mainContent.innerHTML = `
            <h2>Issuing Parts for: <span style="color:#facc15">${activeReg}</span></h2>
            <div class="category-grid">
                ${categories.map(c => `
                    <button onclick="selectCategory('${c.id}')" class="category-card ${c.color}">
                        <span class="category-icon">${c.icon}</span>
                        <span style="font-size:2rem; font-weight:bold;">${c.name}</span>
                    </button>
                `).join('')}
            </div>
        `;
    }

    function renderCategory() {
        const filtered = parts.filter(p => categorize(p) === selectedCategory.id);

        mainContent.innerHTML = `
            <h2>${selectedCategory.icon} ${selectedCategory.name}</h2>
            <div class="category-grid">
                ${filtered.map(p => `
                    <div class="part-card">
                        <h3>${p.name}</h3>
                        <p>#${p.partNo}</p>
                        <button onclick="addToCart('${p.partNo}')" class="add-btn-circular">
                            <i data-lucide="plus"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function renderCheckout() {
        mainContent.innerHTML = `
            <div class="checkout-container">
                <h2>Your Order</h2>
                <div>
                    ${cart.length === 0
                        ? '<p style="text-align:center;">Your cart is empty.</p>'
                        : cart.map((item, i) => `
                            <div class="checkout-row">
                                <div>
                                    <strong>${item.name}</strong><br>
                                    <small>#${item.partNo}</small>
                                </div>
                                <button onclick="removeFromCart(${i})" class="btn-remove">
                                    <i data-lucide="trash-2"></i>
                                </button>
                            </div>
                        `).join('')}
                </div>

                <div class="checkout-footer">
                    <h3>Total: ${cart.length} Parts</h3>
                    <button onclick="confirmOrder()" ${cart.length === 0 ? 'disabled' : ''} class="btn-confirm">
                        Confirm Order
                    </button>
                </div>
            </div>
        `;
    }

    function renderSuccess() {
        const id = lastOrderID;

        mainContent.innerHTML = `
            <div class="success-card">
                <h2>Order Confirmed</h2>
                <div class="order-number">#${id}</div>
                <button class="btn-print" onclick="window.print()">Print Ticket</button>
                <button class="btn-home" onclick="goHome()">Finish</button>
            </div>
        `;
    }

    function renderAdmin() {
        const totalItems = orderHistory.reduce((sum, o) => sum + o.itemCount, 0);

        mainContent.innerHTML = `
            <h2>Admin Dashboard</h2>

            <div class="admin-stats">
                <div>Orders Today: ${orderHistory.length}</div>
                <div>Total Items: ${totalItems}</div>
                <div>Time: ${new Date().toLocaleTimeString()}</div>
            </div>

            <table class="admin-table">
                <thead>
                    <tr><th>Time</th><th>Order ID</th><th>Items</th></tr>
                </thead>
                <tbody>
                    ${orderHistory.map(o => `
                        <tr>
                            <td>${o.time}</td>
                            <td>#${o.id}</td>
                            <td>${o.itemCount}</td>
                        </tr>
                    `).reverse().join('')}
                </tbody>
            </table>

            <button onclick="clearStats()" class="btn-clear">Clear Session Data</button>
        `;
    }

    // -------------------------------
    // NAV / ACTIONS
    // -------------------------------

    window.filterByStatus = s => {
        currentStatusFilter = (currentStatusFilter === s) ? 'all' : s;
        render();
    };

    window.openParts = reg => {
        activeReg = reg;
        currentView = 'issueParts';
        render();
    };

    window.selectCategory = id => {
        selectedCategory = categories.find(c => c.id === id);
        currentView = 'category';
        render();
    };

    window.addToCart = no => {
        const item = parts.find(p => p.partNo === no);
        if (item) cart.push(item);
        render();
    };

    window.removeFromCart = i => {
        cart.splice(i, 1);
        render();
    };

    window.completeJob = reg => {
        const svc = activeServices.find(s => s.reg === reg);
        svc.status = 'Completed';
        svc.statusChangedAt = new Date();
        render();
    };

    window.confirmOrder = () => {
        const id = generateOrderID();

        orderHistory.push({
            id,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            itemCount: cart.length
        });

        lastOrderID = id;
        cart = [];
        currentView = 'success';
        render();
    };

    window.goHome = () => {
        currentView = 'home';
        render();
    };

    window.clearStats = () => {
        if (confirm("Clear session history?")) {
            orderHistory = [];
            renderAdmin();
        }
    };

    function updateBreadcrumbs() {
        if (currentView === 'home' || currentView === 'success') {
            breadcrumbContainer.classList.add('hidden');
            return;
        }
        breadcrumbContainer.classList.remove('hidden');
        breadcrumbContainer.innerHTML =
            `<span onclick="goHome()" style="cursor:pointer; color:#dc2626;">Home</span> > ${currentView}`;
    }

    function setupListeners() {
        backBtn.onclick = goHome;
        homeFooterBtn.onclick = goHome;

        cartBtn.onclick = () => {
            currentView = 'checkout';
            render();
        };

        adminTrigger.onclick = () => {
            adminClicks++;
            clearTimeout(adminTimeout);

            if (adminClicks === 5) {
                adminClicks = 0;
                currentView = 'admin';
                render();
            } else {
                adminTimeout = setTimeout(() => adminClicks = 0, 2000);
            }
        };

        window.onscroll = () => {
            backToTopBtn.className = window.scrollY > 300 ? 'visible-fade' : 'hidden-fade';
        };

        backToTopBtn.onclick = () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };
    }

    // -------------------------------
    // START
    // -------------------------------
    init();

})();