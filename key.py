"""RVM matte + chroma-key refinement + despill -> RGBA PNG sequence."""
import sys, os, torch, numpy as np, cv2, av
from tqdm import tqdm

src, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
dev = "mps" if torch.backends.mps.is_available() else "cpu"
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "third_party_rvm"))
from model import MattingNetwork
model = MattingNetwork("mobilenetv3").eval().to(dev)
model.load_state_dict(torch.load(os.path.join(here, "weights", "rvm_mobilenetv3.pth"), map_location=dev))
import time, json
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
times = []

def chroma_alpha(rgb):
    """Soft green-screen key: how 'not green' is each pixel (0..1)."""
    f = rgb.astype(np.float32) / 255
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    greenness = g - np.maximum(r, b)              # >0 where green dominates
    a = 1 - np.clip((greenness - 0.10) / 0.22, 0, 1)
    return a

def despill(rgb, alpha):
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    limit = (r + b) / 2                            # average despill
    g2 = np.minimum(g, limit)
    out = np.stack([r, g2, b], -1)
    return np.clip(out, 0, 255).astype(np.uint8)

container = av.open(src)
stream = container.streams.video[0]
n = stream.frames or 0
rec = [None] * 4
ratio = 0.4
with torch.no_grad():
    for i, frame in enumerate(tqdm(container.decode(stream), total=n)):
        if LIMIT and i >= LIMIT: break
        t0 = time.time()
        rgb = frame.to_ndarray(format="rgb24")
        t = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255)[None].to(dev)
        fgr, pha, *rec = model(t, *rec, ratio)
        rvm = pha[0, 0].cpu().numpy()
        ck = chroma_alpha(rgb)
        # RVM gives a clean body silhouette; chroma key refines edges & kills
        # holes (between fingers). Take the min where RVM is confident-solid
        # but the key says green; keep RVM semi-transparency for hair.
        alpha = np.minimum(rvm, ck + (1 - ck) * 0.0)
        alpha = np.where(rvm > 0.98, np.maximum(alpha, ck), alpha)
        alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
        alpha = np.clip((alpha - 0.05) / 0.9, 0, 1)
        clean = despill(rgb, alpha)
        rgba = np.dstack([clean, (alpha * 255).astype(np.uint8)])
        cv2.imwrite(f"{outdir}/{i:04d}.png", cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
        times.append(time.time() - t0)
json.dump({"device": dev, "frames": len(times), "ratio": ratio, "res": [rgb.shape[1], rgb.shape[0]],
           "total_s": sum(times), "avg_fps": len(times) / sum(times), "avg_ms": 1000 * sum(times) / len(times)},
          open(os.path.join(outdir, "..", "stats.json"), "w"), indent=2)
