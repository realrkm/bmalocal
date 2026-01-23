(() => {
    const mainContent = document.getElementById('main-content');
    const backBtn = document.getElementById('back-btn');
    const cartBtn = document.getElementById('cart-btn');
    const cartCount = document.getElementById('cart-count');
    const breadcrumbContainer = document.getElementById('breadcrumb-container');
    const backToTopBtn = document.getElementById('back-to-top');
    const homeFooterBtn = document.getElementById('home-footer-btn');
    const adminTrigger = document.getElementById('admin-trigger');

    let parts = [], cart = [], currentView = 'home', selectedCategory = null;
    let searchResults = [], activeSearchFilter = 'all', orderHistory = [], adminClicks = 0;
    let adminTimeout;

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

    async function init() {
        try {
            const res = await fetch('_/theme/data/tbl_carpartnames.csv');
            const data = await res.text();
            parts = data.split('\n').slice(1).filter(l => l.trim()).map(line => {
                const [name, partNo] = line.split(',').map(s => s.trim());
                return { name, partNo };
            });
            setupListeners();
            render();
        } catch (e) { console.error("Initialization Error:", e); }
    }

    function categorize(p) {
        const text = (p.name + p.partNo).toLowerCase();
        for (const cat of categories) if (cat.keywords.some(k => text.includes(k))) return cat.id;
        return 'other';
    }

    function render() {
        backBtn.classList.toggle('hidden', currentView === 'home' || currentView === 'success' || currentView === 'admin');
        cartCount.innerText = cart.length;
        cartCount.classList.toggle('hidden', cart.length === 0 || currentView === 'success');
        updateBreadcrumbs();

        if (currentView === 'home') renderHome();
        else if (currentView === 'category') renderCategory();
        else if (currentView === 'search') renderSearch();
        else if (currentView === 'checkout') renderCheckout();
        else if (currentView === 'success') renderSuccess();
        else if (currentView === 'admin') renderAdmin();

        if (window.lucide) lucide.createIcons();
        window.scrollTo({ top: 0, behavior: 'instant' });
    }

    function renderHome() {
        mainContent.innerHTML = `
            <div class="search-container">
                <input type="text" id="global-search" placeholder="Search parts or serial numbers...">
                <i data-lucide="search" style="position:absolute; left:1.2rem; top:1.2rem; color:#94a3b8"></i>
            </div>
            <div class="category-grid">${categories.map(c => `
                <button onclick="selectCategory('${c.id}')" class="category-card ${c.color}">
                    <span class="category-icon">${c.icon}</span>
                    <span class="category-name" style="font-size:3rem;"">${c.name}</span>
                    <span class="category-count" style="font-size:2rem;">
                        ${parts.filter(p => categorize(p) === c.id).length} Items
                    </span>
                </button>`).join('')}
            </div>`;

        document.getElementById('global-search').onkeypress = (e) => {
            if(e.key === 'Enter' && e.target.value.trim()) {
                searchResults = parts.filter(p => (p.name + p.partNo).toLowerCase().includes(e.target.value.toLowerCase()));
                activeSearchFilter = 'all'; currentView = 'search'; render();
            }
        };
    }

    function renderSuccess() {
        const id = window.lastOrderID;
        const originalTitle = document.title;
        document.title = `Order_Ticket_${id}`;

        mainContent.innerHTML = `
            <div style="text-align:center; padding:4rem 2rem; background:#1e293b; border-radius:2rem; max-width:600px; margin:2rem auto; border:4px solid #22c55e;">
                <div style="background:#22c55e; width:80px; height:80px; border-radius:50%; margin:0 auto 1.5rem; display:flex; align-items:center; justify-content:center;"><i data-lucide="check" style="width:50px; height:50px; color:white;"></i></div>
                <h2 style="font-size:2rem;">Order Confirmed</h2>
                <div style="font-size:4rem; color:#facc15; margin:1.5rem 0; border:2px dashed #475569; padding:1rem; border-radius:1rem; display:inline-block;">#${id}</div>
                <div style="margin:2rem 0;"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ORDER-${id}"></div>
                <div style="display:flex; flex-direction:column; gap:1rem;">
                    <button id="print-ticket-btn" style="background:#475569; color:white; padding:1.2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:2.4rem;">Print Ticket</button>
                    <button onclick="goToHome()" style="background:#dc2626; color:white; padding:1.2rem; border-radius:0.5rem; border:none; font-weight:bold; cursor:pointer; font-size:2.4rem;">Finish</button>
                </div>
            </div>`;

        
        document.getElementById('print-ticket-btn').onclick = () => {
            window.print();
        };
        
        setTimeout(() => { if(currentView === 'success') { document.title = originalTitle; goToHome(); } }, 20000);
    }

    function renderAdmin() {
        const totalItems = orderHistory.reduce((sum, order) => sum + order.itemCount, 0);
        mainContent.innerHTML = `
        <div class="view-animate">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                <h2 style="font-size:3rem;">Admin Dashboard</h2>
                <button onclick="goToHome()" style="background:#dc2626; color:white; border:none; padding:1rem 2rem; border-radius:2rem; cursor:pointer; font-weight:bold; font-size:2.4rem;">Exit Admin</button>
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

    function renderCategory() {
        const filtered = parts.filter(p => categorize(p) === selectedCategory.id);
        mainContent.innerHTML = `<h2 style="font-size:2.5rem; margin-bottom:2rem">${selectedCategory.icon} ${selectedCategory.name}</h2><div class="category-grid">${renderParts(filtered)}</div>`;
    }

    function renderSearch() {
        const resultCats = [...new Set(searchResults.map(p => categorize(p)))].filter(c => c !== 'other');
        const filtered = activeSearchFilter === 'all' ? searchResults : searchResults.filter(p => categorize(p) === activeSearchFilter);
        mainContent.innerHTML = `
            <h2 style="font-size:2.5rem; margin-bottom:1.5rem;">Results (${filtered.length})</h2>
            <div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:2rem;">
                <button onclick="setSearchFilter('all')" style="padding:0.75rem 1.5rem; border-radius:2rem; border:none; cursor:pointer; font-weight:bold; ${activeSearchFilter === 'all' ? 'background:#dc2626; color:white;' : 'background:#334155; color:#94a3b8;'}">All</button>
                ${resultCats.map(cid => `<button onclick="setSearchFilter('${cid}')" style="padding:0.75rem 1.5rem; border-radius:2rem; border:none; cursor:pointer; font-weight:bold; ${activeSearchFilter === cid ? 'background:#dc2626; color:white;' : 'background:#334155; color:#94a3b8;'}">${categories.find(c => c.id === cid).name}</button>`).join('')}
            </div>
            <div class="category-grid">${renderParts(filtered)}</div>`;
    }

    function renderParts(arr) {
        return arr.map(p => `
            <div style="background:#334155; padding:2rem; border-radius:1.5rem; display:flex; flex-direction:column; justify-content:space-between; gap:1.5rem; text-align:center;">
                <div><h3 style="font-size:2.4rem;">${p.name}</h3><p style="color:#94a3b8; margin-top:0.5rem">Part #${p.partNo}</p></div>
                <button onclick="addToCart('${p.partNo}')" class="add-btn-circular"><i data-lucide="plus" style="width:32px; height:32px;"></i></button>
            </div>`).join('');
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

    function updateBreadcrumbs() {
        if (currentView === 'home' || currentView === 'success') { breadcrumbContainer.classList.add('hidden'); return; }
        breadcrumbContainer.classList.remove('hidden');
        breadcrumbContainer.innerHTML = `<span onclick="goToHome()" style="cursor:pointer; color:#dc2626; font-weight:bold;">Home</span> > ${currentView.charAt(0).toUpperCase() + currentView.slice(1)}`;
    }

    function setupListeners() {
        window.selectCategory = (id) => { selectedCategory = categories.find(c => c.id === id); currentView = 'category'; render(); };
        window.addToCart = (no) => { const item = parts.find(p => p.partNo === no); if(item) cart.push(item); render(); };
        window.removeFromCart = (i) => { cart.splice(i,1); render(); };
        window.goToHome = () => { currentView = 'home'; render(); };
        window.setSearchFilter = (f) => { activeSearchFilter = f; render(); };
        window.clearStats = () => { if(confirm("Clear session history?")) { orderHistory = []; renderAdmin(); } };
        
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

        backBtn.onclick = goToHome;
        cartBtn.onclick = () => { currentView = 'checkout'; render(); };
        homeFooterBtn.onclick = goToHome;
        
        // Logo Secret Trigger
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

        window.onscroll = () => backToTopBtn.className = window.scrollY > 300 ? 'visible-fade' : 'hidden-fade';
        backToTopBtn.onclick = () => window.scrollTo({top:0, behavior:'smooth'});
    }

    init();
})();