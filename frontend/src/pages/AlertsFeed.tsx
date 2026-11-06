import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { fetchAlerts, fetchAlertSummary, acknowledgeAlert, AlertItem } from '../api/client';
import { AlertTriangle, CheckCircle, ShieldAlert, Clock, ArrowRight, Check } from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';

export const AlertsFeed: React.FC = () => {
  const queryClient = useQueryClient();
  const [filterTab, setFilterTab] = useState<'All' | 'High' | 'Medium' | 'Unacknowledged'>('Unacknowledged');

  const { data: summary } = useQuery({
    queryKey: ['alertsSummary'],
    queryFn: fetchAlertSummary,
  });

  const severityFilter = filterTab === 'High' ? 'High' : filterTab === 'Medium' ? 'Medium' : undefined;
  const acknowledgedFilter = filterTab === 'Unacknowledged' ? false : undefined;

  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['alerts', filterTab],
    queryFn: () =>
      fetchAlerts({
        severity: severityFilter,
        acknowledged: acknowledgedFilter,
        limit: 100,
      }),
  });

  const ackMutation = useMutation({
    mutationFn: (id: number) => acknowledgeAlert(id),
    onMutate: async (id: number) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['alerts', filterTab] });
      const previous = queryClient.getQueryData(['alerts', filterTab]);
      queryClient.setQueryData(['alerts', filterTab], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          items: old.items.map((item: AlertItem) =>
            item.id === id ? { ...item, acknowledged: true } : item
          ),
        };
      });
      return { previous };
    },
    onError: (_err, _id, context: any) => {
      if (context?.previous) {
        queryClient.setQueryData(['alerts', filterTab], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alertsSummary'] });
    },
  });

  const getTypeBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case 'rule_triggered':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'ml_high_risk':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'stagnation':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'cost_spike':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Proactive Early Warning Alerts</h1>
        <p className="text-sm text-slate-500 mt-1">
          Automated multi-factor anomaly signals triggered by XGBoost/LightGBM risk thresholds and deterministic safety rules.
        </p>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Unacknowledged Alerts */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Unacknowledged</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {summary?.total_active_alerts || 0}
            </div>
            <span className="text-xs text-slate-400">Pending review</span>
          </div>
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* High Severity */}
        <div className="bg-white p-5 rounded-xl border border-rose-200 bg-rose-50/20 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider">High Severity</span>
            <div className="text-2xl font-bold text-rose-600 mt-1">
              {summary?.by_severity?.High || 0}
            </div>
            <span className="text-xs text-rose-500">Urgent intervention required</span>
          </div>
          <div className="p-3 bg-rose-100 text-rose-600 rounded-xl">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>

        {/* Medium Severity */}
        <div className="bg-white p-5 rounded-xl border border-amber-200 bg-amber-50/20 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Medium Severity</span>
            <div className="text-2xl font-bold text-amber-600 mt-1">
              {summary?.by_severity?.Medium || 0}
            </div>
            <span className="text-xs text-amber-600">Watchlist & follow-up</span>
          </div>
          <div className="p-3 bg-amber-100 text-amber-600 rounded-xl">
            <Clock className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex border-b border-slate-200 space-x-2">
        {(['Unacknowledged', 'High', 'Medium', 'All'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilterTab(tab)}
            className={`pb-3 px-3 text-sm font-semibold transition border-b-2 -mb-px ${
              filterTab === tab
                ? 'border-sky-600 text-sky-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {tab === 'Unacknowledged' ? 'Unacknowledged Feed' : `${tab} Severity`}
          </button>
        ))}
      </div>

      {/* Alerts Feed List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500">Loading alerts stream...</div>
        ) : alertsData?.items.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
            <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
            <h3 className="text-base font-semibold text-slate-800">No alerts in this view</h3>
            <p className="text-xs text-slate-500 mt-1">All warnings in this category have been addressed.</p>
          </div>
        ) : (
          alertsData?.items.map((alert) => (
            <div
              key={alert.id}
              className={`p-5 rounded-xl border bg-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 transition hover:shadow-md ${
                alert.severity === 'High'
                  ? 'border-rose-200 border-l-4 border-l-rose-500'
                  : 'border-amber-200 border-l-4 border-l-amber-500'
              } ${alert.acknowledged ? 'opacity-60 bg-slate-50' : ''}`}
            >
              {/* Alert Content */}
              <div className="space-y-1.5 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <RiskBadge band={alert.severity} size="sm" />
                  <span
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded border capitalize ${getTypeBadge(
                      alert.alert_type
                    )}`}
                  >
                    {alert.alert_type.replace(/_/g, ' ')}
                  </span>
                  {alert.project_uid && (
                    <span className="text-xs font-mono text-slate-400">{alert.project_uid}</span>
                  )}
                  {alert.ministry && (
                    <span className="text-xs text-slate-500">• {alert.ministry}</span>
                  )}
                </div>

                <div>
                  {alert.project_uid ? (
                    <Link
                      to={`/projects/${encodeURIComponent(alert.project_uid)}`}
                      className="font-bold text-slate-900 text-sm hover:text-sky-600 transition inline-flex items-center group"
                    >
                      <span>{alert.project_name || alert.project_uid}</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1 opacity-0 group-hover:opacity-100 transition" />
                    </Link>
                  ) : (
                    <span className="font-bold text-slate-900 text-sm">{alert.project_name}</span>
                  )}
                </div>

                <p className="text-xs text-slate-600 leading-relaxed bg-slate-50/70 p-2.5 rounded-lg border border-slate-100">
                  {alert.reason}
                </p>

                <div className="text-[11px] text-slate-400">
                  Triggered: {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Recent'}
                </div>
              </div>

              {/* Acknowledge Button */}
              <div className="flex items-center space-x-2">
                {alert.acknowledged ? (
                  <span className="inline-flex items-center text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                    <Check className="w-3.5 h-3.5 mr-1" />
                    Acknowledged
                  </span>
                ) : (
                  <button
                    onClick={() => ackMutation.mutate(alert.id)}
                    disabled={ackMutation.isPending}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 text-white transition disabled:opacity-50 shadow-sm"
                  >
                    Acknowledge
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
