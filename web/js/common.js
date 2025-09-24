/**
 * Common utilities for all enhanced pages
 */

// API Configuration
const API_BASE_URL = 'https://api.mapmystandards.ai/api';

// Loading overlay HTML
const loadingOverlay = `
    <div id="loadingOverlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; justify-content: center; align-items: center;">
        <div style="background: white; padding: 2rem; border-radius: 10px; text-align: center;">
            <div class="spinner" style="width: 50px; height: 50px; border: 3px solid #f3f3f3; border-top: 3px solid #2c5aa0; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 1rem;"></div>
            <p style="margin: 0; color: #333;">Loading...</p>
        </div>
    </div>
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
`;

// Error message HTML
function createErrorMessage(message, type = 'error') {
    const bgColor = type === 'error' ? '#fee2e2' : type === 'success' ? '#d1fae5' : '#dbeafe';
    const textColor = type === 'error' ? '#991b1b' : type === 'success' ? '#065f46' : '#1e3a8a';
    const icon = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
    
    return `
        <div class="alert-message" style="position: fixed; top: 20px; right: 20px; max-width: 400px; background: ${bgColor}; color: ${textColor}; padding: 1rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); z-index: 10000; display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.2rem;">${icon}</span>
            <p style="margin: 0; flex: 1;">${message}</p>
            <button onclick="this.parentElement.remove()" style="background: none; border: none; color: ${textColor}; font-size: 1.5rem; cursor: pointer; padding: 0; margin-left: 1rem;">&times;</button>
        </div>
    `;
}

// Show loading overlay
function showLoading(message = 'Loading...') {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        document.body.insertAdjacentHTML('beforeend', loadingOverlay);
        overlay = document.getElementById('loadingOverlay');
    }
    overlay.querySelector('p').textContent = message;
    overlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Show alert message
function showAlert(message, type = 'error', duration = 5000) {
    const alertHtml = createErrorMessage(message, type);
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    if (duration > 0) {
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert-message');
            if (alerts.length > 0) {
                alerts[alerts.length - 1].remove();
            }
        }, duration);
    }
}

// API request with error handling
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    if (!token && !endpoint.includes('auth')) {
        window.location.href = 'login-enhanced-v2.html';
        return null;
    }

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        }
    };

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, finalOptions);
        
        if (!response.ok) {
            if (response.status === 401) {
                showAlert('Session expired. Please login again.', 'error');
                setTimeout(() => {
                    localStorage.clear();
                    window.location.href = 'login-enhanced-v2.html';
                }, 2000);
                return null;
            }
            
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `HTTP ${response.status} error`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        showAlert(error.message || 'Network error. Please try again.', 'error');
        throw error;
    }
}

// Mobile menu toggle
function initMobileMenu() {
    const mobileMenuHtml = `
        <button id="mobileMenuToggle" style="display: none; position: fixed; top: 1rem; right: 1rem; z-index: 1000; background: white; border: 1px solid #ddd; padding: 0.5rem; border-radius: 5px; cursor: pointer;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
        </button>
    `;
    
    document.body.insertAdjacentHTML('beforeend', mobileMenuHtml);
    
    const toggle = document.getElementById('mobileMenuToggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (window.innerWidth <= 768) {
        toggle.style.display = 'block';
        if (navLinks) {
            navLinks.style.display = 'none';
        }
    }

    toggle.addEventListener('click', () => {
        if (navLinks) {
            navLinks.style.display = navLinks.style.display === 'none' ? 'flex' : 'none';
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            toggle.style.display = 'block';
            if (navLinks) {
                navLinks.style.display = 'none';
            }
        } else {
            toggle.style.display = 'none';
            if (navLinks) {
                navLinks.style.display = 'flex';
            }
        }
    });
}

// Format date helper
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

// Format file size helper
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize tooltips
function initTooltips() {
    const tooltipStyle = `
        <style>
            .tooltip-trigger {
                position: relative;
                cursor: help;
            }
            .tooltip-content {
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                background: #333;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                font-size: 0.875rem;
                white-space: nowrap;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.3s;
                margin-bottom: 0.5rem;
            }
            .tooltip-content::after {
                content: '';
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border: 5px solid transparent;
                border-top-color: #333;
            }
            .tooltip-trigger:hover .tooltip-content {
                opacity: 1;
            }
        </style>
    `;
    
    if (!document.querySelector('#tooltipStyles')) {
        const styleEl = document.createElement('div');
        styleEl.id = 'tooltipStyles';
        styleEl.innerHTML = tooltipStyle;
        document.head.appendChild(styleEl.firstElementChild);
    }
}

// Add progress bar
function createProgressBar(containerId, progress = 0) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const progressHtml = `
        <div class="progress-container" style="width: 100%; background: #e5e7eb; border-radius: 9999px; overflow: hidden; height: 8px;">
            <div class="progress-bar" style="width: ${progress}%; height: 100%; background: #2c5aa0; transition: width 0.3s ease;"></div>
        </div>
        <p style="text-align: center; margin-top: 0.5rem; color: #666; font-size: 0.875rem;">${progress}% Complete</p>
    `;
    
    container.innerHTML = progressHtml;
}

// Update progress bar
function updateProgressBar(containerId, progress) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const bar = container.querySelector('.progress-bar');
    const text = container.querySelector('p');
    
    if (bar) bar.style.width = `${progress}%`;
    if (text) text.textContent = `${progress}% Complete`;
}

// Logout function with confirmation
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        showLoading('Logging out...');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
        setTimeout(() => {
            window.location.href = '/login-enhanced-v2';
        }, 500);
    }
}

// Check authentication on page load
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const publicPages = ['login-enhanced-v2.html', 'login-enhanced.html', 'homepage-enhanced.html', 'forgot-password.html', 
                        'login-enhanced-v2', 'login-enhanced', 'homepage-enhanced', 'forgot-password', '', 'index.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (!token && !publicPages.includes(currentPage)) {
        window.location.href = '/login-enhanced-v2';
    }
}

// Initialize common features
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initMobileMenu();
    initTooltips();
    
    // Add global error handler
    window.addEventListener('unhandledrejection', event => {
        console.error('Unhandled promise rejection:', event.reason);
        showAlert('An unexpected error occurred. Please refresh the page.', 'error');
    });
});

// Export functions for use in other scripts
window.commonUtils = {
    showLoading,
    hideLoading,
    showAlert,
    apiRequest,
    formatDate,
    formatFileSize,
    debounce,
    createProgressBar,
    updateProgressBar,
    logout,
    checkAuth
};