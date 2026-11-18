import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { AlertItem } from '../types';
import { AlertTriangle, CheckCircle2, Sparkles, Filter } from 'lucide-react';
import { toast } from 'sonner';

export const Alerts: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<'all' | 'open' | 'resolved'>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingDrift, setIsCheckingDrift] = useState(false);

  const loadAlerts = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAlerts();
      setAlerts(data);
    } catch (e: any) {
      toast.error(e.message || 'Failed to fetch alerts.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await api.resolveAlert(id);
      toast.success('Alert resolved.');
      loadAlerts();
    } catch (e: any) {
      toast.error(e.message || 'Resolve failed.');
    }
  };

  const handleTriggerDrift = async () => {
    setIsCheckingDrift(true);
    try {
      const res = await api.triggerDriftCheck();
      toast.info(res.message || 'Drift check completed.');
      loadAlerts();
    } catch (e: any) {
      toast.error(e.message || 'Drift check failed.');
    } finally {
      setIsCheckingDrift(false);
    }
  };

  const openCount = alerts.filter((a) => !a.is_resolved).length;
  const resolvedCount = alerts.filter((a) => a.is_resolved).length;

  const filtered = alerts.filter((a) => {
    const matchesSeverity = filterSeverity === 'all' || a.severity === filterSeverity;
    const matchesStatus =
      filterStatus === 'all'
        ? true
        : filterStatus === 'open'
        ? !a.is_resolved
        : a.is_resolved;
    return matchesSeverity && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-black text-textPrimary tracking-tight">
            System & Model Drift Alerts
          </h1>
          <p className="text-xs text-textSecondary mt-1">
            Real-time monitoring for model degradation, consecutive delay shocks, and corridor anomalies.
          </p>
        </div>

        <button
          onClick={handleTriggerDrift}
          disabled={isCheckingDrift}
          className="inline-flex items-center px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-input shadow-xs transition-colors cursor-pointer disabled:opacity-50"
        >
          <Sparkles className={`w-3.5 h-3.5 mr-1.5 ${isCheckingDrift ? 'animate-spin' : ''}`} />
          {isCheckingDrift ? 'Evaluating Drift...' : 'Run Drift Check Now'}
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface border border-border rounded-card p-3 shadow-card text-xs">
        <div className="flex flex-wrap items-center gap-4">
          {/* Status Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="font-semibold text-textSecondary mr-1">Status:</span>
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-2.5 py-1 rounded-md font-semibold transition-colors cursor-pointer ${
                filterStatus === 'all'
                  ? 'bg-primary text-white shadow-xs'
                  : 'bg-subtle text-textSecondary hover:bg-slate-200'
              }`}
            >
              All ({alerts.length})
            </button>
            <button
              onClick={() => setFilterStatus('open')}
              className={`px-2.5 py-1 rounded-md font-semibold transition-colors cursor-pointer ${
                filterStatus === 'open'
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-subtle text-textSecondary hover:bg-slate-200'
              }`}
            >
              Active ({openCount})
            </button>
            <button
              onClick={() => setFilterStatus('resolved')}
              className={`px-2.5 py-1 rounded-md font-semibold transition-colors cursor-pointer ${
                filterStatus === 'resolved'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-subtle text-textSecondary hover:bg-slate-200'
              }`}
            >
              Resolved ({resolvedCount})
            </button>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-textMuted" />
            <span className="font-semibold text-textSecondary mr-1">Severity:</span>
            {(['all', 'high', 'medium', 'low'] as const).map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2 py-0.5 rounded-md capitalize font-semibold transition-colors cursor-pointer ${
                  filterSeverity === sev
                    ? 'bg-slate-800 text-white shadow-xs'
                    : 'bg-subtle text-textSecondary hover:bg-slate-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        <span className="text-textMuted text-right">
          {isLoading ? 'Refreshing...' : `Showing ${filtered.length} of ${alerts.length} Alerts`}
        </span>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filtered.length > 0 ? (
          filtered.map((a) => (
            <div
              key={a.id}
              className={`bg-surface border rounded-card p-5 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
                a.severity === 'high'
                  ? 'border-red-200 hover:border-red-300'
                  : a.severity === 'medium'
                  ? 'border-amber-200 hover:border-amber-300'
                  : 'border-blue-200 hover:border-blue-300'
              }`}
            >
              <div className="flex items-start space-x-3.5">
                <div
                  className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                    a.severity === 'high'
                      ? 'bg-red-100 text-red-700'
                      : a.severity === 'medium'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-textPrimary capitalize">
                      {a.alert_type.replace('_', ' ')}
                    </span>
                    <span
                      className={`px-2 py-0.2 rounded-full text-[10px] font-bold uppercase ${
                        a.severity === 'high'
                          ? 'bg-red-50 text-red-700 border border-red-200'
                          : a.severity === 'medium'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}
                    >
                      {a.severity} Severity
                    </span>
                  </div>
                  <p className="text-xs text-textSecondary leading-relaxed">{a.message}</p>
                  <p className="text-[10px] text-textMuted">Triggered: {a.created_at?.slice(0, 19).replace('T', ' ')} UTC</p>
                </div>
              </div>

              <div className="shrink-0 flex items-center space-x-2">
                {!a.is_resolved ? (
                  <button
                    onClick={() => handleResolve(a.id)}
                    className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-input text-xs font-semibold transition-colors cursor-pointer"
                  >
                    Resolve Alert
                  </button>
                ) : (
                  <span className="text-xs font-semibold text-emerald-600 flex items-center">
                    <CheckCircle2 className="w-4 h-4 mr-1" />
                    Resolved
                  </span>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="bg-surface border border-dashed border-border rounded-card p-12 text-center flex flex-col items-center justify-center space-y-2">
            <CheckCircle2 className="w-8 h-8 text-ontime-chart" />
            <h3 className="text-sm font-bold text-textPrimary">No Active Operational Alerts</h3>
            <p className="text-xs text-textMuted max-w-sm">
              All transit corridor delays and model accuracy ratios remain within nominal bounds (drift ratio &lt; 1.3).
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
