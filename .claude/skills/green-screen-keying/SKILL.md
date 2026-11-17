---
name: green-screen-keying
description: Use when removing a green/blue screen from video, creating a transparent person cutout, or compositing a subject over a new background. Covers RVM matting, chroma-key refinement, despill, VP9 alpha encoding, and Remotion compositing in this repo.
---

# Green-screen keying (RVM + chroma hybrid)

## Workflow
1. **Inspect**: `ffprobe` the clip; run `ffmpeg -vf cropdetect` to find pillarbox bars. Trim to the section you need first.
2. **Matte**: `python key_fast.py clip.mp4 public/fg.webm` (RVM MobileNetV3, MPS, ratio 0.4, piped to ffmpeg). Use `key.py` if you need PNG frames.
3. **Verify before rendering**: composite one frame over the background and look at it (edges, fingers, held props, green fringe).
4. **Compose**: Remotion `Composite` uses `OffthreadVideo transparent` for `public/fg.webm` over `public/background.jpg`.
5. **Render**: `npm run render` (pass `--browser-executable` for installed Chrome if Remotion's bundled browser fails).

## Tuning rules
- Soft/blobby edges: raise downsample ratio (0.4 → 0.5). Background bleeds through: lower it.
- Holes in subject: the merge keeps `max(rvm, chroma)` where RVM > 0.98; check the threshold.
- Green fringe on skin/hair: tighten the despill (`g = min(g, (r+b)/2)`).
- Flicker: RVM state is recurrent; never reset `rec` between frames of one shot.

## Pitfalls
- RVM is trained on people; held props can vanish.
- Chroma key needs even screen lighting.
- The bottleneck is CPU post-processing and PNG writes, not the model (see docs/performance.html).
