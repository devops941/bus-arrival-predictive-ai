import React from 'react';
import { BookOpen, Sparkles, ShieldCheck, Info } from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Title */}
      <div className="border-b border-border pb-4">
        <h1 className="text-2xl font-black text-textPrimary tracking-tight">
          Transit Methodology, Formulas & Ethics
        </h1>
        <p className="text-xs text-textSecondary mt-1">
          Technical specifications, mathematical foundations, and honest modeling principles of BusArrival AI.
        </p>
      </div>

      {/* Section 1: Objective & Philosophy */}
      <section className="bg-surface border border-border rounded-card p-6 shadow-card space-y-3">
        <h2 className="text-base font-bold text-textPrimary flex items-center">
          <Sparkles className="w-4 h-4 mr-2 text-primary" />
          1. System Philosophy: Classical ML Over Black Boxes
        </h2>
        <p className="text-xs text-textSecondary leading-relaxed">
          Public transit operators and riders require transparent, reproducible, and verifiable estimates.
          Deep neural networks often act as uninterpretable black boxes and can hallucinate when operating outside observed domains.
          BusArrival AI relies exclusively on classical machine learning: L2 Regularized Ridge Regression, Random Forest Ensembles,
          and Gradient Boosted Trees optimized under asymmetric Pinball Quantile Loss.
        </p>
      </section>

      {/* Section 2: Mathematical Formulations */}
      <section className="bg-surface border border-border rounded-card p-6 shadow-card space-y-6">
        <h2 className="text-base font-bold text-textPrimary flex items-center">
          <BookOpen className="w-4 h-4 mr-2 text-primary" />
          2. Mathematical Foundations
        </h2>

        {/* Cyclical Time */}
        <div className="space-y-2 text-xs">
          <h3 className="font-bold text-textPrimary">A. Cyclical Time Representations</h3>
          <p className="text-textSecondary leading-relaxed">
            Standard 24-hour timestamps suffer from a discontinuous jump between 23:59 and 00:00. To preserve continuous temporal proximity, hours are projected onto the unit trigonometric circle:
          </p>
          <div className="p-3 bg-subtle rounded-md font-mono text-[11px] text-textPrimary">
            sin_hour = sin(2 * π * hour / 24.0)<br />
            cos_hour = cos(2 * π * hour / 24.0)
          </div>
        </div>

        {/* Quantile Pinball Loss */}
        <div className="space-y-2 text-xs">
          <h3 className="font-bold text-textPrimary">B. Pinball Quantile Loss ($L_q$)</h3>
          <p className="text-textSecondary leading-relaxed">
            To generate reliable upper-bound arrival forecasts ($P90$) that bound passenger wait times with 90% confidence, models are trained against the tilted absolute loss:
          </p>
          <div className="p-3 bg-subtle rounded-md font-mono text-[11px] text-textPrimary">
            L_q(y, y_hat) = max(q * (y - y_hat), (q - 1) * (y - y_hat))
          </div>
          <p className="text-textMuted text-[11px]">
            Where q = 0.50 yields the conditional median (P50) and q = 0.90 penalizes under-predictions 9x more heavily than over-predictions.
          </p>
        </div>

        {/* Regression Metrics */}
        <div className="space-y-2 text-xs">
          <h3 className="font-bold text-textPrimary">C. Evaluation Metrics</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
            <div className="p-3 bg-subtle rounded-md">
              <span className="font-bold block text-primary">MAE</span>
              <span className="text-[11px] font-mono">Σ |y - y_hat| / n</span>
              <p className="text-[10px] text-textMuted mt-1">Average absolute prediction deviation in minutes.</p>
            </div>
            <div className="p-3 bg-subtle rounded-md">
              <span className="font-bold block text-primary">RMSE</span>
              <span className="text-[11px] font-mono">sqrt(Σ (y - y_hat)² / n)</span>
              <p className="text-[10px] text-textMuted mt-1">Quadratic penalty for severe transit delays.</p>
            </div>
            <div className="p-3 bg-subtle rounded-md">
              <span className="font-bold block text-primary">Systemic Bias</span>
              <span className="text-[11px] font-mono">Σ (y_hat - y) / n</span>
              <p className="text-[10px] text-textMuted mt-1">Detects whether models chronically over- or under-estimate.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Validation Integrity */}
      <section className="bg-surface border border-border rounded-card p-6 shadow-card space-y-3">
        <h2 className="text-base font-bold text-textPrimary flex items-center">
          <ShieldCheck className="w-4 h-4 mr-2 text-emerald-600" />
          3. Validation Integrity & Leakage Prevention
        </h2>
        <ul className="text-xs text-textSecondary space-y-2 list-disc list-inside leading-relaxed">
          <li>
            <strong>Strict Chronological Split:</strong> Models are trained on past observations $[0, T]$ and tested on subsequent trips $(T, T + \Delta]$. No future information ever leaks into historical feature matrices.
          </li>
          <li>
            <strong>Leave-One-Route-Out Validation:</strong> Models are verified on corridors completely omitted from training to ensure transit physics generalize across the city.
          </li>
          <li>
            <strong>Automated Drift Alerters:</strong> If recent corridor MAE exceeds baseline variance by 30% (ratio &ge; 1.3), an automated alert is triggered.
          </li>
        </ul>
      </section>

      {/* Section 4: Honest Disclaimer */}
      <section className="bg-amber-50/70 border border-amber-200 rounded-card p-5 space-y-2">
        <div className="flex items-center space-x-2 text-xs font-bold text-amber-900">
          <Info className="w-4 h-4 text-amber-600" />
          <span>Honest Modeling Disclaimer</span>
        </div>
        <p className="text-xs text-amber-800 leading-relaxed">
          Transit arrivals are influenced by stochastic real-world factors including traffic accidents, signal breakdowns, and weather shocks.
          Predictions provided by BusArrival AI represent statistical likelihoods (P50 median and P90 conservative intervals) derived from historical patterns.
          They are decision aids for riders and operators, not guaranteed absolute schedules.
        </p>
      </section>
    </div>
  );
};
