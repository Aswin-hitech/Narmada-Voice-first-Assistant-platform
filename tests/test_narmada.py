import os
import json
import pytest
from app import app, execute_query, hash_password, verify_password, generate_audit_signature, verify_audit_signature

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test health status and reported services."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "ai_services" in data
    assert "database" in data

def test_officer_login_invalid_and_valid(client):
    """Test security: rejects bad credentials, accepts valid bcrypt officer auth and issues JWT."""
    # Ensure officer exists in officer_users table
    execute_query("DELETE FROM officer_users WHERE username='test_officer'")
    hashed = hash_password("SecretTestPass@2026")
    execute_query("INSERT INTO officer_users (username, password_hash, role) VALUES (%s, %s, %s)",
                  ("test_officer", hashed, "reviewer"))

    # Test invalid login
    bad_res = client.post("/api/officer/login", json={"username": "test_officer", "password": "WrongPassword"})
    assert bad_res.status_code == 401

    # Test valid login
    good_res = client.post("/api/officer/login", json={"username": "test_officer", "password": "SecretTestPass@2026"})
    assert good_res.status_code == 200
    data = good_res.get_json()
    assert "token" in data
    assert data["username"] == "test_officer"
    assert data["role"] == "reviewer"

def test_consent_enforcement_on_start(client):
    """Test DPDP Act Consent: /api/start MUST reject when consent is not True."""
    # Without consent: must reject with 400
    res_no_consent = client.post("/api/start", json={"lang": "ta-IN"})
    assert res_no_consent.status_code == 400
    err_data = res_no_consent.get_json()
    assert err_data.get("consent_required") is True

    # With consent: must succeed, create session with consent metadata and session_token
    res_with_consent = client.post("/api/start", json={"lang": "ta-IN", "consent": True})
    assert res_with_consent.status_code == 200
    start_data = res_with_consent.get_json()
    assert "sid" in start_data
    assert "session_token" in start_data
    assert start_data["lang"] == "ta-IN"

def test_session_authorization_protection(client):
    """Test that beneficiary endpoints require valid session ID and reject invalid ones."""
    # Chat with nonexistent sid
    res_bad_chat = client.post("/api/chat", json={"sid": "nonexistent_sid_12345", "message": "test"})
    assert res_bad_chat.status_code in (403, 404)

    # Valid session creation followed by chat
    start_res = client.post("/api/start", json={"lang": "en-IN", "consent": True})
    assert start_res.status_code == 200
    sid = start_res.get_json()["sid"]
    token = start_res.get_json()["session_token"]

    # Chat with bearer token
    chat_res = client.post("/api/chat",
                           headers={"Authorization": f"Bearer {token}"},
                           json={"sid": sid, "message": "I rear two cows and milk daily for 4 years"})
    assert chat_res.status_code == 200
    chat_data = chat_res.get_json()
    assert "reply" in chat_data
    assert "profile" in chat_data

def test_rag_matching_and_accuracy(client):
    """Test that recommendations cite verified NSQF Qualification Packs from DB and apply PM-AJAY rules."""
    start_res = client.post("/api/start", json={"lang": "hi-IN", "consent": True})
    sid = start_res.get_json()["sid"]
    token = start_res.get_json()["session_token"]

    # Send livelihood dialogue
    client.post("/api/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"sid": sid, "message": "मैं सिलाई मशीन पर कपड़े सिलती हूँ, कैंची और इंची टेप का इस्तेमाल करती हूँ"})

    # Request recommendation
    rec_res = client.post("/api/recommend",
                          headers={"Authorization": f"Bearer {token}"},
                          json={"sid": sid})
    assert rec_res.status_code == 200
    rec_data = rec_res.get_json()

    # RAG correctness assertions: Real QP code and PM-AJAY statutory benefits
    assert "code" in rec_data
    assert rec_data.get("grounded_verified") is True
    # Verify code exists in knowledge base
    kb_row = execute_query("SELECT * FROM kb WHERE code=%s", (rec_data["code"],), fetch="one")
    assert kb_row is not None
    assert rec_data["title"] == kb_row["title"]

    # Verify audit hash and HMAC signature exist
    assert "audit_hash" in rec_data
    assert "audit_signature" in rec_data
    assert len(rec_data["audit_hash"]) == 64
    assert len(rec_data["audit_signature"]) == 64

def test_officer_action_authorization_and_validation(client):
    """Test officer verification actions, allowed statuses, and role protection."""
    # Attempt officer action without auth token: must be 401
    unauth_res = client.post("/api/officer/action", json={"sid": "any_sid", "action": "approved"})
    assert unauth_res.status_code == 401

    # Login as officer to get token
    hashed = hash_password("OfficerPass@2026")
    execute_query("INSERT OR REPLACE INTO officer_users (username, password_hash, role) VALUES (%s, %s, %s)",
                  ("officer_tester", hashed, "reviewer"))
    login_res = client.post("/api/officer/login", json={"username": "officer_tester", "password": "OfficerPass@2026"})
    officer_token = login_res.get_json()["token"]

    # Create a real session to review
    start_res = client.post("/api/start", json={"lang": "en-IN", "consent": True})
    sid = start_res.get_json()["sid"]

    # Invalid status should be rejected
    bad_action_res = client.post("/api/officer/action",
                                 headers={"Authorization": f"Bearer {officer_token}"},
                                 json={"sid": sid, "action": "hacked_status", "notes": "Test notes"})
    assert bad_action_res.status_code == 400

    # Valid status: approve grant
    good_action_res = client.post("/api/officer/action",
                                  headers={"Authorization": f"Bearer {officer_token}"},
                                  json={"sid": sid, "action": "approved", "notes": "Aadhaar verified. Batch 101"})
    assert good_action_res.status_code == 200
    res_data = good_action_res.get_json()
    assert res_data["success"] is True
    assert res_data["status"] == "approved"

    # Confirm session status in DB
    updated_session = execute_query("SELECT status, officer_notes FROM sessions WHERE id=%s", (sid,), fetch="one")
    assert updated_session["status"] == "approved"
    assert "Aadhaar verified" in updated_session["officer_notes"]

def test_speech_reliability_and_transcribe_errors(client):
    """Test /api/transcribe returns clear errors instead of silent failure."""
    # Request without audio or text should return 400
    empty_res = client.post("/api/transcribe", data={})
    assert empty_res.status_code == 400
    assert "detail" in empty_res.get_json()

    # Explicit text input fallback with valid translation
    text_res = client.post("/api/transcribe", data={"text": "Hello I am a farmer", "lang": "en-IN"})
    assert text_res.status_code == 200
    assert text_res.get_json()["transcript"] == "Hello I am a farmer"
