// Officer Dashboard JavaScript

let currentOfficer = null;
let beneficiaries = [];
let selectedBeneficiary = null;

// Load officer data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadOfficerData();
    loadBeneficiaries();
    loadStats();
});

function loadOfficerData() {
    const userStr = localStorage.getItem('narmada_user');
    const token = localStorage.getItem('narmada_token');
    
    if (!userStr || !token) {
        window.location.href = '/signin?role=officer';
        return;
    }
    
    currentOfficer = JSON.parse(userStr);
    
    // Update UI with officer info
    document.getElementById('officer-name').textContent = currentOfficer.name || currentOfficer.username || 'Officer';
}

async function loadBeneficiaries() {
    try {
        const response = await fetch('/api/officer/beneficiaries', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load beneficiaries');
        }
        
        beneficiaries = await response.json();
        displayBeneficiaries(beneficiaries);
        
    } catch (error) {
        console.error('Load beneficiaries error:', error);
        document.getElementById('beneficiaries-list').innerHTML = `
            <div class="error-state">
                <div class="error-icon">&#10060;</div>
                <h3>Failed to load beneficiaries</h3>
                <p>Please try again later.</p>
            </div>
        `;
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load stats');
        }
        
        const stats = await response.json();
        document.getElementById('stat-total').textContent = stats.total_sessions || 0;
        document.getElementById('stat-pending').textContent = stats.pending_review || 0;
        document.getElementById('stat-approved').textContent = stats.approved || 0;
        document.getElementById('stat-recommendations').textContent = stats.total_recommendations || 0;
        
    } catch (error) {
        console.error('Load stats error:', error);
    }
}

function displayBeneficiaries(list) {
    const container = document.getElementById('beneficiaries-list');
    
    if (!list || list.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">&#128101;</div>
                <h3>No beneficiaries found</h3>
                <p>There are no beneficiaries matching your search criteria.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = list.map(b => `
        <div class="beneficiary-card" onclick="openBeneficiaryModal('${b.id || b.session_id}')">
            <div class="beneficiary-info">
                <div class="beneficiary-name">${b.name || b.citizen_name || 'Unknown'}</div>
                <div class="beneficiary-mobile">${b.mobile || b.citizen_mobile || '-'}</div>
                <div class="beneficiary-district">${b.district || '-'}</div>
            </div>
            <div class="beneficiary-status">
                <span class="status-badge status-${b.status || 'pending'}">${b.status || 'pending'}</span>
            </div>
            <div class="beneficiary-date">
                ${b.created ? new Date(b.created).toLocaleDateString() : '-'}
            </div>
        </div>
    `).join('');
}

function filterBeneficiaries() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;
    
    let filtered = beneficiaries;
    
    if (searchTerm) {
        filtered = filtered.filter(b => 
            (b.name || b.citizen_name || '').toLowerCase().includes(searchTerm) ||
            (b.mobile || b.citizen_mobile || '').includes(searchTerm)
        );
    }
    
    if (statusFilter !== 'all') {
        filtered = filtered.filter(b => (b.status || 'pending') === statusFilter);
    }
    
    displayBeneficiaries(filtered);
}

function openBeneficiaryModal(beneficiaryId) {
    selectedBeneficiary = beneficiaries.find(b => (b.id || b.session_id) === beneficiaryId);
    
    if (!selectedBeneficiary) return;
    
    const modalBody = document.getElementById('beneficiary-modal-body');
    modalBody.innerHTML = `
        <div class="detail-field">
            <label>Name</label>
            <p>${selectedBeneficiary.name || selectedBeneficiary.citizen_name || '-'}</p>
        </div>
        <div class="detail-field">
            <label>Mobile</label>
            <p>${selectedBeneficiary.mobile || selectedBeneficiary.citizen_mobile || '-'}</p>
        </div>
        <div class="detail-field">
            <label>District</label>
            <p>${selectedBeneficiary.district || '-'}</p>
        </div>
        <div class="detail-field">
            <label>Status</label>
            <p><span class="status-badge status-${selectedBeneficiary.status || 'pending'}">${selectedBeneficiary.status || 'pending'}</span></p>
        </div>
        <div class="detail-field">
            <label>Profile</label>
            <pre>${JSON.stringify(selectedBeneficiary.profile || {}, null, 2)}</pre>
        </div>
        <div class="detail-field">
            <label>Recommendations</label>
            <pre>${JSON.stringify(selectedBeneficiary.rec || {}, null, 2)}</pre>
        </div>
        <div class="detail-field">
            <label>Officer Notes</label>
            <textarea id="officer-notes" class="form-textarea" rows="4">${selectedBeneficiary.officer_notes || ''}</textarea>
        </div>
    `;
    
    document.getElementById('beneficiary-modal').hidden = false;
}

function closeBeneficiaryModal() {
    document.getElementById('beneficiary-modal').hidden = true;
    selectedBeneficiary = null;
}

async function approveBeneficiary() {
    if (!selectedBeneficiary) return;
    
    const notes = document.getElementById('officer-notes').value;
    
    try {
        const response = await fetch('/api/officer/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            },
            body: JSON.stringify({
                session_id: selectedBeneficiary.id || selectedBeneficiary.session_id,
                action: 'approve',
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to approve beneficiary');
        }
        
        alert('Beneficiary approved successfully.');
        closeBeneficiaryModal();
        loadBeneficiaries();
        loadStats();
        
    } catch (error) {
        console.error('Approve error:', error);
        alert('Failed to approve beneficiary. Please try again.');
    }
}

async function rejectBeneficiary() {
    if (!selectedBeneficiary) return;
    
    if (!confirm('Are you sure you want to reject this beneficiary?')) return;
    
    const notes = document.getElementById('officer-notes').value;
    
    try {
        const response = await fetch('/api/officer/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            },
            body: JSON.stringify({
                session_id: selectedBeneficiary.id || selectedBeneficiary.session_id,
                action: 'reject',
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to reject beneficiary');
        }
        
        alert('Beneficiary rejected.');
        closeBeneficiaryModal();
        loadBeneficiaries();
        loadStats();
        
    } catch (error) {
        console.error('Reject error:', error);
        alert('Failed to reject beneficiary. Please try again.');
    }
}

async function flagBeneficiary() {
    if (!selectedBeneficiary) return;
    
    const notes = document.getElementById('officer-notes').value;
    
    try {
        const response = await fetch('/api/officer/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('narmada_token')}`
            },
            body: JSON.stringify({
                session_id: selectedBeneficiary.id || selectedBeneficiary.session_id,
                action: 'flag',
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to flag beneficiary');
        }
        
        alert('Beneficiary flagged for review.');
        closeBeneficiaryModal();
        loadBeneficiaries();
        loadStats();
        
    } catch (error) {
        console.error('Flag error:', error);
        alert('Failed to flag beneficiary. Please try again.');
    }
}

function exportCSV() {
    if (!beneficiaries || beneficiaries.length === 0) {
        alert('No beneficiaries to export.');
        return;
    }
    
    const headers = ['Name', 'Mobile', 'District', 'Status', 'Created', 'Notes'];
    const rows = beneficiaries.map(b => [
        b.name || b.citizen_name || '',
        b.mobile || b.citizen_mobile || '',
        b.district || '',
        b.status || 'pending',
        b.created || '',
        b.officer_notes || ''
    ]);
    
    const csvContent = [headers, ...rows]
        .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
        .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `beneficiaries_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('narmada_token');
        localStorage.removeItem('narmada_user');
        window.location.href = '/';
    }
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('beneficiary-modal');
    if (e.target === modal) {
        closeBeneficiaryModal();
    }
});
