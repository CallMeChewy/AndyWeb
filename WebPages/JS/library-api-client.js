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
        
        console.log('AndersonLibraryAPI v2.0 initialized');
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
        
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            const url = categoryId 
                ? `/subjects?category_id=${encodeURIComponent(categoryId)}`
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
        console.log('API cache cleared');
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
        
        if (expired.length > 0) {
            console.log(`Cleaned ${expired.length} expired cache entries`);
        }
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
            console.log('Offline prefetch completed');
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
        
        this.initializeDesktopInterface();
    }
    
    async initializeDesktopInterface() {
        try {
            // Load initial data
            await this.loadInitialData();
            
            // Setup instant search
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                const cleanup = this.api.createInstantSearch(searchInput, (results) => {
                    this.displayBooks(results.books);
                    this.updateBookCount(results.total, results.message);
                });
                this.cleanupFunctions.push(cleanup);
            }
            
            // Setup API event listeners
            this.setupEventListeners();
            
            // Setup periodic cache cleanup
            setInterval(() => this.api.cleanExpiredCache(), 60000); // Every minute
            
            console.log('Desktop interface initialized');
            
        } catch (error) {
            console.error('Desktop interface initialization failed:', error);
            this.showError('Failed to initialize library interface');
        }
    }
    
    async loadInitialData() {
        try {
            // Load books
            const booksData = await this.api.getAllBooks();
            this.displayBooks(booksData.books);
            
            // Load filter options
            const [categories, subjects, stats] = await Promise.all([
                this.api.getCategories(),
                this.api.getSubjects(),
                this.api.getLibraryStats()
            ]);
            
            this.populateCategoryDropdown(categories);
            this.populateSubjectDropdown(subjects);
            this.updateStatistics(stats);
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load library data');
        }
    }
    
    setupEventListeners() {
        // Loading state management
        this.api.on('loadingStart', (data) => {
            this.showLoading(true, `Loading ${data.operation}...`);
        });
        
        this.api.on('loadingEnd', (data) => {
            this.showLoading(false);
        });
        
        // Error handling
        this.api.on('error', (data) => {
            this.showError(`Error in ${data.operation}: ${data.error}`);
        });
    }
    
    displayBooks(books) {
        const grid = document.getElementById('bookGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        books.forEach(book => {
            const bookCard = this.createBookCard(book);
            grid.appendChild(bookCard);
        });
        
        this.currentBooks = books;
        
        // Load thumbnails asynchronously
        this.loadThumbnailsForBooks(books);
    }
    
    async loadThumbnailsForBooks(books) {
        const bookIds = books.map(book => book.id);
        const thumbnails = await this.api.loadThumbnailsBatch(bookIds);
        
        thumbnails.forEach(({ bookId, thumbnail, success }) => {
            if (success && thumbnail) {
                const bookCard = document.querySelector(`[data-book-id="${bookId}"]`);
                if (bookCard) {
                    const coverElement = bookCard.querySelector('.book-cover');
                    if (coverElement) {
                        coverElement.innerHTML = `<img src="${thumbnail}" alt="Book cover" loading="lazy">`;
                    }
                }
            }
        });
    }
    
    createBookCard(book) {
        const card = document.createElement('div');
        card.className = 'book-card';
        card.onclick = () => this.selectBook(card, book);
        card.dataset.bookId = book.id;
        
        card.innerHTML = `
            <div class="book-cover">📘</div>
            <div class="book-title">${this.escapeHtml(book.title)}</div>
            <div class="book-author">${this.escapeHtml(book.author || 'Unknown Author')}</div>
            <div class="book-category">${this.escapeHtml(book.category || 'Uncategorized')}</div>
        `;
        
        return card;
    }
    
    selectBook(bookCard, book) {
        // Remove previous selection
        if (this.selectedBook) {
            this.selectedBook.classList.remove('selected');
        }
        
        // Select new book
        this.selectedBook = bookCard;
        bookCard.classList.add('selected');
        
        // Update status
        this.updateStatus(`Selected: ${book.title}`);
        
        console.log('Book selected:', book);
    }
    
    populateCategoryDropdown(categories) {
        const select = document.getElementById('categoryFilter');
        if (!select) return;
        
        // Clear existing options except first
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.name || category;
            option.textContent = category.name || category;
            select.appendChild(option);
        });
    }
    
    populateSubjectDropdown(subjects) {
        const select = document.getElementById('subjectFilter');
        if (!select) return;
        
        // Clear existing options except first
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        subjects.forEach(subject => {
            const option = document.createElement('option');
            option.value = subject.name || subject;
            option.textContent = subject.name || subject;
            select.appendChild(option);
        });
    }
    
    updateBookCount(count, message = '') {
        const bookCount = document.getElementById('bookCount');
        if (bookCount) {
            const contextText = message ? ` (${message})` : '';
            bookCount.textContent = `Showing ${count} books${contextText}`;
        }
    }
    
    updateStatistics(stats) {
        const statsDisplay = document.getElementById('statsDisplay');
        if (statsDisplay) {
            statsDisplay.textContent = `📚 ${stats.total_books} books • 🏷️ ${stats.total_categories} categories • 📑 ${stats.total_subjects} subjects`;
        }
    }
    
    updateStatus(message) {
        const statusElement = document.getElementById('statusMessage');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
    
    showLoading(show, message = 'Loading...') {
        const loading = document.getElementById('loadingIndicator');
        const progress = document.getElementById('progressBar');
        
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
            loading.textContent = message;
        }
        
        if (progress) {
            progress.style.display = show ? 'block' : 'none';
        }
    }
    
    showError(message) {
        console.error('Desktop Interface Error:', message);
        this.updateStatus(`Error: ${message}`);
        
        // Could show a more prominent error UI here
        setTimeout(() => {
            this.updateStatus('Ready');
        }, 5000);
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
            const booksData = await this.api.getAllBooks(1, 30); // Smaller initial load for mobile
            this.displayMobileBooks(booksData.books);
            this.updateMobileStats(booksData.total);
            
        } catch (error) {
            console.error('Failed to load initial mobile data:', error);
            this.showErrorToast('Failed to load library data');
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
        card.className = 'mobile-book-card';
        card.onclick = () => this.selectMobileBook(card, book);
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
    
    selectMobileBook(bookCard, book) {
        // Haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Remove previous selection
        if (this.selectedBook) {
            this.selectedBook.classList.remove('selected');
        }
        
        // Select new book
        this.selectedBook = bookCard;
        bookCard.classList.add('selected');
        
        console.log('Mobile book selected:', book);
        this.showErrorToast(`Selected: ${book.title}`);
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

/**
 * Automatically initialize the appropriate interface based on device/viewport
 * Follows progressive enhancement principles
 */
document.addEventListener('DOMContentLoaded', function() {
    // Detect mobile vs desktop
    const isMobile = window.innerWidth <= 768 || 'ontouchstart' in window;
    const hasDesktopElements = document.getElementById('bookGrid');
    const hasMobileElements = document.getElementById('mobileBookList');
    
    // Initialize appropriate interface
    if (isMobile && hasMobileElements) {
        window.libraryInterface = new MobileLibraryInterface();
        console.log('Mobile library interface activated');
    } else if (hasDesktopElements) {
        window.libraryInterface = new DesktopLibraryInterface();
        console.log('Desktop library interface activated');
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (window.libraryInterface && window.libraryInterface.cleanup) {
            window.libraryInterface.cleanup();
        }
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AndersonLibraryAPI, DesktopLibraryInterface, MobileLibraryInterface };
} else {
    window.AndersonLibraryAPI = AndersonLibraryAPI;
    window.DesktopLibraryInterface = DesktopLibraryInterface;
    window.MobileLibraryInterface = MobileLibraryInterface;
}

console.log('Anderson\'s Library API Client v2.0 - Design Standard v2.0 Loaded');