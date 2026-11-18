import React from 'react';
import type { EtaPredictionResponse } from '../../types';
import { formatTimeOnly, getReliabilityProps } from '../../lib/utils';
import { Clock, ShieldCheck, Info, Sparkles } from 'lucide-react';

interface EtaCardProps {
  prediction: EtaPredictionResponse | null;
  isLoading?: boolean;
}

export const EtaCard: React.FC<EtaCardProps> = ({ prediction, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-8 shadow-card animate-pulse space-y-4">
        <div className="h-6 w-40 bg-subtle rounded-md" />
        <div className="h-16 w-56 bg-subtle rounded-xl" />
        <div className="h-4 w-full bg-subtle rounded-md" />
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="bg-surface border border-dashed border-border rounded-2xl p-8 shadow-card text-center flex flex-col items-center justify-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-primary-soft text-primary flex items-center justify-center">
          <Clock className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-textPrimary">Select Route & Stop to Predict ETA</h2>
        <p className="text-xs text-textSecondary max-w-md">
          Our Gradient Boosting model computes honest arrival time estimates with P50 and P90 confidence intervals
          based on corridor congestion and delay history.
        </p>
      </div>
    );
  }

  const p50Time = formatTimeOnly(prediction.predicted_arrival_p50);
  const p90Time = formatTimeOnly(prediction.predicted_arrival_p90);
  const schedTime = formatTimeOnly(prediction.scheduled_arrival);
  const rel = getReliabilityProps(prediction.reliability_tier);

  return (
    <div className="bg-surface border border-border rounded-2xl p-6 md:p-8 shadow-card relative overflow-hidden space-y-6">
      {/* Background Accent Gradient */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-prediction-soft/40 to-transparent rounded-full -mr-20 -mt-20 pointer-events-none" />

      {/* Header Info: Stop Name + Reliability Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/80 pb-4">
        <div>
          <span className="text-xs font-semibold text-textMuted uppercase tracking-wider">
            Destination Arrival Stop
          </span>
          <h2 className="text-xl font-extrabold text-textPrimary mt-0.5">
            {prediction.stop_name}
          </h2>
          <p className="text-xs text-textSecondary">
            Scheduled arrival:{' '}
            <span className="font-semibold text-textPrimary">{schedTime}</span>
          </p>
        </div>

        {/* Reliability Chip */}
        <div className="flex items-center space-x-2">
          <div className={`px-3 py-1.5 rounded-full border text-xs font-bold flex items-center shadow-xs ${rel.colorClass}`}>
            <ShieldCheck className="w-4 h-4 mr-1.5 shrink-0" />
            <span>{rel.label}</span>
            <span className="ml-2 px-1.5 py-0.2 rounded-full bg-white/80 text-[10px]">
              {prediction.confidence_score}%
            </span>
          </div>
        </div>
      </div>

      {/* Hero ETA Display */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        <div>
          <span className="text-xs font-semibold text-textSecondary uppercase tracking-wider flex items-center">
            <Sparkles className="w-3.5 h-3.5 mr-1 text-prediction-chart" />
            Most Likely Arrival (P50 Median)
          </span>
          <div className="text-4xl md:text-5xl font-black text-prediction-text tracking-tight mt-1 tnum">
            {p50Time}
          </div>
          <div className="flex items-center space-x-2 mt-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                prediction.expected_delay_min > 2
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-green-100 text-green-800'
              }`}
            >
              {prediction.expected_delay_min > 0
                ? `+${prediction.expected_delay_min.toFixed(1)} min delay`
                : 'On-Time'}
            </span>
            <span className="text-xs text-textMuted">
              vs scheduled timetable
            </span>
          </div>
        </div>

        {/* P90 Conservative Range Box */}
        <div className="bg-subtle/80 border border-border rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-textSecondary">Arrival Confidence Interval</span>
            <span className="font-bold text-prediction-text">90% Certainty</span>
          </div>

          {/* Visual Confidence Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-bold text-textPrimary tnum">
              <span>{p50Time} (P50)</span>
              <span>{p90Time} (P90)</span>
            </div>
            <div className="h-3 w-full bg-slate-200 rounded-full relative overflow-hidden">
              <div className="h-full bg-gradient-to-r from-primary to-prediction-chart rounded-full w-full" />
            </div>
            <div className="flex justify-between text-[11px] text-textMuted">
              <span>Standard transit estimate</span>
              <span>Conservative upper bound</span>
            </div>
          </div>
        </div>
      </div>

      {/* Corridor Prediction Disclaimers per Section 1.1 / 16 */}
      <div className="bg-blue-50/60 border border-blue-200/80 rounded-xl p-3.5 flex items-start space-x-3 text-xs text-blue-900">
        <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold">Honest ML Estimate:</span>{' '}
          {prediction.disclaimer ||
            'Arrival times are statistical estimates derived from historical corridor patterns, traffic volume, and weather shocks. Actual arrival may vary with real-time road conditions.'}
        </div>
      </div>
    </div>
  );
};
