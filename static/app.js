/**
 * NARMADA - Native-language Aptitude Recognition & Mentoring Architecture
 * Production-Ready Client-Side Controller
 */

// Global State
let currentSessionId = null;
let currentLanguage = "en-IN";
let currentProfile = {};
let currentRecommendation = null;
let lastSpokenText = "";
let speechSpeed = 1.0;
let baseFontSize = 16;
let isHighContrast = false;

// Audio & Web Speech State
let recognition = null;
let isRecording = false;
let audioContext = null;
let analyserNode = null;
let animationFrameId = null;
let micMediaStream = null;

// Presets Data for Instant Demonstration
const DEMO_PRESETS = {
    "dairy-ta": {
        lang: "ta-IN",
        message: "நான் இரண்டு எருமை மாடுகளை வளர்த்து தினமும் பால் கறந்து கூட்டுறவு சங்கத்திற்கு விற்கிறேன். 5 வருட அனுபவம் உண்டு. பால் கேன்கள், கரவை பாத்திரங்கள் பயன்படுத்துகிறேன்."
    },
    "tailor-hi": {
        lang: "hi-IN",
        message: "मैं पिछले 4 साल से घर पर सिलाई मशीन से महिलाओं के ब्लाउज, सलवार सूट और कपड़े सिलती हूँ। मेरे पास सिलाई मशीन, कैंची और इंची टेप है।"
    },
    "electrician-te": {
        lang: "te-IN",
        message: "నేను గత 3 సంవత్సరాలుగా ఇళ్లలో డొమెస్టిక్ వైరింగ్, స్విచ్ బోర్డులు, ఫ్యాన్లు మరియు చిన్న ఉపకరణాలు రిపేర్ చేస్తున్నాను. టెస్టర్, మల్టీమీటర్, ప్లయర్ ఉపయోగిస్తాను."
    },
    "food-bn": {
        lang: "bn-IN",
        message: "আমি ৩ বছর ধরে বাড়িতে আম ও লেবুর আচার এবং পাঁপড় তৈরি করে স্থানীয় বাজারে বিক্রি করি। সিলিং মেশিন ও ওজন মাপার যন্ত্র ব্যবহার করি।"
    },
    "organic-mr": {
        lang: "mr-IN",
        message: "मी शेतात सेंद्रिय खत, जीवामृत आणि गांडूळ खत वापरून भाजीपाला पिकवतो. मला ४ वर्षांचा नैसर्गिक शेतीचा अनुभव आहे."
    },
    "solar-en": {
        lang: "en-IN",
        message: "I have been installing rooftop solar PV panels, connecting inverters, and servicing solar water pumps for rural farmers for the past 2 years using crimping tools and multimeters."
    }
};

// ----------------- DOM Helpers -----------------
const $ = id => document.getElementById(id);

// ----------------- Accessibility & UI Toggles -----------------
function adjustFontSize(delta) {
    if (delta === 0) {
        baseFontSize = 16;
    } else {
        baseFontSize = Math.min(24, Math.max(13, baseFontSize + delta * 2));
    }
    document.documentElement.style.setProperty("--base-font-size", baseFontSize + "px");
    
    // Update active button state
    document.querySelectorAll(".btn-text-size").forEach(btn => btn.classList.remove("active"));
    if (delta === 0) {
        const defaultBtn = document.querySelectorAll(".btn-text-size")[1];
        if (defaultBtn) defaultBtn.classList.add("active");
    }
}

function toggleHighContrast() {
    isHighContrast = !isHighContrast;
    if (isHighContrast) {
        document.body.classList.add("high-contrast");
        $("contrast-toggle").classList.add("active");
    } else {
        document.body.classList.remove("high-contrast");
        $("contrast-toggle").classList.remove("active");
    }
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-tab").forEach(tab => {
        tab.classList.toggle("active", tab.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.toggle("active", content.id === tabId);
    });

    // Lazy load tab data
    if (tabId === "officer-view") {
        loadOfficerData();
    } else if (tabId === "kb-view") {
        loadKnowledgeBase();
    } else if (tabId === "impact-view") {
        loadImpactStats();
    }
}

// ----------------- Speech Synthesis (TTS) -----------------
function speakText(text, lang) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    
    lastSpokenText = text;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang || currentLanguage || "en-IN";
    utterance.rate = speechSpeed;
    
    // Match available Indic voices if present
    const voices = window.speechSynthesis.getVoices();
    const voiceMatch = voices.find(v => v.lang === utterance.lang || v.lang.startsWith(utterance.lang.split("-")[0]));
    if (voiceMatch) {
        utterance.voice = voiceMatch;
    }
    
    $("audio-player-bar").hidden = false;
    window.speechSynthesis.speak(utterance);
}

function replayLastSpeech() {
    if (lastSpokenText) {
        speakText(lastSpokenText, currentLanguage);
    }
}

function stopSpeech() {
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
}

function updateAudioSpeed() {
    const select = $("audio-speed-select");
    speechSpeed = parseFloat(select.value) || 1.0;
    if (window.speechSynthesis.speaking) {
        replayLastSpeech();
    }
}

// ----------------- Speech Recognition & Audio Waveform -----------------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function setupAudioVisualizer(stream) {
    try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        audioContext = new AudioContextClass();
        const source = audioContext.createMediaStreamSource(stream);
        analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 256;
        source.connect(analyserNode);

        const canvas = $("waveform-canvas");
        const ctx = canvas.getContext("2d");
        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function draw() {
            if (!isRecording) return;
            animationFrameId = requestAnimationFrame(draw);
            analyserNode.getByteTimeDomainData(dataArray);

            ctx.fillStyle = "#0f172a";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.lineWidth = 2.5;
            ctx.strokeStyle = "#e8871e";
            ctx.beginPath();

            const sliceWidth = canvas.width * 1.0 / bufferLength;
            let x = 0;
            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * canvas.height / 2;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
                x += sliceWidth;
            }
            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
        }
        draw();
    } catch (e) {
        console.warn("Waveform visualizer not supported or permission denied", e);
    }
}

function toggleVoiceRecording() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

function startVoiceRecording() {
    if (!SpeechRecognition) {
        alert("Voice recognition requires Chrome, Edge, or an Android browser. You can still type your response.");
        return;
    }

    try {
        recognition = new SpeechRecognition();
        recognition.lang = $("lang-select").value || "en-IN";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
            isRecording = true;
            $("btn-mic").classList.add("recording");
            $("btn-mic").querySelector(".mic-label").textContent = "Stop";
            $("waveform-container").hidden = false;

            // Start Audio Context for Oscilloscope
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                    micMediaStream = stream;
                    setupAudioVisualizer(stream);
                }).catch(() => {});
            }
        };

        recognition.onresult = event => {
            const transcript = event.results[0][0].transcript;
            $("user-input-field").value = transcript;
            sendMessage();
        };

        recognition.onerror = event => {
            console.error("Speech recognition error:", event.error);
            stopVoiceRecording();
        };

        recognition.onend = () => {
            stopVoiceRecording();
        };

        recognition.start();
    } catch (err) {
        console.error("Failed to start voice recognition", err);
        stopVoiceRecording();
    }
}

function stopVoiceRecording() {
    isRecording = false;
    if (recognition) {
        try { recognition.stop(); } catch (e) {}
    }
    $("btn-mic").classList.remove("recording");
    $("btn-mic").querySelector(".mic-label").textContent = "Speak";
    $("waveform-container").hidden = true;

    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }
    if (micMediaStream) {
        micMediaStream.getTracks().forEach(track => track.stop());
        micMediaStream = null;
    }
}

// ----------------- Chat Stream UI -----------------
function appendMessage(text, sender) {
    const welcome = $("welcome-box");
    if (welcome) welcome.remove();

    const stream = $("chat-stream");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    bubble.textContent = text;
    stream.appendChild(bubble);
    stream.scrollTop = stream.scrollHeight;
}

// ----------------- Work Profile Display -----------------
function updateProfileDisplay(prof) {
    currentProfile = prof || {};
    
    // Domain
    $("prof-domain").textContent = prof.domain || "In progress...";
    
    // Activities
    const actContainer = $("prof-activities");
    actContainer.innerHTML = "";
    if (prof.activities && prof.activities.length > 0) {
        prof.activities.forEach(act => {
            const tag = document.createElement("span");
            tag.className = "tag-badge";
            tag.textContent = act;
            actContainer.appendChild(tag);
        });
    } else {
        actContainer.innerHTML = '<span class="tag-empty">Capturing daily activities...</span>';
    }

    // Tools
    const toolsContainer = $("prof-tools");
    toolsContainer.innerHTML = "";
    if (prof.tools && prof.tools.length > 0) {
        prof.tools.forEach(tool => {
            const tag = document.createElement("span");
            tag.className = "tag-badge";
            tag.textContent = tool;
            toolsContainer.appendChild(tag);
        });
    } else {
        toolsContainer.innerHTML = '<span class="tag-empty">Identifying tools & equipment...</span>';
    }

    // Experience & Frequency
    $("prof-freq").textContent = prof.frequency || "-";
    $("prof-exp").textContent = prof.experience || "-";

    // Communication Signal
    const commText = prof.communication || "Standard";
    $("prof-comm-text").textContent = commText;
    
    const scoreMatch = commText.match(/(\d+)%/);
    const score = scoreMatch ? parseInt(scoreMatch[1]) : 78;
    $("prof-comm-score").textContent = score + "%";
    $("prof-comm-bar").style.width = score + "%";
}

// ----------------- API Actions -----------------
async function postJSON(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function startSession() {
    currentLanguage = $("lang-select").value;
    const btn = $("btn-start");
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Connecting to Discovery Agent...</span>';

    try {
        const res = await postJSON("/api/start", { lang: currentLanguage });
        currentSessionId = res.sid;

        $("btn-start").hidden = true;
        $("active-input-row").hidden = false;
        $("chat-stream").innerHTML = "";

        appendMessage(res.reply, "assistant");
        speakText(res.reply, currentLanguage);
        updateProfileDisplay(res.profile);

        loadPendingCount();
    } catch (err) {
        console.error("Failed to start session:", err);
        appendMessage("Unable to connect to the NARMADA assistant. Please verify your connection.", "system");
        btn.disabled = false;
        btn.innerHTML = '<span>🚀 Begin Voice Assistance</span>';
    }
}

async function sendMessage() {
    const input = $("user-input-field");
    const message = input.value.trim();
    if (!message || !currentSessionId) return;

    input.value = "";
    appendMessage(message, "user");

    try {
        const res = await postJSON("/api/chat", {
            sid: currentSessionId,
            message: message
        });

        appendMessage(res.reply, "assistant");
        speakText(res.reply, currentLanguage);
        updateProfileDisplay(res.profile);

        if (res.enough) {
            $("rec-trigger-bar").hidden = false;
            $("btn-get-rec").focus();
        }
    } catch (err) {
        console.error("Chat error:", err);
        appendMessage("An error occurred processing your voice. Please try speaking again.", "system");
    }
}

function handleInputKey(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}

async function requestRecommendation() {
    if (!currentSessionId) return;

    const recBtn = $("btn-get-rec");
    recBtn.disabled = true;
    recBtn.innerHTML = '<span>🔍 Grounded RAG Matching in Progress...</span>';

    try {
        const res = await postJSON("/api/recommend", { sid: currentSessionId });
        currentRecommendation = res;

        // Render Recommendation Card
        $("rec-result-card").hidden = false;
        $("rec-nsqf-level").textContent = `NSQF Level ${res.level}`;
        $("rec-qp-code").textContent = res.code;
        $("rec-sector").textContent = res.sector;
        $("rec-title").textContent = res.title;
        $("rec-why").textContent = res.why;
        $("rec-career").textContent = res.career_path || "-";
        $("rec-wage").textContent = res.wage_potential || "-";
        $("rec-center").textContent = res.nearest_center || "-";

        if (res.pm_ajay_benefit) {
            $("rec-toolkit-text").innerHTML = `<strong>Tool Kit & Grant:</strong> ${res.pm_ajay_benefit}`;
        }

        // Modules
        const modContainer = $("rec-modules");
        modContainer.innerHTML = "";
        if (res.training_modules && res.training_modules.length > 0) {
            res.training_modules.forEach(m => {
                const li = document.createElement("li");
                li.textContent = m;
                modContainer.appendChild(li);
            });
        }

        // Alternatives
        const altContainer = $("rec-alts");
        altContainer.innerHTML = "";
        if (res.alternatives && res.alternatives.length > 0) {
            res.alternatives.forEach(alt => {
                const d = document.createElement("div");
                d.className = "alt-item";
                d.textContent = `• [${alt.code}] ${alt.title} (${alt.sector || "Allied"})`;
                altContainer.appendChild(d);
            });
        }

        // Spoken audio playback
        if (res.spoken) {
            speakText(res.spoken, currentLanguage);
        }

        // Smooth scroll into recommendation card
        $("rec-result-card").scrollIntoView({ behavior: "smooth", block: "start" });

        loadPendingCount();
    } catch (err) {
        console.error("Recommendation error:", err);
        alert("Failed to retrieve NSQF recommendation. Please try again.");
    } finally {
        recBtn.disabled = false;
        recBtn.innerHTML = '<span>🎯 Generate NSQF Skilling Pathway</span>';
    }
}

// ----------------- Quick Demo Presets -----------------
async function loadPreset(presetKey) {
    const preset = DEMO_PRESETS[presetKey];
    if (!preset) return;

    // Switch Language Selector
    $("lang-select").value = preset.lang;
    currentLanguage = preset.lang;

    // Start Session automatically if not active
    if (!currentSessionId) {
        await startSession();
    }

    // Populate message and simulate voice submission
    $("user-input-field").value = preset.message;
    await sendMessage();

    // Auto-trigger recommendation for instantaneous complete demonstration
    setTimeout(() => {
        if (!$("rec-result-card").hidden === false) {
            requestRecommendation();
        }
    }, 1200);
}

// ----------------- Continuous Weekly Mentor -----------------
let currentMentorAudioText = "";

async function triggerMentorCheckin(week) {
    if (!currentSessionId) {
        alert("Please begin a voice session in the Citizen Companion tab first.");
        switchTab("citizen-view");
        return;
    }

    // Highlight timeline step
    [1, 2, 3].forEach(w => {
        const step = $(`step-w${w}`);
        if (step) step.classList.toggle("active", w <= week);
    });

    try {
        const res = await postJSON("/api/mentor", {
            sid: currentSessionId,
            week: week,
            status: "progressing",
            feedback: "Beneficiary attending regular training session."
        });

        $("mentor-audio-box").hidden = false;
        $("mentor-week-title").textContent = `Week ${res.week} Voice Guidance`;
        $("mentor-speech-text").textContent = res.mentor_reply;
        currentMentorAudioText = res.mentor_reply;

        speakText(res.mentor_reply, currentLanguage);

        // Update Log Entries
        const logContainer = $("mentor-log-entries");
        logContainer.innerHTML = "";
        if (res.mentor_history && res.mentor_history.length > 0) {
            res.mentor_history.forEach(item => {
                const div = document.createElement("div");
                div.className = "log-entry-item";
                div.innerHTML = `<span><strong>Week ${item.week}:</strong> ${item.mentor_reply.substring(0, 75)}...</span><span class="text-muted">${new Date(item.timestamp).toLocaleDateString()}</span>`;
                logContainer.appendChild(div);
            });
        }
    } catch (err) {
        console.error("Mentor check-in error:", err);
    }
}

function replayMentorAudio() {
    if (currentMentorAudioText) {
        speakText(currentMentorAudioText, currentLanguage);
    }
}

// ----------------- Printable Livelihood Passport & QR -----------------
function openPassportModal() {
    if (!currentRecommendation) return;

    const r = currentRecommendation;
    const bid = r.beneficiary_id || `PMAJAY-SC-${currentSessionId.substring(0, 8).toUpperCase()}`;

    $("p-bid").textContent = bid;
    $("p-lang").textContent = $("lang-select").options[$("lang-select").selectedIndex].text;
    $("p-domain").textContent = currentProfile.domain || r.sector;
    $("p-exp").textContent = currentProfile.experience || "2-3 years";
    $("p-comm").textContent = currentProfile.communication || "High Clarity (82%)";
    $("p-title").textContent = r.title;
    $("p-code").textContent = r.code;
    $("p-level").textContent = r.level;
    $("p-time").textContent = r.generated_at || new Date().toLocaleString();
    $("p-hash").textContent = r.audit_hash || "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

    // Generate Dynamic QR Code
    const qrContainer = $("passport-qrcode");
    qrContainer.innerHTML = "";
    new QRCode(qrContainer, {
        text: `https://socialjustice.gov.in/pm-ajay/verify?bid=${bid}&hash=${r.audit_hash}&qp=${r.code}`,
        width: 100,
        height: 100,
        colorDark: "#0f2447",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M
    });

    $("passport-modal").hidden = false;
}

function closePassportModal() {
    $("passport-modal").hidden = true;
}

// ----------------- Privacy Modal -----------------
function openPrivacyModal() {
    $("privacy-modal").hidden = false;
}

function closePrivacyModal() {
    $("privacy-modal").hidden = true;
}

// ----------------- State Skilling Officer Portal -----------------
let officerBeneficiariesList = [];
let activeOfficerSid = null;

async function loadOfficerData() {
    const tbody = $("officer-table-body");
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4">Refreshing registry from database...</td></tr>';

    try {
        const res = await fetch("/api/officer/beneficiaries").then(r => r.json());
        officerBeneficiariesList = res.beneficiaries || [];
        renderOfficerTable(officerBeneficiariesList);
        updateOfficerCounts(officerBeneficiariesList);
    } catch (err) {
        console.error("Failed to load officer data:", err);
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-danger">Failed to fetch registry data.</td></tr>';
    }
}

function renderOfficerTable(list) {
    const tbody = $("officer-table-body");
    tbody.innerHTML = "";

    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4">No mapped beneficiaries found. Start a voice session in Tab 1.</td></tr>';
        return;
    }

    list.forEach(b => {
        const tr = document.createElement("tr");
        const statusClass = b.status === "approved" ? "approved" : b.status === "flagged" ? "flagged" : "active";
        const statusLabel = b.status === "approved" ? "Grant Approved" : b.status === "flagged" ? "Assessment Needed" : "Pending Review";

        tr.innerHTML = `
            <td><strong>${b.beneficiary_id}</strong></td>
            <td>${b.lang}</td>
            <td><strong>${b.domain}</strong></td>
            <td>${b.experience}</td>
            <td>${b.communication.substring(0, 30)}</td>
            <td><span class="tag-badge">${b.qp_code}</span> ${b.recommended_qp}</td>
            <td><span class="status-pill ${statusClass}">${statusLabel}</span></td>
            <td>
                <button class="btn btn-outline" style="padding: 3px 8px; font-size: 0.78rem;" onclick="openOfficerModal('${b.id}')">Review / Action</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateOfficerCounts(list) {
    const total = list.length;
    const pending = list.filter(b => b.status === "active" || !b.status).length;
    const approved = list.filter(b => b.status === "approved").length;
    const flagged = list.filter(b => b.status === "flagged").length;

    $("count-all").textContent = total;
    $("count-pending").textContent = pending;
    $("count-approved").textContent = approved;
    $("count-flagged").textContent = flagged;
    $("pending-badge").textContent = pending;
}

function filterOfficerQueue(status) {
    document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
    event.target.classList.add("active");

    if (status === "all") {
        renderOfficerTable(officerBeneficiariesList);
    } else if (status === "active") {
        renderOfficerTable(officerBeneficiariesList.filter(b => b.status === "active" || !b.status));
    } else {
        renderOfficerTable(officerBeneficiariesList.filter(b => b.status === status));
    }
}

function openOfficerModal(sid) {
    const b = officerBeneficiariesList.find(x => x.id === sid);
    if (!b) return;

    activeOfficerSid = sid;
    $("m-bid").textContent = b.beneficiary_id;
    $("m-domain").textContent = b.domain;
    $("m-exp").textContent = b.experience;
    $("m-qp").textContent = `[${b.qp_code}] ${b.recommended_qp}`;
    $("m-level").textContent = b.nsqf_level;
    $("m-tools").textContent = (b.tools || []).join(", ") || "Standard Manual Tools";
    $("m-comm").textContent = b.communication;
    $("m-hash").textContent = b.audit_hash;
    $("officer-notes-input").value = b.officer_notes || "";

    $("officer-modal").hidden = false;
}

function closeOfficerModal() {
    $("officer-modal").hidden = true;
    activeOfficerSid = null;
}

async function submitOfficerAction(action) {
    if (!activeOfficerSid) return;
    const notes = $("officer-notes-input").value.trim();

    try {
        await postJSON("/api/officer/action", {
            sid: activeOfficerSid,
            action: action,
            notes: notes
        });

        closeOfficerModal();
        loadOfficerData();
    } catch (err) {
        console.error("Officer action error:", err);
        alert("Failed to submit officer verification.");
    }
}

function exportBeneficiariesCSV() {
    if (officerBeneficiariesList.length === 0) {
        alert("No records to export.");
        return;
    }

    let csv = "Beneficiary ID,Language,Inferred Livelihood,Experience,Communication Clarity,NSQF Code,Matched Qualification,Status,Officer Notes,Audit Hash\n";
    officerBeneficiariesList.forEach(b => {
        csv += `"${b.beneficiary_id}","${b.lang}","${b.domain}","${b.experience}","${b.communication.replace(/"/g, '""')}","${b.qp_code}","${b.recommended_qp}","${b.status}","${(b.officer_notes||'').replace(/"/g, '""')}","${b.audit_hash}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `NARMADA_Beneficiaries_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

// ----------------- Knowledge Base Hub -----------------
let fullKnowledgeBase = [];

async function loadKnowledgeBase() {
    const grid = $("kb-grid");
    grid.innerHTML = '<div class="text-center py-4">Loading verified NSQF documents...</div>';

    try {
        const res = await fetch("/api/kb").then(r => r.json());
        fullKnowledgeBase = res.knowledge_base || [];
        renderKBGrid(fullKnowledgeBase);
    } catch (err) {
        console.error("Failed to load KB:", err);
        grid.innerHTML = '<div class="text-center py-4 text-danger">Failed to fetch Knowledge Base documents.</div>';
    }
}

function renderKBGrid(docs) {
    const grid = $("kb-grid");
    grid.innerHTML = "";

    if (docs.length === 0) {
        grid.innerHTML = '<div class="text-center py-4">No matching qualification packs found.</div>';
        return;
    }

    docs.forEach(d => {
        const card = document.createElement("div");
        card.className = `kb-card ${d.kind === 'rule' ? 'rule' : ''}`;
        
        const modulesArr = Array.isArray(d.modules) ? d.modules : [];
        const modulesHTML = modulesArr.length > 0 
            ? `<div class="kb-modules"><strong>Curriculum Modules:</strong><br>${modulesArr.slice(0, 3).join(" • ")}</div>` 
            : "";

        card.innerHTML = `
            <div class="kb-header">
                <div>
                    <span class="nsqf-level-badge">${d.kind === 'rule' ? 'PM-AJAY Guideline' : `NSQF Level ${d.level}`}</span>
                    <span class="nsqf-code-badge">${d.code}</span>
                </div>
                <span class="sector-badge">${d.sector || 'Statutory'}</span>
            </div>
            <h4 class="kb-title">${d.title}</h4>
            <p class="kb-desc">${d.body}</p>
            ${modulesHTML}
            ${d.wage_potential ? `<div style="font-size:0.75rem; color:var(--green-primary); font-weight:700;">💰 Earning Potential: ${d.wage_potential}</div>` : ''}
            ${d.pm_ajay_grant ? `<div style="font-size:0.75rem; color:var(--navy-primary); font-weight:600;">🏛️ GIA Entitlement: ${d.pm_ajay_grant}</div>` : ''}
        `;
        grid.appendChild(card);
    });
}

function filterKB() {
    const query = ($("kb-search-input").value || "").toLowerCase();
    const sectorFilter = $("kb-sector-filter").value;

    const filtered = fullKnowledgeBase.filter(d => {
        const matchesQuery = !query || 
            d.title.toLowerCase().includes(query) || 
            d.body.toLowerCase().includes(query) || 
            d.code.toLowerCase().includes(query) ||
            (d.sector && d.sector.toLowerCase().includes(query));

        const matchesSector = !sectorFilter || (d.sector && d.sector.includes(sectorFilter)) || (sectorFilter === "Statutory" && d.kind === "rule");

        return matchesQuery && matchesSector;
    });

    renderKBGrid(filtered);
}

// ----------------- National Impact & Statistics -----------------
async function loadImpactStats() {
    try {
        const res = await fetch("/api/stats").then(r => r.json());
        $("stat-active-mapped").textContent = res.active_beneficiaries_mapped;
        $("stat-nsqf-issued").textContent = res.nsqf_recommendations_issued;
        $("stat-grants-approved").textContent = res.officer_approved_grants;
        $("stat-dpdp-logs").textContent = res.dpdp_trust_verifications;
    } catch (err) {
        console.error("Failed to load statistics:", err);
    }
}

async function loadPendingCount() {
    try {
        const res = await fetch("/api/stats").then(r => r.json());
        loadImpactStats();
    } catch (e) {}
}

// ----------------- Window Load Initialization -----------------
window.addEventListener("DOMContentLoaded", () => {
    loadImpactStats();
    loadKnowledgeBase();

    // Populate Speech Synthesis Voices on load
    if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }
});
