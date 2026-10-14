// Sign-in page JavaScript

const translations = {
    en: {
        signin_heading: "Sign In to NARMADA",
        signin_description: "Enter your credentials to access your account",
        label_mobile: "Mobile Number",
        help_mobile: "Enter your registered 10-digit mobile number",
        label_username: "Username",
        help_username: "Enter your officer username",
        label_password: "Password",
        help_password: "Password must be at least 6 characters",
        btn_sign_in: "Sign In",
        no_account: "Don't have an account?",
        register_link: "Register here",
        forgot_password: "Forgot password?",
        error_missing_fields: "Please fill in all required fields",
        error_invalid_credentials: "Invalid credentials. Please check your mobile/username and password.",
        error_network: "Network error. Please try again.",
        signing_in: "Signing in..."
    },
    hi: {
        signin_heading: "NARMADA में साइन इन करें",
        signin_description: "अपने खाते तक पहुंचने के लिए अपने क्रेडेंशियल दर्ज करें",
        label_mobile: "मोबाइल नंबर",
        help_mobile: "अपना पंजीकृत 10-अंकीय मोबाइल नंबर दर्ज करें",
        label_username: "उपयोगकर्ता नाम",
        help_username: "अपना अधिकारी उपयोगकर्ता नाम दर्ज करें",
        label_password: "पासवर्ड",
        help_password: "पासवर्ड कम से कम 6 अक्षरों का होना चाहिए",
        btn_sign_in: "साइन इन",
        no_account: "खाता नहीं है?",
        register_link: "यहां पंजीकरण करें",
        forgot_password: "पासवर्ड भूल गए?",
        error_missing_fields: "कृपया सभी आवश्यक फ़ील्ड भरें",
        error_invalid_credentials: "अमान्य क्रेडेंशियल। कृपया अपना मोबाइल/उपयोगकर्ता नाम और पासवर्ड जांचें।",
        error_network: "नेटवर्क त्रुटि। कृपया पुनः प्रयास करें।",
        signing_in: "साइन इन हो रहा है..."
    }
};

let currentLang = localStorage.getItem('narmada_lang') || 'en';
let currentRole = 'citizen';

function applyTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang] && translations[currentLang][key]) {
            el.textContent = translations[currentLang][key];
        }
    });
}

function setupForRole() {
    const urlParams = new URLSearchParams(window.location.search);
    currentRole = urlParams.get('role') || localStorage.getItem('narmada_role') || 'citizen';
    
    const roleBadge = document.getElementById('role-badge');
    const roleIcon = document.getElementById('role-icon');
    const roleLabel = document.getElementById('role-label');
    const mobileGroup = document.getElementById('mobile-group');
    const usernameGroup = document.getElementById('username-group');
    const citizenRegisterLink = document.getElementById('citizen-register-link');
    const officerForgotLink = document.getElementById('officer-forgot-link');
    
    if (currentRole === 'officer') {
        roleIcon.innerHTML = '&#128188;';
        roleLabel.textContent = 'Officer';
        mobileGroup.style.display = 'none';
        usernameGroup.style.display = 'block';
        usernameGroup.querySelector('input').required = true;
        mobileGroup.querySelector('input').required = false;
        citizenRegisterLink.style.display = 'none';
        officerForgotLink.style.display = 'inline';
    } else {
        roleIcon.innerHTML = '&#128100;';
        roleLabel.textContent = 'Citizen';
        mobileGroup.style.display = 'block';
        usernameGroup.style.display = 'none';
        mobileGroup.querySelector('input').required = true;
        usernameGroup.querySelector('input').required = false;
        citizenRegisterLink.style.display = 'inline';
        officerForgotLink.style.display = 'none';
    }
}

function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('password-toggle-icon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.innerHTML = '&#128064;';
    } else {
        passwordInput.type = 'password';
        toggleIcon.innerHTML = '&#128065;';
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

async function handleSignIn(event) {
    event.preventDefault();
    hideError();
    
    const submitBtn = document.getElementById('submit-btn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = translations[currentLang].signing_in || 'Signing in...';
    
    try {
        let endpoint, payload;
        
        if (currentRole === 'officer') {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                throw new Error(translations[currentLang].error_missing_fields || 'Please fill in all required fields');
            }
            
            endpoint = '/api/officer/login';
            payload = { username, password };
        } else {
            const mobile = document.getElementById('mobile').value.trim();
            const password = document.getElementById('password').value;
            
            if (!mobile || !password) {
                throw new Error(translations[currentLang].error_missing_fields || 'Please fill in all required fields');
            }
            
            if (!/^[0-9]{10}$/.test(mobile)) {
                throw new Error('Invalid mobile number. Please enter a valid 10-digit number.');
            }
            
            endpoint = '/api/citizen/login';
            payload = { mobile, password };
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.error || translations[currentLang].error_invalid_credentials);
        }
        
        // Store token and user info
        localStorage.setItem('narmada_token', data.token);
        localStorage.setItem('narmada_user', JSON.stringify({
            role: data.role,
            name: data.name || data.username,
            mobile: data.mobile,
            username: data.username,
            district: data.district || '',
            lang: data.lang || 'en',
            occupation: data.occupation || ''
        }));
        
        // Redirect to appropriate dashboard
        if (data.role === 'officer') {
            window.location.href = '/officer-dashboard';
        } else {
            window.location.href = '/citizen-dashboard';
        }
        
    } catch (error) {
        showError(error.message || translations[currentLang].error_network || 'Network error. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function goBack() {
    window.location.href = '/role-select';
}

document.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
    setupForRole();
});
