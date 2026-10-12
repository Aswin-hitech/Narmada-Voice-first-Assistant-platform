"""
Test script to verify database initialization fix
"""
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Testing database initialization...")
    from app import init_db, USE_POSTGRES, get_db
    
    # Initialize the database
    init_db()
    
    print("[OK] Database initialized successfully!")
    print(f"[OK] Using PostgreSQL: {USE_POSTGRES}")
    
    # Verify connection works
    conn = get_db()
    if conn:
        print("[OK] Database connection successful")
        conn.close()
    
    print("\n[OK] All tests passed!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
