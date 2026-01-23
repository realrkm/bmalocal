(() => {
    // --- DOM Elements ---
    const mainContent = document.getElementById('main-content');
    const backBtn = document.getElementById('back-btn');
    const cartBtn = document.getElementById('cart-btn');
    const cartCount = document.getElementById('cart-count');
    const homeFooterBtn = document.getElementById('home-footer-btn');

    // --- State Management ---
    let parts = [];
    let cart = [];
    let currentView = 'home';
    let selectedCategory = null;
    let searchTerm = '';

    const categories = [
        { id: 'engine', name: 'Engine Components', icon: '⚙️', color: 'bg-red', keywords: ['engine', 'piston', 'cylinder', 'valve', 'gasket'] },
        { id: 'brakes', name: 'Brake System', icon: '🛑', color: 'bg-orange', keywords: ['brake', 'rotor', 'caliper', 'pad'] },
        { id: 'suspension', name: 'Suspension & Steering', icon: '🔧', color: 'bg-blue', keywords: ['suspension', 'shock', 'strut', 'spring'] },
        { id: 'electrical', name: 'Electrical & Lighting', icon: '💡', color: 'bg-yellow', keywords: ['battery', 'alternator', 'starter', 'light'] },
        { id: 'cooling', name: 'Cooling System', icon: '❄️', color: 'bg-cyan', keywords: ['radiator', 'fan', 'coolant', 'thermostat'] },
        { id: 'transmission', name: 'Transmission', icon: '⚡', color: 'bg-purple', keywords: ['transmission', 'clutch', 'gearbox'] },
        { id: 'exhaust', name: 'Exhaust System', icon: '💨', color: 'bg-gray', keywords: ['exhaust', 'muffler', 'catalytic'] },
        { id: 'filters', name: 'Filters & Fluids', icon: '🔍', color: 'bg-green', keywords: ['filter', 'air filter', 'oil filter'] },
        { id: 'body', name: 'Body & Exterior', icon: '🚗', color: 'bg-indigo', keywords: ['bumper', 'fender', 'door', 'hood'] }
    ];

    // --- Helpers ---
    async function loadParts() {
        try {
            const response = await fetch('_/theme/data/tbl_carpartnames.csv'); 
            const data = await response.text();
            const lines = data.split('\n').slice(1).filter(line => line.trim());
            parts = lines.map(line => {
                const [name, partNo] = line.split(',').map(s => s.trim());
                return { name, partNo };
            });
        } catch (error) { console.error('Error loading CSV:', error); }
    }

    function categorizePart(part) {
        const searchText = (part.name + ' ' + part.partNo).toLowerCase();
        for (const category of categories) {
            if (category.keywords.some(keyword => searchText.includes(keyword))) return category.id;
        }
        return 'other';
    }

    // --- Rendering Logic ---
    function render() {
        backBtn.classList.toggle('hidden', currentView === 'home');
        cartCount.innerText = cart.length;
        cartCount.classList.toggle('hidden', cart.length === 0);

        if (currentView === 'home') renderHome();
        else if (currentView === 'category') renderPartsList(parts.filter(p => categorizePart(p) === selectedCategory.id), selectedCategory.name, selectedCategory.icon);
        else if (currentView === 'search') {
            const filtered = parts.filter(p => p.name.toLowerCase().includes(searchTerm.toLowerCase()) || p.partNo.toLowerCase().includes(searchTerm.toLowerCase()));
            renderPartsList(filtered, `Search Results (${filtered.length})`, '🔍');
        } else if (currentView === 'cart') renderCart();

        if (window.lucide) window.lucide.createIcons();
    }

    function renderHome() {
        mainContent.innerHTML = `
            <div class="view-animate">
                <h2 class="page-title" style="text-align:center; font-size: 3rem; margin-bottom: 2rem;">Select a Category</h2>
                <div class="search-container" style="margin-bottom: 3rem; text-align:center;">
                    <input type="text" id="search-input" placeholder="Search for part name or number..." value="${searchTerm}" style="width: 100%; max-width: 768px; padding: 1.5rem; border-radius: 1rem; border: 4px solid #475569; background:#334155; color:white; font-size: 1.5rem;">
                </div>
                <div class="category-grid">
                    ${categories.map(cat => `
                        <button onclick="selectCategory('${cat.id}')" class="category-card ${cat.color}">
                            <div class="category-icon">${cat.icon}</div>
                            <div class="category-name">${cat.name}</div>
                            <div class="category-count">${parts.filter(p => categorizePart(p) === cat.id).length} parts</div>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        document.getElementById('search-input').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            if (searchTerm.length > 0) { currentView = 'search'; render(); document.getElementById('search-input').focus(); }
        });
    }

    function renderPartsList(partArray, title, icon) {
        mainContent.innerHTML = `
            <div class="view-animate">
                <div style="display:flex; align-items:center; gap:1rem; margin-bottom:2rem;">
                    <span style="font-size:3.75rem;">${icon}</span>
                    <h2 style="font-size:3rem; font-weight:bold;">${title}</h2>
                </div>
                <div class="parts-grid">
                    ${partArray.map(part => `
                        <div class="part-card">
                            <h3 style="font-size:1.5rem; margin-bottom:0.5rem;">${part.name}</h3>
                            <p style="color:#cbd5e1; margin-bottom:1rem; font-size:1.25rem;">Part #: ${part.partNo}</p>
                            <button onclick="addToCart('${part.partNo}')" class="add-to-cart-btn">Add to Order</button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function renderCart() {
        mainContent.innerHTML = `
            <div class="view-animate">
                <h2 style="font-size:3rem; margin-bottom:2rem;">Your Order</h2>
                ${cart.length === 0 ? '<p style="font-size:1.5rem;">Your cart is empty.</p>' : 
                cart.map((p, i) => `
                    <div class="part-card" style="margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center;">
                        <div><h3>${p.name}</h3><p>#${p.partNo}</p></div>
                        <button onclick="removeFromCart(${i})" style="color:#ef4444; background:none; border:none; font-size:1.25rem; cursor:pointer;">Remove</button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // --- Global Methods ---
    window.selectCategory = (id) => {
        mainContent.innerHTML = '<div style="text-align:center;"><span class="loader"></span></div>';
        setTimeout(() => {
            selectedCategory = categories.find(c => c.id === id);
            currentView = 'category';
            render();
        }, 300);
    };

    window.addToCart = (partNo) => {
        const item = parts.find(p => p.partNo === partNo);
        if (item) cart.push(item);
        render();
    };

    window.removeFromCart = (index) => { cart.splice(index, 1); render(); };
    window.goToHome = () => { currentView = 'home'; searchTerm = ''; render(); };

    // --- Init ---
    async function init() {
        await loadParts();
        backBtn.addEventListener('click', window.goToHome);
        homeFooterBtn.addEventListener('click', window.goToHome);
        cartBtn.addEventListener('click', () => { currentView = 'cart'; render(); });
        render();
    }
    init();
})();