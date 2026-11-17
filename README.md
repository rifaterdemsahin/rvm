> https://rifaterdemsahin.github.io/rvm/
> 
# rvm

Yes. Running locally works well, and **RobustVideoMatting (RVM)** is the most practical choice: free, fast, stable on video, and it runs on an Apple Silicon Mac.

**Which model for which machine**
| Machine | Model | Speed (1080p) |
|---|---|---|
| MacBook (M-series) | RVM MobileNetV3 | near real-time to a few fps |
| NVIDIA GPU box | RVM ResNet50 or **MatAnyone** | MatAnyone gives the best hair detail |
| CPU only | RVM MobileNetV3 | slow, but works |

**Setup (one-off)**
```bash
python3 -m venv ~/rvm && source ~/rvm/bin/activate
pip install torch torchvision av tqdm pims
brew install ffmpeg
```

**key.py**
```python
import sys, torch
src, out = sys.argv[1], sys.argv[2]
dev = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

model = torch.hub.load("PeterL1n/RobustVideoMatting", "mobilenetv3").to(dev).eval()
convert = torch.hub.load("PeterL1n/RobustVideoMatting", "converter")

convert(model,
        input_source=src,
        output_type="png_sequence",
        output_composition=out,   # RGBA PNGs = cutout with alpha
        downsample_ratio=0.25,    # 0.25 for 1080p, 0.125 for 4K
        seq_chunk=8,
        device=dev)
```

**Run it and wrap it for Resolve**
```bash
python key.py clip.mp4 frames
ffmpeg -framerate 25 -i frames/%04d.png \
  -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le clip_keyed.mov
```
Set `-framerate` to your clip's fps. Drop `clip_keyed.mov` above your background in Resolve: the transparency comes through automatically. Keep the original clip for the audio.

**How to get a good result**
- **Downsample ratio matters most.** If edges look soft or blobby, try 0.4. If the background bleeds through, go lower.
- **Fix spill afterwards.** Add a Despill or Hue vs Sat node in Resolve, because RVM cuts the person out but doesn't remove green reflections on skin and hair.
- **For hair-heavy shots**, use the hybrid from before: RVM matte for the body, Delta Keyer for the edges.
- **Trim first.** Process only the section you're using, not the full recording.

**Limits**
- RVM is trained on people. It handles a person well but can miss props held in the hand, like a mug or a pen.
- Fast arm movement can blur the edges. MatAnyone handles that better if you have a CUDA GPU.

I can turn this into a batch script for your Shorts pipeline: drop clips into a folder and get ProRes 4444 cutouts back. Or I can test it on one of your clips here first, if you upload one.
