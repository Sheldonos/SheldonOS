import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

interface DataPoint {
  label: string;
  value: number;
}

interface DataVisualizationProps {
  data: DataPoint[];
  title: string;
}

export const DataVisualization: React.FC<DataVisualizationProps> = ({
  data,
  title,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const maxValue = Math.max(...data.map((d) => d.value));
  const barWidth = (width * 0.8) / data.length;
  const chartHeight = height * 0.6;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#f0f0f0',
        padding: 60,
      }}
    >
      {/* Title */}
      <div
        style={{
          fontSize: 48,
          fontWeight: 'bold',
          marginBottom: 40,
          textAlign: 'center',
        }}
      >
        {title}
      </div>

      {/* Chart */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'center',
          height: chartHeight,
          gap: 20,
        }}
      >
        {data.map((point, index) => {
          // Animate each bar with a delay
          const barHeight = interpolate(
            frame,
            [index * 10, index * 10 + 30],
            [0, (point.value / maxValue) * chartHeight],
            {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }
          );

          return (
            <div
              key={point.label}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              {/* Value label */}
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 'bold',
                  marginBottom: 10,
                }}
              >
                {point.value}
              </div>

              {/* Bar */}
              <div
                style={{
                  width: barWidth - 20,
                  height: barHeight,
                  backgroundColor: `hsl(${(index * 360) / data.length}, 70%, 50%)`,
                  borderRadius: 8,
                }}
              />

              {/* Label */}
              <div
                style={{
                  fontSize: 18,
                  marginTop: 10,
                  textAlign: 'center',
                }}
              >
                {point.label}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
