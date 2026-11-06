import React from 'react';

export const CardSkeleton: React.FC = () => (
  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm animate-pulse space-y-3">
    <div className="flex justify-between items-center">
      <div className="h-3 bg-slate-200 rounded w-24" />
      <div className="w-8 h-8 bg-slate-200 rounded-lg" />
    </div>
    <div className="h-7 bg-slate-200 rounded w-20" />
    <div className="h-3 bg-slate-100 rounded w-36" />
  </div>
);

export const TableRowSkeleton: React.FC<{ cols?: number }> = ({ cols = 6 }) => (
  <tr className="animate-pulse">
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i} className="py-3 px-4">
        <div className="h-4 bg-slate-200 rounded w-full" />
      </td>
    ))}
  </tr>
);

