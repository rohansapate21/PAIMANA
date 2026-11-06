import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';

interface SHAPBarChartProps {
  features: {
    name: string;
    impact: number;
    description?: string;
  }[];
  height?: number;
}

export const SHAPBarChart: React.FC<SHAPBarChartProps> = ({ features, height = 250 }) => {
  if (!features || features.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-xs text-slate-400">
        No feature drivers available.
      </div>
    );
  }

  const sorted = [...features].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={sorted} layout="vertical" margin={{ top: 5, right: 30, left: 90, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
          <XAxis type="number" stroke="#94a3b8" fontSize={11} />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#64748b"
            fontSize={11}
            width={110}
            tickFormatter={(val) => (val.length > 18 ? `${val.substring(0, 18)}...` : val)}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
            formatter={(val: any) => [`Impact: ${val}`, 'SHAP Value']}
          />
          <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
            {sorted.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.impact >= 0 ? '#ef4444' : '#10b981'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

