---
name: remotion-video-generator
description: Create videos programmatically using React and Remotion. Use when generating videos from code, creating animated content, data visualizations, personalized videos, or any programmatic video generation task.
---

# Remotion Video Generator

Create videos programmatically using React components. Remotion enables building videos with the full power of web technologies: React, CSS, Canvas, SVG, WebGL, and the entire npm ecosystem.

## Quick Start

### Install and Create Project

Use the setup script for fastest initialization:

```bash
bash /home/ubuntu/skills/remotion-video-generator/scripts/setup_remotion.sh my-video
```

Or manually:

```bash
npx create-video@latest my-video
cd my-video
npm run dev  # Opens Remotion Studio
```

### Create a Simple Video

Create a composition in `src/MyVideo.tsx`:

```tsx
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';

export const MyVideo: React.FC = () => {
  const frame = useCurrentFrame();
  
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: 'white', justifyContent: 'center', alignItems: 'center' }}>
      <h1 style={{ fontSize: 100, opacity }}>Hello World</h1>
    </AbsoluteFill>
  );
};
```

Register in `src/Root.tsx`:

```tsx
import { Composition } from 'remotion';
import { MyVideo } from './MyVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MyVideo"
      component={MyVideo}
      durationInFrames={150}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

### Render the Video

```bash
npx remotion render MyVideo output.mp4
```

Or use the Python wrapper:

```bash
python /home/ubuntu/skills/remotion-video-generator/scripts/render_video.py MyVideo -o output.mp4 --codec h264 --quality 90
```

## Core Concepts

### Frame-Based Rendering

Remotion renders videos frame by frame. Use `useCurrentFrame()` to get the current frame number and create animations by changing content based on the frame.

```tsx
const frame = useCurrentFrame();  // 0, 1, 2, 3, ...
```

### Video Properties

Every video has four properties accessible via `useVideoConfig()`:

- `width`: Video width in pixels
- `height`: Video height in pixels
- `fps`: Frames per second
- `durationInFrames`: Total number of frames

```tsx
const { width, height, fps, durationInFrames } = useVideoConfig();
const durationInSeconds = durationInFrames / fps;
```

### Compositions

A composition combines a React component with video metadata. Register compositions in `src/Root.tsx` to make them renderable.

### Animations

Use `interpolate()` for linear animations and `spring()` for natural motion:

```tsx
// Linear fade in
const opacity = interpolate(frame, [0, 30], [0, 1]);

// Spring animation
const scale = spring({ frame, fps, from: 0, to: 1 });
```

## Common Patterns

### Animated Text

Use the template at `/home/ubuntu/skills/remotion-video-generator/templates/animated_text.tsx` for text with fade-in, scale, and slide animations.

### Data Visualization

Use the template at `/home/ubuntu/skills/remotion-video-generator/templates/data_visualization.tsx` for animated bar charts with custom data.

### Sequences

Show different content at different times using `<Sequence>`:

```tsx
<Sequence from={0} durationInFrames={60}>
  <Scene1 />
</Sequence>
<Sequence from={60} durationInFrames={60}>
  <Scene2 />
</Sequence>
```

Or use `<Series>` to chain sequences automatically:

```tsx
<Series>
  <Series.Sequence durationInFrames={60}><Scene1 /></Series.Sequence>
  <Series.Sequence durationInFrames={60}><Scene2 /></Series.Sequence>
</Series>
```

### Adding Media

```tsx
import { Img, Video, Audio } from 'remotion';

<Img src="/path/to/image.png" />
<Video src="/path/to/video.mp4" />
<Audio src="/path/to/audio.mp3" volume={0.5} />
```

### Dynamic Props

Pass data to compositions via props:

```tsx
export const MyVideo: React.FC<{ title: string; color: string }> = ({ title, color }) => {
  return <h1 style={{ color }}>{title}</h1>;
};
```

Render with props:

```bash
npx remotion render MyVideo --props='{"title":"Custom","color":"blue"}'
```

### Async Data Loading

Use `delayRender()` and `continueRender()` for fetching data:

```tsx
const [handle] = useState(() => delayRender());
const [data, setData] = useState(null);

useEffect(() => {
  fetchData().then(result => {
    setData(result);
    continueRender(handle);
  });
}, [handle]);
```

## Rendering Options

### Quality Settings

**High quality (final output)**:
```bash
npx remotion render MyVideo output.mp4 --codec=h264 --crf=18
```

**Fast preview**:
```bash
npx remotion render MyVideo output.mp4 --scale=0.5 --quality=50
```

### Output Formats

- **Video**: MP4 (h264, h265), WebM (vp8, vp9), ProRes
- **Image sequence**: Use `--sequence` flag
- **Still image**: Use `npx remotion still MyVideo output.png --frame=30`
- **GIF**: Render with `.gif` extension

### Performance

- Set `--concurrency` to number of CPU cores for faster rendering
- Use `--scale` to reduce resolution for previews
- Use `jpeg` image format (default) for speed, `png` for transparency

For detailed rendering options, see `/home/ubuntu/skills/remotion-video-generator/references/rendering_options.md`.

## API Reference

For comprehensive API documentation including all hooks, components, and utilities, see `/home/ubuntu/skills/remotion-video-generator/references/api_reference.md`.

Key APIs:
- `useCurrentFrame()` - Get current frame number
- `useVideoConfig()` - Get video properties
- `interpolate()` - Create linear animations
- `spring()` - Create spring animations
- `<AbsoluteFill>` - Full-screen layout component
- `<Sequence>` - Time-based content display
- `<Img>`, `<Video>`, `<Audio>` - Media components

## Templates

Ready-to-use templates are available in `/home/ubuntu/skills/remotion-video-generator/templates/`:

- `basic_composition.tsx` - Simple starter template
- `animated_text.tsx` - Text with fade, scale, and slide animations
- `data_visualization.tsx` - Animated bar chart with custom data

Copy templates into your project and customize as needed.

## Troubleshooting

### Installation Issues

Ensure Node.js 16+ or Bun 1.0.3+ is installed. On Linux, install required packages:

```bash
sudo apt-get install -y chromium-browser ffmpeg
```

### Rendering Issues

**Out of memory**: Reduce `--concurrency` or `--scale`

**Slow rendering**: Increase `--concurrency`, simplify composition, or use `--scale` for previews

**Quality issues**: Lower `--crf` value (18 recommended), use `png` image format, or increase `--quality`

### Development Tips

- Use Remotion Studio (`npm run dev`) for live preview with Fast Refresh
- Test renders at low quality/scale first, then render final at high quality
- Use `console.log(frame)` to debug animation timing
- Check browser console in Studio for runtime errors

## Server-Side Rendering

For scalable cloud rendering:

**AWS Lambda** (recommended):
```bash
npx remotion lambda render MyVideo
```

**Google Cloud Run** (alpha):
```bash
npx remotion cloudrun render MyVideo
```

Both support the same composition code and rendering options.

## License

Remotion requires a company license for commercial use. See [remotion.dev/license](https://remotion.dev/license) for details.
