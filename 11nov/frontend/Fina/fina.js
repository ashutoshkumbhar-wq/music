class FinaRecomApp {
    constructor() {
        this.apiBase = 'http://localhost:3000/api';
        this.selectedMode = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkStatus();
    }

    bindEvents() {
        // Generate profile button
        document.getElementById('generate-profile-btn').addEventListener('click', () => {
            this.generateProfile();
        });

        // Mode selection
        document.querySelectorAll('[data-mode]').forEach(card => {
            card.addEventListener('click', () => {
                this.selectMode(card.dataset.mode);
            });
        });

        // Start recommendations button
        document.getElementById('start-recommendations-btn').addEventListener('click', () => {
            this.startRecommendations();
        });
    }

    async checkStatus() {
        try {
            const response = await fetch(`${this.apiBase}/fina-recom/status`);
            const data = await response.json();

            if (data.ok) {
                this.updateStatus(data.status);
                if (data.status.profile_exists) {
                    this.showProfileSection(data.status.profile_info);
                    this.showRecommendationModes();
                }
            } else {
                this.showError('Failed to check system status: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    updateStatus(status) {
        const statusContent = document.getElementById('status-content');
        
        if (status.profile_exists) {
            statusContent.innerHTML = `
                <div class="status-indicator">
                    <div class="status-dot active"></div>
                    <span style="color: #10b981; font-weight: 600;">System Ready</span>
                </div>
                <div style="margin-top: 12px; font-size: 13px;">
                    <p style="margin: 0;">Profile exists with <strong>${status.profile_info.top_artists_count}</strong> artists, <strong>${status.profile_info.top_tracks_count}</strong> tracks</p>
                </div>
            `;
        } else {
            statusContent.innerHTML = `
                <div class="status-indicator">
                    <div class="status-dot idle"></div>
                    <span style="color: #f59e0b; font-weight: 600;">Profile Not Found</span>
                </div>
                <div style="margin-top: 12px; font-size: 13px;">
                    <p style="margin: 0;">Generate your music profile to start getting recommendations</p>
                </div>
            `;
        }
    }

    showProfileSection(profileInfo) {
        const profileSection = document.getElementById('profile-section');
        const profileContent = document.getElementById('profile-content');
        
        profileContent.innerHTML = `
            <div class="stat-box">
                <div class="stat-value" style="color: #667eea;">${profileInfo.top_artists_count}</div>
                <div class="stat-label">Top Artists</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #10b981;">${profileInfo.top_tracks_count}</div>
                <div class="stat-label">Favorite Tracks</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #a855f7;">${profileInfo.genres_count}</div>
                <div class="stat-label">Genres</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #f97316;">${profileInfo.playlists_summary ? 'Yes' : 'No'}</div>
                <div class="stat-label">Playlist Data</div>
            </div>
        `;
        
        profileSection.classList.remove('hidden');
    }

    showRecommendationModes() {
        document.getElementById('recommendation-modes').classList.remove('hidden');
        document.getElementById('generate-profile-section').classList.add('hidden');
    }

    selectMode(mode) {
        // Remove previous selection
        document.querySelectorAll('[data-mode]').forEach(card => {
            card.classList.remove('selected');
        });

        // Select new mode
        const selectedCard = document.querySelector(`[data-mode="${mode}"]`);
        selectedCard.classList.add('selected');

        this.selectedMode = mode;
        document.getElementById('start-recommendations-btn').disabled = false;
    }

    async generateProfile() {
        this.showLoading('Generating your music profile...');
        
        try {
            const response = await fetch(`${this.apiBase}/fina-recom/generate-profile`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            this.hideLoading();

            if (data.ok) {
                this.showSuccess('Profile generated successfully!');
                this.showProfileSection(data.profile_summary);
                this.showRecommendationModes();
                this.updateStatus({ profile_exists: true, profile_info: data.profile_summary });
            } else {
                this.showError('Failed to generate profile: ' + data.error);
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error: ' + error.message);
        }
    }

    async startRecommendations() {
        if (!this.selectedMode) {
            this.showError('Please select a recommendation mode first');
            return;
        }

        this.showLoading('Starting smart recommendations...');
        
        try {
            const response = await fetch(`${this.apiBase}/fina-recom/start-recommendations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mode: this.selectedMode })
            });

            const data = await response.json();
            this.hideLoading();

            if (data.ok) {
                this.showSuccess(`Recommendations started in ${data.mode} mode!`);
                this.showCurrentStatus(data);
            } else {
                this.showError('Failed to start recommendations: ' + data.error);
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error: ' + error.message);
        }
    }

    showCurrentStatus(data) {
        const currentStatus = document.getElementById('current-status');
        const currentStatusContent = document.getElementById('current-status-content');
        
        currentStatusContent.innerHTML = `
            <div class="status-indicator" style="margin-bottom: 16px;">
                <div class="status-dot active"></div>
                <span style="color: #10b981; font-weight: 600;">Recommendations Active</span>
            </div>
            <div style="background: var(--surface-2); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 16px;">
                <h4 style="font-weight: 700; margin: 0 0 8px 0; color: var(--text-primary);">Mode: <span style="color: #667eea;">${data.mode}</span></h4>
                <p style="font-size: 13px; color: var(--text-secondary); margin: 0 0 12px 0;">${data.message}</p>
                <div style="font-size: 12px; color: var(--text-muted);">
                    The system is now building your personalized queue and will start playing music automatically.
                </div>
            </div>
        `;
        
        currentStatus.classList.remove('hidden');
    }

    showLoading(text) {
        document.getElementById('loading-text').textContent = text;
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.add('hidden');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        const container = document.getElementById('message-container');
        const messageEl = document.createElement('div');
        messageEl.className = `message-toast ${type}`;
        
        const icon = type === 'success' ? 
            '<svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>' :
            '<svg fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>';
        
        messageEl.innerHTML = `
            ${icon}
            <span>${message}</span>
        `;
        
        container.appendChild(messageEl);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 5000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FinaRecomApp();
});