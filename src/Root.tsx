import React from 'react';
import {Composition} from 'remotion';
import {Composite} from './Composite';

export const FPS = 30;
export const DURATION = 360; // 12s @ 30fps

export const Root: React.FC = () => (
  <Composition id="Composite" component={Composite} durationInFrames={DURATION}
    fps={FPS} width={1920} height={1080} />
);
