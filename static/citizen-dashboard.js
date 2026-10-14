// Citizen Dashboard JavaScript

let currentUser = null;
let currentSession = null;
let isRecording = false;

// Load user data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUserData();
    loadProfile();
});

function loadUserData() {
    const userStr = localStorage.getItem('narmada_user');
    const token = localStorage.getItem('narmada_token');
    
    if (!userStr || !token) {
        window.location.href = '/signin?role=citizen';
        return;
    }
    
    currentUser = JSON.parse(userStr);
    
    // Update UI with user info
    document.getElementById('user-name').textContent = currentUser.name || 'Citizen';
    document.getElementById('welcome-heading').textContent = `Welcome, ${currentUser.name || 'Citizen'}!`;
}

function loadProfile() {
    if (!currentUser) return;
    
    document.getElementById('profile-name').textContent = currentUser.name || '-';
    document.getElementById('profile-mobile').textContent = currentUser.mobile || '-';
    document.getElementById('profile-district').textContent = currentUser.district || '-';
    document.getElementById('profile-lang').textContent = currentUser.lang || 'English';
    document.getElementById('profile-occupation').textContent = currentUser.occupation || '-';
    
    // Set language selector
    const langSelect = document.getElementById('settings-lang');
    if (langSelect && currentUser.lang) {
        langSelect.value = currentUser.lang;
    }
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active');
    });

    // Remove active class from all nav cards
    document.querySelectorAll('.nav-card').forEach(card => {
        card.classList.remove('active');
    });

    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('active');
    }

    // Add active class to the nav card that was clicked
    const cards = document.querySelectorAll('.nav-card');
    const sectionMap = ['profile','discover','recommendations','progress','mentor','passport','settings'];
    const idx = sectionMap.indexOf(sectionName);
    if (idx >= 0 && cards[idx]) {
        cards[idx].classList.add('active');
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Start session if not exists
        if (!currentSession) {
            await startSession();
        }
        
        // Send message to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            },
            body: JSON.stringify({
                sid: currentSession,
                message: message
            })
        });
        
        hideTypingIndicator();
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        addMessageToChat('bot', data.reply || 'I received your message.');
        
    } catch (error) {
        hideTypingIndicator();
        addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.');
        console.error('Chat error:', error);
    }
}

async function startSession() {
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            },
            body: JSON.stringify({
                lang: currentUser.lang || 'en',
                consent: true
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to start session');
        }
        
        const data = await response.json();
        currentSession = data.sid;
        
    } catch (error) {
        console.error('Session start error:', error);
    }
}

function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const sender = role === 'user' ? 'You' : 'NARMADA Assistant';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>${sender}:</strong>
            <p>${content}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <p><em>NARMADA Assistant is typing...</em></p>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function toggleVoice() {
    // Voice recording functionality - placeholder for now
    const micBtn = document.getElementById('mic-btn');
    const micIcon = document.getElementById('mic-icon');
    
    if (!isRecording) {
        isRecording = true;
        micIcon.innerHTML = '&#128308;'; // Red circle
        micBtn.classList.add('recording');
        alert('Voice recording feature coming soon. Please use text input for now.');
    } else {
        isRecording = false;
        micIcon.innerHTML = '&#127908;'; // Microphone
        micBtn.classList.remove('recording');
    }
}

async function generateRecommendations() {
    if (!currentSession) {
        alert('Please complete your skill discovery conversation first.');
        return;
    }
    
    const recommendationsContent = document.getElementById('recommendations-content');
    recommendationsContent.innerHTML = '<div class="loading-state"><p>Generating recommendations...</p></div>';
    
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            },
            body: JSON.stringify({
                sid: currentSession
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate recommendations');
        }
        
        const data = await response.json();
        displayRecommendations(data);
        
    } catch (error) {
        recommendationsContent.innerHTML = `
            <div class="error-state">
                <div class="error-icon">&#10060;</div>
                <h3>Failed to generate recommendations</h3>
                <p>Please try again later.</p>
            </div>
        `;
        console.error('Recommendations error:', error);
    }
}

function displayRecommendations(data) {
    const recommendationsContent = document.getElementById('recommendations-content');
    
    if (!data || !data.qualification) {
        recommendationsContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">&#127891;</div>
                <h3>No recommendations available</h3>
                <p>Complete more of your skill discovery conversation to get personalized recommendations.</p>
            </div>
        `;
        return;
    }
    
    recommendationsContent.innerHTML = `
        <div class="recommendation-card">
            <h3>${data.qualification.title || 'Recommended Qualification'}</h3>
            <div class="rec-field">
                <label>Qualification Pack Code</label>
                <p>${data.qualification.code || '-'}</p>
            </div>
            <div class="rec-field">
                <label>Skill Level</label>
                <p>${data.qualification.level || '-'}</p>
            </div>
            <div class="rec-field">
                <label>Training Modules</label>
                <p>${data.qualification.modules || '-'}</p>
            </div>
            <div class="rec-field">
                <label>Wage Potential</label>
                <p>${data.qualification.wage_potential || '-'}</p>
            </div>
            <div class="rec-field">
                <label>PM-AJAY Benefits</label>
                <p>${data.qualification.pm_ajay_benefit || '-'}</p>
            </div>
            <div class="rec-field">
                <label>Next Steps</label>
                <p>${data.qualification.next_step || '-'}</p>
            </div>
        </div>
    `;
}

function editProfile() {
    alert('Profile editing feature coming soon.');
}

function changeLanguage(lang) {
    localStorage.setItem('narmada_lang', lang);
    if (currentUser) {
        currentUser.lang = lang;
        localStorage.setItem('narmada_user', JSON.stringify(currentUser));
    }
    alert(`Language changed to ${lang}. Please refresh the page to apply.`);
}

function adjustFontSize(direction) {
    const currentSize = parseInt(localStorage.getItem('font_size') || '16');
    let newSize = currentSize;
    
    if (direction === -1) newSize = Math.max(12, currentSize - 2);
    else if (direction === 1) newSize = Math.min(24, currentSize + 2);
    else newSize = 16;
    
    localStorage.setItem('font_size', newSize);
    document.documentElement.style.fontSize = `${newSize}px`;
}

function deleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        alert('Account deletion feature coming soon. Please contact support.');
    }
}

function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('narmada_token');
        localStorage.removeItem('narmada_user');
        window.location.href = '/';
    }
}

// Handle keyboard navigation for nav cards
document.addEventListener('DOMContentLoaded', () => {
    const navCards = document.querySelectorAll('.nav-card');
    navCards.forEach(card => {
        card.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });
});
