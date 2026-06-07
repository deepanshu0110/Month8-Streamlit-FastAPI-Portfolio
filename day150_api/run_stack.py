import subprocess
import sys
import time
import signal
import requests

print("🚀 Starting FreelanceHub full stack...")
print("   FastAPI  → http://localhost:8000")
print("   Swagger  → http://localhost:8000/docs")
print("   Streamlit→ http://localhost:8501")
print("   Press Ctrl+C to stop both servers.\n")

api_proc = subprocess.Popen(
    ["uvicorn", "day149_api.main:app", "--reload", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

print("⏳ Waiting for FastAPI to initialise (3s)...")
time.sleep(3)

if api_proc.poll() is not None:
    print("❌ FastAPI failed to start. Check day149_api/main.py for errors.")
    sys.exit(1)

print("✅ FastAPI running.")

# Seed the database
print("🌱 Seeding database...")
try:
    resp = requests.post(
        "http://localhost:8000/seed-db",
        headers={"X-API-Key": "freelancehub-2024-secret"},
        timeout=10
    )
    if resp.status_code == 200:
        print(f"   ✅ Seeded {resp.json()['seeded']} projects")
    else:
        print(f"   ⚠️ Seed failed: {resp.status_code}")
except Exception as e:
    print(f"   ⚠️ Could not seed: {e}")

st_proc = subprocess.Popen(
    ["streamlit", "run", "day149_app/streamlit_app.py",
     "--server.port", "8501", "--server.headless", "false"]
)

print("✅ Streamlit running.\n")

def shutdown(sig, frame):
    print("\n🛑 Shutting down servers...")
    api_proc.terminate()
    st_proc.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

api_proc.wait()
st_proc.wait()