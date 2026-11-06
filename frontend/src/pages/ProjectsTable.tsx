import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { fetchProjects, fetchMinistryBreakdown, ProjectFilters } from '../api/client';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, ExternalLink, AlertCircle } from 'lucide-react';

export const ProjectsTable: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Read URL query params
  const initialRiskBand = searchParams.get('risk_band') || '';
  const initialMinistry = searchParams.get('ministry') || '';
  const initialSearch = searchParams.get('search') || '';

  const [searchTerm, setSearchTerm] = useState(initialSearch);
  const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);

  const [filters, setFilters] = useState<ProjectFilters>({
    risk_band: initialRiskBand,
    ministry: initialMinistry,
    search: initialSearch,
    sort_by: 'risk_score',
    sort_order: 'desc',
    limit: 25,
    offset: 0,
  });

  // Debounce search term by 400ms
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Update filters when debounced search changes
  useEffect(() => {
    setFilters((prev) => ({ ...prev, search: debouncedSearch, offset: 0 }));
  }, [debouncedSearch]);

  // Fetch ministries for dropdown
  const { data: ministries } = useQuery({
    queryKey: ['ministryList'],
    queryFn: fetchMinistryBreakdown,
  });

  // Fetch paginated projects
  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['projects', filters],
    queryFn: () => fetchProjects(filters),
    placeholderData: (prev) => prev,
  });

  const handleMinistryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setFilters((prev) => ({ ...prev, ministry: val, offset: 0 }));
  };

  const handleRiskBandChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setFilters((prev) => ({ ...prev, risk_band: val, offset: 0 }));
  };

  const handleSortToggle = (field: string) => {
    setFilters((prev) => {
      const isCurrent = prev.sort_by === field;
      const newOrder = isCurrent && prev.sort_order === 'desc' ? 'asc' : 'desc';
      return { ...prev, sort_by: field, sort_order: newOrder, offset: 0 };
    });
  };

  const totalPages = data ? Math.ceil(data.total / (filters.limit || 25)) : 1;
  const currentPage = Math.floor((filters.offset || 0) / (filters.limit || 25)) + 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Monitored Infrastructure Projects</h1>
        <p className="text-sm text-slate-500 mt-1">
          Longitudinal database of Central Sector Infrastructure Projects (₹150+ Cr). Filter by ministry, risk classification, and predictive metrics.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search project name, UID, agency..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Ministry Filter */}
          <select
            value={filters.ministry || ''}
            onChange={handleMinistryChange}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white max-w-[220px]"
          >
            <option value="">All Ministries</option>
            {ministries?.map((m) => (
              <option key={m.ministry} value={m.ministry}>
                {m.ministry}
              </option>
            ))}
          </select>

          {/* Risk Band Filter */}
          <select
            value={filters.risk_band || ''}
            onChange={handleRiskBandChange}
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          >
            <option value="">All Risk Bands</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </select>

          {/* Reset Filters */}
          {(filters.risk_band || filters.ministry || searchTerm) && (
            <button
              onClick={() => {
                setSearchTerm('');
                setFilters({
                  risk_band: '',
                  ministry: '',
                  search: '',
                  sort_by: 'risk_score',
                  sort_order: 'desc',
                  limit: 25,
                  offset: 0,
                });
              }}
              className="text-xs font-semibold text-rose-600 hover:text-rose-700 underline px-2"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {isLoading && !data ? (
          <div className="p-12 text-center text-slate-500 flex items-center justify-center space-x-2">
            <div className="w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
            <span>Loading projects...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th
                    className="py-3 px-4 cursor-pointer hover:text-slate-800"
                    onClick={() => handleSortToggle('project_name')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Project Name</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th className="py-3 px-4">Ministry / Sector</th>
                  <th
                    className="py-3 px-4 text-right cursor-pointer hover:text-slate-800"
                    onClick={() => handleSortToggle('revised_cost_cr')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Cost (₹ Cr)</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 text-right cursor-pointer hover:text-slate-800"
                    onClick={() => handleSortToggle('physical_progress_pct')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Progress</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 text-center cursor-pointer hover:text-slate-800"
                    onClick={() => handleSortToggle('schedule_delay_months')}
                  >
                    <div className="flex items-center justify-center space-x-1">
                      <span>Delay</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th
                    className="py-3 px-4 text-center cursor-pointer hover:text-slate-800"
                    onClick={() => handleSortToggle('risk_score')}
                  >
                    <div className="flex items-center justify-center space-x-1">
                      <span>Risk Score</span>
                      <ArrowUpDown className="w-3.5 h-3.5" />
                    </div>
                  </th>
                  <th className="py-3 px-4 text-left">SHAP Reason Rationale</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.items.map((p) => {
                  const bandBadge =
                    p.risk_band === 'High'
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : p.risk_band === 'Medium'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200';

                  const barColor =
                    p.risk_score >= 70 ? 'bg-rose-500' : p.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500';

                  return (
                    <tr
                      key={p.project_uid}
                      onClick={() => navigate(`/projects/${encodeURIComponent(p.project_uid)}`)}
                      className="hover:bg-sky-50/40 transition-colors cursor-pointer"
                    >
                      {/* Name & UID */}
                      <td className="py-3 px-4 max-w-xs">
                        <div className="font-semibold text-slate-900 truncate" title={p.project_name}>
                          {p.project_name}
                        </div>
                        <div className="text-xs text-slate-400 font-mono flex items-center space-x-2 mt-0.5">
                          <span>{p.project_uid}</span>
                          {p.state && <span>• {p.state}</span>}
                        </div>
                      </td>

                      {/* Ministry & Sector */}
                      <td className="py-3 px-4 max-w-[200px]">
                        <div className="text-slate-800 font-medium truncate" title={p.ministry}>
                          {p.ministry}
                        </div>
                        <div className="text-xs text-slate-400">{p.sector}</div>
                      </td>

                      {/* Cost */}
                      <td className="py-3 px-4 text-right">
                        <div className="font-semibold text-slate-900">
                          ₹{(p.revised_cost_cr || p.original_cost_cr || 0).toLocaleString()} Cr
                        </div>
                        {p.revised_cost_cr && p.original_cost_cr && p.revised_cost_cr > p.original_cost_cr && (
                          <div className="text-[11px] text-rose-600 font-medium">
                            +₹{(p.revised_cost_cr - p.original_cost_cr).toFixed(0)} Cr overrun
                          </div>
                        )}
                      </td>

                      {/* Physical Progress */}
                      <td className="py-3 px-4 text-right">
                        <div className="font-semibold text-slate-800">{p.physical_progress_pct || 0}%</div>
                        <div className="w-20 bg-slate-100 rounded-full h-1.5 ml-auto mt-1">
                          <div
                            className="bg-sky-500 h-1.5 rounded-full"
                            style={{ width: `${Math.min(100, p.physical_progress_pct || 0)}%` }}
                          />
                        </div>
                      </td>

                      {/* Schedule Delay */}
                      <td className="py-3 px-4 text-center">
                        {p.schedule_delay_months && p.schedule_delay_months > 0 ? (
                          <span className="font-semibold text-rose-600">{p.schedule_delay_months} mos</span>
                        ) : (
                          <span className="text-emerald-600 text-xs font-medium">On schedule</span>
                        )}
                      </td>

                      {/* Risk Score & Mini Bar */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold border ${bandBadge}`}>
                            {p.risk_score.toFixed(1)}
                          </span>
                        </div>
                        <div className="w-16 bg-slate-100 rounded-full h-1 mx-auto mt-1">
                          <div
                            className={`${barColor} h-1 rounded-full`}
                            style={{ width: `${Math.min(100, p.risk_score)}%` }}
                          />
                        </div>
                      </td>

                      {/* SHAP Reason Preview */}
                      <td className="py-3 px-4 max-w-xs text-xs text-slate-600">
                        {p.shap_explanation ? (
                          <span className="truncate block" title={p.shap_explanation}>
                            {p.shap_explanation.length > 70
                              ? `${p.shap_explanation.substring(0, 70)}...`
                              : p.shap_explanation}
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/projects/${encodeURIComponent(p.project_uid)}`);
                          }}
                          className="p-1.5 text-sky-600 hover:text-sky-800 hover:bg-sky-50 rounded transition"
                          title="View 360 Risk Profile"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Toolbar */}
        <div className="p-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div>
            Showing <span className="font-semibold text-slate-700">{filters.offset! + 1}</span> to{' '}
            <span className="font-semibold text-slate-700">
              {Math.min((filters.offset || 0) + (filters.limit || 25), data?.total || 0)}
            </span>{' '}
            of <span className="font-semibold text-slate-700">{data?.total.toLocaleString() || 0}</span> projects
          </div>

          <div className="flex items-center space-x-2">
            <button
              disabled={filters.offset === 0}
              onClick={() =>
                setFilters((prev) => ({
                  ...prev,
                  offset: Math.max(0, (prev.offset || 0) - (prev.limit || 25)),
                }))
              }
              className="inline-flex items-center px-3 py-1.5 border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 disabled:opacity-30 disabled:hover:bg-white transition"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </button>

            <span className="px-2 font-medium text-slate-700">
              Page {currentPage} of {totalPages}
            </span>

            <button
              disabled={!data || (filters.offset || 0) + (filters.limit || 25) >= data.total}
              onClick={() =>
                setFilters((prev) => ({
                  ...prev,
                  offset: (prev.offset || 0) + (prev.limit || 25),
                }))
              }
              className="inline-flex items-center px-3 py-1.5 border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 disabled:opacity-30 disabled:hover:bg-white transition"
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
