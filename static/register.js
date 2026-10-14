// Registration page JavaScript

const translations = {
    en: {
        register_heading: "Create Your Account",
        register_description: "Register to discover your skills and find your future",
        label_full_name: "Full Name",
        help_full_name: "As it appears on your official documents",
        label_mobile: "Mobile Number",
        help_mobile_register: "This will be your login ID",
        label_password: "Password",
        label_confirm_password: "Confirm Password",
        help_confirm_password: "Must match the password above",
        label_district: "District",
        help_district: "Optional - helps match local training",
        label_language: "Preferred Language",
        help_language: "We'll communicate in this language",
        label_occupation: "Current Occupation / Work",
        help_occupation: "Optional - helps us understand your background",
        consent_text: "I consent to share my information for skill assessment and training recommendations. I understand my data is protected under DPDP Act and I can delete my account anytime.",
        consent_help: "You must accept to continue",
        btn_register: "Create Account",
        have_account: "Already have an account?",
        signin_link: "Sign in here",
        error_missing_fields: "Please fill in all required fields",
        error_password_mismatch: "Passwords do not match",
        error_invalid_mobile: "Please enter a valid 10-digit mobile number",
        error_account_exists: "An account with this mobile number already exists",
        error_network: "Network error. Please try again.",
        error_weak_password: "Password must be at least 6 characters",
        creating_account: "Creating account..."
    },
    hi: {
        register_heading: "अपना खाता बनाएं",
        register_description: "अपने कौशल की खोज करने और अपना भविष्य खोजने के लिए पंजीकरण करें",
        label_full_name: "पूरा नाम",
        help_full_name: "जैसा कि आपके आधिकारिक दस्तावेजों पर दिखाई देता है",
        label_mobile: "मोबाइल नंबर",
        help_mobile_register: "यह आपका लॉगिन आईडी होगा",
        label_password: "पासवर्ड",
        label_confirm_password: "पासवर्ड की पुष्टि करें",
        help_confirm_password: "ऊपर दिए गए पासवर्ड से मेल खाना चाहिए",
        label_district: "जिला",
        help_district: "वैकल्पिक - स्थानीय प्रशिक्षण से मिलान करने में मदद करता है",
        label_language: "पसंदीदा भाषा",
        help_language: "हम इस भाषा में संवाद करेंगे",
        label_occupation: "वर्तमान पेशे / काम",
        help_occupation: "वैकल्पिक - हमें आपके पृष्ठभूमि को समझने में मदद करता है",
        consent_text: "मैं कौशल मूल्यांकन और प्रशिक्षण सिफारिशों के लिए अपनी जानकारी साझा करने की सहमति देता हूं। मैं समझता हूं कि मेरा डेटा DPDP अधिनियम के तहत सुरक्षित है और मैं किसी भी समय अपना खाता हटा सकता हूं।",
        consent_help: "जारी रखने के लिए आपको स्वीकार करना होगा",
        btn_register: "खाता बनाएं",
        have_account: "पहले से खाता है?",
        signin_link: "यहां साइन इन करें",
        error_missing_fields: "कृपया सभी आवश्यक फ़ील्ड भरें",
        error_password_mismatch: "पासवर्ड मेल नहीं खाते",
        error_invalid_mobile: "कृपया एक वैध 10-अंकीय मोबाइल नंबर दर्ज करें",
        error_account_exists: "इस मोबाइल नंबर के साथ एक खाता पहले से मौजूद है",
        error_network: "नेटवर्क त्रुटि। कृपया पुनः प्रयास करें।",
        error_weak_password: "पासवर्ड कम से कम 6 अक्षरों का होना चाहिए",
        creating_account: "खाता बनाया जा रहा है..."
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

function togglePassword(fieldId) {
    const passwordInput = document.getElementById(fieldId);
    const toggleBtn = passwordInput.parentElement.querySelector('.password-toggle-icon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleBtn.innerHTML = '&#128064;';
    } else {
        passwordInput.type = 'password';
        toggleBtn.innerHTML = '&#128065;';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    const errorDiv = document.getElementById('error-message');
    errorDiv.style.display = 'none';
}

async function handleRegister(event) {
    event.preventDefault();
    hideError();
    
    const submitBtn = document.getElementById('submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = translations[currentLang].creating_account || 'Creating account...';
    
    try {
        const full_name = document.getElementById('full_name').value.trim();
        const mobile = document.getElementById('mobile').value.trim();
        const password = document.getElementById('password').value;
        const confirm_password = document.getElementById('confirm_password').value;
        const district = document.getElementById('district').value.trim();
        const lang = document.getElementById('lang').value;
        const occupation = document.getElementById('occupation').value.trim();
        const consent = document.getElementById('consent').checked;
        
        // Validation
        if (!full_name || !mobile || !password || !confirm_password) {
            throw new Error(translations[currentLang].error_missing_fields || 'Please fill in all required fields');
        }
        
        if (!/^[0-9]{10}$/.test(mobile)) {
            throw new Error(translations[currentLang].error_invalid_mobile || 'Please enter a valid 10-digit mobile number');
        }
        
        if (password.length < 6) {
            throw new Error(translations[currentLang].error_weak_password || 'Password must be at least 6 characters');
        }
        
        if (password !== confirm_password) {
            throw new Error(translations[currentLang].error_password_mismatch || 'Passwords do not match');
        }
        
        if (!consent) {
            throw new Error('You must accept the privacy policy to continue');
        }
        
        const payload = {
            full_name,
            mobile,
            password,
            confirm_password,
            district,
            lang,
            occupation,
            consent
        };
        
        const response = await fetch('/api/citizen/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 409) {
                throw new Error(translations[currentLang].error_account_exists || 'An account with this mobile number already exists');
            }
            throw new Error(data.detail || data.error || translations[currentLang].error_network);
        }
        
        // Store token and user info
        localStorage.setItem('narmada_token', data.token);
        localStorage.setItem('narmada_user', JSON.stringify({
            role: data.role,
            name: data.name,
            mobile: data.mobile,
            district: district,
            lang: lang,
            occupation: occupation
        }));
        
        // Redirect to citizen dashboard
        window.location.href = '/citizen-dashboard';
        
    } catch (error) {
        showError(error.message || translations[currentLang].error_network || 'Network error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function goBack() {
    window.location.href = '/signin?role=citizen';
}

document.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
    
    // Set default language from localStorage
    const langSelect = document.getElementById('lang');
    if (langSelect && currentLang) {
        langSelect.value = currentLang;
    }
});
