class I18n {
    constructor() {
        this.currentLanguage = this.detectLanguage();
        this.translations = {};
        this.loadTranslations();
    }

    detectLanguage() {
        // Check localStorage first
        const savedLang = localStorage.getItem('sakha-language');
        if (savedLang) {
            return savedLang;
        }

        // Check browser language
        const browserLang = navigator.language || navigator.userLanguage;
        const langCode = browserLang.split('-')[0];
        
        // Supported languages
        const supportedLangs = ['en', 'hi', 'fr', 'es'];
        if (supportedLangs.includes(langCode)) {
            return langCode;
        }

        // Default to English
        return 'en';
    }

    async loadTranslations() {
        try {
            const response = await fetch(`/static/languages/${this.currentLanguage}.json`);
            if (response.ok) {
                this.translations = await response.json();
                this.applyTranslations();
            } else {
                console.warn(`Failed to load ${this.currentLanguage} translations, falling back to English`);
                await this.loadFallbackTranslations();
            }
        } catch (error) {
            console.error('Error loading translations:', error);
            await this.loadFallbackTranslations();
        }
    }

    async loadFallbackTranslations() {
        try {
            const response = await fetch('/static/languages/en.json');
            this.translations = await response.json();
            this.applyTranslations();
        } catch (error) {
            console.error('Failed to load fallback translations:', error);
        }
    }

    applyTranslations() {
        // Update document title
        document.title = this.t('app.title');

        // Update elements with data-i18n attributes
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Update elements with data-i18n-html attributes (for HTML content)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            const translation = this.t(key);
            element.innerHTML = translation;
        });

        // Update elements with data-i18n-placeholder attributes
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            const translation = this.t(key);
            element.placeholder = translation;
        });

        // Update language selector
        this.updateLanguageSelector();
    }

    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                console.warn(`Translation key not found: ${key}`);
                return key; // Return the key if translation not found
            }
        }

        if (typeof value === 'string') {
            // Replace parameters in the translation
            return value.replace(/\{\{(\w+)\}\}/g, (match, param) => {
                return params[param] || match;
            });
        }

        return value;
    }

    async setLanguage(langCode) {
        if (this.currentLanguage === langCode) return;

        this.currentLanguage = langCode;
        localStorage.setItem('sakha-language', langCode);
        
        await this.loadTranslations();
        
        // Trigger custom event for other components
        document.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: langCode }
        }));
    }

    updateLanguageSelector() {
        const selector = document.getElementById('language-selector');
        if (selector) {
            selector.value = this.currentLanguage;
        }
    }

    getSupportedLanguages() {
        return [
            { code: 'en', name: 'English', flag: '🇺🇸' },
            { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
            { code: 'ta', name: 'தமிழ்', flag: '🇮🇳' },
            { code: 'te', name: 'తెలుగు', flag: '🇮🇳' },
            { code: 'pa', name: 'ਪੰਜਾਬੀ', flag: '🇮🇳' },
            { code: 'fr', name: 'Français', flag: '🇫🇷' },
            { code: 'es', name: 'Español', flag: '🇪🇸' }
        ];
    }
}

// Initialize i18n
window.i18n = new I18n();
