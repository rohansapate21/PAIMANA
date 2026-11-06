import React from 'react';
import { ResponsiveContainer, AreaChart, Area } from 'recharts';

interface MiniSparklineProps {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export const MiniSparkline: React.FC<MiniSparklineProps> = ({
  data,
  color = '#0ea5e9',
  width = 65,
  height = 20,
}) => {
  if (!data || data.length === 0) return null;

  const chartData = data.map((val, idx) => ({ idx, val }));

  return (
    <div style={{ width, height }} className="inline-block overflow-hidden">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 1, right: 1, left: 1, bottom: 1 }}>
          <Area
            type="monotone"
            dataKey="val"
            stroke={color}
            fill={color}
            fillOpacity={0.15}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

