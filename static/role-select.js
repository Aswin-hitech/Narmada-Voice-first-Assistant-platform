// Role selection page JavaScript

const translations = {
    en: {
        role_select_heading: "How will you use NARMADA?",
        role_select_description: "Choose your role to continue. You can change this later.",
        role_citizen_title: "Citizen / Beneficiary",
        role_citizen_desc: "Discover your skills, explore training opportunities, and receive guidance in your language.",
        role_citizen_btn: "Continue as Citizen",
        role_officer_title: "Government Officer",
        role_officer_desc: "Review beneficiary assessments and manage authorized verification tasks.",
        role_officer_btn: "Continue as Officer"
    },
    hi: {
        role_select_heading: "आप NARMADA का उपयोग कैसे करेंगे?",
        role_select_description: "जारी रखने के लिए अपनी भूमिका चुनें। आप इसे बाद में बदल सकते हैं।",
        role_citizen_title: "नागरिक / लाभार्थी",
        role_citizen_desc: "अपने कौशल की खोज करें, प्रशिक्षण अवसरों का पता लगाएं, और अपनी भाषा में मार्गदर्शन प्राप्त करें।",
        role_citizen_btn: "नागरिक के रूप में जारी रखें",
        role_officer_title: "सरकारी अधिकारी",
        role_officer_desc: "लाभार्थी मूल्यांकनों की समीक्षा करें और अधिकृत सत्यापन कार्यों का प्रबंधन करें।",
        role_officer_btn: "अधिकारी के रूप में जारी रखें"
    }
};

let currentLang = localStorage.getItem('narmada_lang') || 'en';

function applyTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang] && translations[currentLang][key]) {
            el.textContent = translations[currentLang][key];
        }
    });
}

function selectRole(role) {
    localStorage.setItem('narmada_role', role);
    if (role === 'citizen') {
        window.location.href = '/signin?role=citizen';
    } else if (role === 'officer') {
        window.location.href = '/signin?role=officer';
    }
}

function goBack() {
    window.location.href = '/';
}

// Handle keyboard navigation for role cards
document.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
    
    const roleCards = document.querySelectorAll('.role-card');
    roleCards.forEach(card => {
        card.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });
});
