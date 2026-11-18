import React from 'react';
import { Link } from 'react-router-dom';
import {
  Bus,
  Clock,
  ShieldCheck,
  BarChart3,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-base text-textPrimary font-sans select-none flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="h-16 bg-surface border-b border-border px-6 md:px-12 flex items-center justify-between shadow-xs sticky top-0 z-30">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-primary text-white flex items-center justify-center shadow-xs">
            <Bus className="w-5 h-5" />
          </div>
          <span className="font-extrabold text-lg tracking-tight text-textPrimary">
            BusArrival <span className="text-primary font-bold">AI</span>
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/login"
            className="px-3.5 py-1.5 text-xs font-semibold text-textSecondary hover:text-textPrimary hover:bg-subtle rounded-input transition-colors"
          >
            Sign In
          </Link>
          <Link
            to="/dashboard"
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-input shadow-xs transition-colors flex items-center"
          >
            Launch Dashboard
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-6 py-12 md:py-20 space-y-16">
        <div className="text-center space-y-5 max-w-3xl mx-auto">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary-soft text-primary text-xs font-bold border border-primary/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Final-Year Smart Cities Intelligence Project</span>
          </div>

          <h1 className="text-4xl md:text-5xl font-black text-textPrimary tracking-tight leading-tight">
            Predictive Public Transit Arrival Intelligence
          </h1>

          <p className="text-base md:text-lg text-textSecondary leading-relaxed">
            Replacing static timetables with classic machine learning arrival forecasts.
            Always computed with honest <strong className="text-textPrimary font-semibold">P50 & P90 confidence intervals</strong>,
            hourly delay profiling, and corridor bottleneck analytics.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/eta"
              className="w-full sm:w-auto px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-input text-sm font-bold shadow-md transition-all flex items-center justify-center"
            >
              Predict Stop Arrival (ETA)
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
            <Link
              to="/dashboard"
              className="w-full sm:w-auto px-6 py-3 bg-surface hover:bg-slate-100 border border-border text-textPrimary rounded-input text-sm font-semibold transition-all flex items-center justify-center shadow-xs"
            >
              View Delay Trends & Heatmaps
            </Link>
          </div>
        </div>

        {/* Hero Interactive ETA Card Mockup */}
        <div className="bg-surface border border-border rounded-2xl p-6 md:p-8 shadow-dropdown max-w-2xl mx-auto space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-4">
            <div className="flex items-center space-x-2">
              <span className="w-7 h-5 rounded bg-primary-soft text-primary font-bold text-xs flex items-center justify-center">
                101
              </span>
              <span className="text-sm font-bold text-textPrimary">Metro Core Line &bull; City Center Station</span>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              High Confidence (92%)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
            <div>
              <span className="text-xs font-semibold text-textSecondary uppercase">Predicted Arrival (P50)</span>
              <div className="text-4xl font-black text-prediction-text mt-1 tnum">14:32</div>
              <p className="text-xs text-textMuted mt-1">Expected delay: +3.2m vs scheduled 14:28</p>
            </div>
            <div className="bg-subtle/80 p-4 rounded-xl border border-border space-y-2 text-xs">
              <div className="flex justify-between font-bold">
                <span className="text-textSecondary">P90 Confidence Interval</span>
                <span className="text-prediction-text">14:32 — 14:36</span>
              </div>
              <div className="h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-primary to-prediction-chart w-full" />
              </div>
              <span className="text-[11px] text-textMuted block">90% chance bus arrives by 14:36</span>
            </div>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
          <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-3">
            <div className="w-10 h-10 rounded-xl bg-prediction-soft text-prediction-text flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-textPrimary">P50 & P90 Quantile Interval</h3>
            <p className="text-xs text-textSecondary leading-relaxed">
              Never a single naive number. Riders receive both median expected arrival and a 90th-percentile conservative bound.
            </p>
          </div>

          <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-3">
            <div className="w-10 h-10 rounded-xl bg-primary-soft text-primary flex items-center justify-center">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-textPrimary">Corridor Heatmaps</h3>
            <p className="text-xs text-textSecondary leading-relaxed">
              Dissect traffic bottlenecks across all 24 hours and 7 days. Spot rain shocks and commuter rush hours instantly.
            </p>
          </div>

          <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-3">
            <div className="w-10 h-10 rounded-xl bg-teal-soft text-teal flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-textPrimary">Classic ML Governance</h3>
            <p className="text-xs text-textSecondary leading-relaxed">
              No black-box deep learning. Gradient boosting and regularized regression trained with TimeSeriesSplit and Leave-One-Route-Out validation.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-surface border-t border-border py-8 px-6 text-center text-xs text-textMuted space-y-2">
        <p className="font-semibold text-textSecondary">
          BusArrival AI &bull; Predictive Public Transit Arrival Intelligence
        </p>
        <p>Built with React 18, Vite, TypeScript, Tailwind CSS, FastAPI, and MongoDB Atlas.</p>
        <div className="pt-2 flex justify-center space-x-4">
          <Link to="/about" className="hover:text-primary transition-colors">Methodology & Formulas</Link>
          <span>&bull;</span>
          <Link to="/login" className="hover:text-primary transition-colors">Sign In</Link>
          <span>&bull;</span>
          <Link to="/dashboard" className="hover:text-primary transition-colors">Transit Dashboard</Link>
        </div>
      </footer>
    </div>
  );
};
