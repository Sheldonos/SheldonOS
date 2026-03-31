# Remotion Rendering Options

## CLI Rendering

### Basic Rendering
```bash
npx remotion render <composition-id> [output-path]
```

### Common Options

**Quality & Format**
- `--codec`: Video codec (h264, h265, vp8, vp9, prores)
- `--quality`: Quality setting 0-100 (higher is better)
- `--crf`: CRF value for quality control (lower is better, 18 recommended)
- `--image-format`: Frame format (jpeg, png)

**Performance**
- `--concurrency`: Number of parallel rendering threads
- `--timeout`: Timeout for rendering in milliseconds

**Output**
- `--output`: Output file path
- `--overwrite`: Overwrite existing output file
- `--sequence`: Output as image sequence instead of video

**Scaling**
- `--scale`: Scale factor (e.g., 0.5 for half size)

**Props**
- `--props`: JSON string of props to pass to composition

### Examples

High quality H.264:
```bash
npx remotion render MyVideo out.mp4 --codec=h264 --crf=18
```

Fast preview:
```bash
npx remotion render MyVideo --scale=0.5 --quality=50
```

With custom props:
```bash
npx remotion render MyVideo --props='{"title":"Hello","color":"blue"}'
```

## Programmatic Rendering

### Using renderMedia()

```typescript
import { renderMedia, selectComposition } from '@remotion/renderer';
import path from 'path';

const compositionId = 'MyVideo';
const bundleLocation = path.join(process.cwd(), 'out');

const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: compositionId,
});

await renderMedia({
  composition,
  serveUrl: bundleLocation,
  codec: 'h264',
  outputLocation: 'out/video.mp4',
  inputProps: {
    title: 'Custom Title',
  },
});
```

## Rendering Formats

### Video Formats
- **MP4 (H.264)**: Most compatible, good quality
- **MP4 (H.265)**: Better compression, smaller files
- **WebM (VP8/VP9)**: Web-optimized format
- **ProRes**: High-quality for editing

### Image Sequences
Use `--sequence` to output frames as images:
```bash
npx remotion render MyVideo --sequence
```

### Still Images
Render a single frame:
```bash
npx remotion still MyVideo out.png --frame=30
```

### GIF
```bash
npx remotion render MyVideo out.gif
```

## Server-Side Rendering

### Remotion Lambda
Deploy to AWS Lambda for scalable cloud rendering:

```bash
npx remotion lambda render <composition-id>
```

### Cloud Run
Deploy to Google Cloud Run (alpha):

```bash
npx remotion cloudrun render <composition-id>
```

## Quality Guidelines

### Recommended Settings

**High Quality (for final output)**
- Codec: h264 or h265
- CRF: 18
- Image format: png (if transparency needed)

**Medium Quality (for previews)**
- Codec: h264
- Quality: 80
- Scale: 1.0

**Low Quality (for fast iteration)**
- Codec: h264
- Quality: 50
- Scale: 0.5
- Concurrency: max available

## Performance Optimization

### Concurrency
Set to number of CPU cores for best performance:
```bash
npx remotion render MyVideo --concurrency=8
```

### Image Format
- Use `jpeg` for faster rendering (default)
- Use `png` only when transparency is needed

### Scale
Reduce scale for faster preview renders:
```bash
npx remotion render MyVideo --scale=0.5
```

## Troubleshooting

### Out of Memory
- Reduce concurrency
- Reduce scale
- Use jpeg instead of png

### Slow Rendering
- Increase concurrency
- Simplify composition (fewer effects)
- Use hardware acceleration if available

### Quality Issues
- Increase CRF value (lower number = better quality)
- Use png image format
- Increase quality setting
