# Remotion API Reference

## Core Hooks

### useCurrentFrame()
Returns the current frame number (0-indexed).

```tsx
import { useCurrentFrame } from 'remotion';

const frame = useCurrentFrame();
// frame is 0 at the start, increases each frame
```

### useVideoConfig()
Returns video configuration: width, height, fps, durationInFrames.

```tsx
import { useVideoConfig } from 'remotion';

const { width, height, fps, durationInFrames } = useVideoConfig();
const durationInSeconds = durationInFrames / fps;
```

### interpolate()
Maps a frame range to a value range. Essential for animations.

```tsx
import { interpolate, useCurrentFrame } from 'remotion';

const frame = useCurrentFrame();
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

### spring()
Creates spring-based animations for natural motion.

```tsx
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const scale = spring({
  frame,
  fps,
  from: 0,
  to: 1,
  config: {
    damping: 100,
    stiffness: 200,
  },
});
```

## Layout Components

### <AbsoluteFill>
Fills the entire composition with absolute positioning.

```tsx
import { AbsoluteFill } from 'remotion';

<AbsoluteFill style={{ backgroundColor: 'blue' }}>
  <h1>Centered Content</h1>
</AbsoluteFill>
```

### <Sequence>
Shows content for a specific frame range.

```tsx
import { Sequence } from 'remotion';

<Sequence from={0} durationInFrames={60}>
  <Scene1 />
</Sequence>
<Sequence from={60} durationInFrames={60}>
  <Scene2 />
</Sequence>
```

### <Series>
Chains sequences one after another automatically.

```tsx
import { Series } from 'remotion';

<Series>
  <Series.Sequence durationInFrames={60}>
    <Scene1 />
  </Series.Sequence>
  <Series.Sequence durationInFrames={90}>
    <Scene2 />
  </Series.Sequence>
</Series>
```

## Media Components

### <Img>
Optimized image component for Remotion.

```tsx
import { Img } from 'remotion';

<Img src="/path/to/image.png" />
```

### <Video>
Video component with frame-accurate playback.

```tsx
import { Video } from 'remotion';

<Video src="/path/to/video.mp4" />
```

### <Audio>
Audio component for sound effects and music.

```tsx
import { Audio } from 'remotion';

<Audio src="/path/to/audio.mp3" volume={0.5} />
```

## Composition Registration

### <Composition>
Registers a video composition in Root.tsx.

```tsx
import { Composition } from 'remotion';
import { MyVideo } from './MyVideo';

<Composition
  id="MyVideo"
  component={MyVideo}
  durationInFrames={150}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{
    title: "Hello World"
  }}
/>
```

## Animation Utilities

### Easing Functions
Available easing functions for interpolate():

- `easeIn`, `easeOut`, `easeInOut`
- `easeInCubic`, `easeOutCubic`, `easeInOutCubic`
- `easeInQuad`, `easeOutQuad`, `easeInOutQuad`
- `easeInQuart`, `easeOutQuart`, `easeInOutQuart`

```tsx
import { interpolate, Easing } from 'remotion';

const x = interpolate(frame, [0, 100], [0, 1000], {
  easing: Easing.bezier(0.8, 0.22, 0.96, 0.65),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

## Data Fetching

### delayRender() / continueRender()
Delay rendering until async data is loaded.

```tsx
import { delayRender, continueRender } from 'remotion';
import { useEffect, useState } from 'react';

const [handle] = useState(() => delayRender());
const [data, setData] = useState(null);

useEffect(() => {
  fetch('/api/data')
    .then(res => res.json())
    .then(data => {
      setData(data);
      continueRender(handle);
    });
}, [handle]);
```

## Input Props

Access props passed to compositions:

```tsx
export const MyVideo: React.FC<{ title: string }> = ({ title }) => {
  return <h1>{title}</h1>;
};
```

Pass props via CLI:
```bash
npx remotion render MyVideo --props='{"title":"Custom Title"}'
```
