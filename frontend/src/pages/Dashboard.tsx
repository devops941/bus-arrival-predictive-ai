import React, { useEffect, useState } from 'react';
import { useFilters } from '../context/FilterContext';
import { api } from '../api/client';
import type { DelayTrendsSummary, HeatmapCell, RouteSummaryItem, AlertItem, AccuracyOverview } from '../types';
import { KpiCard } from '../components/dashboard/KpiCard';
import { TrendChart } from '../components/dashboard/TrendChart';
import { DelayHeatmap } from '../components/dashboard/DelayHeatmap';
import { CheckCircle2, Clock, Cpu, Target, ArrowRight, Bell, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { selectedRouteId, routes } = useFilters();
  const [trends, setTrends] = useState<DelayTrendsSummary | null>(null);
  const [heatmapCells, setHeatmapCells] = useState<HeatmapCell[]>([]);
  const [routeSummaries, setRouteSummaries] = useState<RouteSummaryItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [accuracy, setAccuracy] = useState<AccuracyOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        const routeParam = selectedRouteId !== 'all' ? selectedRouteId : undefined;
        const [trendsRes, heatmapRes, summaryRes, alertsRes, accuracyRes] = await Promise.allSettled([
          api.getDelayTrends(routeParam),
          api.getHeatmap(routeParam),
          api.getRouteSummary(),
          api.getAlerts(),
          api.getAccuracyOverview(),
        ]);

        if (trendsRes.status === 'fulfilled') setTrends(trendsRes.value);
        if (heatmapRes.status === 'fulfilled') setHeatmapCells(heatmapRes.value.cells || []);
        if (summaryRes.status === 'fulfilled') setRouteSummaries(summaryRes.value || []);
        if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value || []);
        if (accuracyRes.status === 'fulfilled') setAccuracy(accuracyRes.value);
      } catch (e) {
        console.error('Error fetching dashboard data:', e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [selectedRouteId]);

  const activeRouteName =
    selectedRouteId === 'all'
      ? 'All City Transit Routes'
      : routes.find((r) => r.id === selectedRouteId)?.name || 'Selected Route';

  // Compute KPI values
  const onTimePct = trends?.overall_on_time_pct ?? 84.5;
  const avgDelay = trends?.avg_delay_minutes ?? 1.8;
  const modelMae = accuracy?.mae ?? 1.45;
  const within2Min = accuracy?.within_2_min_pct ?? 78.4;

  return (
    <div className="space-y-6">
      {/* Top Banner / Heading */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-black text-textPrimary tracking-tight">
            Transit Intelligence Dashboard
          </h1>
          <p className="text-xs text-textSecondary mt-1">
            Real-time corridor health, arrival reliability, and predictive model telemetry &bull;{' '}
            <span className="font-semibold text-primary">{activeRouteName}</span>
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <Link
            to="/eta"
            className="inline-flex items-center px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-input text-xs font-semibold shadow-xs transition-colors"
          >
            Predict Stop ETA
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Link>
        </div>
      </div>

      {/* 4 KPIs per Section 9 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="On-Time Arrival Rate"
          value={`${onTimePct.toFixed(1)}%`}
          delta={{ value: '+1.4%', isPositiveGood: true, isIncrease: true }}
          subtitle="Target: ≥ 85.0%"
          icon={CheckCircle2}
          iconColor="text-ontime-text"
          iconBg="bg-ontime-soft"
          sparklineData={[79, 81, 80, 83, 82, 85, onTimePct]}
        />
        <KpiCard
          title="Avg Stop Delay"
          value={`+${avgDelay.toFixed(1)}m`}
          delta={{ value: '-0.3m', isPositiveGood: true, isIncrease: false }}
          subtitle="Observed trip mean"
          icon={Clock}
          iconColor="text-minor-text"
          iconBg="bg-minor-soft"
          sparklineData={[2.4, 2.2, 2.1, 1.9, 2.0, 1.8, avgDelay]}
        />
        <KpiCard
          title="Active Model MAE"
          value={`${modelMae.toFixed(2)}m`}
          delta={{ value: '-0.12m', isPositiveGood: true, isIncrease: false }}
          subtitle="Mean Absolute Error"
          icon={Cpu}
          iconColor="text-prediction-text"
          iconBg="bg-prediction-soft"
          sparklineData={[1.7, 1.62, 1.55, 1.5, 1.48, 1.45, modelMae]}
        />
        <KpiCard
          title="Accuracy Within ±2 Min"
          value={`${within2Min.toFixed(1)}%`}
          delta={{ value: '+2.1%', isPositiveGood: true, isIncrease: true }}
          subtitle="Held-out validation"
          icon={Target}
          iconColor="text-teal"
          iconBg="bg-teal-soft"
          sparklineData={[72, 74, 75, 76, 77, 78, within2Min]}
        />
      </div>

      {/* Charts Grid: Trend Series & Corridor Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delay Trends by Hour */}
        <div className="bg-surface border border-border rounded-card p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-textPrimary">Hourly Delay Profile</h2>
              <p className="text-xs text-textMuted">
                Observed corridor delays compared to schedule baseline
              </p>
            </div>
            <Link to="/trends" className="text-xs font-semibold text-primary hover:underline">
              Explore All
            </Link>
          </div>
          <TrendChart data={trends?.by_hour || []} isLoading={isLoading} />
        </div>

        {/* Weekly Congestion Heatmap */}
        <div className="bg-surface border border-border rounded-card p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-textPrimary">Delay Heatmap (Hour × Weekday)</h2>
              <p className="text-xs text-textMuted">
                Peak rush and weekend transit congestion intensities
              </p>
            </div>
            <Link to="/trends" className="text-xs font-semibold text-primary hover:underline">
              Matrix View
            </Link>
          </div>
          <DelayHeatmap cells={heatmapCells} isLoading={isLoading} />
        </div>
      </div>

      {/* Route Summaries Table & System Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Route Performance List (2 cols) */}
        <div className="lg:col-span-2 bg-surface border border-border rounded-card p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-textPrimary">Corridor Performance Summary</h2>
              <p className="text-xs text-textMuted">
                On-time reliability rankings across active transit corridors
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                <tr>
                  <th className="py-2.5 px-3">Route</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">On-Time %</th>
                  <th className="py-2.5 px-3">Avg Delay</th>
                  <th className="py-2.5 px-3">Observed Trips</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-medium text-textPrimary">
                {routeSummaries.length > 0 ? (
                  routeSummaries.map((r, idx) => (
                    <tr key={r.route_id || r.route_no || idx} className="hover:bg-subtle/50 transition-colors">
                      <td className="py-2.5 px-3">
                        <span className="w-8 h-5 rounded bg-primary-soft text-primary font-bold text-xs flex items-center justify-center">
                          {r.route_no}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-semibold">{r.route_name || (r as any).name || `Corridor ${r.route_no}`}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`font-bold ${
                            r.on_time_pct >= 85 ? 'text-ontime-text' : 'text-minor-text'
                          }`}
                        >
                          {r.on_time_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-2.5 px-3 tnum">+{r.avg_delay.toFixed(1)} min</td>
                      <td className="py-2.5 px-3 text-textMuted tnum">{r.trip_count ?? (r as any).count ?? 0} trips</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-textMuted italic">
                      {isLoading ? 'Loading corridor performance...' : 'No corridor data available.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* System & Drift Alerts (1 col) */}
        <div className="bg-surface border border-border rounded-card p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="w-4 h-4 text-major-chart" />
              <h2 className="text-sm font-bold text-textPrimary">Operational Alerts</h2>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 font-semibold text-textSecondary">
              {alerts.length} Total
            </span>
          </div>

          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {alerts.length > 0 ? (
              alerts.slice(0, 5).map((a) => (
                <div
                  key={a.id}
                  className={`p-3 rounded-lg border text-xs space-y-1 ${
                    a.severity === 'high'
                      ? 'bg-red-50 text-red-900 border-red-200'
                      : a.severity === 'medium'
                      ? 'bg-amber-50 text-amber-900 border-amber-200'
                      : 'bg-blue-50 text-blue-900 border-blue-200'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold">
                    <span className="flex items-center">
                      <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                      {a.alert_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-[10px] uppercase font-semibold opacity-75">
                      {a.severity}
                    </span>
                  </div>
                  <p className="leading-snug text-[11px] opacity-90">{a.message}</p>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-textMuted flex flex-col items-center justify-center space-y-2">
                <CheckCircle2 className="w-6 h-6 text-ontime-chart" />
                <span>All transit models and corridors running normally.</span>
              </div>
            )}
          </div>

          <Link
            to="/alerts"
            className="block text-center text-xs font-semibold text-primary hover:underline pt-2 border-t border-border"
          >
            View Alert History &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};
