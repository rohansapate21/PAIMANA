import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  fetchDashboardSummary,
  fetchMinistryBreakdown,
  fetchRiskTrend,
  fetchProjects,
} from '../api/client';
import {
  AlertTriangle,
  TrendingUp,
  IndianRupee,
  Clock,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { IndiaMap } from '../components/IndiaMap';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

const RISK_COLORS = {
  High: '#ef4444',
  Medium: '#f59e0b',
  Low: '#10b981',
};

export const Overview: React.FC = () => {
  const navigate = useNavigate();

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: fetchDashboardSummary,
  });

  const { data: ministries, isLoading: loadingMinistries } = useQuery({
    queryKey: ['ministryBreakdown'],
    queryFn: fetchMinistryBreakdown,
  });

  const { data: trend, isLoading: loadingTrend } = useQuery({
    queryKey: ['riskTrend'],
    queryFn: fetchRiskTrend,
  });

  const { data: topRisks, isLoading: loadingTopRisks } = useQuery({
    queryKey: ['topHighRiskProjects'],
    queryFn: () => fetchProjects({ sort_by: 'risk_score', sort_order: 'desc', limit: 10 }),
  });

  if (loadingSummary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-500 flex items-center space-x-2">
          <div className="w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading portfolio overview...</span>
        </div>
      </div>
    );
  }

  const highPct =
    summary && summary.active_scored_projects > 0
      ? ((summary.high_risk_count / summary.active_scored_projects) * 100).toFixed(1)
      : '0.0';

  const donutData = summary
    ? [
        { name: 'High', value: summary.high_risk_count, color: RISK_COLORS.High },
        { name: 'Medium', value: summary.medium_risk_count, color: RISK_COLORS.Medium },
        { name: 'Low', value: summary.low_risk_count, color: RISK_COLORS.Low },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Risk Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time portfolio surveillance for major infrastructure projects (₹150+ Cr). Reporting Period:{' '}
            <span className="font-semibold text-slate-700">{summary?.latest_report_month || '2026-08'}</span>
          </p>
        </div>
        <div className="mt-3 sm:mt-0 flex items-center space-x-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
            AI Surveillance Active
          </span>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Tracked Projects */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Tracked</span>
            <div className="p-2 bg-sky-50 text-sky-600 rounded-lg">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">{summary?.total_projects.toLocaleString()}</span>
            <span className="text-xs text-slate-500">projects</span>
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Active Scored (Latest): <span className="font-semibold text-slate-700">{summary?.active_scored_projects}</span>
          </div>
        </div>

        {/* High Risk Proportion */}
        <div className="bg-white p-5 rounded-xl border border-rose-200 bg-rose-50/20 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider">High Risk Share</span>
            <div className="p-2 bg-rose-100 text-rose-600 rounded-lg">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-rose-600">{highPct}%</span>
            <span className="text-xs text-rose-500">({summary?.high_risk_count} projects)</span>
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Rules Violations: <span className="font-semibold text-rose-600">{summary?.rule_triggered_count}</span>
          </div>
        </div>

        {/* Cost & Expenditure */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Sanctioned</span>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <IndianRupee className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">
              ₹{(summary?.total_original_cost_cr || 0).toLocaleString()}
            </span>
            <span className="text-xs text-slate-500">Cr</span>
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Cumulative Spent: ₹{(summary?.total_expenditure_cr || 0).toLocaleString()} Cr
          </div>
        </div>

        {/* Schedule Delay */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Avg Schedule Delay</span>
            <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">{summary?.avg_schedule_delay_months}</span>
            <span className="text-xs text-slate-500">months</span>
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Active Alerts: <span className="font-semibold text-amber-600">{summary?.active_alerts_count}</span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Row: Risk Donut + Trend Line */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Donut Chart: Risk Distribution */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm lg:col-span-5 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold text-slate-800">Risk Band Breakdown</h2>
            <span className="text-xs text-slate-400">Click slice to filter</span>
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={4}
                  dataKey="value"
                  onClick={(entry) => navigate(`/projects?risk_band=${entry.name}`)}
                  className="cursor-pointer focus:outline-none"
                >
                  {donutData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any, name: any) => [`${value} Projects`, `${name} Risk`]}
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100 text-center text-xs">
            <div
              onClick={() => navigate('/projects?risk_band=High')}
              className="p-1.5 rounded cursor-pointer hover:bg-rose-50 transition"
            >
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-rose-500 mr-1" />
              <span className="font-semibold text-rose-600">High ({summary?.high_risk_count})</span>
            </div>
            <div
              onClick={() => navigate('/projects?risk_band=Medium')}
              className="p-1.5 rounded cursor-pointer hover:bg-amber-50 transition"
            >
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-amber-500 mr-1" />
              <span className="font-semibold text-amber-600">Medium ({summary?.medium_risk_count})</span>
            </div>
            <div
              onClick={() => navigate('/projects?risk_band=Low')}
              className="p-1.5 rounded cursor-pointer hover:bg-emerald-50 transition"
            >
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 mr-1" />
              <span className="font-semibold text-emerald-600">Low ({summary?.low_risk_count})</span>
            </div>
          </div>
        </div>

        {/* Risk Trend Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm lg:col-span-7 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold text-slate-800">Longitudinal Risk Trend</h2>
            <span className="text-xs text-slate-400">Monthly Project Counts</span>
          </div>
          <div className="h-64 w-full">
            {trend && trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="report_month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                  <Line type="monotone" dataKey="High" stroke={RISK_COLORS.High} strokeWidth={2.5} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="Medium" stroke={RISK_COLORS.Medium} strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="Low" stroke={RISK_COLORS.Low} strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No longitudinal trend data available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* State-wise Surveillance Map Grid */}
      <IndiaMap />

      {/* Top 10 Highest Risk Projects Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Highest Risk Projects Requiring Urgent Intervention</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked by composite risk score (Cost Overrun Risk + Delay Risk + Stagnation + Violations)
            </p>
          </div>
          <button
            onClick={() => navigate('/projects?risk_band=High')}
            className="inline-flex items-center text-xs font-semibold text-sky-600 hover:text-sky-700"
          >
            <span>View All High Risk</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-4">Project</th>
                <th className="py-3 px-4">Ministry</th>
                <th className="py-3 px-4 text-right">Sanctioned (₹ Cr)</th>
                <th className="py-3 px-4 text-right">Delay (Mos)</th>
                <th className="py-3 px-4 text-center">Risk Score</th>
                <th className="py-3 px-4 text-center">Safety Rules</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {topRisks?.items.map((p) => (
                <tr key={p.project_uid} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 max-w-sm">
                    <div className="font-semibold text-slate-900 truncate" title={p.project_name}>
                      {p.project_name}
                    </div>
                    <div className="text-xs text-slate-400 font-mono">{p.project_uid} • {p.sector}</div>
                  </td>
                  <td className="py-3 px-4 text-slate-600 max-w-[200px] truncate" title={p.ministry}>
                    {p.ministry}
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-slate-800">
                    ₹{(p.original_cost_cr || 0).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="font-semibold text-rose-600">{p.schedule_delay_months || 0} mos</span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      {p.risk_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    {p.rule_triggered ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-800">
                        Triggered
                      </span>
                    ) : (
                      <span className="text-slate-400 text-xs">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => navigate(`/projects/${encodeURIComponent(p.project_uid)}`)}
                      className="p-1.5 text-sky-600 hover:text-sky-800 hover:bg-sky-50 rounded transition"
                      title="Inspect Root Cause"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
