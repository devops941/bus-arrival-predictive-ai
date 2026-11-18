import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, ArrowDownRight } from 'lucide-react';
import { getDelayCategory } from '../../lib/utils';

interface StatusBadgeProps {
  delayMinutes: number;
  showMinutes?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ delayMinutes, showMinutes = true }) => {
  const cat = getDelayCategory(delayMinutes);

  if (cat === 'early') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
        <ArrowDownRight className="w-3.5 h-3.5 mr-1 text-sky-600" />
        Early {showMinutes && `(${Math.abs(delayMinutes).toFixed(1)}m)`}
      </span>
    );
  }

  if (cat === 'ontime') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-ontime-soft text-ontime-text border border-green-200">
        <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-ontime-chart" />
        On-Time {showMinutes && `(${delayMinutes >= 0 ? '+' : ''}${delayMinutes.toFixed(1)}m)`}
      </span>
    );
  }

  if (cat === 'minor') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-minor-soft text-minor-text border border-amber-200">
        <Clock className="w-3.5 h-3.5 mr-1 text-minor-chart" />
        Minor Delay {showMinutes && `(+${delayMinutes.toFixed(1)}m)`}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-major-soft text-major-text border border-red-200">
      <AlertTriangle className="w-3.5 h-3.5 mr-1 text-major-chart" />
      Major Delay {showMinutes && `(+${delayMinutes.toFixed(1)}m)`}
    </span>
  );
};
