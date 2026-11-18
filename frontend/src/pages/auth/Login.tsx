import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Bus, Eye, EyeOff, ShieldCheck, Clock, BarChart3, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await login(email, password);
      toast.success('Welcome back to BusArrival AI');
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setIsLoading(true);
    setError(null);
    try {
      await login(demoEmail, demoPass);
      toast.success(`Signed in as ${demoEmail}`);
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err.message || 'Demo login failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-base font-sans select-none">
      {/* Left Brand Panel - Soft Blue Gradient with Route SVG */}
      <div className="md:w-1/2 bg-gradient-to-br from-[#EAF1FF] via-[#F1F5FD] to-[#F6F8FB] p-8 md:p-14 flex flex-col justify-between border-b md:border-b-0 md:border-r border-border relative overflow-hidden">
        {/* Subtle Transit Route Line Background Illustration */}
        <div className="absolute inset-0 opacity-15 pointer-events-none">
          <svg className="w-full h-full" viewBox="0 0 600 600" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M 50 100 C 200 100, 250 250, 450 250 S 550 450, 550 550" stroke="#1D4ED8" strokeWidth="6" strokeDasharray="12 12" />
            <circle cx="50" cy="100" r="10" fill="#1D4ED8" />
            <circle cx="250" cy="250" r="8" fill="#0D9488" />
            <circle cx="450" cy="250" r="8" fill="#D97706" />
            <circle cx="550" cy="550" r="10" fill="#15803D" />
            <path d="M 100 500 C 150 350, 350 350, 500 150" stroke="#7C3AED" strokeWidth="4" />
          </svg>
        </div>

        {/* Brand Header */}
        <div className="relative z-10">
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-12 h-12 rounded-2xl bg-primary text-white flex items-center justify-center shadow-md">
              <Bus className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-extrabold text-2xl text-textPrimary tracking-tight">
                BusArrival <span className="text-primary">AI</span>
              </span>
              <p className="text-xs font-semibold uppercase tracking-wider text-textMuted">
                Predictive Transit Intelligence
              </p>
            </div>
          </div>

          <div className="space-y-4 max-w-lg">
            <h1 className="text-3xl md:text-4xl font-extrabold text-textPrimary tracking-tight leading-tight">
              Know when your bus arrives.
            </h1>
            <p className="text-base text-textSecondary leading-relaxed">
              Classical machine learning intelligence replacing static timetables with accurate,
              confidence-banded arrival times and delay diagnostics.
            </p>
          </div>
        </div>

        {/* 3 Value Propositions per wireframe */}
        <div className="space-y-4 my-8 relative z-10 max-w-md">
          <div className="flex items-start space-x-3.5 bg-surface/70 backdrop-blur-xs p-3.5 rounded-card border border-white shadow-xs">
            <div className="p-2 rounded-lg bg-prediction-soft text-prediction-text shrink-0">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-textPrimary">P50 & P90 Arrival Intervals</h2>
              <p className="text-xs text-textSecondary mt-0.5">
                Always paired with honest confidence bounds so riders never miss a connection.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3.5 bg-surface/70 backdrop-blur-xs p-3.5 rounded-card border border-white shadow-xs">
            <div className="p-2 rounded-lg bg-ontime-soft text-ontime-text shrink-0">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-textPrimary">Corridor Delay Diagnostics</h2>
              <p className="text-xs text-textSecondary mt-0.5">
                Analyze bottleneck stops, hourly rush patterns, and rain-induced delay shocks.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3.5 bg-surface/70 backdrop-blur-xs p-3.5 rounded-card border border-white shadow-xs">
            <div className="p-2 rounded-lg bg-primary-soft text-primary shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-textPrimary">Role-Governed Operations</h2>
              <p className="text-xs text-textSecondary mt-0.5">
                Tailored interfaces for Public Passengers, Data Analysts, and Transit Administrators.
              </p>
            </div>
          </div>
        </div>

        {/* Footer Meta */}
        <div className="relative z-10 text-xs text-textMuted flex items-center justify-between">
          <span>Final-Year Smart Cities Project</span>
          <span className="font-semibold text-textSecondary">v1.0 (Light Transit Theme)</span>
        </div>
      </div>

      {/* Right Login Form Card */}
      <div className="md:w-1/2 flex items-center justify-center p-6 md:p-14">
        <div className="w-full max-w-md bg-surface border border-border rounded-2xl shadow-card p-8 md:p-10 space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-textPrimary tracking-tight">Sign In</h2>
            <p className="text-sm text-textSecondary mt-1">
              Access arrival predictions and operator analytics
            </p>
          </div>

          {error && (
            <div className="p-3.5 bg-major-soft text-major-text rounded-lg border border-red-200 text-sm flex items-start space-x-2.5">
              <AlertCircle className="w-5 h-5 text-major-chart shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@transit.local"
                className="w-full h-11 px-3.5 text-sm bg-subtle border border-border rounded-input text-textPrimary placeholder:text-textMuted focus:ring-2 focus:ring-primary focus:bg-white focus:outline-none transition-all"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-textSecondary uppercase tracking-wider">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-primary hover:text-primary-hover hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full h-11 px-3.5 pr-10 text-sm bg-subtle border border-border rounded-input text-textPrimary placeholder:text-textMuted focus:ring-2 focus:ring-primary focus:bg-white focus:outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-3 text-textMuted hover:text-textPrimary"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 text-primary rounded border-border focus:ring-primary"
                />
                <span className="text-xs font-medium text-textSecondary">Remember me</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-11 bg-primary hover:bg-primary-hover text-white rounded-input font-semibold text-sm transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center cursor-pointer"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Quick Demo Logins for Instant Testing */}
          <div className="pt-4 border-t border-border">
            <p className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2.5 text-center">
              Quick Demo Accounts
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoLogin('admin@busarrival.local', 'AdminSecure2026!')}
                className="py-1.5 px-2 text-xs font-medium bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 rounded-md transition-colors"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleDemoLogin('analyst@busarrival.local', 'AnalystPass123!')}
                className="py-1.5 px-2 text-xs font-medium bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200 rounded-md transition-colors"
              >
                Analyst
              </button>
              <button
                type="button"
                onClick={() => handleDemoLogin('passenger@busarrival.local', 'PassengerPass123!')}
                className="py-1.5 px-2 text-xs font-medium bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 rounded-md transition-colors"
              >
                Passenger
              </button>
            </div>
          </div>

          <div className="text-center text-xs text-textSecondary">
            Don't have an account?{' '}
            <Link to="/register" className="font-semibold text-primary hover:underline">
              Create an account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
