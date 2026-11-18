import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';

interface TrendChartProps {
  data: Array<{
    hour: number;
    avg_delay: number;
    count?: number;
    on_time_pct?: number;
  }>;
  isLoading?: boolean;
}

export const TrendChart: React.FC<TrendChartProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="h-72 w-full bg-subtle/50 animate-pulse rounded-card flex items-center justify-center">
        <p className="text-xs font-semibold text-textMuted">Loading delay trend series...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-72 w-full bg-subtle/30 rounded-card flex flex-col items-center justify-center border border-dashed border-border p-6 text-center">
        <p className="text-sm font-semibold text-textPrimary">No Trend Data Available</p>
        <p className="text-xs text-textMuted mt-1">
          Transit observations will populate delay patterns as trips are logged.
        </p>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = data.map((d) => ({
    hourLabel: `${String(d.hour).padStart(2, '0')}:00`,
    actualDelay: Number(d.avg_delay.toFixed(1)),
    scheduledReference: 0,
    onTimeRate: d.on_time_pct !== undefined ? Number(d.on_time_pct.toFixed(1)) : 80,
  }));

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#EDF1F7" vertical={false} />
          <XAxis
            dataKey="hourLabel"
            stroke="#7C8CA3"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: '#DCE3EE' }}
          />
          <YAxis
            stroke="#7C8CA3"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: '#DCE3EE' }}
            tickFormatter={(val) => `${val}m`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderColor: '#DCE3EE',
              borderRadius: '8px',
              fontSize: '12px',
              boxShadow: '0 4px 6px -1px rgba(15, 30, 51, 0.08)',
            }}
            formatter={(value: any, name: string) => {
              if (name === 'Actual Observed Delay') return [`+${value} min`, name];
              if (name === 'Scheduled Target') return ['0 min (on-time)', name];
              return [value, name];
            }}
          />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ paddingBottom: '12px', fontSize: '12px' }}
          />
          <ReferenceLine y={2} stroke="#F59E0B" strokeDasharray="3 3" label={{ value: 'Minor (+2m)', fill: '#B45309', fontSize: 10 }} />
          <ReferenceLine y={5} stroke="#EF4444" strokeDasharray="3 3" label={{ value: 'Major (+5m)', fill: '#B91C1C', fontSize: 10 }} />
          {/* Schedule reference line = Teal dashed */}
          <Line
            type="monotone"
            dataKey="scheduledReference"
            name="Scheduled Target"
            stroke="#0D9488"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
          />
          {/* Observed actual delay = Blue line with points */}
          <Line
            type="monotone"
            dataKey="actualDelay"
            name="Actual Observed Delay"
            stroke="#1D4ED8"
            strokeWidth={2.5}
            activeDot={{ r: 6, fill: '#1D4ED8' }}
            dot={{ r: 3, fill: '#1D4ED8' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
