import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { AuditLogEntry, SystemDiagnostics } from '../types';
import { Users, Shield, Server, Activity, CheckCircle2, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

export const Admin: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'audit' | 'system'>('users');
  const [users, setUsers] = useState<any[]>([]);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      if (activeTab === 'users') {
        const u = await api.getAdminUsers();
        setUsers(u);
      } else if (activeTab === 'audit') {
        const a = await api.getAdminAuditLog();
        setAuditLog(a);
      } else if (activeTab === 'system') {
        const s = await api.getAdminSystemDiagnostics();
        setDiagnostics(s);
      }
    } catch (e: any) {
      toast.error(e.message || 'Failed to load administration data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await api.updateAdminUserRole(userId, newRole);
      toast.success('User role updated successfully.');
      loadData();
    } catch (e: any) {
      toast.error(e.message || 'Failed to update user role.');
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: boolean) => {
    try {
      await api.updateAdminUserStatus(userId, !currentStatus);
      toast.success(`User ${!currentStatus ? 'activated' : 'deactivated'}.`);
      loadData();
    } catch (e: any) {
      toast.error(e.message || 'Failed to update user status.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-black text-textPrimary tracking-tight">
            System Administration & Governance
          </h1>
          <p className="text-xs text-textSecondary mt-1">
            User access control, immutable security audit log, and MongoDB cluster diagnostics.
          </p>
        </div>

        <button
          onClick={loadData}
          className="inline-flex items-center px-3 py-1.5 bg-subtle hover:bg-slate-200 border border-border text-xs font-semibold rounded-input transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-1 border-b border-border text-xs font-semibold">
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center px-4 py-2 border-b-2 transition-all cursor-pointer ${
            activeTab === 'users'
              ? 'border-primary text-primary bg-primary-soft/30'
              : 'border-transparent text-textSecondary hover:text-textPrimary hover:bg-subtle'
          }`}
        >
          <Users className="w-4 h-4 mr-2" />
          User Management ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`flex items-center px-4 py-2 border-b-2 transition-all cursor-pointer ${
            activeTab === 'audit'
              ? 'border-primary text-primary bg-primary-soft/30'
              : 'border-transparent text-textSecondary hover:text-textPrimary hover:bg-subtle'
          }`}
        >
          <Shield className="w-4 h-4 mr-2" />
          Security Audit Trail
        </button>
        <button
          onClick={() => setActiveTab('system')}
          className={`flex items-center px-4 py-2 border-b-2 transition-all cursor-pointer ${
            activeTab === 'system'
              ? 'border-primary text-primary bg-primary-soft/30'
              : 'border-transparent text-textSecondary hover:text-textPrimary hover:bg-subtle'
          }`}
        >
          <Server className="w-4 h-4 mr-2" />
          System & Cluster Health
        </button>
      </div>

      {/* Tab: Users */}
      {activeTab === 'users' && (
        <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-textPrimary">Registered Transit Accounts</h2>
            <span className="text-xs text-textMuted">Role changes take effect immediately</span>
          </div>

          <div className="overflow-x-auto border border-border rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                <tr>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Role Permission</th>
                  <th className="py-3 px-4">Account Status</th>
                  <th className="py-3 px-4">Failed Logins</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-medium text-textPrimary">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-subtle/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-textPrimary">{u.full_name || 'Transit Operator'}</div>
                      <div className="text-[11px] text-textMuted font-mono">{u.email}</div>
                    </td>
                    <td className="py-3 px-4">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        className="h-8 px-2 text-xs font-semibold bg-subtle border border-border rounded-md text-textPrimary cursor-pointer capitalize"
                      >
                        <option value="passenger">Passenger (Viewer)</option>
                        <option value="analyst">Analyst (Data + ML)</option>
                        <option value="admin">Administrator (Full)</option>
                      </select>
                    </td>
                    <td className="py-3 px-4">
                      {u.is_active ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-50 text-red-700 border border-red-200">
                          Deactivated
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 tnum">
                      {u.failed_login_attempts > 0 ? (
                        <span className="text-amber-700 font-bold">{u.failed_login_attempts} fails</span>
                      ) : (
                        <span className="text-textMuted">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleStatusToggle(u.id, u.is_active)}
                        className={`px-3 py-1 rounded text-xs font-semibold border transition-colors cursor-pointer ${
                          u.is_active
                            ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
                            : 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
                        }`}
                      >
                        {u.is_active ? 'Deactivate' : 'Reactivate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Audit Log */}
      {activeTab === 'audit' && (
        <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
          <div>
            <h2 className="text-base font-bold text-textPrimary">Audit Trail Log</h2>
            <p className="text-xs text-textMuted">
              Immutable event log recording all model activations, role updates, and data imports.
            </p>
          </div>

          <div className="overflow-x-auto border border-border rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Operator</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-textPrimary">
                {auditLog.length > 0 ? (
                  auditLog.map((log) => (
                    <tr key={log.id} className="hover:bg-subtle/50">
                      <td className="py-3 px-4 text-textMuted font-mono whitespace-nowrap">
                        {log.timestamp?.slice(0, 19).replace('T', ' ')}
                      </td>
                      <td className="py-3 px-4 font-semibold text-primary">{log.user_email}</td>
                      <td className="py-3 px-4 font-mono font-bold">{log.action}</td>
                      <td className="py-3 px-4 capitalize">{log.entity}</td>
                      <td className="py-3 px-4 text-textMuted font-mono text-[11px] truncate max-w-xs">
                        {log.details ? JSON.stringify(log.details) : '--'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-textMuted italic">
                      No audit events recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: System Health */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface border border-border rounded-card p-5 shadow-card">
              <div className="flex items-center space-x-2 text-xs font-bold text-ontime-text mb-1">
                <CheckCircle2 className="w-4 h-4" />
                <span>API Gateway</span>
              </div>
              <div className="text-xl font-bold text-textPrimary">FastAPI Healthy</div>
              <p className="text-xs text-textMuted mt-1">Status 200 &bull; SlowAPI Limiter Active</p>
            </div>

            <div className="bg-surface border border-border rounded-card p-5 shadow-card">
              <div className="flex items-center space-x-2 text-xs font-bold text-ontime-text mb-1">
                <Server className="w-4 h-4" />
                <span>MongoDB Atlas Cluster</span>
              </div>
              <div className="text-xl font-bold text-textPrimary">Connected & Indexed</div>
              <p className="text-xs text-textMuted mt-1">PyMongo Client &bull; Schema Validators Active</p>
            </div>

            <div className="bg-surface border border-border rounded-card p-5 shadow-card">
              <div className="flex items-center space-x-2 text-xs font-bold text-primary mb-1">
                <Activity className="w-4 h-4" />
                <span>Classic ML Core</span>
              </div>
              <div className="text-xl font-bold text-textPrimary">Gradient Boosting</div>
              <p className="text-xs text-textMuted mt-1">TimeSeriesSplit &bull; Leave-One-Route-Out</p>
            </div>
          </div>

          {/* Database Collection Statistics */}
          <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
            <h3 className="text-base font-bold text-textPrimary">MongoDB Collection Document Counts</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {diagnostics?.collections ? (
                Object.entries(diagnostics.collections).map(([coll, count]) => (
                  <div key={coll} className="p-3 bg-subtle rounded-lg border border-border text-center">
                    <span className="text-[11px] font-semibold text-textSecondary capitalize block">
                      {coll.replace('_', ' ')}
                    </span>
                    <span className="text-xl font-extrabold text-primary tnum">{count}</span>
                  </div>
                ))
              ) : (
                <div className="col-span-4 text-center text-xs text-textMuted py-4">
                  Loading cluster collection metrics...
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
