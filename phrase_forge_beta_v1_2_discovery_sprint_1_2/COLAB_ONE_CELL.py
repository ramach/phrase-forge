# Paste this entire file into ONE Google Colab code cell after uploading/cloning
# the Phrase Forge Beta 1.0 project into the runtime.
import os, re, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path.cwd()
required = ["app.py", "game_backend.py", "leaderboard_db.py", "requirements.txt", "data/phrases.json"]
missing = [name for name in required if not (ROOT / name).exists()]
if missing:
    raise FileNotFoundError("Missing Phrase Forge files: " + ", ".join(missing))

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])

cloudflared = ROOT / "cloudflared"
if not cloudflared.exists():
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    urllib.request.urlretrieve(url, cloudflared)
    cloudflared.chmod(0o755)

streamlit_log = open(ROOT / "streamlit.log", "w")
tunnel_log = open(ROOT / "cloudflared.log", "w")
streamlit_proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
    stdout=streamlit_log, stderr=subprocess.STDOUT,
)

for _ in range(60):
    try:
        urllib.request.urlopen("http://127.0.0.1:8501/_stcore/health", timeout=1)
        break
    except Exception:
        time.sleep(1)
else:
    streamlit_log.close()
    print((ROOT / "streamlit.log").read_text(errors="ignore")[-6000:])
    raise RuntimeError("Streamlit did not become healthy.")

tunnel_proc = subprocess.Popen(
    [str(cloudflared), "tunnel", "--url", "http://127.0.0.1:8501", "--no-autoupdate"],
    stdout=tunnel_log, stderr=subprocess.STDOUT,
)

tunnel_log.flush()
public_url = None
for _ in range(90):
    time.sleep(1)
    tunnel_log.flush()
    text = (ROOT / "cloudflared.log").read_text(errors="ignore")
    match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
    if match:
        public_url = match.group(0)
        break

if public_url:
    print("\n" + "=" * 72)
    print("PHRASE FORGE PUBLIC TEST URL")
    print(public_url)
    print("=" * 72)
    print("Keep this Colab runtime running. Configure DATABASE_URL for persistent data.")
else:
    print("Cloudflare tunnel URL was not detected. Recent logs:\n")
    print((ROOT / "cloudflared.log").read_text(errors="ignore")[-6000:])
