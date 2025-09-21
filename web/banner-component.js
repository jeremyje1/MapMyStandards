// Reusable banner component for MapMyStandards
// This script creates and manages the informational banner across all pages

class MapMyStandardsBanner {
    constructor() {
        this.bannerId = 'mms-info-banner';
        this.storageKey = 'mms-banner-dismissed';
        this.init();
    }

    init() {
        // Check if banner should be shown
        if (this.shouldShowBanner()) {
            this.createBanner();
            this.attachEventListeners();
        }
    }

    shouldShowBanner() {
        // Check if user has dismissed the banner
        const dismissed = localStorage.getItem(this.storageKey);
        const dismissedTime = dismissed ? parseInt(dismissed) : 0;
        const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
        
        // Show banner again after 7 days
        return !dismissed || daysSinceDismissed > 7;
    }

    createBanner() {
        // Create banner HTML
        const bannerHTML = `
            <div id="${this.bannerId}" class="mms-banner">
                <div class="mms-banner-content">
                    <div class="mms-banner-text">
                        <span class="mms-banner-icon">🎓</span>
                        <span class="mms-banner-message">
                            <strong>New here?</strong> Learn how to select standards, map evidence, review risk, and generate narratives.
                        </span>
                        <span class="mms-banner-links">
                            <a href="/documentation" class="mms-banner-link">User Guide</a>
                            <span class="mms-banner-separator">·</span>
                            <a href="/faq" class="mms-banner-link">FAQ</a>
                        </span>
                    </div>
                    <div class="mms-banner-actions">
                        <button class="mms-banner-button mms-banner-tutorial" onclick="window.location.href='/tutorial'">
                            Show Tutorial
                        </button>
                        <button class="mms-banner-button mms-banner-dismiss" aria-label="Dismiss banner">
                            Dismiss
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add CSS styles
        const styles = `
            <style>
                .mms-banner {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
                    color: white;
                    padding: 12px 20px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    animation: slideDown 0.3s ease-out;
                }

                @keyframes slideDown {
                    from {
                        transform: translateY(-100%);
                    }
                    to {
                        transform: translateY(0);
                    }
                }

                .mms-banner-content {
                    max-width: 1200px;
                    margin: 0 auto;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 20px;
                    flex-wrap: wrap;
                }

                .mms-banner-text {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex: 1;
                }

                .mms-banner-icon {
                    font-size: 24px;
                }

                .mms-banner-message {
                    font-size: 14px;
                    line-height: 1.5;
                }

                .mms-banner-links {
                    margin-left: 10px;
                }

                .mms-banner-link {
                    color: #93bbfc;
                    text-decoration: none;
                    font-weight: 500;
                    transition: color 0.2s;
                }

                .mms-banner-link:hover {
                    color: white;
                    text-decoration: underline;
                }

                .mms-banner-separator {
                    margin: 0 8px;
                    color: #93bbfc;
                }

                .mms-banner-actions {
                    display: flex;
                    gap: 10px;
                }

                .mms-banner-button {
                    padding: 6px 16px;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .mms-banner-tutorial {
                    background: white;
                    color: #1e40af;
                }

                .mms-banner-tutorial:hover {
                    background: #f0f4ff;
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }

                .mms-banner-dismiss {
                    background: transparent;
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }

                .mms-banner-dismiss:hover {
                    background: rgba(255, 255, 255, 0.1);
                }

                /* Adjust body padding to account for banner */
                body.has-banner {
                    padding-top: 60px;
                }

                /* Mobile responsiveness */
                @media (max-width: 768px) {
                    .mms-banner-content {
                        flex-direction: column;
                        align-items: stretch;
                        gap: 15px;
                    }

                    .mms-banner-text {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 8px;
                    }

                    .mms-banner-links {
                        margin-left: 0;
                    }

                    .mms-banner-actions {
                        justify-content: stretch;
                    }

                    .mms-banner-button {
                        flex: 1;
                    }

                    body.has-banner {
                        padding-top: 120px;
                    }
                }
            </style>
        `;

        // Insert styles and banner into page
        document.head.insertAdjacentHTML('beforeend', styles);
        document.body.insertAdjacentHTML('afterbegin', bannerHTML);
        document.body.classList.add('has-banner');
    }

    attachEventListeners() {
        // Dismiss button
        const dismissBtn = document.querySelector('.mms-banner-dismiss');
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => this.dismissBanner());
        }

        // Tutorial button tracking
        const tutorialBtn = document.querySelector('.mms-banner-tutorial');
        if (tutorialBtn) {
            tutorialBtn.addEventListener('click', () => {
                // Track tutorial click
                this.trackEvent('banner_tutorial_clicked');
            });
        }

        // Link tracking
        document.querySelectorAll('.mms-banner-link').forEach(link => {
            link.addEventListener('click', (e) => {
                this.trackEvent('banner_link_clicked', { link: e.target.textContent });
            });
        });
    }

    dismissBanner() {
        const banner = document.getElementById(this.bannerId);
        if (banner) {
            // Animate out
            banner.style.animation = 'slideUp 0.3s ease-in';
            setTimeout(() => {
                banner.remove();
                document.body.classList.remove('has-banner');
            }, 300);

            // Store dismissal time
            localStorage.setItem(this.storageKey, Date.now().toString());
            this.trackEvent('banner_dismissed');
        }
    }

    trackEvent(eventName, data = {}) {
        // Track banner interactions (can be connected to analytics)
        console.log('Banner event:', eventName, data);
        
        // If analytics service is available, send event
        if (typeof window.analytics !== 'undefined' && window.analytics.track) {
            window.analytics.track(eventName, {
                ...data,
                banner_id: this.bannerId,
                page: window.location.pathname
            });
        }
    }
}

// Initialize banner when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new MapMyStandardsBanner();
    });
} else {
    new MapMyStandardsBanner();
}

// Export for use in other scripts
window.MapMyStandardsBanner = MapMyStandardsBanner;