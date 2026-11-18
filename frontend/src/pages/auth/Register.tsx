import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Bus, Check, X, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'passenger' | 'analyst' | 'admin'>('passenger');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Password strength calculation
  const hasMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);

  const strengthScore = [hasMinLength, hasNumber, hasUpper, hasSpecial].filter(Boolean).length;
  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong'];
  const strengthColors = ['bg-red-400', 'bg-orange-400', 'bg-amber-400', 'bg-emerald-500', 'bg-green-600'];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasMinLength) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await register({
        email,
        password,
        full_name: fullName,
        role,
      });
      toast.success('Registration successful! Welcome aboard.');
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base p-6 select-none">
      <div className="w-full max-w-lg bg-surface border border-border rounded-2xl shadow-card p-8 md:p-10 space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-primary text-white flex items-center justify-center">
            <Bus className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-textPrimary">Create an Account</h1>
            <p className="text-xs text-textSecondary">Join BusArrival AI transit intelligence</p>
          </div>
        </div>

        {error && (
          <div className="p-3.5 bg-major-soft text-major-text rounded-lg border border-red-200 text-sm flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-major-chart shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. Alex Morgan"
              className="w-full h-10 px-3.5 text-sm bg-subtle border border-border rounded-input text-textPrimary focus:ring-2 focus:ring-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alex@transit.local"
              className="w-full h-10 px-3.5 text-sm bg-subtle border border-border rounded-input text-textPrimary focus:ring-2 focus:ring-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
              Desired Role (Testing Demo)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['passenger', 'analyst', 'admin'] as const).map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => setRole(r)}
                  className={`py-2 text-xs font-semibold capitalize rounded-md border transition-all ${
                    role === r
                      ? 'bg-primary text-white border-primary shadow-xs'
                      : 'bg-subtle text-textSecondary border-border hover:bg-slate-100'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-textSecondary uppercase tracking-wider mb-1.5">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-10 px-3.5 text-sm bg-subtle border border-border rounded-input text-textPrimary focus:ring-2 focus:ring-primary focus:outline-none"
            />

            {/* Password Strength Meter */}
            {password.length > 0 && (
              <div className="mt-2 space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-textMuted font-medium">Strength:</span>
                  <span className="font-semibold text-textSecondary">
                    {strengthLabels[strengthScore]}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-subtle rounded-full overflow-hidden flex space-x-1">
                  {[1, 2, 3, 4].map((step) => (
                    <div
                      key={step}
                      className={`h-full flex-1 transition-all ${
                        strengthScore >= step ? strengthColors[strengthScore] : 'bg-slate-200'
                      }`}
                    />
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-1 pt-1 text-[11px] text-textMuted">
                  <span className="flex items-center">
                    {hasMinLength ? <Check className="w-3 h-3 text-ontime-chart mr-1" /> : <X className="w-3 h-3 text-textMuted mr-1" />}
                    8+ characters
                  </span>
                  <span className="flex items-center">
                    {hasNumber ? <Check className="w-3 h-3 text-ontime-chart mr-1" /> : <X className="w-3 h-3 text-textMuted mr-1" />}
                    Contains number
                  </span>
                  <span className="flex items-center">
                    {hasUpper ? <Check className="w-3 h-3 text-ontime-chart mr-1" /> : <X className="w-3 h-3 text-textMuted mr-1" />}
                    Uppercase letter
                  </span>
                  <span className="flex items-center">
                    {hasSpecial ? <Check className="w-3 h-3 text-ontime-chart mr-1" /> : <X className="w-3 h-3 text-textMuted mr-1" />}
                    Special character
                  </span>
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full h-11 bg-primary hover:bg-primary-hover text-white rounded-input font-semibold text-sm transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center cursor-pointer mt-2"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="text-center text-xs text-textSecondary pt-2 border-t border-border">
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-primary hover:underline">
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  );
};
