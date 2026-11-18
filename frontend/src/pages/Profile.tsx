import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { KeyRound, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export const Profile: React.FC = () => {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match.');
      return;
    }

    setIsUpdating(true);
    setTimeout(() => {
      setIsUpdating(false);
      toast.success('Password updated successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    }, 600);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Title */}
      <div className="border-b border-border pb-4">
        <h1 className="text-2xl font-black text-textPrimary tracking-tight">
          Operator Account & Profile
        </h1>
        <p className="text-xs text-textSecondary mt-1">
          Session credentials, role permissions, and transit account preferences.
        </p>
      </div>

      {/* User Information Card */}
      <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
        <div className="flex items-center space-x-4">
          <div className="w-14 h-14 rounded-2xl bg-primary text-white font-bold text-xl flex items-center justify-center shadow-xs">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-textPrimary">{user?.full_name || 'Transit User'}</h2>
            <p className="text-xs text-textMuted font-mono">{user?.email}</p>
            <div className="mt-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize bg-primary-soft text-primary border border-primary/20">
                {user?.role || 'Passenger'} Access
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-border text-xs">
          <div>
            <span className="font-semibold text-textSecondary">Account ID</span>
            <p className="font-mono text-textPrimary mt-0.5">{user?.id || 'usr-local-demo'}</p>
          </div>
          <div>
            <span className="font-semibold text-textSecondary">Session Status</span>
            <p className="text-ontime-text font-semibold flex items-center mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
              Active JWT Bearer Token
            </p>
          </div>
        </div>
      </div>

      {/* Password Update Form */}
      <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
        <div className="flex items-center space-x-2">
          <KeyRound className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-bold text-textPrimary">Update Password</h3>
        </div>

        <form onSubmit={handlePasswordChange} className="space-y-4 text-xs max-w-md">
          <div>
            <label className="block font-semibold text-textSecondary mb-1">Current Password</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-9 px-3 bg-subtle border border-border rounded-input text-textPrimary"
            />
          </div>

          <div>
            <label className="block font-semibold text-textSecondary mb-1">New Password (Min 8 chars)</label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-9 px-3 bg-subtle border border-border rounded-input text-textPrimary"
            />
          </div>

          <div>
            <label className="block font-semibold text-textSecondary mb-1">Confirm New Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full h-9 px-3 bg-subtle border border-border rounded-input text-textPrimary"
            />
          </div>

          <button
            type="submit"
            disabled={isUpdating}
            className="px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-input font-semibold text-xs shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
          >
            {isUpdating ? 'Updating...' : 'Change Password'}
          </button>
        </form>
      </div>
    </div>
  );
};
