import React from 'react';
import type { Route, CorridorStopPrediction } from '../../types';
import { Bus, MapPin, CheckCircle } from 'lucide-react';
import { formatTimeOnly } from '../../lib/utils';

interface RouteLineDiagramProps {
  route: Route | null;
  selectedStopId: string;
  corridorPredictions?: CorridorStopPrediction[];
  onSelectStop?: (stopId: string) => void;
}

export const RouteLineDiagram: React.FC<RouteLineDiagramProps> = ({
  route,
  selectedStopId,
  corridorPredictions = [],
  onSelectStop,
}) => {
  if (!route || !route.stops || route.stops.length === 0) {
    return (
      <div className="p-8 text-center bg-subtle/30 rounded-xl border border-dashed border-border text-xs text-textMuted">
        Select a transit route to view stop corridor sequence.
      </div>
    );
  }

  // Map predictions by stop_id for quick lookup
  const predMap = new Map<string, CorridorStopPrediction>();
  corridorPredictions.forEach((p) => predMap.set(p.stop_id, p));

  const selectedIndex = route.stops.findIndex(
    (s) => s.stop_id === selectedStopId || (s as any).stop_code === selectedStopId
  );

  return (
    <div className="bg-surface border border-border rounded-xl p-6 shadow-card space-y-5">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/70 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center font-bold text-xs shadow-xs">
            {route.route_no}
          </div>
          <div>
            <h3 className="text-sm font-bold text-textPrimary">Corridor Stop Sequence & Progression</h3>
            <p className="text-xs text-textMuted">
              {route.origin} &rarr; {route.destination} &bull; {route.total_distance_km} km Corridor
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="px-2 py-0.5 rounded-full bg-subtle font-semibold text-textSecondary border border-border">
            {route.stops.length} Stops
          </span>
          <span className="text-textMuted text-[11px]">Click any stop to predict ETA</span>
        </div>
      </div>

      {/* Corridor Diagram Line */}
      <div className="relative pt-10 pb-4 overflow-x-auto">
        <div className="min-w-[720px] flex items-start justify-between relative px-6">
          {/* Base Horizontal Track Line */}
          <div className="absolute left-10 right-10 top-3.5 h-1.5 bg-slate-200 rounded-full -z-0" />
          {/* Active Traversed Line */}
          <div
            className="absolute left-10 top-3.5 h-1.5 bg-primary rounded-full -z-0 transition-all duration-300"
            style={{
              width:
                selectedIndex >= 0
                  ? `${Math.min(100, Math.round((selectedIndex / Math.max(1, route.stops.length - 1)) * 100))}%`
                  : '0%',
            }}
          />

          {route.stops.map((rs, idx) => {
            const isSelected = rs.stop_id === selectedStopId || (rs as any).stop_code === selectedStopId;
            const isPast = selectedIndex > idx;
            const pred = predMap.get(rs.stop_id);
            const estTime = pred ? formatTimeOnly(pred.predicted_eta_p50) : null;
            const estDelay = pred ? pred.predicted_delay_min : null;
            const stopLabel = pred?.stop_name || (rs as any).name || `Stop ${rs.sequence}`;

            return (
              <div
                key={rs.stop_id}
                onClick={() => onSelectStop && onSelectStop(rs.stop_id)}
                className="relative z-10 flex flex-col items-center group cursor-pointer"
                style={{ flex: '1 1 0', minWidth: '85px', maxWidth: '125px' }}
              >
                {/* Active Bus Icon if current stop */}
                {isSelected && (
                  <div className="absolute -top-8 px-2.5 py-0.5 rounded-full bg-primary text-white text-[10px] font-bold flex items-center shadow-md ring-2 ring-white">
                    <Bus className="w-3 h-3 mr-1" />
                    Selected
                  </div>
                )}

                {/* Node Circle */}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center border-2 transition-all shadow-xs ${
                    isSelected
                      ? 'bg-primary border-primary ring-4 ring-primary-soft text-white scale-110'
                      : isPast
                      ? 'bg-primary border-primary text-white'
                      : 'bg-surface border-slate-300 text-textMuted group-hover:border-primary group-hover:text-primary'
                  }`}
                >
                  {isPast ? (
                    <CheckCircle className="w-3.5 h-3.5" />
                  ) : isSelected ? (
                    <MapPin className="w-3.5 h-3.5" />
                  ) : (
                    <span className="text-[11px] font-bold">{rs.sequence}</span>
                  )}
                </div>

                {/* Stop Meta Details */}
                <div className="mt-2.5 text-center w-full px-1">
                  <p
                    className={`text-[11px] leading-tight font-bold truncate ${
                      isSelected ? 'text-primary' : 'text-textPrimary'
                    }`}
                    title={stopLabel}
                  >
                    {stopLabel}
                  </p>
                  <p className="text-[10px] text-textMuted tnum mt-0.5">
                    {rs.distance_from_origin_km} km
                  </p>

                  {/* Sched & ETA comparison */}
                  <div className="mt-1.5 pt-1 border-t border-slate-100 flex flex-col items-center space-y-0.5">
                    {pred?.scheduled_time && (
                      <span className="text-[10px] text-textMuted tnum">
                        Sched: <strong className="font-semibold text-textSecondary">{formatTimeOnly(pred.scheduled_time)}</strong>
                      </span>
                    )}
                    {estTime && (
                      <div className="flex items-center justify-center gap-1">
                        <span className={`text-[11px] font-extrabold tnum ${
                          isSelected ? 'text-primary font-black' : 'text-prediction-text'
                        }`}>
                          {estTime}
                        </span>
                        {estDelay !== null && (
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                              estDelay > 2 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                            }`}
                          >
                            +{estDelay.toFixed(0)}m
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
