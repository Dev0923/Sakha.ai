class SakhaAI {
    constructor() {
        this.isConnected = false;
        this.initializeElements();
        this.attachEventListeners();
        this.checkHealth();
        this.setupAutoResize();
        this.setupLanguageSupport();
    }

    initializeElements() {
        // Main elements
        this.welcomeMessage = document.getElementById('welcome-message');
        this.chatContainer = document.getElementById('chat-container');
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.loadingOverlay = document.getElementById('loading-overlay');
        
        // Status elements
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        
        // Crisis modal elements
        this.crisisModal = document.getElementById('crisis-modal');
        this.closeCrisisModal = document.getElementById('close-crisis-modal');
        
        // Mode selector elements
        this.modeButtons = document.querySelectorAll('.mode-btn');
        this.currentMode = 'normal';
        
        // Language selector
        this.languageSelector = document.getElementById('language-selector');
        
        // Crisis button
        this.crisisButton = document.getElementById('crisis-button');
    }

    attachEventListeners() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input validation
        this.messageInput.addEventListener('input', () => {
            const hasText = this.messageInput.value.trim().length > 0;
            this.sendButton.disabled = !hasText || !this.isConnected;
        });

        // Crisis modal
        this.closeCrisisModal.addEventListener('click', () => {
            this.crisisModal.classList.remove('show');
        });

        // Close modal on backdrop click
        this.crisisModal.addEventListener('click', (e) => {
            if (e.target === this.crisisModal) {
                this.crisisModal.classList.remove('show');
            }
        });

        // Mode selector events
        this.modeButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.setMode(button.dataset.mode);
            });
        });

        // Language selector events
        if (this.languageSelector) {
            this.languageSelector.addEventListener('change', (e) => {
                this.changeLanguage(e.target.value);
            });
        }

        // Crisis button events
        if (this.crisisButton) {
            this.crisisButton.addEventListener('click', () => {
                this.showCrisisModal();
            });
        }
    }

    setupLanguageSupport() {
        // Listen for language changes
        document.addEventListener('languageChanged', (e) => {
            this.updatePlaceholders();
        });
        
        // Initial placeholder update
        this.updatePlaceholders();
    }

    async changeLanguage(langCode) {
        if (window.i18n) {
            await window.i18n.setLanguage(langCode);
        }
    }

    updatePlaceholders() {
        if (window.i18n && this.messageInput) {
            const placeholderKey = `app.placeholders.${this.currentMode}`;
            this.messageInput.placeholder = window.i18n.t(placeholderKey);
        }
    }

    setMode(mode) {
        this.currentMode = mode;
        
        // Update UI
        this.modeButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        // Update placeholder based on mode
        this.updatePlaceholders();
    }

    setupAutoResize() {
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateConnectionStatus(true, data.ai_enabled);
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected, aiEnabled = false) {
        this.isConnected = connected;
        
        if (connected) {
            this.statusDot.classList.remove('disconnected');
            const statusKey = aiEnabled ? 'app.status.aiReady' : 'app.status.connectedLimited';
            this.statusText.textContent = window.i18n ? window.i18n.t(statusKey) : (aiEnabled ? 'AI Ready' : 'Connected (Limited AI)');
        } else {
            this.statusDot.classList.add('disconnected');
            this.statusText.textContent = window.i18n ? window.i18n.t('app.status.disconnected') : 'Disconnected';
        }
        
        this.sendButton.disabled = !connected || this.messageInput.value.trim().length === 0;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;

        // Show chat container if this is the first message
        if (this.welcomeMessage.style.display !== 'none') {
            this.welcomeMessage.style.display = 'none';
            this.chatContainer.style.display = 'flex';
        }

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.sendButton.disabled = true;

        // Show loading
        this.showLoading();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    mode: this.currentMode,
                    language: window.i18n ? window.i18n.currentLanguage : 'en'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Hide loading
            this.hideLoading();
            
            // Add assistant response
            this.addMessage(data.response, 'assistant');
            
            // Check for crisis
            if (data.crisis_detected) {
                this.showCrisisModal();
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideLoading();
            const errorMessage = window.i18n ? window.i18n.t('app.error') : 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment. If the problem persists, please refresh the page.';
            this.addMessage(errorMessage, 'assistant', true);
        }
    }

    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-heart"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isError) {
            messageContent.style.background = '#fef2f2';
            messageContent.style.color = '#dc2626';
            messageContent.style.borderLeft = '4px solid #dc2626';
        }
        
        // Process markdown-like formatting for assistant messages
        if (sender === 'assistant') {
            messageContent.innerHTML = this.formatMessage(content);
        } else {
            messageContent.textContent = content;
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Basic markdown-like formatting
        let formatted = content
            // Convert **text** to bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Convert *text* to italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Convert line breaks
            .replace(/\n/g, '<br>')
            // Convert URLs to links
            .replace(/https?:\/\/[^\s<>]+/g, '<a href="$&" target="_blank" rel="noopener noreferrer">$&</a>')
            // Convert horizontal rules
            .replace(/---/g, '<hr>')
            // Convert headers
            .replace(/^### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^## (.*$)/gm, '<h3>$1</h3>')
            // Convert bullet points
            .replace(/^• (.*$)/gm, '<li>$1</li>')
            .replace(/^- (.*$)/gm, '<li>$1</li>');
        
        // Wrap consecutive <li> elements in <ul>
        formatted = formatted.replace(/(<li>.*<\/li>)(\s*<li>.*<\/li>)*/g, '<ul>$&</ul>');
        
        return formatted;
    }

    showLoading() {
        this.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }

    showCrisisModal() {
        this.crisisModal.classList.add('show');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }, 100);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SakhaAI();
});

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}