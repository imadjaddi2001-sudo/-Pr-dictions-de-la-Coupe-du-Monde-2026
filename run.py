#!/usr/bin/env python3
"""Quick launcher — installs deps then starts the app."""
import subprocess, sys, webbrowser, threading, time

def install():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:5000")

if __name__ == "__main__":
    print("📦 Installing dependencies...")
    install()
    print("🚀 Starting WC 2026 Predictor...")
    threading.Thread(target=open_browser, daemon=True).start()
    from app import app
    app.run(debug=False, port=5000, host="0.0.0.0")
