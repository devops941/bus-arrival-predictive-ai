import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Navigation,
  LineChart,
  Database,
  SlidersHorizontal,
  Cpu,
  CheckCircle2,
  Bell,
  FileSpreadsheet,
  Settings,
  User,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Bus,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils';

export const Sidebar: React.FC = () => {
  const { role } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const isAnalystOrAdmin = role === 'analyst' || role === 'admin';
  const isAdmin = role === 'admin';

  const navItems = [
    {
      category: 'Transit Intelligence',
      items: [
        { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
        { label: 'ETA Predictor', to: '/eta', icon: Navigation, badge: 'Live P90' },
        { label: 'Trend Explorer', to: '/trends', icon: LineChart },
      ],
    },
    ...(isAnalystOrAdmin
      ? [
          {
            category: 'ML & Operations',
            items: [
              { label: 'Data Entry & Import', to: '/data-entry', icon: Database },
              { label: 'Features Pipeline', to: '/features', icon: SlidersHorizontal },
              { label: 'Model Registry', to: '/models', icon: Cpu },
              { label: 'Accuracy & Drift', to: '/accuracy', icon: CheckCircle2 },
              { label: 'Reports', to: '/reports', icon: FileSpreadsheet },
            ],
          },
        ]
      : []),
    {
      category: 'System',
      items: [
        { label: 'Alerts & Drift', to: '/alerts', icon: Bell },
        ...(isAdmin ? [{ label: 'Admin Management', to: '/admin', icon: Settings }] : []),
        { label: 'Operator Profile', to: '/profile', icon: User },
        { label: 'Methodology & Ethics', to: '/about', icon: BookOpen },
      ],
    },
  ];

  return (
    <aside
      className={cn(
        'h-screen bg-surface border-r border-border flex flex-col justify-between transition-all duration-200 z-40 select-none',
        collapsed ? 'w-18' : 'w-64'
      )}
    >
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-border">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-primary text-white flex items-center justify-center shrink-0 shadow-sm">
              <Bus className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="font-bold text-base text-textPrimary tracking-tight flex items-center">
                  BusArrival <span className="ml-1 text-xs px-1.5 py-0.5 rounded bg-primary-soft text-primary font-semibold">AI</span>
                </span>
                <span className="text-[11px] text-textMuted font-medium">Predictive Transit</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="p-1.5 text-textMuted hover:text-textPrimary hover:bg-subtle rounded-md transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-6 overflow-y-auto max-h-[calc(100vh-8rem)]">
          {navItems.map((group, idx) => (
            <div key={idx} className="space-y-1">
              {!collapsed && (
                <p className="px-3 text-[11px] font-semibold text-textMuted uppercase tracking-wider mb-2">
                  {group.category}
                </p>
              )}
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    title={collapsed ? item.label : undefined}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group',
                        isActive
                          ? 'bg-primary-soft text-primary font-semibold shadow-xs'
                          : 'text-textSecondary hover:text-textPrimary hover:bg-subtle'
                      )
                    }
                  >
                    <Icon className={cn('w-4 h-4 shrink-0', collapsed ? 'mx-auto' : 'mr-3')} />
                    {!collapsed && (
                      <div className="flex items-center justify-between w-full overflow-hidden">
                        <span className="truncate">{item.label}</span>
                        {item.badge && (
                          <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-prediction-soft text-prediction-text shrink-0">
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer Info Box */}
      {!collapsed && (
        <div className="p-4 border-t border-border bg-slate-50/50 m-3 rounded-card border">
          <div className="flex items-center space-x-2 text-xs font-semibold text-textPrimary mb-1">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span>Classic ML Core</span>
          </div>
          <p className="text-[11px] text-textMuted leading-relaxed">
            Gradient Boosting & Quantile models with P50/P90 error confidence bounds.
          </p>
        </div>
      )}
    </aside>
  );
};
