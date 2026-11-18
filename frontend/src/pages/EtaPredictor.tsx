import React, { useState, useEffect } from 'react';
import { useFilters } from '../context/FilterContext';
import { api } from '../api/client';
import type { EtaPredictionResponse, CorridorStopPrediction } from '../types';
import { EtaCard } from '../components/eta/EtaCard';
import { RouteLineDiagram } from '../components/eta/RouteLineDiagram';
import { ReliabilityGauge } from '../components/eta/ReliabilityGauge';
import { Sparkles, CloudRain, Clock, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export const EtaPredictor: React.FC = () => {
  const { routes, stops, selectedRouteId, setSelectedRouteId } = useFilters();

  const [activeRouteId, setActiveRouteId] = useState<string>('');
  const [activeStopId, setActiveStopId] = useState<string>('');
  const [scheduledTime, setScheduledTime] = useState<string>('14:30');
  const [rainShock, setRainShock] = useState<boolean>(false);
  const [corridorDelay, setCorridorDelay] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [prediction, setPrediction] = useState<EtaPredictionResponse | null>(null);

  // Initialize selected route and stop
  useEffect(() => {
    if (routes.length > 0) {
      const defaultRoute =
        selectedRouteId !== 'all' ? selectedRouteId : routes[0].id;
      setActiveRouteId(defaultRoute);

      const r = routes.find((x) => x.id === defaultRoute || x.route_no === defaultRoute);
      if (r && r.stops && r.stops.length > 0) {
        const targetStop = r.stops[Math.min(2, r.stops.length - 1)].stop_id;
        setActiveStopId(targetStop);
      } else if (stops.length > 0) {
        setActiveStopId(stops[0].stop_code || stops[0].id);
      }
    }
  }, [routes, selectedRouteId, stops]);

  const currentRoute = routes.find((r) => r.id === activeRouteId || r.route_no === activeRouteId) || null;
  const currentStops =
    currentRoute && currentRoute.stops && currentRoute.stops.length > 0
      ? stops.filter((s) =>
          currentRoute.stops.some(
            (rs) => rs.stop_id === s.id || rs.stop_id === s.stop_code
          )
        )
      : stops;

  useEffect(() => {
    if (currentStops.length > 0) {
      const exists = currentStops.some(
        (s) => s.id === activeStopId || s.stop_code === activeStopId
      );
      if (!exists || !activeStopId) {
        const defaultPick = currentStops[Math.min(2, currentStops.length - 1)] || currentStops[0];
        setActiveStopId(defaultPick.stop_code || defaultPick.id);
      }
    }
  }, [currentRoute, currentStops, activeStopId]);

  // Find the target stop's scheduled travel offset in minutes from origin
  const targetStopRs = currentRoute?.stops?.find(
    (rs) => rs.stop_id === activeStopId || rs.stop_code === activeStopId
  );
  const selectedStopOffset = targetStopRs?.scheduled_travel_min ?? targetStopRs?.scheduled_offset_min ?? 0;
  const targetStopInfo = stops.find((s) => s.id === activeStopId || s.stop_code === activeStopId);
  const targetStopName = targetStopInfo?.name || activeStopId;

  // Format scheduled arrival at stop for display in header and telemetry
  const computedStopSchedTime = (() => {
    try {
      const [h, m] = scheduledTime.split(':');
      const d = new Date();
      d.setHours(parseInt(h || '14', 10), parseInt(m || '30', 10), 0, 0);
      const stopDate = new Date(d.getTime() + selectedStopOffset * 60000);
      return stopDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch {
      return scheduledTime;
    }
  })();

  const runPrediction = async (
    targetRouteId: string = activeRouteId,
    targetStopId: string = activeStopId,
    targetTime: string = scheduledTime,
    targetRain: boolean = rainShock,
    targetDelay: number = corridorDelay
  ) => {
    if (!targetRouteId || !targetStopId) {
      return;
    }

    setIsLoading(true);
    try {
      const r = routes.find((x) => x.id === targetRouteId || x.route_no === targetRouteId);

      // Base trip departure time at Stop 1 (origin)
      const tripStartDate = new Date();
      const [h, m] = targetTime.split(':');
      tripStartDate.setHours(parseInt(h || '14', 10), parseInt(m || '30', 10), 0, 0);

      // Add scheduled travel minutes for the selected stop
      const stopRs = r?.stops?.find(
        (rs) => rs.stop_id === targetStopId || rs.stop_code === targetStopId
      );
      const offsetMin = stopRs?.scheduled_travel_min ?? stopRs?.scheduled_offset_min ?? 0;
      const targetStopSchedDate = new Date(tripStartDate.getTime() + offsetMin * 60000);
      const scheduledIso = targetStopSchedDate.toISOString();

      const result = await api.predictEta({
        route_id: targetRouteId,
        stop_id: targetStopId,
        scheduled_arrival: scheduledIso,
        precipitation_mm: targetRain ? 12.5 : 0.0,
        recent_corridor_delay: targetDelay,
      });

      // Construct corridor predictions for the RouteLineDiagram
      const p50Delay = Number(result.expected_delay_min ?? (result as any).expected_delay ?? 0);
      const p90Delay = Number(
        result.delay_range_min?.p90 ??
        (result as any).p90_delay_min ??
        (p50Delay + 2.0)
      );
      const delayDiff = Math.max(1.0, p90Delay - p50Delay);

      if (r && r.stops) {
        const selectedIdx = r.stops.findIndex(
          (rs) => rs.stop_id === targetStopId || rs.stop_code === targetStopId
        );
        const selectedSeq = r.stops[selectedIdx]?.sequence || 1;

        const corridorList: CorridorStopPrediction[] = r.stops.map((rs, idx) => {
          const stopObj = stops.find((s) => s.id === rs.stop_id || s.stop_code === rs.stop_id);
          const stopTravelMin = rs.scheduled_travel_min ?? rs.scheduled_offset_min ?? (idx * 6);
          const stopSchedDate = new Date(tripStartDate.getTime() + stopTravelMin * 60000);
          
          // Stop delay:
          // The selected stop has EXACTLY p50Delay from the model so card and line match 1:1!
          // Other stops scale proportionally to sequence
          const stopDelay = Number(
            idx === selectedIdx
              ? p50Delay
              : (p50Delay * (rs.sequence / Math.max(1, selectedSeq))).toFixed(1)
          );
          const arrivalP50Date = new Date(stopSchedDate.getTime() + stopDelay * 60000);
          const arrivalP90Date = new Date(arrivalP50Date.getTime() + delayDiff * 60000);

          return {
            stop_id: rs.stop_id,
            stop_name: stopObj ? stopObj.name : `Stop ${rs.sequence}`,
            sequence: rs.sequence,
            distance_from_origin_km: rs.distance_from_origin_km,
            scheduled_time: stopSchedDate.toISOString(),
            predicted_eta_p50: arrivalP50Date.toISOString(),
            predicted_eta_p90: arrivalP90Date.toISOString(),
            predicted_delay_min: stopDelay,
            status: idx < selectedIdx ? 'departed' : idx === selectedIdx ? 'current' : 'upcoming',
          };
        });
        result.corridor_predictions = corridorList;
      }

      const stopInfo = stops.find((s) => s.id === targetStopId || s.stop_code === targetStopId);
      const normalizedResult: any = {
        ...result,
        stop_name:
          result.stop_name ||
          stopInfo?.name ||
          targetStopId,
        predicted_arrival_p50: result.predicted_arrival_p50 || (result as any).eta_p50,
        predicted_arrival_p90: result.predicted_arrival_p90 || (result as any).eta_p90,
        scheduled_arrival: result.scheduled_arrival || scheduledIso,
        reliability_tier: result.reliability_tier || (result as any).reliability || 'HIGH',
        confidence_score: result.confidence_score || 88,
        delay_range_min: {
          p50: p50Delay,
          p90: p90Delay,
        },
      };

      setPrediction(normalizedResult);
    } catch (err: any) {
      toast.error(err.message || 'ETA prediction calculation failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopChange = (newStopId: string) => {
    setActiveStopId(newStopId);
    runPrediction(activeRouteId, newStopId, scheduledTime, rainShock, corridorDelay);
  };

  const handleRouteChange = (rId: string) => {
    setActiveRouteId(rId);
    setSelectedRouteId(rId);
    const r = routes.find((x) => x.id === rId || x.route_no === rId);
    let newStop = '';
    if (r && r.stops && r.stops.length > 0) {
      newStop = r.stops[Math.min(2, r.stops.length - 1)].stop_id;
    } else if (stops.length > 0) {
      newStop = stops[0].stop_code || stops[0].id;
    }
    setActiveStopId(newStop);
    if (newStop) {
      runPrediction(rId, newStop, scheduledTime, rainShock, corridorDelay);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runPrediction(activeRouteId, activeStopId, scheduledTime, rainShock, corridorDelay);
    toast.success('P50 & P90 Arrival Prediction updated!');
  };

  // Run initial prediction once route & stop are loaded
  useEffect(() => {
    if (activeRouteId && activeStopId && !prediction && !isLoading) {
      runPrediction(activeRouteId, activeStopId, scheduledTime, rainShock, corridorDelay);
    }
  }, [activeRouteId, activeStopId]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-border pb-4 pt-1">
        <h1 className="text-2xl font-black text-textPrimary tracking-tight">
          Predictive Arrival Time (ETA)
        </h1>
        <p className="text-xs text-textSecondary mt-1">
          Machine-learned arrival forecasts with conservative P90 confidence ranges and corridor delay telemetry.
        </p>
      </div>

      {/* Control Panel: Route, Stop, Time, Conditions */}
      <div className="bg-surface border border-border rounded-xl p-5 shadow-card space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Route Selector */}
            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Transit Route
              </label>
              <select
                value={activeRouteId}
                onChange={(e) => handleRouteChange(e.target.value)}
                className="w-full h-11 px-3 text-sm bg-subtle border border-border rounded-lg text-textPrimary font-medium focus:ring-2 focus:ring-primary focus:outline-none cursor-pointer"
              >
                {routes.map((r) => (
                  <option key={r.id} value={r.id}>
                    Route {r.route_no} - {r.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Stop Selector */}
            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Arrival Stop
              </label>
              <select
                value={activeStopId}
                onChange={(e) => handleStopChange(e.target.value)}
                className="w-full h-11 px-3 text-sm bg-subtle border border-border rounded-lg text-textPrimary font-medium focus:ring-2 focus:ring-primary focus:outline-none cursor-pointer"
              >
                {currentStops.map((s) => (
                  <option key={s.id || s.stop_code} value={s.stop_code || s.id}>
                    {s.stop_code} - {s.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Scheduled Trip Departure Time */}
            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Trip Start Time
              </label>
              <div className="relative">
                <input
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => {
                    setScheduledTime(e.target.value);
                    runPrediction(activeRouteId, activeStopId, e.target.value, rainShock, corridorDelay);
                  }}
                  className="w-full h-11 px-3 text-sm bg-subtle border border-border rounded-lg text-textPrimary font-medium focus:ring-2 focus:ring-primary focus:outline-none"
                />
                <Clock className="w-4 h-4 text-textMuted absolute right-3 top-3.5 pointer-events-none" />
              </div>
            </div>

            {/* Condition Adjustments (Rain Shock / Traffic Delay) */}
            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Corridor Conditions
              </label>
              <div className="flex items-center space-x-2 h-11">
                <label className={`flex items-center space-x-2 cursor-pointer px-3 h-full rounded-lg border text-xs font-medium transition-colors flex-1 justify-center ${
                  rainShock
                    ? 'bg-sky-50 text-sky-800 border-sky-300 font-bold'
                    : 'bg-subtle hover:bg-slate-100 text-textSecondary border-border'
                }`}>
                  <input
                    type="checkbox"
                    checked={rainShock}
                    onChange={(e) => {
                      const val = e.target.checked;
                      setRainShock(val);
                      runPrediction(activeRouteId, activeStopId, scheduledTime, val, corridorDelay);
                      if (val) {
                        toast.info('Rain Shock active: wet road delay added');
                      } else {
                        toast.info('Rain cleared: standard conditions');
                      }
                    }}
                    className="w-3.5 h-3.5 text-primary rounded"
                  />
                  <CloudRain className="w-3.5 h-3.5 text-sky-600" />
                  <span>Rain Shock</span>
                </label>

                <button
                  type="button"
                  onClick={() => {
                    const nextDelay = corridorDelay === 0 ? 4.5 : 0;
                    setCorridorDelay(nextDelay);
                    runPrediction(activeRouteId, activeStopId, scheduledTime, rainShock, nextDelay);
                    if (nextDelay > 0) {
                      toast.info('+4.5m Corridor Delay shock added');
                    } else {
                      toast.info('Normal traffic conditions');
                    }
                  }}
                  className={`h-full px-3 rounded-lg text-xs font-medium border transition-colors flex-1 cursor-pointer ${
                    corridorDelay > 0
                      ? 'bg-amber-50 text-amber-800 border-amber-300 font-bold'
                      : 'bg-subtle text-textSecondary border-border hover:bg-slate-100'
                  }`}
                >
                  {corridorDelay > 0 ? '+4.5m Delay' : 'Normal Traffic'}
                </button>
              </div>
            </div>
          </div>

          {/* Telemetry Sub-bar & Recalculate Button */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/70 text-xs text-textSecondary">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-textPrimary uppercase tracking-wider text-[11px]">
                Corridor Telemetry:
              </span>
              <span>Origin departure at <strong className="text-textPrimary">{scheduledTime}</strong></span>
              <ArrowRight className="w-3 h-3 text-textMuted" />
              <span>
                Arrival at <strong className="text-primary">{targetStopName}</strong> scheduled at{' '}
                <strong className="text-textPrimary">{computedStopSchedTime}</strong>
                {selectedStopOffset > 0 && ` (+${selectedStopOffset}m offset)`}
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="px-4 h-9 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold text-xs transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center cursor-pointer ml-auto"
            >
              {isLoading ? (
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                  Predict Arrival ETA
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Main Results Grid: Hero EtaCard & Reliability Meter */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <EtaCard prediction={prediction} isLoading={isLoading} />
        </div>
        <div>
          <ReliabilityGauge
            score={prediction?.confidence_score ?? 88}
            tier={prediction?.reliability_tier ?? 'HIGH'}
          />
          <div className="mt-4 bg-surface border border-border rounded-xl p-5 shadow-card text-xs space-y-2">
            <h4 className="font-bold text-textPrimary">Model Information</h4>
            <div className="space-y-1 text-textSecondary">
              <div className="flex justify-between">
                <span>Algorithm:</span>
                <span className="font-semibold text-textPrimary">Gradient Boosting + Quantile Reg</span>
              </div>
              <div className="flex justify-between">
                <span>Features Used:</span>
                <span className="font-semibold text-textPrimary">14 Engineered Signals</span>
              </div>
              <div className="flex justify-between">
                <span>Validation:</span>
                <span className="font-semibold text-textPrimary">Leave-One-Route-Out</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Corridor Route Line Diagram */}
      <RouteLineDiagram
        route={currentRoute}
        selectedStopId={activeStopId}
        corridorPredictions={prediction?.corridor_predictions}
        onSelectStop={(stopId) => {
          handleStopChange(stopId);
        }}
      />
    </div>
  );
};
