"""
Launch script for the Django backend and PyQt6 frontend application.
This script will:
1. Ensure virtual environment is activated
2. Start Django backend server
3. Start PyQt6 frontend application
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Get project paths
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_DIR = PROJECT_ROOT / ".venv"

def check_venv():
    """Check if virtual environment exists."""
    if not VENV_DIR.exists():
        print("❌ Virtual environment not found!")
        print("Please run: python.exe .\\backend\\script.py")
        sys.exit(1)
    print("✓ Virtual environment found")

def get_venv_python():
    """Get the path to the virtual environment's Python executable."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def check_files():
    """Check if required files exist."""
    manage_py = BACKEND_DIR / "manage.py"
    main_py = FRONTEND_DIR / "main.py"
    
    if not manage_py.exists():
        print(f"❌ Backend manage.py not found at: {manage_py}")
        sys.exit(1)
    
    if not main_py.exists():
        print(f"❌ Frontend main.py not found at: {main_py}")
        sys.exit(1)
    
    print("✓ All required files found")

def launch_backend(python_path):
    """Launch Django backend server in a separate process."""
    print("\n" + "="*60)
    print("Starting Django Backend Server...")
    print("="*60)
    
    backend_cmd = [str(python_path), "manage.py", "runserver"]
    
    try:
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"✓ Backend server starting (PID: {backend_process.pid})")
        print("  URL: http://127.0.0.1:8000/")
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        sys.exit(1)

def launch_frontend(python_path):
    """Launch PyQt6 frontend application."""
    print("\n" + "="*60)
    print("Starting PyQt6 Frontend Application...")
    print("="*60)
    
    frontend_cmd = [str(python_path), "main.py"]
    
    try:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR)
        )
        print(f"✓ Frontend application starting (PID: {frontend_process.pid})")
        return frontend_process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main launch function."""
    print("\n" + "="*60)
    print("DJANGO + PYQT6 APPLICATION LAUNCHER")
    print("="*60)
    
    # Check prerequisites
    check_venv()
    check_files()
    
    # Get Python path from venv
    python_path = get_venv_python()
    print(f"✓ Using Python: {python_path}\n")
    
    # Launch backend server
    backend_process = launch_backend(python_path)
    
    # Wait a bit for backend to start
    print("\nWaiting 3 seconds for backend to initialize...")
    time.sleep(3)
    
    # Launch frontend
    frontend_process = launch_frontend(python_path)
    
    # Monitor processes
    print("\n" + "="*60)
    print("BOTH APPLICATIONS ARE RUNNING")
    print("="*60)
    print("\n📌 Backend Server: http://127.0.0.1:8000/")
    print("📌 Frontend: PyQt6 Application Window")
    print("\n⚠️  Press Ctrl+C to stop all processes\n")
    print("="*60)
    
    try:
        # Wait for frontend to close (blocking)
        if frontend_process:
            frontend_process.wait()
            print("\n✓ Frontend application closed")
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutdown signal received...")
    finally:
        # Cleanup: terminate backend
        print("🛑 Stopping backend server...")
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
                print("✓ Backend server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing backend server...")
                backend_process.kill()
                backend_process.wait()
        
        print("\n" + "="*60)
        print("ALL PROCESSES STOPPED")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
