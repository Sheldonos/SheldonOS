import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  spring,
} from 'remotion';

interface AnimatedTextProps {
  text: string;
  color?: string;
}

export const AnimatedText: React.FC<AnimatedTextProps> = ({
  text,
  color = '#000',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade in animation
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Spring scale animation
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

  // Slide in from left
  const translateX = interpolate(frame, [0, 30], [-100, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: 'white',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          fontSize: 80,
          fontWeight: 'bold',
          color,
          opacity,
          transform: `scale(${scale}) translateX(${translateX}px)`,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
