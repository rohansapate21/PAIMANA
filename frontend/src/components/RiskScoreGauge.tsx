import React from 'react';

interface RiskScoreGaugeProps {
  score: number;
  size?: number;
}

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({ score, size = 140 }) => {
  const normalizedScore = Math.min(100, Math.max(0, score || 0));
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = Math.PI * radius; // Half circle
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let color = '#10b981'; // Green
  if (normalizedScore >= 70) {
    color = '#ef4444'; // Red
  } else if (normalizedScore >= 40) {
    color = '#f59e0b'; // Amber
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size / 2 + 15 }}>
        <svg width={size} height={size / 2 + 10} className="overflow-visible">
          {/* Background track */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
            fill="none"
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Active fill */}
          <path
            d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-3xl font-black text-slate-900 leading-none">{normalizedScore.toFixed(1)}</span>
          <span className="text-[10px] text-slate-400 uppercase font-semibold mt-0.5">Risk Score</span>
        </div>
      </div>
    </div>
  );
};

