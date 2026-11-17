"""Benchmark RVM speed options on MPS. Usage: python bench.py clip.mp4 [frames]"""
import sys, os, time, json, torch, av, numpy as np
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "third_party_rvm"))
from model import MattingNetwork
dev = "mps"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 60
frames = []
c = av.open(sys.argv[1])
for i, f in enumerate(c.decode(c.streams.video[0])):
    if i >= N: break
    frames.append(f.to_ndarray(format="rgb24"))
base = MattingNetwork("mobilenetv3").eval()
base.load_state_dict(torch.load(os.path.join(here, "weights", "rvm_mobilenetv3.pth"), map_location="cpu"))

def run(ratio, half, d=dev):
    m = (base.half() if half else base.float()).to(d)
    rec = [None]*4; dt = torch.float16 if half else torch.float32
    with torch.no_grad():
        for i, rgb in enumerate(frames):
            if i == 5: torch.mps.synchronize() if d=="mps" else None; t0 = time.time()
            t = torch.from_numpy(rgb).permute(2,0,1)[None].to(d).to(dt).div(255)
            _, pha, *rec = m(t, *rec, ratio)
            pha.float().cpu()
    if d=="mps": torch.mps.synchronize()
    n = len(frames)-5
    return n/(time.time()-t0)
out = []
for name, ratio, half, d in [("fp32 ratio 0.4 (current)",0.4,False,"mps"),("fp32 ratio 0.25",0.25,False,"mps"),("fp32 ratio 0.5",0.5,False,"mps"),
                             ("fp16 ratio 0.4",0.4,True,"mps"),("fp16 ratio 0.25",0.25,True,"mps"),("CPU fp32 ratio 0.4",0.4,False,"cpu")]:
    base = MattingNetwork("mobilenetv3").eval(); base.load_state_dict(torch.load(os.path.join(here,"weights","rvm_mobilenetv3.pth"),map_location="cpu"))
    try: fps = run(ratio, half, d)
    except Exception as e: fps = None; print(name, "failed", str(e)[:80])
    print(f"{name}: {fps and round(fps,1)} fps"); out.append({"name":name,"fps":fps})
json.dump({"frames":len(frames)-5,"res":list(frames[0].shape[1::-1]),"model_only_fps":out}, open(os.path.join(here,"docs","bench.json"),"w"), indent=1)
