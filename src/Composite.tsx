import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

// Layers: background (slow push-in + soft depth blur) -> RVM/chroma-keyed
// person (transparent WebM) -> grade + vignette. Audio from the original clip.
export const Composite: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const zoom = interpolate(frame, [0, durationInFrames], [1.04, 1.12]);
  const fade = interpolate(frame, [0, 10, durationInFrames - 10, durationInFrames], [0, 1, 1, 0]);

  return (
    <AbsoluteFill style={{backgroundColor: '#000', opacity: fade}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>
        <Img src={staticFile('background.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(3px) brightness(0.92)'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
        <OffthreadVideo src={staticFile('fg.webm')} transparent muted
          style={{height: '100%', filter: 'contrast(1.05) saturate(1.05) drop-shadow(0 0 18px rgba(0,0,0,0.35))'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)'}} />
      <Audio src={staticFile('audio.m4a')} />
    </AbsoluteFill>
  );
};
