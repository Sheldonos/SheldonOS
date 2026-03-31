import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';

export const BasicComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: 'white',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <div style={{ fontSize: 60, color: 'black' }}>
        Frame: {frame} / {durationInFrames}
      </div>
    </AbsoluteFill>
  );
};
