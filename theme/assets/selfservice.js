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
        { id: 'engine', name: 'Engine Components', icon: '⚙️', color: 'bg-red-500', keywords: ['engine', 'piston', 'cylinder', 'valve', 'gasket', 'crankshaft', 'camshaft', 'timing', 'oil', 'spark', 'injector', 'turbo', 'manifold', 'pump'] },
        { id: 'brakes', name: 'Brake System', icon: '🛑', color: 'bg-orange-500', keywords: ['brake', 'rotor', 'caliper', 'pad', 'disc', 'drum', 'abs', 'master cylinder', 'booster'] },
        { id: 'suspension', name: 'Suspension & Steering', icon: '🔧', color: 'bg-blue-500', keywords: ['suspension', 'shock', 'strut', 'spring', 'arm', 'ball joint', 'tie rod', 'steering', 'rack', 'bushing', 'sway bar', 'link'] },
        { id: 'electrical', name: 'Electrical & Lighting', icon: '💡', color: 'bg-yellow-500', keywords: ['battery', 'alternator', 'starter', 'light', 'bulb', 'lamp', 'sensor', 'switch', 'relay', 'fuse', 'wire', 'ignition', 'coil'] },
        { id: 'cooling', name: 'Cooling System', icon: '❄️', color: 'bg-cyan-500', keywords: ['radiator', 'fan', 'coolant', 'thermostat', 'hose', 'water pump', 'cooling', 'condenser'] },
        { id: 'transmission', name: 'Transmission & Drivetrain', icon: '⚡', color: 'bg-purple-500', keywords: ['transmission', 'clutch', 'gearbox', 'axle', 'driveshaft', 'differential', 'cv joint', 'flywheel'] },
        { id: 'exhaust', name: 'Exhaust System', icon: '💨', color: 'bg-gray-600', keywords: ['exhaust', 'muffler', 'catalytic', 'pipe', 'emissions', 'oxygen sensor'] },
        { id: 'filters', name: 'Filters & Fluids', icon: '🔍', color: 'bg-green-500', keywords: ['filter', 'air filter', 'fuel filter', 'cabin filter', 'fluid', 'oil filter'] },
        { id: 'body', name: 'Body & Exterior', icon: '🚗', color: 'bg-indigo-500', keywords: ['bumper', 'fender', 'door', 'hood', 'mirror', 'panel', 'trim', 'grille', 'body', 'molding', 'windshield', 'window'] },
        { id: 'interior', name: 'Interior & Accessories', icon: '🪟', color: 'bg-pink-500', keywords: ['seat', 'carpet', 'dashboard', 'console', 'handle', 'knob', 'vent', 'mat', 'interior'] },
        { id: 'hvac', name: 'Climate Control', icon: '🌡️', color: 'bg-teal-500', keywords: ['ac', 'air conditioning', 'heater', 'blower', 'evaporator', 'compressor', 'hvac', 'climate'] },
        { id: 'other', name: 'Other Parts', icon: '🔩', color: 'bg-slate-500', keywords: [] }
    ];

    // --- Core Logic & Helpers ---
    async function loadParts() {
        try {
            // Updated to use the correct path for Flask setup
            const response = await fetch('_/theme/data/tbl_carpartnames.csv'); 
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
        // Update Header/State UI
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
            <h2 class="text-white text-5xl font-bold mb-8 text-center">Select a Category</h2>
            <div class="mb-12">
                <div class="relative max-w-3xl mx-auto">
                    <i data-lucide="search" class="absolute left-6 top-1/2 transform -translate-y-1/2 text-slate-400 w-8 h-8"></i>
                    <input type="text" id="search-input" placeholder="Search for part name or number..." value="${searchTerm}"
                        class="w-full pl-20 pr-8 py-6 text-2xl rounded-2xl border-4 border-slate-600 focus:border-red-500 focus:outline-none bg-slate-700 text-white">
                </div>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                ${categories.map(cat => `
                    <button onclick="selectCategory('${cat.id}')" class="${cat.color} category-card text-white p-8 rounded-3xl shadow-2xl flex flex-col items-center justify-center gap-4 transition hover:-translate-y-2">
                        <div class="text-7xl">${cat.icon}</div>
                        <div class="text-2xl font-bold text-center">${cat.name}</div>
                        <div class="text-lg bg-white/20 px-4 py-2 rounded-full">${getPartsForCategory(cat.id).length} parts</div>
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
            <div class="flex items-center gap-4 mb-8">
                <div class="text-6xl">${icon}</div>
                <h2 class="text-white text-5xl font-bold">${title}</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                ${partArray.map((part) => `
                    <div class="bg-slate-700 text-white p-6 rounded-xl shadow-lg hover:bg-slate-600 transition">
                        <div class="flex-1 mb-4">
                            <h3 class="text-2xl font-bold mb-2">${part.name}</h3>
                            <p class="text-xl text-slate-300">Part #: ${part.partNo}</p>
                        </div>
                        <button onclick="addToCart('${part.partNo}')" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-6 rounded-xl text-xl transition">
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
                <h2 class="text-white text-5xl font-bold mb-8">Your Order</h2>
                <div class="bg-slate-700 text-white p-12 rounded-2xl text-center">
                    <p class="text-3xl mb-6">Your cart is empty</p>
                    <button onclick="goToHome()" class="bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-8 rounded-xl text-2xl">Start Shopping</button>
                </div>
            `;
            return;
        }

        mainContent.innerHTML = `
            <h2 class="text-white text-5xl font-bold mb-8">Your Order</h2>
            <div class="space-y-4 mb-8">
                ${cart.map((part, index) => `
                    <div class="bg-slate-700 text-white p-6 rounded-xl shadow-lg flex justify-between items-center">
                        <div>
                            <h3 class="text-2xl font-bold">${part.name}</h3>
                            <p class="text-xl text-slate-300">Part #: ${part.partNo}</p>
                        </div>
                        <button onclick="removeFromCart(${index})" class="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg text-lg">Remove</button>
                    </div>
                `).join('')}
            </div>
            <div class="bg-slate-700 text-white p-8 rounded-2xl border-2 border-red-500">
                <div class="text-4xl font-bold mb-6">Total Items: ${cart.length}</div>
                <button class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-6 px-8 rounded-xl text-3xl transition">Proceed to Checkout</button>
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
        
        // Attach static listeners
        backBtn.addEventListener('click', window.goToHome);
        homeFooterBtn.addEventListener('click', window.goToHome);
        cartBtn.addEventListener('click', () => {
            currentView = 'cart';
            render();
        });

        render();
    }

    // Start App
    init();

})();