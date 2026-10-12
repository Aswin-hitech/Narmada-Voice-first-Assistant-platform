"""
Test script to verify the full app startup works correctly
"""
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Testing full app startup...")
    
    # Import the app module - this will trigger initialization
    import app as app_module
    
    # Verify the Flask app was created
    assert hasattr(app_module, 'app'), "Flask app not found"
    print("[OK] Flask app created")
    
    # Verify database was initialized
    print(f"[OK] Using PostgreSQL: {app_module.USE_POSTGRES}")
    
    # Test a simple database query
    result = app_module.execute_query(
        "SELECT count(*) as count FROM officer_users", 
        fetch="one"
    )
    print(f"[OK] Database query successful: {result}")
    
    # Test creating a session
    import uuid
    test_session_id = f"test-{uuid.uuid4().hex[:8]}"
    app_module.execute_query("""
        INSERT INTO sessions (id, lang, history, profile, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (test_session_id, "en", "[]", "{}", "active"))
    print(f"[OK] Session created: {test_session_id}")
    
    # Verify the session was created
    session = app_module.execute_query(
        "SELECT * FROM sessions WHERE id=%s", 
        (test_session_id,), 
        fetch="one"
    )
    assert session is not None, "Session not found after creation"
    print(f"[OK] Session retrieved: {session['id']}")
    
    # Clean up test session
    app_module.execute_query("DELETE FROM sessions WHERE id=%s", (test_session_id,))
    print(f"[OK] Test session cleaned up")
    
    print("\n[OK] All app startup tests passed!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
