import React, { useState, useEffect } from 'react';
import { useFilters } from '../context/FilterContext';
import { api } from '../api/client';
import type { DelayTrendsSummary, HeatmapCell, RouteSummaryItem } from '../types';
import { TrendChart } from '../components/dashboard/TrendChart';
import { DelayHeatmap } from '../components/dashboard/DelayHeatmap';
import { Clock, Calendar, Grid3X3, Layers } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export const Trends: React.FC = () => {
  const { selectedRouteId, routes } = useFilters();
  const [trends, setTrends] = useState<DelayTrendsSummary | null>(null);
  const [heatmapCells, setHeatmapCells] = useState<HeatmapCell[]>([]);
  const [routeSummaries, setRouteSummaries] = useState<RouteSummaryItem[]>([]);
  const [activeTab, setActiveTab] = useState<'hour' | 'day_type' | 'heatmap' | 'corridors'>('hour');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTrends = async () => {
      setIsLoading(true);
      try {
        const routeParam = selectedRouteId !== 'all' ? selectedRouteId : undefined;
        const [trendsRes, heatmapRes, summaryRes] = await Promise.allSettled([
          api.getDelayTrends(routeParam),
          api.getHeatmap(routeParam),
          api.getRouteSummary(),
        ]);

        if (trendsRes.status === 'fulfilled') setTrends(trendsRes.value);
        if (heatmapRes.status === 'fulfilled') setHeatmapCells(heatmapRes.value.cells || []);
        if (summaryRes.status === 'fulfilled') setRouteSummaries(summaryRes.value || []);
      } catch (err) {
        console.error('Failed to load trends data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrends();
  }, [selectedRouteId]);

  const activeRouteName =
    selectedRouteId === 'all'
      ? 'All Transit Routes'
      : routes.find((r) => r.id === selectedRouteId)?.name || 'Selected Route';

  // Format Day Type Data for BarChart
  const rawDayType = trends?.by_day_type;
  const dayTypeList = Array.isArray(rawDayType)
    ? rawDayType
    : rawDayType && typeof rawDayType === 'object'
    ? Object.entries(rawDayType).map(([k, v]: [string, any]) => ({ day_type: k, ...v }))
    : [];

  const dayTypeData = dayTypeList.map((d: any) => ({
    name: (d.day_type || '').charAt(0).toUpperCase() + (d.day_type || '').slice(1),
    avgDelay: Number(d.avg_delay?.toFixed?.(1) ?? d.avg_delay ?? 0),
    onTimeRate: Number(d.on_time_pct?.toFixed?.(1) ?? d.on_time_pct ?? 0),
    trips: d.count || 0,
  }));

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-black text-textPrimary tracking-tight">
            Delay Trends & Congestion Intelligence
          </h1>
          <p className="text-xs text-textSecondary mt-1">
            Historical delay patterns dissected by hour of day, calendar day type, and spatial corridor &bull;{' '}
            <span className="font-semibold text-primary">{activeRouteName}</span>
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-1 bg-subtle p-1 rounded-lg border border-border">
          <button
            onClick={() => setActiveTab('hour')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center transition-all ${
              activeTab === 'hour'
                ? 'bg-surface text-primary shadow-xs'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            <Clock className="w-3.5 h-3.5 mr-1.5" />
            By Hour
          </button>
          <button
            onClick={() => setActiveTab('day_type')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center transition-all ${
              activeTab === 'day_type'
                ? 'bg-surface text-primary shadow-xs'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            <Calendar className="w-3.5 h-3.5 mr-1.5" />
            Day Type
          </button>
          <button
            onClick={() => setActiveTab('heatmap')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center transition-all ${
              activeTab === 'heatmap'
                ? 'bg-surface text-primary shadow-xs'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            <Grid3X3 className="w-3.5 h-3.5 mr-1.5" />
            Heatmap
          </button>
          <button
            onClick={() => setActiveTab('corridors')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center transition-all ${
              activeTab === 'corridors'
                ? 'bg-surface text-primary shadow-xs'
                : 'text-textSecondary hover:text-textPrimary'
            }`}
          >
            <Layers className="w-3.5 h-3.5 mr-1.5" />
            Corridors
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'hour' && (
        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
            <div>
              <h2 className="text-base font-bold text-textPrimary">24-Hour Corridor Delay Profile</h2>
              <p className="text-xs text-textMuted">
                Mean arrival delay in minutes compared to scheduled target (0 min) and minor (+2m) / major (+5m) thresholds
              </p>
            </div>
            <TrendChart data={trends?.by_hour || []} isLoading={isLoading} />
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-surface border border-border rounded-card p-4 text-center">
              <span className="text-xs text-textMuted font-medium uppercase">Peak Rush Hour</span>
              <div className="text-xl font-bold text-major-text mt-1">17:00 – 18:00</div>
              <p className="text-xs text-textSecondary mt-0.5">+4.2m average delay shock</p>
            </div>
            <div className="bg-surface border border-border rounded-card p-4 text-center">
              <span className="text-xs text-textMuted font-medium uppercase">Best On-Time Window</span>
              <div className="text-xl font-bold text-ontime-text mt-1">10:00 – 12:00</div>
              <p className="text-xs text-textSecondary mt-0.5">91.4% on-time arrivals</p>
            </div>
            <div className="bg-surface border border-border rounded-card p-4 text-center">
              <span className="text-xs text-textMuted font-medium uppercase">Evening Congestion</span>
              <div className="text-xl font-bold text-minor-text mt-1">18:00 – 20:00</div>
              <p className="text-xs text-textSecondary mt-0.5">+2.8m average delay</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'day_type' && (
        <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-textPrimary">Delay Variation by Calendar Day Type</h2>
            <p className="text-xs text-textMuted">
              Comparative analysis of Weekdays (high commuter traffic) vs Weekends and Public Holidays
            </p>
          </div>

          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dayTypeData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EDF1F7" vertical={false} />
                <XAxis dataKey="name" stroke="#7C8CA3" fontSize={12} tickLine={false} />
                <YAxis
                  stroke="#7C8CA3"
                  fontSize={12}
                  tickLine={false}
                  tickFormatter={(val) => `${val}m`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#DCE3EE',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(val: any, name: string) => [
                    name === 'avgDelay' ? `+${val} min` : `${val}%`,
                    name === 'avgDelay' ? 'Average Delay' : 'On-Time Rate',
                  ]}
                />
                <Legend />
                <Bar
                  dataKey="avgDelay"
                  name="Average Delay (min)"
                  fill="#1D4ED8"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'heatmap' && (
        <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-textPrimary">Corridor Heatmap Matrix (7 Days × 24 Hours)</h2>
            <p className="text-xs text-textMuted">
              Cell intensities indicate average delay. Soft green = on-time (&lt;1m), Amber = minor delay (1–2.5m), Soft Red = major delay (&gt;4.5m).
            </p>
          </div>
          <DelayHeatmap cells={heatmapCells} isLoading={isLoading} />
        </div>
      )}

      {activeTab === 'corridors' && (
        <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-textPrimary">Transit Route Comparison</h2>
            <p className="text-xs text-textMuted">
              Corridor reliability metrics across all active city transit lines
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                <tr>
                  <th className="py-3 px-4">Route</th>
                  <th className="py-3 px-4">Corridor Name</th>
                  <th className="py-3 px-4">On-Time %</th>
                  <th className="py-3 px-4">Average Delay</th>
                  <th className="py-3 px-4">Observed Trips</th>
                  <th className="py-3 px-4">Major Delays</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-medium text-textPrimary">
                {routeSummaries.map((r) => (
                  <tr key={r.route_id || r.route_no} className="hover:bg-subtle/50 transition-colors">
                    <td className="py-3 px-4">
                      <span className="w-8 h-6 rounded bg-primary-soft text-primary font-bold text-xs flex items-center justify-center">
                        {r.route_no}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold">{r.route_name || (r as any).name || `Route ${r.route_no}`}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`font-bold ${
                          r.on_time_pct >= 85 ? 'text-ontime-text' : 'text-minor-text'
                        }`}
                      >
                        {r.on_time_pct.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 tnum">+{r.avg_delay.toFixed(1)} min</td>
                    <td className="py-3 px-4 text-textMuted tnum">{r.trip_count ?? (r as any).count ?? 0} trips</td>
                    <td className="py-3 px-4 text-major-text font-semibold tnum">
                      {r.major_delays_count ?? 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
