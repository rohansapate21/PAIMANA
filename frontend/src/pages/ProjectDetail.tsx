import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchProjectRisk, fetchProjectHistory } from '../api/client';
import {
  ArrowLeft,
  AlertTriangle,
  ShieldAlert,
  Clock,
  IndianRupee,
  Activity,
  Info,
  Calendar,
  Building,
  CheckCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
  Cell,
} from 'recharts';

export const ProjectDetail: React.FC = () => {
  const { uid } = useParams<{ uid: string }>();

  const { data: project, isLoading: loadingProject } = useQuery({
    queryKey: ['projectRisk', uid],
    queryFn: () => fetchProjectRisk(uid || ''),
    enabled: !!uid,
  });

  const { data: history, isLoading: loadingHistory } = useQuery({
    queryKey: ['projectHistory', uid],
    queryFn: () => fetchProjectHistory(uid || ''),
    enabled: !!uid,
  });

  if (loadingProject) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-500 flex items-center space-x-2">
          <div className="w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
          <span>Loading 360° risk evaluation...</span>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
        <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto mb-2" />
        <h2 className="text-lg font-bold text-slate-800">Project Not Found</h2>
        <p className="text-xs text-slate-500 mt-1">
          Could not locate infrastructure project with UID: <code className="font-mono">{uid}</code>
        </p>
        <Link
          to="/projects"
          className="mt-4 inline-flex items-center text-xs font-semibold text-sky-600 hover:text-sky-700"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Projects List
        </Link>
      </div>
    );
  }

  const { risk_assessment, latest_metrics, explanations, alerts } = project;
  const isHighRisk = risk_assessment.risk_band === 'High';

  // Format SHAP data for horizontal bar chart
  const shapChartData = explanations.map((e) => ({
    name: e.feature_name.replace(/_/g, ' '),
    impact: Number(e.shap_value.toFixed(3)),
    isPositive: e.shap_value >= 0,
  }));

  // Format timeline data
  const timelineData = history?.map((h) => ({
    month: h.report_month,
    sanctionedCost: project.original_cost_cr || 0,
    revisedCost: h.revised_cost_cr || 0,
    expenditure: h.expenditure_cr || 0,
    progress: h.physical_progress_pct || 0,
    delayMonths: h.schedule_delay_months || 0,
    riskScore: h.risk_score || 0,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link to="/projects" className="inline-flex items-center text-xs font-semibold text-sky-600 hover:text-sky-700">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Projects List
        </Link>
      </div>

      {/* Project Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                {project.project_uid}
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-sky-50 text-sky-700 border border-sky-100">
                {project.sector}
              </span>
              {project.state && (
                <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-slate-100 text-slate-600">
                  {project.state}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">{project.project_name}</h1>
            <p className="text-sm text-slate-500">
              {project.ministry} • Agency:{' '}
              <span className="font-medium text-slate-700">{project.implementing_agency || 'MoSPI Central Agency'}</span>
            </p>
          </div>

          {/* Risk Score Pill */}
          <div className="flex items-center space-x-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div className="text-right">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Composite Risk</div>
              <div className="text-3xl font-black text-slate-900 mt-0.5">
                {risk_assessment.risk_score?.toFixed(1) || 'N/A'}
              </div>
            </div>
            <div
              className={`px-3 py-1.5 rounded-lg text-sm font-bold border ${
                isHighRisk
                  ? 'bg-rose-100 text-rose-800 border-rose-200'
                  : risk_assessment.risk_band === 'Medium'
                  ? 'bg-amber-100 text-amber-800 border-amber-200'
                  : 'bg-emerald-100 text-emerald-800 border-emerald-200'
              }`}
            >
              {risk_assessment.risk_band} Risk
            </div>
          </div>
        </div>

        {/* Milestone Cards Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-100 text-sm">
          <div>
            <span className="text-xs text-slate-400">Sanctioned Cost</span>
            <div className="text-base font-bold text-slate-900">
              ₹{(project.original_cost_cr || 0).toLocaleString()} Cr
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-400">Current Cost</span>
            <div className="text-base font-bold text-slate-900">
              ₹{(latest_metrics.revised_cost_cr || 0).toLocaleString()} Cr
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-400">Physical Progress</span>
            <div className="text-base font-bold text-slate-900">{latest_metrics.physical_progress_pct || 0}%</div>
          </div>
          <div>
            <span className="text-xs text-slate-400">Schedule Delay</span>
            <div className="text-base font-bold text-rose-600">
              {latest_metrics.schedule_delay_months || 0} months
            </div>
          </div>
        </div>
      </div>

      {/* SHAP Natural Language Explanation & Root Cause Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* SHAP Summary Text */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
              <Info className="w-5 h-5 text-sky-600" />
              <h2 className="text-base font-bold text-slate-900">AI Root Cause & Diagnostic Summary</h2>
            </div>
            <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm leading-relaxed text-slate-700">
              {risk_assessment.shap_explanation || 'No significant risk triggers detected for this reporting month.'}
            </div>

            {/* Model Breakdown Probabilities */}
            <div className="mt-4 space-y-2 text-xs">
              <div className="flex justify-between p-2 rounded bg-slate-50 border border-slate-100">
                <span className="text-slate-600">Severe Cost Overrun Probability:</span>
                <span className="font-bold text-slate-800">
                  {risk_assessment.cost_risk_prob != null ? `${(risk_assessment.cost_risk_prob * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between p-2 rounded bg-slate-50 border border-slate-100">
                <span className="text-slate-600">Severe Delay Probability:</span>
                <span className="font-bold text-slate-800">
                  {risk_assessment.delay_risk_prob != null ? `${(risk_assessment.delay_risk_prob * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between p-2 rounded bg-slate-50 border border-slate-100">
                <span className="text-slate-600">Deterministic Safety Rule Score:</span>
                <span className="font-bold text-rose-600">
                  {risk_assessment.rule_score != null ? `${risk_assessment.rule_score} pts` : '0 pts'}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 text-[11px] text-slate-400">
            Model Engine: LightGBM + XGBoost + TreeExplainer SHAP (Version: {risk_assessment.model_version})
          </div>
        </div>

        {/* SHAP Feature Contribution Bar Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm lg:col-span-7 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900">Top Predictive Risk Contributors (SHAP Values)</h2>
            <span className="text-xs text-rose-600 font-semibold">+ Impacts Risk</span>
          </div>
          <div className="h-64 w-full mt-3">
            {shapChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={shapChartData} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                  <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={11} width={100} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    formatter={(val: any) => [`Impact: ${val}`, 'SHAP Contribution']}
                  />
                  <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                    {shapChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.isPositive ? '#ef4444' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No feature contributions recorded.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Historical Longitudinal Trends */}
      {timelineData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost Revision & Expenditure Trajectory */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-2">Cost & Expenditure Progression (₹ Cr)</h3>
            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} />
                  <YAxis stroke="#94a3b8" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                  <Line
                    type="stepAfter"
                    dataKey="revisedCost"
                    name="Revised Cost"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="expenditure"
                    name="Expenditure"
                    stroke="#0284c7"
                    strokeWidth={2}
                    dot={{ r: 2 }}
                  />
                  <ReferenceLine
                    y={project.original_cost_cr || 0}
                    label={{ value: 'Original Sanction', fill: '#64748b', fontSize: 10 }}
                    stroke="#64748b"
                    strokeDasharray="4 4"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Physical Progress & Delay Progression */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-2">Physical Progress (%) & Delay (Months)</h3>
            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} />
                  <YAxis stroke="#94a3b8" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                  <Area
                    type="monotone"
                    dataKey="progress"
                    name="Progress (%)"
                    stroke="#0ea5e9"
                    fill="#e0f2fe"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="delayMonths"
                    name="Delay (Months)"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={{ r: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Early Warning Alerts Attached to this Project */}
      {alerts && alerts.length > 0 && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-3 flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <span>Active Project Warnings ({alerts.length})</span>
          </h3>
          <div className="space-y-2">
            {alerts.map((a) => (
              <div
                key={a.id}
                className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-xs"
              >
                <div>
                  <span
                    className={`font-bold mr-2 px-2 py-0.5 rounded ${
                      a.severity === 'High' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                    }`}
                  >
                    {a.severity}
                  </span>
                  <span className="font-semibold text-slate-800">{a.reason}</span>
                </div>
                <div className="text-slate-400 font-mono">
                  {a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Active'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
