import React, { useState } from 'react';
import type { HeatmapCell } from '../../types';

interface DelayHeatmapProps {
  cells: HeatmapCell[];
  isLoading?: boolean;
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export const DelayHeatmap: React.FC<DelayHeatmapProps> = ({ cells, isLoading }) => {
  const [hoveredCell, setHoveredCell] = useState<HeatmapCell | null>(null);

  if (isLoading) {
    return (
      <div className="h-64 w-full bg-subtle/50 animate-pulse rounded-card flex items-center justify-center">
        <p className="text-xs font-semibold text-textMuted">Loading corridor delay heatmap...</p>
      </div>
    );
  }

  // Map cells into a 2D lookup key: "weekday-hour"
  const cellMap = new Map<string, HeatmapCell>();
  cells.forEach((c) => {
    cellMap.set(`${c.weekday}-${c.hour}`, c);
  });

  const getIntensityClass = (delay: number) => {
    if (delay <= 1.0) return 'bg-[#DCFCE7] hover:ring-2 hover:ring-emerald-400 text-emerald-900'; // soft on-time green
    if (delay <= 2.5) return 'bg-[#FEF3C7] hover:ring-2 hover:ring-amber-400 text-amber-900'; // soft warning amber
    if (delay <= 4.5) return 'bg-[#FED7AA] hover:ring-2 hover:ring-orange-400 text-orange-900'; // orange
    return 'bg-[#FEE2E2] hover:ring-2 hover:ring-red-400 text-red-900'; // soft major delay red
  };

  return (
    <div className="space-y-3">
      {/* Heatmap Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="min-w-[680px]">
          {/* Header with Hours */}
          <div className="flex items-center text-[10px] text-textMuted font-semibold mb-1 pl-10">
            {HOURS.map((h) => (
              <div key={h} className="flex-1 text-center">
                {h % 3 === 0 ? `${h}h` : ''}
              </div>
            ))}
          </div>

          {/* Weekday Rows */}
          {WEEKDAYS.map((dayName, dayIdx) => (
            <div key={dayName} className="flex items-center space-x-1 mb-1">
              <span className="w-9 text-xs font-semibold text-textSecondary text-right pr-2 shrink-0">
                {dayName}
              </span>
              <div className="flex-1 flex space-x-1">
                {HOURS.map((hour) => {
                  const cell = cellMap.get(`${dayIdx}-${hour}`) || {
                    weekday: dayIdx,
                    weekday_name: dayName,
                    hour,
                    avg_delay: 0,
                    observation_count: 0,
                    congestion_level: 'low',
                  };
                  const delay = cell.avg_delay;
                  return (
                    <div
                      key={hour}
                      onMouseEnter={() => setHoveredCell(cell)}
                      onMouseLeave={() => setHoveredCell(null)}
                      className={`h-6 flex-1 rounded-xs flex items-center justify-center cursor-pointer transition-all ${getIntensityClass(
                        delay
                      )}`}
                      title={`${dayName} ${hour}:00 - Avg delay: +${delay.toFixed(1)}m (${cell.observation_count} trips)`}
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Details: Active Hover Tooltip & Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs pt-2 border-t border-border gap-2">
        <div className="text-textSecondary h-5 flex items-center">
          {hoveredCell ? (
            <span className="font-medium">
              <strong className="text-textPrimary">{hoveredCell.weekday_name} {hoveredCell.hour}:00</strong>: Average delay{' '}
              <strong className={hoveredCell.avg_delay > 2.5 ? 'text-major-text' : 'text-ontime-text'}>
                +{hoveredCell.avg_delay.toFixed(1)} min
              </strong>{' '}
              ({hoveredCell.observation_count} observed trips)
            </span>
          ) : (
            <span className="text-textMuted italic">Hover over any time slot to view specific delay stats.</span>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-2 shrink-0 text-[11px] text-textMuted">
          <span className="font-semibold text-textSecondary">Delay scale:</span>
          <span className="flex items-center">
            <span className="w-3 h-3 rounded-xs bg-[#DCFCE7] border border-green-200 mr-1" />
            &lt;1m
          </span>
          <span className="flex items-center">
            <span className="w-3 h-3 rounded-xs bg-[#FEF3C7] border border-amber-200 mr-1" />
            1–2.5m
          </span>
          <span className="flex items-center">
            <span className="w-3 h-3 rounded-xs bg-[#FED7AA] border border-orange-200 mr-1" />
            2.5–4.5m
          </span>
          <span className="flex items-center">
            <span className="w-3 h-3 rounded-xs bg-[#FEE2E2] border border-red-200 mr-1" />
            &gt;4.5m
          </span>
        </div>
      </div>
    </div>
  );
};
