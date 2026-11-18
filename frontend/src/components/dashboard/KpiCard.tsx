import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../../lib/utils';

interface KpiCardProps {
  title: string;
  value: string | number;
  delta?: {
    value: string;
    isPositiveGood?: boolean;
    isIncrease?: boolean;
    neutral?: boolean;
  };
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  sparklineData?: number[];
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  delta,
  subtitle,
  icon: Icon,
  iconColor = 'text-primary',
  iconBg = 'bg-primary-soft',
  sparklineData = [12, 14, 13, 15, 17, 16, 18],
}) => {
  return (
    <div className="bg-surface border border-border rounded-card p-5 shadow-card hover:shadow-cardHover transition-all flex flex-col justify-between">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-textSecondary uppercase tracking-wider">
            {title}
          </p>
          <div className="text-2xl md:text-3xl font-extrabold text-textPrimary tracking-tight mt-1 tnum">
            {value}
          </div>
        </div>
        <div className={cn('p-2.5 rounded-xl shrink-0', iconBg, iconColor)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs">
        {delta ? (
          <div className="flex items-center space-x-1.5">
            {delta.neutral ? (
              <span className="flex items-center text-textMuted font-medium">
                <Minus className="w-3.5 h-3.5 mr-0.5" />
                {delta.value}
              </span>
            ) : delta.isIncrease ? (
              <span
                className={cn(
                  'flex items-center font-semibold',
                  delta.isPositiveGood ? 'text-ontime-text' : 'text-major-text'
                )}
              >
                <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
                {delta.value}
              </span>
            ) : (
              <span
                className={cn(
                  'flex items-center font-semibold',
                  delta.isPositiveGood ? 'text-ontime-text' : 'text-major-text'
                )}
              >
                <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
                {delta.value}
              </span>
            )}
            <span className="text-textMuted">{subtitle || 'vs previous period'}</span>
          </div>
        ) : (
          <span className="text-textMuted">{subtitle || 'Active corridor metric'}</span>
        )}

        {/* Mini SVG Sparkline */}
        {sparklineData && sparklineData.length > 1 && (
          <div className="w-16 h-5 flex items-end space-x-0.5 shrink-0 opacity-70">
            {sparklineData.map((v, i) => {
              const max = Math.max(...sparklineData);
              const min = Math.min(...sparklineData);
              const heightPct = max === min ? 50 : Math.max(15, Math.round(((v - min) / (max - min)) * 100));
              return (
                <div
                  key={i}
                  style={{ height: `${heightPct}%` }}
                  className="w-2 bg-primary/70 rounded-t-xs hover:bg-primary transition-colors"
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
