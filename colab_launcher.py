# Copy this entire script into one Google Colab cell after uploading the project files.
import os, re, stat, subprocess, sys, time, urllib.request
from pathlib import Path

required = ["app.py", "game_backend.py", "leaderboard_db.py"]
missing = [name for name in required if not Path(name).exists()]
if missing:
    raise FileNotFoundError("Upload these files first: " + ", ".join(missing))

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "streamlit", "wordfreq", "python-dotenv"])
streamlit_log = open("streamlit.log", "w")
streamlit = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
    stdout=streamlit_log, stderr=subprocess.STDOUT,
)

for _ in range(60):
    try:
        urllib.request.urlopen("http://127.0.0.1:8501/_stcore/health", timeout=2)
        break
    except Exception:
        if streamlit.poll() is not None:
            print(Path("streamlit.log").read_text(errors="replace"))
            raise RuntimeError("Streamlit failed to start.")
        time.sleep(1)
else:
    print(Path("streamlit.log").read_text(errors="replace"))
    raise RuntimeError("Streamlit health check timed out.")

machine = os.uname().machine.lower()
arch = "amd64" if machine in {"x86_64", "amd64"} else "arm64"
url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}"
urllib.request.urlretrieve(url, "cloudflared")
os.chmod("cloudflared", os.stat("cloudflared").st_mode | stat.S_IEXEC)

tunnel_log = open("cloudflared.log", "w")
tunnel = subprocess.Popen(
    ["./cloudflared", "tunnel", "--url", "http://127.0.0.1:8501", "--no-autoupdate"],
    stdout=tunnel_log, stderr=subprocess.STDOUT,
)

endpoint = None
for _ in range(90):
    time.sleep(1)
    text = Path("cloudflared.log").read_text(errors="replace")
    match = re.search(r"https://[-a-z0-9]+\.trycloudflare\.com", text)
    if match:
        endpoint = match.group(0)
        break
    if tunnel.poll() is not None:
        break

if not endpoint:
    print("STREAMLIT LOG:\n", Path("streamlit.log").read_text(errors="replace"))
    print("CLOUDFLARE LOG:\n", Path("cloudflared.log").read_text(errors="replace"))
    raise RuntimeError("Cloudflare tunnel failed to provide an endpoint.")

print("\nPHRASE FORGE PUBLIC ENDPOINT:\n" + endpoint + "\n")
print("Streamlit PID:", streamlit.pid, "Cloudflare PID:", tunnel.pid)
