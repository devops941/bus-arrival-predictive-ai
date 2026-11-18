import React from 'react';
import { ShieldCheck, ShieldAlert, Shield } from 'lucide-react';
import { getReliabilityProps } from '../../lib/utils';

interface ReliabilityGaugeProps {
  score?: number;
  tier?: 'HIGH' | 'MEDIUM' | 'LOW';
}

export const ReliabilityGauge: React.FC<ReliabilityGaugeProps> = ({
  score = 85,
  tier = 'HIGH',
}) => {
  const props = getReliabilityProps(tier);

  return (
    <div className="bg-surface border border-border rounded-card p-5 shadow-card space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-textSecondary uppercase tracking-wider">
          Prediction Confidence Meter
        </h3>
        <span className="text-xs font-bold text-textPrimary">{score}%</span>
      </div>

      {/* Progress Track */}
      <div className="h-3 w-full bg-subtle rounded-full overflow-hidden p-0.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            tier === 'HIGH'
              ? 'bg-emerald-500'
              : tier === 'MEDIUM'
              ? 'bg-amber-500'
              : 'bg-rose-500'
          }`}
          style={{ width: `${Math.min(100, Math.max(10, score))}%` }}
        />
      </div>

      <div className="flex items-start space-x-2.5 pt-1 text-xs">
        {tier === 'HIGH' ? (
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
        ) : tier === 'MEDIUM' ? (
          <Shield className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        ) : (
          <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
        )}
        <div>
          <span className="font-bold text-textPrimary">{props.label}</span>
          <p className="text-[11px] text-textMuted mt-0.5 leading-normal">
            {props.description}
          </p>
        </div>
      </div>
    </div>
  );
};
