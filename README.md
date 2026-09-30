# NARMADA 🌊
### Native-language Aptitude Recognition & Mentoring Architecture Driving Advancement

> **“Right Voice. Right Skill. Right Livelihood. Deserving Opportunity.”**  
> *The river that carries every learner forward → SPEAK. UNDERSTAND. MATCH. GUIDE.*

---

## 📌 Problem Statement Overview
- **Competition:** Smart India Hackathon (SIH 2026)
- **Problem Statement ID:** `SIH26097`
- **Problem Statement Title:** AI-Driven Voice Assistant for Livelihood Mapping and NSQF-Aligned Skilling Recommendations for SC Communities under GIA component of PM-AJAY
- **Theme:** Agriculture, FoodTech & Rural Development
- **Category:** Software
- **Team ID:** 153375
- **Team Name:** CodeRhythm

---

## 🏛️ Background & Objective
Under the **Grants-in-Aid (GIA)** component of **PM-AJAY (Pradhan Mantri Anusuchit Jaati Abhyuday Yojana)**, Scheduled Caste (SC) community members need to be mapped to relevant, NSQF-aligned skilling programs. Two major barriers block this today:
1. **No structured way to capture what someone already knows:** Everyday rural and semi-urban livelihoods are informal, undocumented, and difficult to express in formal application forms.
2. **Interface barrier:** Low-literacy, vernacular-speaking citizens are excluded by complex English-first web forms.

**NARMADA** solves this by providing a **multilingual voice companion** that converts informal spoken descriptions into structured skill profiles, matches them to certified NSQF Qualification Packs via **Hybrid RAG**, and guides the citizen through continuous weekly voice mentoring.

---

## ⚙️ Core Architecture & The 4 Pillars

```
+---------------------------------------------------------------------------------------------------+
|                                         CITIZEN (VOICE)                                           |
|                           Speaks daily work in native language (23 Indic langs)                   |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                   AGENT 1 — DISCOVERY AGENT                                       |
|  • Speech Recognition (Bhashini / Saaras v3 / Web Speech API)                                     |
|  • Work Profile Extraction (Activities, Tools, Experience, Frequency)                            |
|  • Communication-Confidence Signal Analysis (Clarity, Fluency & Articulation Score)                |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                               HYBRID RAG & KNOWLEDGE RETRIEVAL                                    |
|  • 25+ Verified NCVET NSQF Qualification Packs (Agriculture, Apparel, Solar, FoodTech, etc.)       |
|  • PM-AJAY GIA Statutory Rules & Tool Kit Guidelines (₹15,000 subsidy, 100% grant)                |
|  • Dense Vector (OpenAI/BGE-M3) + Token-Weighted Indic Keyword Matching                           |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                   AGENT 2 — GUIDANCE AGENT                                        |
|  • Deterministic PM-AJAY Eligibility Verification                                                 |
|  • Grounded NSQF Qualification Mapping (Level 3-4 QP Code, Syllabus Modules, Wage Potential)      |
|  • Spoken Native Audio Script Generation (TTS Playback in Native Dialect)                         |
|  • SHA-256 Cryptographic Audit Hashing (DPDP Act 2023 Trust Layer)                                |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                           CONTINUOUS WEEKLY VOICE MENTORING (POST-RECOMMENDATION)                 |
|  • Week 1: Induction, Training Handbook & Tool Kit Handover Check-in                              |
|  • Week 2: Practical Skills Milestone & Aadhaar DBT Conveyance Stipend Verification               |
|  • Week 3+: NCVET Certification & PM-AJAY Income Generation Project (IGP) ₹50,000 Micro-Loan      |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                STATE SKILLING OFFICER REVIEW PORTAL                               |
|  • Auditable Decision Trail, Verification Queue, Human-in-the-Loop Grant Sanction                 |
+---------------------------------------------------------------------------------------------------+
```

---

## 🌟 Key Features

1. **Voice-First Indic Pipeline (11+ Major Languages Supported)**
   - English, Hindi (हिन्दी), Tamil (தமிழ்), Telugu (తెలుగు), Kannada (ಕನ್ನಡ), Malayalam (മലയാളം), Marathi (मराठी), Bengali (বাংলা), Gujarati (ગુજરાતી), Odia (ଓଡ଼ିଆ), Punjabi (ਪੰਜਾਬੀ).
   - Real-time **Web Audio API Oscilloscope Waveform Visualizer**.
   - Natural Indic Speech Synthesis with rate adjustment and replay.

2. **Communication-Confidence Signal Analysis**
   - In addition to extracting hard vocational skills, NARMADA measures articulation clarity, domain terminology richness, and communication confidence (0–100%) to recommend appropriate skill levels (NSQF Level 3 vs Level 4).

3. **Grounded NSQF Knowledge Base (25+ Detailed Qualification Packs)**
   - Includes official Qualification Packs across **Agriculture & Allied**, **Apparel & Textiles**, **Green Energy & Solar**, **Electronics & Hardware**, **Food Processing**, **Automotive & Mechanics**, **Healthcare**, **Plumbing & Construction**, and **Handicrafts**.

4. **NARMADA Livelihood & Skilling Passport (Printable Card + QR Code)**
   - Generates an official, printable Beneficiary Livelihood Passport complete with Beneficiary ID, matched NSQF Pack, PM-AJAY GIA grant entitlement, and a dynamic **QR Code** verifying the **SHA-256 cryptographic audit hash**.

5. **State Skilling Officer (Human-in-the-Loop Verification Dashboard)**
   - Auditable review queue to inspect extracted profiles and citations.
   - One-click **Grant Sanction** or **Refer for Assessment**.
   - Export registry to CSV/Excel for State MIS reporting.

6. **DPDP Act 2023 Trust Layer & Privacy First Design**
   - Explicit multilingual consent recording.
   - Minimal data retention policy.
   - Immutable SHA-256 decision fingerprinting.

7. **Universal Resilience & Zero-Configuration Execution**
   - Auto-switches between PostgreSQL (if `DATABASE_URL` is set) and built-in SQLite (`narmada.db`).
   - Supports OpenAI API embeddings & completions if key is configured, plus built-in high-accuracy **Indic NLP heuristic & semantic vector retrieval engine** for flawless offline/local execution.

---

## 🚀 Quickstart & Setup (No Docker)

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12+
- Any modern web browser (Chrome or Edge recommended for native Speech Recognition)

### 2. Installation
Clone or navigate to the project directory and install the required Python packages:

```bash
cd "d:\Aswin Projects\Narmada-Voice first Assistant platform"
pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
Copy `.env.example` to `.env` if you wish to use PostgreSQL or an OpenAI API key:

```env
# Optional: If omitted, NARMADA runs seamlessly with SQLite + Local Semantic Engine
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
```

### 4. Run the Application
Start the Flask development server:

```bash
python app.py
```

Open your browser and navigate to:  
👉 **`http://localhost:5000`**

---

## 🧪 Testing the Live Demo

1. Open `http://localhost:5000` in Google Chrome or Microsoft Edge.
2. Click any of the **Quick Demo Presets** (e.g. *Dairy Farmer (Tamil)* or *Tailor (Hindi)*) to watch the complete end-to-end voice ingestion, extraction, and NSQF recommendation in real-time.
3. Switch to the **Weekly Voice Mentor** tab to experience ongoing check-ins.
4. Switch to the **State Skilling Officer Portal** tab to review, verify, and approve grants.
5. Click **View & Print Livelihood Passport** to generate the official verified QR credential card.

---

## 📜 Official Benchmarks & Impact Indicators (PM-AJAY FY23–24)
- **70,934** SC beneficiaries under PM-AJAY GIA skill-development projects (FY 2023–24).
- **913** Skill-development projects approved under PM-AJAY Grant-in-Aid.
- **30,660** SC persons entered NSQF-compliant certified training.
- **201.38 Million** Scheduled Caste population in India (16.63% national target).

---

## 👥 Team & Submission Information
- **Smart India Hackathon 2026**
- **Team CodeRhythm (153375)**
- **Theme:** Agriculture, FoodTech & Rural Development
- **Problem Statement ID:** `SIH26097`
