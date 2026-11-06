import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchStateBreakdown, StateBreakdown } from '../api/client';
import { MapPin, Search, ArrowRight, ShieldAlert } from 'lucide-react';

export const IndiaMap: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');

  const { data: states, isLoading } = useQuery({
    queryKey: ['stateBreakdown'],
    queryFn: fetchStateBreakdown,
  });

  const filteredStates = states?.filter((s) =>
    s.state.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (isLoading) {
    return <div className="p-8 text-center text-slate-500">Loading State-wise surveillance data...</div>;
  }

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-sky-50 text-sky-600 rounded-lg">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">State-wise Infrastructure Risk Surveillance</h2>
            <p className="text-xs text-slate-500">Click any state to drill into its active project portfolio.</p>
          </div>
        </div>

        {/* State Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search state..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>
      </div>

      {/* States Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-96 overflow-y-auto pr-1">
        {filteredStates.map((s) => {
          const isHigh = s.avg_risk_score >= 50;
          const isMed = s.avg_risk_score >= 35 && s.avg_risk_score < 50;
          const scoreBadge = isHigh
            ? 'bg-rose-100 text-rose-800'
            : isMed
            ? 'bg-amber-100 text-amber-800'
            : 'bg-emerald-100 text-emerald-800';

          return (
            <div
              key={s.state}
              onClick={() => navigate(`/projects?state=${encodeURIComponent(s.state)}`)}
              className="p-3.5 rounded-xl border border-slate-200 hover:border-sky-300 hover:bg-sky-50/30 transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-slate-900 text-sm group-hover:text-sky-600 transition truncate max-w-[140px]" title={s.state}>
                    {s.state}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {s.total_projects} projects
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${scoreBadge}`}>
                  {s.avg_risk_score.toFixed(1)}
                </span>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
                {s.high_risk_count > 0 ? (
                  <span className="text-rose-600 font-semibold flex items-center">
                    <ShieldAlert className="w-3 h-3 mr-1" />
                    {s.high_risk_count} High Risk
                  </span>
                ) : (
                  <span className="text-slate-400">0 High Risk</span>
                )}
                <span className="text-slate-500">₹{(s.total_original_cost_cr / 1000).toFixed(1)}k Cr</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

