import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  triggerIngestion,
  triggerRetraining,
  fetchIngestionLogs,
  fetchDataQuality,
  fetchSystemUsers,
} from '../api/client';
import {
  Shield,
  Database,
  RefreshCw,
  CheckCircle,
  ExternalLink,
  Users,
  CheckCheck,
  FileSpreadsheet,
  AlertOctagon,
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export const AdminPanel: React.FC = () => {
  const { user } = useAuthStore();
  const [ingestMsg, setIngestMsg] = useState<string | null>(null);
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null);

  const { data: logs, refetch: refetchLogs } = useQuery({
    queryKey: ['ingestionLogs'],
    queryFn: fetchIngestionLogs,
    enabled: user?.role === 'admin',
  });

  const { data: dataQuality } = useQuery({
    queryKey: ['dataQualityReport'],
    queryFn: fetchDataQuality,
    enabled: user?.role === 'admin',
  });

  const { data: systemUsers } = useQuery({
    queryKey: ['systemUsers'],
    queryFn: fetchSystemUsers,
    enabled: user?.role === 'admin',
  });

  const ingestMutation = useMutation({
    mutationFn: triggerIngestion,
    onSuccess: (data) => {
      setIngestMsg(data.message);
      setTimeout(() => refetchLogs(), 2000);
    },
  });

  const retrainMutation = useMutation({
    mutationFn: triggerRetraining,
    onSuccess: (data) => {
      setRetrainMsg(data.message);
    },
  });

  if (user?.role !== 'admin') {
    return (
      <div className="p-16 text-center bg-white rounded-xl border border-slate-200">
        <Shield className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h2 className="text-xl font-bold text-slate-900">Administrator Clearance Required</h2>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Administrative endpoints, pipeline dispatchers, and data quality logs require elevated MoSPI Admin privileges.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System Operations & Admin Console</h1>
          <p className="text-sm text-slate-500 mt-1">
            Pipeline orchestration, continuous ML model retraining, data quality auditing, and role management.
          </p>
        </div>

        {/* MLflow Link */}
        <a
          href="http://localhost:5000"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition"
        >
          <span>MLflow Experiment Hub</span>
          <ExternalLink className="w-3.5 h-3.5 ml-1" />
        </a>
      </div>

      {/* Action Pipeline Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Ingestion Card */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-sky-50 text-sky-600 rounded-lg">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Run Automated Ingestion</h3>
              <p className="text-xs text-slate-500">
                Executes clean_master.py, pandera schemas validation, and hydrates PostgreSQL/SQLite tables.
              </p>
            </div>
          </div>

          <button
            onClick={() => ingestMutation.mutate()}
            disabled={ingestMutation.isPending}
            className="w-full py-2.5 px-4 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm rounded-lg transition disabled:opacity-50 shadow-sm"
          >
            {ingestMutation.isPending ? 'Queuing Ingestion Task...' : 'Trigger Pipeline Ingestion'}
          </button>

          {ingestMsg && (
            <div className="p-3 bg-emerald-50 text-emerald-700 text-xs rounded-lg border border-emerald-200 flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span>{ingestMsg}</span>
            </div>
          )}
        </div>

        {/* Retraining Card */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <RefreshCw className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Retrain ML Models (XGBoost + LightGBM)</h3>
              <p className="text-xs text-slate-500">
                Builds causal lag features, retrains Cost/Delay models, and re-calculates SHAP explanations.
              </p>
            </div>
          </div>

          <button
            onClick={() => retrainMutation.mutate()}
            disabled={retrainMutation.isPending}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-lg transition disabled:opacity-50 shadow-sm"
          >
            {retrainMutation.isPending ? 'Queuing Retraining Task...' : 'Trigger Model Retraining'}
          </button>

          {retrainMsg && (
            <div className="p-3 bg-emerald-50 text-emerald-700 text-xs rounded-lg border border-emerald-200 flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              <span>{retrainMsg}</span>
            </div>
          )}
        </div>
      </div>

      {/* Data Quality Report */}
      {dataQuality && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
            <CheckCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-bold text-slate-900">Data Quality & Pipeline Hygiene Audit</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-500 font-semibold uppercase">Total Projects</span>
              <div className="text-xl font-bold text-slate-900 mt-1">
                {dataQuality.total_projects.toLocaleString()}
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-500 font-semibold uppercase">Panel Observations</span>
              <div className="text-xl font-bold text-slate-900 mt-1">
                {dataQuality.total_observations.toLocaleString()}
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-[11px] text-slate-500 font-semibold uppercase">Outlier Flags</span>
              <div className="text-xl font-bold text-amber-600 mt-1">
                {dataQuality.outlier_flagged_records}
              </div>
            </div>
            <div className="p-3 bg-emerald-50/40 rounded-xl border border-emerald-200">
              <span className="text-[11px] text-emerald-700 font-semibold uppercase">Completeness</span>
              <div className="text-xl font-bold text-emerald-600 mt-1">
                {dataQuality.completeness_score_pct}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Management Section */}
      {systemUsers && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <Users className="w-5 h-5 text-sky-600" />
            <h2 className="text-base font-bold text-slate-900">Registered System Users & RBAC Roles</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Email</th>
                  <th className="py-2.5 px-3 text-center">Role</th>
                  <th className="py-2.5 px-3">Ministry Scope</th>
                  <th className="py-2.5 px-3 text-right">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {systemUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-semibold text-slate-900">{u.full_name || 'System User'}</td>
                    <td className="py-2.5 px-3 font-mono text-xs text-slate-600">{u.email}</td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                          u.role === 'admin'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-sky-100 text-sky-800'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-xs text-slate-500">
                      {u.ministry_scope || 'All Ministries (National Scope)'}
                    </td>
                    <td className="py-2.5 px-3 text-right text-xs text-slate-400 font-mono">
                      {u.id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Ingestion Audit Trail */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 mb-4">Ingestion Execution Audit Trail</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs font-semibold text-slate-500 uppercase">
                <th className="py-2.5 px-3">Run Timestamp</th>
                <th className="py-2.5 px-3">Report Period</th>
                <th className="py-2.5 px-3 text-right">Rows Ingested</th>
                <th className="py-2.5 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs?.map((l: any) => (
                <tr key={l.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-mono text-xs text-slate-600">{l.run_at}</td>
                  <td className="py-2.5 px-3 font-medium text-slate-800">{l.report_month}</td>
                  <td className="py-2.5 px-3 text-right font-mono">{l.rows_extracted?.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {l.status}
                    </span>
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
