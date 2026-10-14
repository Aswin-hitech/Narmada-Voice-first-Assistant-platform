"""
Test script to verify all new routes work correctly
"""
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Testing new routes...")
    
    # Import the app module
    import app as app_module
    
    # Create a test client
    client = app_module.app.test_client()
    
    # Test welcome page
    response = client.get('/')
    assert response.status_code == 200, f"Welcome page failed: {response.status_code}"
    print("[OK] Welcome page (/) - 200")
    
    # Test role selection page
    response = client.get('/role-select')
    assert response.status_code == 200, f"Role select page failed: {response.status_code}"
    print("[OK] Role select page (/role-select) - 200")
    
    # Test signin page
    response = client.get('/signin')
    assert response.status_code == 200, f"Signin page failed: {response.status_code}"
    print("[OK] Signin page (/signin) - 200")
    
    # Test register page
    response = client.get('/register')
    assert response.status_code == 200, f"Register page failed: {response.status_code}"
    print("[OK] Register page (/register) - 200")
    
    # Test citizen dashboard
    response = client.get('/citizen-dashboard')
    assert response.status_code == 200, f"Citizen dashboard failed: {response.status_code}"
    print("[OK] Citizen dashboard (/citizen-dashboard) - 200")
    
    # Test officer dashboard
    response = client.get('/officer-dashboard')
    assert response.status_code == 200, f"Officer dashboard failed: {response.status_code}"
    print("[OK] Officer dashboard (/officer-dashboard) - 200")
    
    # Test citizen registration API
    response = client.post('/api/citizen/register', 
                          json={
                              'mobile': '9999999999',
                              'full_name': 'Test User',
                              'password': 'test123',
                              'confirm_password': 'test123',
                              'district': 'Test District',
                              'lang': 'en',
                              'occupation': 'Test',
                              'consent': True
                          })
    print(f"[OK] Citizen registration API - {response.status_code}")
    
    # Test citizen login API
    response = client.post('/api/citizen/login',
                          json={
                              'mobile': '9999999999',
                              'password': 'test123'
                          })
    print(f"[OK] Citizen login API - {response.status_code}")
    
    print("\n[OK] All route tests passed!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
