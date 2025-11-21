#!/usr/bin/env python3
"""
Launcher script for running FastAPI backend + Streamlit frontend together.

This script will:
1. Start the FastAPI backend on port 8000
2. Start the Streamlit frontend on port 8501
3. Handle graceful shutdown of both services

Run with: python run_full_app.py
"""

import subprocess
import sys
import time
import signal
import os
from threading import Thread

# ANSI color codes for terminal output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

processes = []

def print_banner():
    """Print a nice banner."""
    print(f"""
{BLUE}{BOLD}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           📡 1NCE IoT Dashboard - Full Stack App              ║
║                                                               ║
║     FastAPI Backend  : http://localhost:8000/docs             ║
║     Streamlit Frontend : http://localhost:8501                ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
""")

def start_fastapi():
    """Start the FastAPI backend server."""
    print(f"\n{GREEN}[FastAPI]{RESET} Starting backend server on port 8000...")
    
    try:
        process = subprocess.Popen(
            ["uvicorn", "test_1nce_api:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        
        # Stream output
        for line in process.stdout:
            print(f"{GREEN}[FastAPI]{RESET} {line}", end='')
            
    except Exception as e:
        print(f"{RED}[FastAPI]{RESET} Error: {e}")
        sys.exit(1)

def start_streamlit():
    """Start the Streamlit frontend server."""
    print(f"\n{BLUE}[Streamlit]{RESET} Starting frontend on port 8501...")
    
    # Wait a moment for FastAPI to start
    time.sleep(2)
    
    try:
        process = subprocess.Popen(
            [
                "streamlit", "run", "streamlit_frontend.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0",
                "--server.headless", "true"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        
        # Stream output
        for line in process.stdout:
            print(f"{BLUE}[Streamlit]{RESET} {line}", end='')
            
    except Exception as e:
        print(f"{RED}[Streamlit]{RESET} Error: {e}")
        sys.exit(1)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print(f"\n\n{YELLOW}Shutting down services...{RESET}")
    
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    
    print(f"{GREEN}✓ All services stopped{RESET}")
    sys.exit(0)

def check_dependencies():
    """Check if required packages are installed."""
    required = ['uvicorn', 'streamlit', 'fastapi', 'httpx', 'plotly', 'pandas']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"{RED}Missing required packages:{RESET}")
        for package in missing:
            print(f"  - {package}")
        print(f"\n{YELLOW}Install with:{RESET}")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)

def main():
    """Main entry point."""
    print_banner()
    
    # Check dependencies
    print(f"{YELLOW}Checking dependencies...{RESET}")
    check_dependencies()
    print(f"{GREEN}✓ All dependencies installed{RESET}")
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start both services in separate threads
    fastapi_thread = Thread(target=start_fastapi, daemon=True)
    streamlit_thread = Thread(target=start_streamlit, daemon=True)
    
    fastapi_thread.start()
    streamlit_thread.start()
    
    # Wait for threads
    try:
        fastapi_thread.join()
        streamlit_thread.join()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
