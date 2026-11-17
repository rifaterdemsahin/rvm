"""Faster variant of key.py: no PNG files. Raw RGBA frames are piped straight into ffmpeg -> transparent VP9 WebM.
Usage: python key_fast.py clip.mp4 out.webm"""
import sys, os, subprocess, time, torch, numpy as np, cv2, av
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "third_party_rvm"))
from model import MattingNetwork
src_text = open(os.path.join(here, "key.py")).read()
ns = {}
exec(src_text[src_text.index("def chroma_alpha"):src_text.index("container = av.open")], {"np": np, "cv2": cv2}, ns)
chroma_alpha, despill = ns["chroma_alpha"], ns["despill"]

src, out = sys.argv[1], sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
dev = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
model = MattingNetwork("mobilenetv3").eval().to(dev)
model.load_state_dict(torch.load(os.path.join(here, "weights", "rvm_mobilenetv3.pth"), map_location=dev))
c = av.open(src); st = c.streams.video[0]; W, H = st.codec_context.width, st.codec_context.height
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                       "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "22", "-auto-alt-ref", "0",
                       "-row-mt", "1", "-cpu-used", "4", out], stdin=subprocess.PIPE)
rec = [None] * 4; t0 = time.time(); n = 0
with torch.no_grad():
    for i, frame in enumerate(c.decode(st)):
        if LIMIT and i >= LIMIT: break
        rgb = frame.to_ndarray(format="rgb24")
        t = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255)[None].to(dev)
        _, pha, *rec = model(t, *rec, 0.4)
        rvm = pha[0, 0].cpu().numpy(); ck = chroma_alpha(rgb)
        alpha = np.minimum(rvm, ck)
        alpha = np.where(rvm > 0.98, np.maximum(alpha, ck), alpha)
        alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
        alpha = np.clip((alpha - 0.05) / 0.9, 0, 1)
        ff.stdin.write(np.dstack([despill(rgb, alpha), (alpha * 255).astype(np.uint8)]).tobytes()); n += 1
ff.stdin.close(); ff.wait()
print(f"device={dev} {n} frames in {time.time()-t0:.1f}s -> {n/(time.time()-t0):.1f} fps end-to-end (matte+encode)")
