// File: library-api-client.js
// Path: WebPages/js/library-api-client.js
// Standard: AIDEV-PascalCase-2.0
// Ecosystem Requirement: kebab-case filename for JavaScript module bundler compatibility
// Framework: Vanilla JavaScript ES6+ with Fetch API
// Function Naming: camelCase per JavaScript ecosystem standards  
// Class Naming: PascalCase per JavaScript ecosystem standards
// Constants: UPPER_SNAKE_CASE per JavaScript ecosystem standards
// API Integration: FastAPI backend with Design Standard v2.0 compliance
// Created: 2025-07-07
// Last Modified: 2025-07-07  09:13PM
/**
 * Description: Anderson's Library API Client - Design Standard v2.0
 * Connects desktop web twin and mobile app to FastAPI backend
 * Provides exact same functionality as desktop PySide6 version
 * Follows JavaScript ecosystem conventions while maintaining backend compatibility
 */

/**
 * Anderson's Library API Client Class
 * Handles all communication with FastAPI backend
 * Maintains compatibility with both desktop web and mobile interfaces
 */
class AndersonLibraryAPI {
    constructor() {
        // API Configuration
        this.baseURL = window.location.protocol + '//' + window.location.host;
        this.apiBase = this.baseURL + '/api';
        
        // Request Configuration
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client': 'Anderson-Library-Web-v2.0'
        };
        
        // State Management
        this.currentBooks = [];
        this.currentFilters = {
            search: '',
            category: '',
            subject: '',
            rating: 0,
            page: 1,
            limit: 50
        };
        
        // Performance & Caching
        this.isLoading = false;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        this.requestTimeouts = new Map();
        
        // Event Handling
        this.eventListeners = new Map();
        
        // API initialized
    }

    // ==================== CORE API METHODS ====================

    /**
     * Search Books - Google-type instant search
     * Maintains exact desktop functionality with debouncing
     */
    async searchBooks(searchTerm, useCache = true) {
        const cacheKey = `search_${searchTerm}_${this.currentFilters.page}_${this.currentFilters.limit}`;
        
        // Check cache first
        if (useCache && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            this.isLoading = true;
            this.emit('loadingStart', { operation: 'search', query: searchTerm });

            const requestBody = {
                query: searchTerm,
                page: this.currentFilters.page,
                limit: this.currentFilters.limit,
                filters: {
                    category: this.currentFilters.category,
                    subject: this.currentFilters.subject,
                    rating: this.currentFilters.rating
                }
            };

            const response = await this.makeRequest('POST', '/books/search', requestBody);
            
            // Cache successful results
            this.cache.set(cacheKey, {
                data: response,
                timestamp: Date.now()
            });
            
            this.emit('loadingEnd', { operation: 'search', success: true });
            return response;

        } catch (error) {
            console.error('Search error:', error);
            this.emit('loadingEnd', { operation: 'search', success: false });
            this.emit('error', { operation: 'search', error: error.message });
            return { books: [], total: 0, message: 'Search failed' };
        }
    }

    /**
     * Get All Books - Paginated book retrieval
     * Maintains exact desktop pagination behavior
     */
    async getAllBooks(page = 1, limit = 50) {
        const cacheKey = `all_books_${page}_${limit}`;
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            this.isLoading = true;
            this.emit('loadingStart', { operation: 'getAllBooks', page, limit });

            const response = await this.makeRequest('GET', `/books?page=${page}&limit=${limit}`);
            
            // Cache results
            this.cache.set(cacheKey, {
                data: response,
                timestamp: Date.now()
            });
            
            this.emit('loadingEnd', { operation: 'getAllBooks', success: true });
            return response;

        } catch (error) {
            console.error('Get all books error:', error);
            this.emit('loadingEnd', { operation: 'getAllBooks', success: false });
            this.emit('error', { operation: 'getAllBooks', error: error.message });
            return { books: [], total: 0, message: 'Failed to load books' };
        }
    }

    /**
     * Filter Books by Category/Subject/Rating
     * Maintains exact desktop filter behavior
     */
    async getBooksByFilters(category = '', subject = '', rating = 0, page = 1, limit = 50) {
        const cacheKey = `filters_${category}_${subject}_${rating}_${page}_${limit}`;
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            this.isLoading = true;
            this.emit('loadingStart', { operation: 'filter', category, subject, rating });

            const params = new URLSearchParams();
            if (category) params.append('category', category);
            if (subject) params.append('subject', subject);
            if (rating > 0) params.append('min_rating', rating.toString());
            params.append('page', page.toString());
            params.append('limit', limit.toString());

            const response = await this.makeRequest('GET', `/books/filter?${params}`);
            
            // Cache results
            this.cache.set(cacheKey, {
                data: response,
                timestamp: Date.now()
            });
            
            this.emit('loadingEnd', { operation: 'filter', success: true });
            return response;

        } catch (error) {
            console.error('Filter error:', error);
            this.emit('loadingEnd', { operation: 'filter', success: false });
            this.emit('error', { operation: 'filter', error: error.message });
            return { books: [], total: 0, message: 'Filter failed' };
        }
    }

    /**
     * Get Categories for dropdown population
     * Cached for performance
     */
    async getCategories() {
        const cacheKey = 'categories';
        
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            const response = await this.makeRequest('GET', '/categories');
            
            // Cache for longer period (categories don't change often)
            this.cache.set(cacheKey, {
                data: response,
                timestamp: Date.now()
            });
            
            return response;

        } catch (error) {
            console.error('Categories error:', error);
            this.emit('error', { operation: 'getCategories', error: error.message });
            return [];
        }
    }

    /**
     * Get Subjects for dropdown population
     * Optionally filtered by category
     */
    async getSubjects(categoryId = null) {
        const cacheKey = `subjects_${categoryId || 'all'}`;
        
        // Temporarily disable caching for debugging
        // if (this.cache.has(cacheKey)) {
        //     const cached = this.cache.get(cacheKey);
        //     if (Date.now() - cached.timestamp < this.cacheTimeout) {
        //         return cached.data;
        //     }
        // }

        try {
            const url = categoryId 
                ? `/subjects?category=${encodeURIComponent(categoryId)}`
                : '/subjects';
                
            const response = await this.makeRequest('GET', url);
            
            this.cache.set(cacheKey, {
                data: response,
                timestamp: Date.now()
            });
            
            return response;

        } catch (error) {
            console.error('Subjects error:', error);
            this.emit('error', { operation: 'getSubjects', error: error.message });
            return [];
        }
    }

    /**
     * Get Library Statistics for status display
     * Matches desktop status bar information
     */
    async getLibraryStats() {
        const cacheKey = 'library_stats';
        
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            const response = await this.makeRequest('GET', '/stats');
            
            this.cache.set(cacheKey, {
                data: response,
                timestamp: Date.now()
            });
            
            return response;

        } catch (error) {
            console.error('Stats error:', error);
            this.emit('error', { operation: 'getLibraryStats', error: error.message });
            return { 
                total_books: 0, 
                total_categories: 0, 
                total_subjects: 0,
                message: 'Stats unavailable'
            };
        }
    }

    /**
     * Get Book Thumbnail
     * Returns blob URL for display
     */
    async getBookThumbnail(bookId) {
        const cacheKey = `thumbnail_${bookId}`;
        
        // Check cache for blob URL
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            const response = await fetch(`${this.apiBase}/books/${bookId}/thumbnail`, {
                method: 'GET',
                headers: {
                    'Accept': 'image/*',
                    'X-Client': 'Anderson-Library-Web-v2.0'
                }
            });
            
            if (!response.ok) {
                return null; // No thumbnail available
            }

            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            
            // Cache the blob URL
            this.cache.set(cacheKey, {
                data: blobUrl,
                timestamp: Date.now()
            });
            
            return blobUrl;

        } catch (error) {
            console.error('Thumbnail error:', error);
            return null;
        }
    }

    // ==================== UTILITY METHODS ====================

    /**
     * Generic HTTP request handler with error handling
     * Follows REST API best practices
     */
    async makeRequest(method, endpoint, body = null) {
        const url = `${this.apiBase}${endpoint}`;
        
        const requestConfig = {
            method,
            headers: { ...this.defaultHeaders },
            credentials: 'same-origin'
        };
        
        if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            requestConfig.body = JSON.stringify(body);
        }
        
        // Add request timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        requestConfig.signal = controller.signal;
        
        try {
            const response = await fetch(url, requestConfig);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - please try again');
            }
            
            throw error;
        }
    }

    /**
     * Create Google-type instant search with debouncing
     * Maintains exact desktop search behavior
     */
    createInstantSearch(inputElement, resultsCallback, debounceMs = 300) {
        if (!inputElement || typeof resultsCallback !== 'function') {
            throw new Error('Invalid parameters for instant search');
        }
        
        let searchTimeout = null;
        
        const searchHandler = async (event) => {
            const searchTerm = event.target.value.trim();
            
            // Clear previous timeout
            clearTimeout(searchTimeout);
            
            // If empty, show all books
            if (searchTerm.length === 0) {
                try {
                    const results = await this.getAllBooks();
                    resultsCallback(results);
                } catch (error) {
                    console.error('Error loading all books:', error);
                }
                return;
            }
            
            // Debounce search - exactly like desktop version
            searchTimeout = setTimeout(async () => {
                try {
                    const results = await this.searchBooks(searchTerm);
                    resultsCallback(results);
                } catch (error) {
                    console.error('Search error in instant search:', error);
                    resultsCallback({ books: [], total: 0, error: error.message });
                }
            }, debounceMs);
        };
        
        inputElement.addEventListener('input', searchHandler);
        
        // Return cleanup function
        return () => {
            inputElement.removeEventListener('input', searchHandler);
            clearTimeout(searchTimeout);
        };
    }

    /**
     * Batch load thumbnails for performance
     * Used by grid views to load multiple thumbnails efficiently
     */
    async loadThumbnailsBatch(bookIds) {
        const thumbnailPromises = bookIds.map(async (bookId) => {
            try {
                const thumbnail = await this.getBookThumbnail(bookId);
                return { bookId, thumbnail, success: true };
            } catch (error) {
                console.error(`Failed to load thumbnail for book ${bookId}:`, error);
                return { bookId, thumbnail: null, success: false };
            }
        });
        
        return Promise.all(thumbnailPromises);
    }

    // ==================== EVENT SYSTEM ====================

    /**
     * Event system for UI updates
     * Allows UI components to listen for API events
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
        
        // Return unsubscribe function
        return () => {
            const listeners = this.eventListeners.get(event);
            if (listeners) {
                const index = listeners.indexOf(callback);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
            }
        };
    }

    /**
     * Emit events to registered listeners
     */
    emit(event, data = {}) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // ==================== CACHE MANAGEMENT ====================

    /**
     * Clear all cached data
     * Used for refresh operations
     */
    clearCache() {
        // Clean up blob URLs to prevent memory leaks
        for (const [key, cached] of this.cache.entries()) {
            if (key.startsWith('thumbnail_') && cached.data) {
                try {
                    URL.revokeObjectURL(cached.data);
                } catch (error) {
                    // Ignore errors when revoking blob URLs
                }
            }
        }
        
        this.cache.clear();
        // Cache cleared
    }

    /**
     * Clean expired cache entries
     * Prevents memory buildup over time
     */
    cleanExpiredCache() {
        const now = Date.now();
        const expired = [];
        
        for (const [key, cached] of this.cache.entries()) {
            if (now - cached.timestamp > this.cacheTimeout) {
                expired.push(key);
                
                // Clean up blob URLs
                if (key.startsWith('thumbnail_') && cached.data) {
                    try {
                        URL.revokeObjectURL(cached.data);
                    } catch (error) {
                        // Ignore errors
                    }
                }
            }
        }
        
        expired.forEach(key => this.cache.delete(key));
        
        // Cleaned expired cache entries
    }

    // ==================== HEALTH CHECK ====================

    /**
     * Check API health and connectivity
     * Used for debugging and status display
     */
    async checkHealth() {
        try {
            const response = await this.makeRequest('GET', '/health');
            return {
                healthy: true,
                status: response.status || 'OK',
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    // ==================== MOBILE-SPECIFIC METHODS ====================

    /**
     * Mobile-optimized search with smaller result sets
     * Reduces data usage on mobile networks
     */
    async searchBooksMobile(searchTerm, limit = 20) {
        return this.searchBooks(searchTerm, true);
    }

    /**
     * Prefetch data for offline use
     * Used by PWA for offline functionality
     */
    async prefetchForOffline() {
        try {
            // Prefetch essential data
            const promises = [
                this.getCategories(),
                this.getSubjects(),
                this.getLibraryStats(),
                this.getAllBooks(1, 20) // First page only
            ];
            
            await Promise.all(promises);
            // Offline prefetch completed
            return true;
        } catch (error) {
            console.error('Offline prefetch failed:', error);
            return false;
        }
    }
}

// ==================== INTEGRATION CLASSES ====================

/**
 * Desktop Web Twin Integration
 * Maintains exact desktop PySide6 functionality
 */
class DesktopLibraryInterface {
    constructor() {
        this.api = new AndersonLibraryAPI();
        this.selectedBook = null;
        this.currentBooks = [];
        this.cleanupFunctions = [];
        this.currentCategory = '';
        this.currentSubject = '';
        this.searchTimeout = null;
        this.apiServerRunning = false;

        // Setup event listeners immediately (synchronously)
        this.setupEventListeners();
        
        // Initialize app data (asynchronously)
        this.initializeApp();
    }

    async initializeApp() {
        try {
            this.updateStatus('Initializing Anderson\'s Library...');

            // Check if API server is running
            const serverRunning = await this.checkAPIServer();

            if (!serverRunning) {
                this.updateStatus('API server not available');
                this.showAPIWarning();
                return;
            }

            // Show startup screen initially
            this.showStartupScreen();

            // Load initial data
            await Promise.all([
                this.loadCategories(),
                this.loadStats()
            ]);

            this.updateStatus('Ready');

        } catch (error) {
            console.error('Initialization failed:', error);
            this.updateStatus('Failed to initialize application');
        }
    }

    async checkAPIServer() {
        try {
            // Add timeout to prevent hanging
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('API check timeout')), 3000)
            );
            
            const statsPromise = this.api.getLibraryStats();
            const stats = await Promise.race([statsPromise, timeoutPromise]);
            
            this.apiServerRunning = stats && stats.total_books !== undefined;
            return this.apiServerRunning;
        } catch (error) {
            console.warn('API server not accessible:', error);
            this.apiServerRunning = false;
            return false;
        }
    }

    showAPIWarning() {
        const grid = document.getElementById('booksGrid');
        if (!grid) return;
        grid.innerHTML = `
            <div class="api-warning">
                <strong>⚠️ API Server Not Running</strong>
                <p>Please start the FastAPI server to access your library:</p>
                <code style="background: rgba(0,0,0,0.3); padding: 5px 10px; border-radius: 3px; display: inline-block; margin: 10px 0;">
                    python StartAndyWeb.py
                </code>
                <p>Then visit: <strong>http://127.0.0.1:8001/app</strong></p>
            </div>
        `;

        document.getElementById('bookCount').textContent = 'API Server Required';
        document.getElementById('statusStats').textContent = 'Server offline';
    }

    setupEventListeners() {
        // Force remove all existing onclick handlers that might be interfering
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            if (el.onclick) {
                el.removeAttribute('onclick');
            }
        });
        
        // Use capturing phase to ensure we get clicks first
        document.addEventListener('click', (e) => {
            // Handle view toggle button
            if (e.target && e.target.id === 'viewToggleBtn') {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                this.toggleViewMode();
                return false;
            }
            
            // Handle dropdown menu items
            if (e.target && e.target.classList.contains('dropdown-item')) {
                const action = e.target.getAttribute('data-action');
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                switch (action) {
                    case 'showAbout':
                        this.showAboutBox();
                        break;
                    case 'showStats':
                        this.showStats();
                        break;
                    case 'exitApp':
                        this.exitApp();
                        break;
                    case 'setViewMode':
                        const mode = e.target.getAttribute('data-mode');
                        this.setViewMode(mode);
                        break;
                    case 'toggleViewMode':
                        this.toggleViewMode();
                        break;
                    case 'refreshLibrary':
                        this.refreshLibrary();
                        break;
                    case 'exportData':
                        this.exportData();
                        break;
                    case 'showHelp':
                        this.showHelp();
                        break;
                }
                return false;
            }
        }, true); // Use capturing phase
        
        // Direct attachment with multiple attempts
        this.attachDirectHandlers();
        
        // Dropdown change handlers
        const categorySelect = document.getElementById('categorySelect');
        const subjectSelect = document.getElementById('subjectSelect');
        
        if (categorySelect) {
            categorySelect.addEventListener('change', (e) => {
                this.onCategoryChange();
            });
        }
        
        if (subjectSelect) {
            subjectSelect.addEventListener('change', (e) => {
                this.onSubjectChange();
            });
        }
        
        // Search with debouncing
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.trim();
                if (searchTerm.length > 0) {
                    if (categorySelect) {
                        categorySelect.value = '';
                        this.currentCategory = '';
                    }
                    if (subjectSelect) {
                        subjectSelect.value = '';
                        this.currentSubject = '';
                    }
                }
                
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.performSearch();
                }, 300);
            });

            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
    }

    attachDirectHandlers() {
        // Try multiple times to attach handlers as backup
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                const gridBtn = document.getElementById('viewToggleBtn');
                
                if (gridBtn && !gridBtn.hasAttribute('data-handler-attached')) {
                    gridBtn.setAttribute('data-handler-attached', 'true');
                    gridBtn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.toggleViewMode();
                        return false;
                    };
                }
            }, i * 200);
        }
    }

    showAboutBox() {
        const grid = document.getElementById('booksGrid');
        if (!grid) return;
        grid.innerHTML = `
            <div class="initial-display">
                <div class="initial-card">
                    <div class="library-icon">
                        <img src="Assets/BowersWorld.png" alt="Anderson's Library" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                        <div class="icon-fallback" style="display: none;">📚</div>
                    </div>
                    <div class="initial-title">Anderson's Library</div>
                    <div class="initial-subtitle">Professional Edition</div>
                    <div class="library-status">Ready to search or browse books</div>
                </div>
            </div>
        `;

        document.getElementById('bookCount').textContent = 'Select a category or search for books';
    }

    async loadCategories() {
        try {
            const categories = await this.api.getCategories();
            const sortedCategories = categories.sort((a, b) => a.name.localeCompare(b.name));

            const categorySelect = document.getElementById('categorySelect');
            if (!categorySelect) return;
            categorySelect.innerHTML = '<option value="">All Categories</option>';

            sortedCategories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.name;
                option.textContent = `${category.name} (${category.count})`;
                categorySelect.appendChild(option);
            });

            // Categories loaded

        } catch (error) {
            console.error('Failed to load categories:', error);

            // Show placeholder categories when server isn't available
            const categorySelect = document.getElementById('categorySelect');
            if (!categorySelect) return;
            categorySelect.innerHTML = `
                <option value="">All Categories</option>
                <option value="Programming Languages">Programming Languages</option>
                <option value="Reference">Reference</option>
                <option value="Math">Math</option>
                <option value="Business">Business</option>
            `;

            if (!this.apiServerRunning) {
                categorySelect.disabled = true;
                categorySelect.title = "Requires API server to be running";
            }
        }
    }

    async loadSubjects(categoryFilter = '') {
        try {
            const subjects = await this.api.getSubjects(categoryFilter);
            const sortedSubjects = subjects.sort((a, b) => a.name.localeCompare(b.name));

            const subjectSelect = document.getElementById('subjectSelect');
            if (!subjectSelect) return;
            subjectSelect.innerHTML = '<option value="">All Subjects</option>';

            sortedSubjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.name;
                option.textContent = `${subject.name} (${subject.count})`;
                subjectSelect.appendChild(option);
            });

            // Subjects loaded

        } catch (error) {
            console.error('Failed to load subjects:', error);

            // Show placeholder subjects when server isn't available
            const subjectSelect = document.getElementById('subjectSelect');
            if (!subjectSelect) return;
            subjectSelect.innerHTML = `
                <option value="">All Subjects</option>
                <option value="Python">Python</option>
                <option value="JavaScript">JavaScript</option>
                <option value="Data Science">Data Science</option>
                <option value="Web Development">Web Development</option>
            `;

            if (!this.apiServerRunning) {
                subjectSelect.disabled = true;
                subjectSelect.title = "Requires API server to be running";
            }
        }
    }

    async loadStats() {
        try {
            console.log('Loading stats from API');
            const stats = await this.api.getLibraryStats();
            console.log('Stats response:', stats);

            const categoriesCount = stats.total_categories || stats.categories || 0;
            const subjectsCount = stats.total_subjects || stats.subjects || 0;
            const booksCount = stats.total_books || stats.books || 0;

            document.getElementById('statusStats').textContent =
                `${categoriesCount} Categories • ${subjectsCount} Subjects • ${booksCount} Total eBooks`;

        } catch (error) {
            console.error('Failed to load stats:', error);

            // Show placeholder stats when server isn't available
            if (!this.apiServerRunning) {
                document.getElementById('statusStats').textContent = 'Server Required • Start python StartAndyWeb.py';
            } else {
                document.getElementById('statusStats').textContent = 'Stats unavailable';
            }
        }
    }

    async loadBooks(filters = {}) {
        // Don't try to load books if API server isn't running
        if (!this.apiServerRunning) {
            this.showAPIWarning();
            return;
        }

        try {
            this.updateStatus('Loading books...');

            let data;
            if (filters.search) {
                data = await this.api.searchBooks(filters.search);
            } else {
                data = await this.api.getBooksByFilters(filters.category, filters.subject);
            }

            this.currentBooks = data.books || [];

            this.renderBooks(this.currentBooks);
            this.updateBookCount(data.total || this.currentBooks.length, filters);
            this.updateStatus('Ready');

        } catch (error) {
            console.error('Failed to load books:', error);
            this.renderError(`Failed to load books: ${error.message}. Please ensure the API server is running and data is valid.`);
            this.updateStatus('Error loading books');
        }
    }

    renderBooks(books) {
        const grid = document.getElementById('booksGrid');
        if (!grid) return;

        if (!books || books.length === 0) {
            this.showStartupScreen();
            return;
        }

        grid.innerHTML = books.map(book => {
            const bookJson = JSON.stringify(book).replace(/"/g, '&quot;');
            return `
                <div class="book-card" onclick="window.libraryInterface.openPDFReader(${bookJson})" data-book-id="${book.id}">
                    <div class="book-thumbnail" id="thumb-${book.id}">
                        <img src="${this.api.apiBase}/books/${book.id}/thumbnail"
                             alt="${book.title}"
                             onerror="handleThumbnailError(this, ${book.id})"
                             onload="handleThumbnailLoad(this)">
                    </div>
                    <div class="book-info">
                        <div class="book-title">${book.title || 'Unknown Title'}</div>
                        <div class="book-author">${book.author || 'Unknown Author'}</div>
                        <div class="book-category">${book.category || 'General'}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    handleThumbnailError(img, bookId) {
        const container = img.parentElement;
        container.className = 'book-thumbnail no-image';
        container.innerHTML = '<div>No<br>Image</div>';
    }

    handleThumbnailLoad(img) {
        img.style.opacity = '1';
    }

    renderError(message) {
        const grid = document.getElementById('booksGrid');
        if (!grid) return;
        grid.innerHTML = `<div class="error">${message}</div>`;
    }

    async onCategoryChange() {
        if (!this.apiServerRunning) {
            this.updateStatus('Please start the API server to use filters');
            return;
        }

        const categorySelect = document.getElementById('categorySelect');
        if (!categorySelect) return;
        this.currentCategory = categorySelect.value;

        // Clear search box when category is selected
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
        }

        // Reset subject dropdown
        this.currentSubject = '';
        const subjectSelect = document.getElementById('subjectSelect');
        if (subjectSelect) subjectSelect.value = '';

        // Load subjects for this category
        await this.loadSubjects(this.currentCategory);

        // Reload books
        await this.loadBooks({
            category: this.currentCategory,
            subject: this.currentSubject,
            search: ''
        });
    }

    async onSubjectChange() {
        if (!this.apiServerRunning) {
            this.updateStatus('Please start the API server to use filters');
            return;
        }

        const subjectSelect = document.getElementById('subjectSelect');
        if (!subjectSelect) return;
        this.currentSubject = subjectSelect.value;

        // Clear search box when subject is selected
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
        }

        // Reload books
        await this.loadBooks({
            category: this.currentCategory,
            subject: this.currentSubject,
            search: ''
        });
    }

    async performSearch() {
        if (!this.apiServerRunning) {
            this.updateStatus('Please start the API server to search books');
            this.showAPIWarning();
            return;
        }

        const searchInput = document.getElementById('searchInput');
        const searchTerm = searchInput ? searchInput.value : '';

        await this.loadBooks({
            category: this.currentCategory,
            subject: this.currentSubject,
            search: searchTerm
        });
    }

    selectBook(book) {
        // Remove previous selection
        if (this.selectedBook) {
            const prevSelectedCard = document.querySelector(`[data-book-id="${this.selectedBook.id}"]`);
            if (prevSelectedCard) {
                prevSelectedCard.classList.remove('selected');
            }
        }

        // Select new book
        const newSelectedCard = document.querySelector(`[data-book-id="${book.id}"]`);
        if (newSelectedCard) {
            this.selectedBook = book;
            newSelectedCard.classList.add('selected');
        }

        // Update status
        this.updateStatus(`Selected: ${book.title}`);

        console.log('Book selected:', book);
    }

    updateBookCount(count, filters = {}) {
        let context = '';
        const filterParts = [];

        if (filters.category) filterParts.push(`Category: ${filters.category}`);
        if (filters.subject) filterParts.push(`Subject: ${filters.subject}`);
        if (filters.search) filterParts.push(`Search: "${filters.search}"`);

        if (filterParts.length > 0) {
            context = ` (${filterParts.join(', ')})`;
        }

        const bookCountElement = document.getElementById('bookCount');
        if (bookCountElement) {
            bookCountElement.textContent = `Showing ${count} books${context}`;
        }
    }

    updateStatus(message) {
        const statusMessageElement = document.getElementById('statusMessage');
        if (statusMessageElement) {
            statusMessageElement.textContent = message;
        }
    }

    setViewMode(mode) {
        const button = document.getElementById('viewToggleBtn');
        const booksGrid = document.getElementById('booksGrid');
        
        if (!booksGrid || !button) return;
        
        if (mode === 'grid') {
            booksGrid.classList.remove('view-list');
            booksGrid.classList.add('view-grid');
            button.textContent = 'Grid View';
            button.dataset.mode = 'grid';
        } else {
            booksGrid.classList.remove('view-grid');
            booksGrid.classList.add('view-list');
            button.textContent = 'List View';
            button.dataset.mode = 'list';
        }

        this.updateStatus(`View mode: ${mode}`);
    }

    toggleViewMode() {
        const button = document.getElementById('viewToggleBtn');
        if (!button) return;
        
        const currentMode = button.dataset.mode || 'grid';
        const newMode = currentMode === 'grid' ? 'list' : 'grid';
        this.setViewMode(newMode);
    }

    openPDFReader(book) {
        // Open PDF directly without confirmation
        const pdfUrl = `${this.api.apiBase}/books/${book.id}/pdf`;
        // Opening PDF
        window.open(pdfUrl, '_blank');
    }
    
    showStartupScreen() {
        const grid = document.getElementById('booksGrid');
        if (!grid) return;
        
        grid.innerHTML = `
            <div class="startup-display">
                <div class="startup-card">
                    <div class="startup-icon">
                        <img src="/assets/BowersWorld.png" alt="Anderson's Library">
                    </div>
                    <div class="startup-title">Anderson's Library</div>
                    <div class="startup-subtitle">Professional Edition</div>
                    <div class="startup-description">Another Intuitive Product<br>from the folks at<br><strong>BowersWorld.com</strong></div>
                    <div class="startup-footer">
                        <div class="startup-copyright">© 2025</div>
                        <div class="startup-version">Design Standard v2.1</div>
                        <div class="startup-project">Project Himalaya</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Dialog functions for menu items
    showAboutBox() {
        // Create modal overlay
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="about-dialog">
                <div class="bowers-logo">
                    <img src="/assets/BowersWorld.png" alt="BowersWorld Logo">
                </div>
                <h2>Anderson's Library</h2>
                <p><strong>Professional Edition</strong></p>
                <hr>
                <p>Another Intuitive Product</p>
                <p>from the folks at</p>
                <p><strong>BowersWorld.com</strong></p>
                <hr>
                <p>© 2025</p>
                <p>Design Standard v2.1</p>
                <p>Project Himalaya</p>
                <button onclick="this.parentElement.parentElement.remove()">Close</button>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.remove();
            }
        });
    }
    
    showStats() {
        alert('Library Statistics:\n\nBooks: ' + this.currentBooks.length + '\nView: Desktop Interface\nStatus: Ready');
    }
    
    refreshLibrary() {
        this.api.clearCache();
        this.loadStats();
        this.loadCategories();
        this.updateStatus('Library refreshed');
    }
    
    exportData() {
        alert('Export functionality coming soon!');
    }
    
    exitApp() {
        if (confirm('Are you sure you want to exit Anderson\'s Library?')) {
            this.shutdownServer();
        }
    }
    
    showHelp() {
        alert('Anderson\'s Library Help:\n\n1. Use search to find books\n2. Filter by category or subject\n3. Click books to read PDFs\n4. Toggle between Grid and List view\n\nDesign Standard v2.1');
    }
    
    async shutdownServer() {
        try {
            await this.api.makeRequest('POST', '/shutdown');
            setTimeout(() => {
                window.close();
            }, 1000);
        } catch (error) {
            console.error('Error shutting down server:', error);
            window.close();
        }
    }
    
    // Original cleanup function, kept for completeness
    cleanup() {
        this.cleanupFunctions.forEach(cleanup => cleanup());
        this.api.clearCache();
    }
}

/**
 * Mobile Library Interface
 * Touch-optimized with PWA features
 */
class MobileLibraryInterface {
    constructor() {
        this.api = new AndersonLibraryAPI();
        this.selectedBook = null;
        this.currentBooks = [];
        this.cleanupFunctions = [];

        this.initializeMobileInterface();
    }

    async initializeMobileInterface() {
        try {
            // Load initial data
            await this.loadInitialData();

            // Setup mobile search
            const searchInput = document.getElementById('mobileSearchInput');
            if (searchInput) {
                const cleanup = this.api.createInstantSearch(searchInput, (results) => {
                    this.displayMobileBooks(results.books);
                    this.updateMobileStats(results.total);

                    if (results.books.length === 0) {
                        this.showEmptyState(true);
                    } else {
                        this.showEmptyState(false);
                    }
                });
                this.cleanupFunctions.push(cleanup);
            }

            // Setup API event listeners
            this.setupMobileEventListeners();

            // Prefetch for offline use
            this.api.prefetchForOffline();

            console.log('Mobile interface initialized');

        } catch (error) {
            console.error('Mobile interface initialization failed:', error);
            this.showErrorToast('Failed to initialize library');
        }
    }

    async loadInitialData() {
        try {
            // Load books
            await this.loadBooks();

            // Load filter options
            await this.loadCategories();
            await this.loadSubjects();
            await this.loadStats();

        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.renderError('Failed to load library data');
        }
    }

    setupMobileEventListeners() {
        this.api.on('loadingStart', (data) => {
            this.showMobileLoading(true);
        });

        this.api.on('loadingEnd', (data) => {
            this.showMobileLoading(false);
        });

        this.api.on('error', (data) => {
            this.showErrorToast(`Error: ${data.error}`);
        });
    }

    displayMobileBooks(books) {
        const list = document.getElementById('mobileBookList');
        if (!list) return;

        list.innerHTML = '';

        books.forEach(book => {
            const card = this.createMobileBookCard(book);
            list.appendChild(card);
        });

        this.currentBooks = books;
    }

    createMobileBookCard(book) {
        const card = document.createElement('div');
        card.className = 'book-card';
        card.onclick = () => this.selectBook(book);
        card.dataset.bookId = book.id;

        card.innerHTML = `
            <div class="mobile-book-cover">📘</div>
            <div class="mobile-book-info">
                <div class="mobile-book-title">${this.escapeHtml(book.title)}</div>
                <div class="mobile-book-author">${this.escapeHtml(book.author || 'Unknown Author')}</div>
                <div class="mobile-book-meta">
                    <div class="mobile-category-tag">${this.escapeHtml(book.subject || book.category || 'General')}</div>
                    <div class="mobile-rating">${'⭐'.repeat(book.rating || 0)}</div>
                </div>
            </div>
            <div class="mobile-book-arrow">›</div>
        `;

        return card;
    }

    selectBook(book) {
        // Remove previous selection
        if (this.selectedBook) {
            const prevSelectedCard = document.querySelector(`[data-book-id="${this.selectedBook.id}"]`);
            if (prevSelectedCard) {
                prevSelectedCard.classList.remove('selected');
            }
        }

        // Select new book
        const newSelectedCard = document.querySelector(`[data-book-id="${book.id}"]`);
        if (newSelectedCard) {
            this.selectedBook = book;
            newSelectedCard.classList.add('selected');
        }

        // Update status
        this.updateStatus(`Selected: ${book.title}`);

        console.log('Book selected:', book);
    }

    updateMobileStats(totalBooks) {
        const element = document.getElementById('totalBooks');
        if (element) {
            element.textContent = totalBooks;
        }
    }

    showMobileLoading(show) {
        const loading = document.getElementById('mobileLoading');
        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
        }
    }

    showEmptyState(show) {
        const emptyState = document.getElementById('emptyState');
        const bookList = document.getElementById('mobileBookList');

        if (emptyState && bookList) {
            if (show) {
                emptyState.style.display = 'flex';
                bookList.style.display = 'none';
            } else {
                emptyState.style.display = 'none';
                bookList.style.display = 'block';
            }
        }
    }

    showErrorToast(message) {
        const toast = document.getElementById('errorToast');
        if (toast) {
            toast.textContent = message;
            toast.classList.add('show');

            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    cleanup() {
        this.cleanupFunctions.forEach(cleanup => cleanup());
        this.api.clearCache();
    }
}

// ==================== AUTO-INITIALIZATION ====================



// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AndersonLibraryAPI, DesktopLibraryInterface, MobileLibraryInterface };
} else {
    window.AndersonLibraryAPI = AndersonLibraryAPI;
    window.DesktopLibraryInterface = DesktopLibraryInterface;
    window.MobileLibraryInterface = MobileLibraryInterface;
}

console.log('Anderson\'s Library API Client v2.0 - Design Standard v2.0 Loaded');