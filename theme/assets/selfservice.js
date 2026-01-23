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
        { id: 'engine', name: 'Engine Components', icon: '⚙️', color: 'bg-red', keywords: ['engine', 'piston', 'cylinder', 'valve', 'gasket', 'crankshaft', 'camshaft', 'timing', 'oil', 'spark', 'injector', 'turbo', 'manifold', 'pump'] },
        { id: 'brakes', name: 'Brake System', icon: '🛑', color: 'bg-orange', keywords: ['brake', 'rotor', 'caliper', 'pad', 'disc', 'drum', 'abs', 'master cylinder', 'booster'] },
        { id: 'suspension', name: 'Suspension & Steering', icon: '🔧', color: 'bg-blue', keywords: ['suspension', 'shock', 'strut', 'spring', 'arm', 'ball joint', 'tie rod', 'steering', 'rack', 'bushing', 'sway bar', 'link'] },
        { id: 'electrical', name: 'Electrical & Lighting', icon: '💡', color: 'bg-yellow', keywords: ['battery', 'alternator', 'starter', 'light', 'bulb', 'lamp', 'sensor', 'switch', 'relay', 'fuse', 'wire', 'ignition', 'coil'] },
        { id: 'cooling', name: 'Cooling System', icon: '❄️', color: 'bg-cyan', keywords: ['radiator', 'fan', 'coolant', 'thermostat', 'hose', 'water pump', 'cooling', 'condenser'] },
        { id: 'transmission', name: 'Transmission & Drivetrain', icon: '⚡', color: 'bg-purple', keywords: ['transmission', 'clutch', 'gearbox', 'axle', 'driveshaft', 'differential', 'cv joint', 'flywheel'] },
        { id: 'exhaust', name: 'Exhaust System', icon: '💨', color: 'bg-gray', keywords: ['exhaust', 'muffler', 'catalytic', 'pipe', 'emissions', 'oxygen sensor'] },
        { id: 'filters', name: 'Filters & Fluids', icon: '🔍', color: 'bg-green', keywords: ['filter', 'air filter', 'fuel filter', 'cabin filter', 'fluid', 'oil filter'] },
        { id: 'body', name: 'Body & Exterior', icon: '🚗', color: 'bg-indigo', keywords: ['bumper', 'fender', 'door', 'hood', 'mirror', 'panel', 'trim', 'grille', 'body', 'molding', 'windshield', 'window'] },
        { id: 'interior', name: 'Interior & Accessories', icon: '🪟', color: 'bg-pink', keywords: ['seat', 'carpet', 'dashboard', 'console', 'handle', 'knob', 'vent', 'mat', 'interior'] },
        { id: 'hvac', name: 'Climate Control', icon: '🌡️', color: 'bg-teal', keywords: ['ac', 'air conditioning', 'heater', 'blower', 'evaporator', 'compressor', 'hvac', 'climate'] },
        { id: 'other', name: 'Other Parts', icon: '🔩', color: 'bg-slate', keywords: [] }
    ];

    // --- Core Logic & Helpers ---
    async function loadParts() {
        try {
            // Update the path below to match your Flask route for the CSV
            const response = await fetch('/data/tbl_carpartnames.csv'); 
            const data = await response.text();
            const lines = data.split('\n').slice(1).filter(line => line.trim());
            parts = lines.map(line => {
                const [name, partNo] = line.split(',').map(s => s.trim());
                return { name, partNo };
            });
        } catch (error) {
            console.error('Error loading CSV:', error);
        }
    }

    function categorizePart(part) {
        const searchText = (part.name + ' ' + part.partNo).toLowerCase();
        for (const category of categories) {
            if (category.keywords.some(keyword => searchText.includes(keyword))) {
                return category.id;
            }
        }
        return 'other';
    }

    function getPartsForCategory(categoryId) {
        return parts.filter(part => categorizePart(part) === categoryId);
    }

    // --- Rendering Logic ---
    function render() {
        backBtn.classList.toggle('hidden', currentView === 'home');
        cartCount.innerText = cart.length;
        cartCount.classList.toggle('hidden', cart.length === 0);

        if (currentView === 'home') {
            renderHome();
        } else if (currentView === 'category') {
            renderPartsList(getPartsForCategory(selectedCategory.id), selectedCategory.name, selectedCategory.icon);
        } else if (currentView === 'search') {
            const filtered = parts.filter(p => 
                p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                p.partNo.toLowerCase().includes(searchTerm.toLowerCase())
                                         );
            renderPartsList(filtered, `Search Results (${filtered.length})`, '🔍');
        } else if (currentView === 'cart') {
            renderCart();
        }

        if (window.lucide) window.lucide.createIcons();
    }

    function renderHome() {
        mainContent.innerHTML = `
            <h2 class="page-title">Select a Category</h2>
            <div class="search-container">
                <div class="search-wrapper">
                    <i data-lucide="search" class="search-icon"></i>
                    <input type="text" id="search-input" placeholder="Search for part name or number..." value="${searchTerm}">
                </div>
            </div>
            <div class="category-grid">
                ${categories.map(cat => `
                    <button onclick="selectCategory('${cat.id}')" class="category-card ${cat.color}">
                        <div class="category-icon">${cat.icon}</div>
                        <div class="category-name">${cat.name}</div>
                        <div class="category-count">${getPartsForCategory(cat.id).length} parts</div>
                    </button>
                `).join('')}
            </div>
        `;

        document.getElementById('search-input').addEventListener('input', (e) => {
            searchTerm = e.target.value;
            if (searchTerm.length > 0) {
                currentView = 'search';
                render();
                document.getElementById('search-input').focus();
            }
        });
    }

    function renderPartsList(partArray, title, icon) {
        mainContent.innerHTML = `
            <div class="section-header">
                <div class="section-icon">${icon}</div>
                <h2 class="section-title">${title}</h2>
            </div>
            <div class="parts-grid">
                ${partArray.map((part) => `
                    <div class="part-card">
                        <div class="part-info">
                            <h3 class="part-name">${part.name}</h3>
                            <p class="part-number">Part #: ${part.partNo}</p>
                        </div>
                        <button onclick="addToCart('${part.partNo}')" class="add-to-cart-btn">
                            Add to Order
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    function renderCart() {
        if (cart.length === 0) {
            mainContent.innerHTML = `
                <h2 class="page-title">Your Order</h2>
                <div class="empty-cart">
                    <p class="empty-cart-text">Your cart is empty</p>
                    <button onclick="goToHome()" class="start-shopping-btn">Start Shopping</button>
                </div>
            `;
            return;
        }

        mainContent.innerHTML = `
            <h2 class="page-title">Your Order</h2>
            <div class="cart-items">
                ${cart.map((part, index) => `
                    <div class="cart-item">
                        <div>
                            <h3 class="part-name">${part.name}</h3>
                            <p class="part-number">Part #: ${part.partNo}</p>
                        </div>
                        <button onclick="removeFromCart(${index})" class="remove-btn">Remove</button>
                    </div>
                `).join('')}
            </div>
            <div class="cart-summary">
                <div class="cart-total">Total Items: ${cart.length}</div>
                <button class="checkout-btn">Proceed to Checkout</button>
            </div>
        `;
    }

    // --- Actions & Global Exposure ---
    window.selectCategory = (id) => {
        selectedCategory = categories.find(c => c.id === id);
        currentView = 'category';
        render();
    };

    window.addToCart = (partNo) => {
        const item = parts.find(p => p.partNo === partNo);
        if (item) cart.push(item);
        render();
    };

    window.removeFromCart = (index) => {
        cart.splice(index, 1);
        render();
    };

    window.goToHome = () => {
        currentView = 'home';
        searchTerm = '';
        render();
    };

    // --- Initialization ---
    async function init() {
        await loadParts();
        
        backBtn.addEventListener('click', window.goToHome);
        homeFooterBtn.addEventListener('click', window.goToHome);
        cartBtn.addEventListener('click', () => {
            currentView = 'cart';
            render();
        });

        render();
    }

    init();
})();