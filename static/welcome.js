// Welcome page JavaScript

// Translations for all 11 languages
const translations = {
    en: {
        welcome_heading: "Discover Your Skills. Find Your Future.",
        welcome_description: "NARMADA helps you discover your natural abilities, explore training opportunities, and find the right livelihood path - all in your language, through voice and conversation.",
        feature_voice_title: "Voice-First",
        feature_voice_desc: "Speak in your language, no typing needed",
        feature_skills_title: "Skill Discovery",
        feature_skills_desc: "AI-powered assessment of your abilities",
        feature_training_title: "Training Matches",
        feature_training_desc: "NSQF-certified qualification packs",
        feature_mentor_title: "Voice Mentor",
        feature_mentor_desc: "Weekly guidance and support",
        btn_get_started: "Get Started",
        btn_sign_in: "Sign In",
        info_livelihood_title: "Livelihood Mapping",
        info_livelihood_desc: "Tell us about your daily work, tools you use, and experience. Our AI will help identify your skills and match you with relevant training programs.",
        info_privacy_title: "Privacy & Security",
        info_privacy_desc: "Your data is protected. We follow DPDP Act guidelines. You control what information you share and can delete your account anytime.",
        info_accessibility_title: "Accessibility",
        info_accessibility_desc: "Designed for everyone - large buttons, voice assistance, high contrast mode, and simple language. Works on mobile and desktop.",
        footer_about_title: "About NARMADA",
        footer_about_desc: "A voice-first AI platform for livelihood mapping and skill development, supporting PM-AJAY scheme beneficiaries across India.",
        footer_support_title: "Support",
        footer_help: "Help & FAQ",
        footer_contact: "Contact Us",
        footer_accessibility: "Accessibility",
        footer_legal_title: "Legal",
        footer_privacy: "Privacy Policy",
        footer_terms: "Terms of Service",
        footer_dpdp: "DPDP Notice",
        footer_copyright: "NARMADA Platform. Built for public service."
    },
    hi: {
        welcome_heading: "अपने कौशल की खोज करें। अपना भविष्य खोजें।",
        welcome_description: "NARMADA आपकी प्राकृतिक क्षमताओं की खोज करने, प्रशिक्षण अवसरों का पता लगाने और सही आजीविका पथ खोजने में आपकी मदद करता है - सब आपकी भाषा में, आवाज और बातचीत के माध्यम से।",
        feature_voice_title: "आवाज-प्रथम",
        feature_voice_desc: "अपनी भाषा में बोलें, टाइपिंग की आवश्यकता नहीं",
        feature_skills_title: "कौशल खोज",
        feature_skills_desc: "आपकी क्षमताओं का AI-संचालित मूल्यांकन",
        feature_training_title: "प्रशिक्षण मैच",
        feature_training_desc: "NSQF-प्रमाणित योग्यता पैक",
        feature_mentor_title: "आवाज मेंटर",
        feature_mentor_desc: "साप्ताहिक मार्गदर्शन और सहायता",
        btn_get_started: "शुरू करें",
        btn_sign_in: "साइन इन",
        info_livelihood_title: "आजीविका मैपिंग",
        info_livelihood_desc: "हमें अपने दैनिक कार्य, उपयोग किए जाने वाले उपकरणों और अनुभव के बारे में बताएं। हमारा AI आपके कौशल की पहचान करने और आपको प्रासंगिक प्रशिक्षण कार्यक्रमों से मैच करने में मदद करेगा।",
        info_privacy_title: "गोपनीयता और सुरक्षा",
        info_privacy_desc: "आपका डेटा सुरक्षित है। हम DPDP अधिनियम दिशानिर्देशों का पालन करते हैं। आप नियंत्रित करते हैं कि आप कौन सी जानकारी साझा करते हैं और किसी भी समय अपना खाता हटा सकते हैं।",
        info_accessibility_title: "सुलभता",
        info_accessibility_desc: "सभी के लिए डिज़ाइन किया गया - बड़े बटन, आवाज सहायता, उच्च कंट्रास्ट मोड, और सरल भाषा। मोबाइल और डेस्कटॉप पर काम करता है।",
        footer_about_title: "NARMADA के बारे में",
        footer_about_desc: "आजीविका मैपिंग और कौशल विकास के लिए एक आवाज-प्रथम AI प्लेटफॉर्म, भारत भर में PM-AJAY योजना लाभार्थियों का समर्थन।",
        footer_support_title: "सहायता",
        footer_help: "सहायता और FAQ",
        footer_contact: "संपर्क करें",
        footer_accessibility: "सुलभता",
        footer_legal_title: "कानूनी",
        footer_privacy: "गोपनीयता नीति",
        footer_terms: "सेवा की शर्तें",
        footer_dpdp: "DPDP नोटिस",
        footer_copyright: "NARMADA प्लेटफॉर्म। सार्वजनिक सेवा के लिए निर्मित।"
    }
    // Additional languages will be added similarly
};

// Load saved language or default to English
let currentLang = localStorage.getItem('narmada_lang') || 'en';

function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('narmada_lang', lang);
    applyTranslations();
}

function applyTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang] && translations[currentLang][key]) {
            el.textContent = translations[currentLang][key];
        }
    });
    
    // Update language selector
    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
        langSelect.value = currentLang;
    }
}

function navigateToRoleSelection() {
    window.location.href = '/role-select';
}

function navigateToSignIn() {
    window.location.href = '/signin';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
});
