"""Run the RVM keying pipeline inside an E2B sandbox and time it.
The API key is read from Azure Key Vault at run time (never written to disk):
  export E2B_API_KEY=$(az keyvault secret show --vault-name dp-kv-deliverypilot --name e2b-api-key --query value -o tsv)
Usage: python e2b_run.py [--probe] [--frames N] [--cpus N]"""
import os, sys, time, json, argparse
from e2b import Sandbox

ap = argparse.ArgumentParser()
ap.add_argument("--probe", action="store_true"); ap.add_argument("--frames", type=int, default=None)
ap.add_argument("--cpus", type=int, default=None); ap.add_argument("--template", default=None); a = ap.parse_args()
assert os.environ.get("E2B_API_KEY"), "set E2B_API_KEY (see docstring)"
here = os.path.dirname(os.path.abspath(__file__)); T = {}
def tick(name, t0): T[name] = round(time.time() - t0, 1); print(f"[{name}] {T[name]} s", flush=True)

t = time.time(); sbx = Sandbox.create(template=a.template, timeout=3300, **({"cpu_count": a.cpus} if a.cpus else {})); tick("create_sandbox", t)
def sh(cmd, timeout=1800):
    r = sbx.commands.run(cmd, timeout=timeout, on_stderr=lambda e: None); return r.stdout
try:
    print(sh("nproc; lscpu | grep -m1 'Model name'; free -m | sed -n 2p; which ffmpeg python3; python3 --version; whoami"))
    if a.probe: sys.exit()
    t = time.time(); sh("mkdir -p /home/user/rvm/weights /home/user/rvm/third_party_rvm/model")
    for f in ["key.py", "key_fast.py", "weights/rvm_mobilenetv3.pth", "work/clip.mp4"]:
        sbx.files.write(f"/home/user/rvm/{f}", open(os.path.join(here, f), "rb").read())
    for f in os.listdir(os.path.join(here, "third_party_rvm", "model")):
        p = os.path.join(here, "third_party_rvm", "model", f)
        if os.path.isfile(p): sbx.files.write(f"/home/user/rvm/third_party_rvm/model/{f}", open(p, "rb").read())
    tick("upload", t)
    t = time.time()
    if a.template: print("deps preinstalled in template")
    elif "ffmpeg" not in sh("which ffmpeg || true"): sh("sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg", 900)
    if not a.template: sh("pip install -q torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu av numpy opencv-python-headless pillow", 1500)
    tick("install_deps", t)
    t = time.time()
    out = sh(f"cd /home/user/rvm && python3 key_fast.py work/clip.mp4 fg.webm {a.frames or ''} > run.log 2>&1; echo exit=$?; grep -v objc run.log | tail -4; free -m | sed -n 2p", 3000)
    tick("keying", t); print(out)
    t = time.time(); data = sbx.files.read("/home/user/rvm/fg.webm", format="bytes"); open(os.path.join(here, "work", "fg_e2b.webm"), "wb").write(data); tick("download", t)
    json.dump({"timings_s": T, "frames": a.frames or 360, "log": out.strip()}, open(os.path.join(here, "docs", "e2b_result.json"), "w"), indent=1)
finally:
    sbx.kill(); print("sandbox killed")
