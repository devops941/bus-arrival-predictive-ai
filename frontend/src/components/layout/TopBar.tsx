import React, { useState } from 'react';
import { Search, Bell, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useFilters } from '../../context/FilterContext';

interface TopBarProps {
  onOpenCommandPalette: () => void;
  unreadAlertsCount?: number;
}

export const TopBar: React.FC<TopBarProps> = ({ onOpenCommandPalette, unreadAlertsCount = 0 }) => {
  const { user, logout } = useAuth();
  const { routes, stops, selectedRouteId, setSelectedRouteId, selectedStopId, setSelectedStopId } = useFilters();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Filter stops based on selected route
  const activeRoute = routes.find((r) => r.id === selectedRouteId);
  const relevantStops = activeRoute
    ? stops.filter((s) => activeRoute.stops?.some((rs) => rs.stop_id === s.id))
    : stops;

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'admin':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">Admin</span>;
      case 'analyst':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">Analyst</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Passenger</span>;
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-surface border-b border-border flex items-center justify-between px-6 transition-all shadow-xs">
      {/* Route & Stop Dropdowns */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <label htmlFor="route-select" className="text-xs font-medium text-textSecondary uppercase tracking-wider hidden md:block">
            Route:
          </label>
          <select
            id="route-select"
            value={selectedRouteId}
            onChange={(e) => {
              setSelectedRouteId(e.target.value);
              setSelectedStopId('all');
            }}
            aria-label="Filter by Route"
            className="h-9 px-3 text-sm bg-subtle hover:bg-slate-100 border border-border rounded-input text-textPrimary font-medium focus:ring-2 focus:ring-primary focus:outline-none transition-colors cursor-pointer"
          >
            <option value="all">All Transit Routes</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                Route {r.route_no} - {r.name}
              </option>
            ))}
          </select>
        </div>

        {selectedRouteId !== 'all' && (
          <div className="flex items-center space-x-2">
            <label htmlFor="stop-select" className="text-xs font-medium text-textSecondary uppercase tracking-wider hidden md:block">
              Stop:
            </label>
            <select
              id="stop-select"
              value={selectedStopId}
              onChange={(e) => setSelectedStopId(e.target.value)}
              aria-label="Filter by Stop"
              className="h-9 px-3 text-sm bg-subtle hover:bg-slate-100 border border-border rounded-input text-textPrimary font-medium focus:ring-2 focus:ring-primary focus:outline-none transition-colors cursor-pointer max-w-[200px] truncate"
            >
              <option value="all">All Stops Along Route</option>
              {relevantStops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.stop_code} - {s.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right Tools: Search Command Palette, Notifications, Profile */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center h-9 px-3 text-sm text-textMuted bg-subtle hover:bg-slate-100 border border-border rounded-input transition-colors group cursor-pointer"
          title="Open search & quick actions (Ctrl+K)"
        >
          <Search className="w-4 h-4 mr-2 text-textMuted group-hover:text-primary transition-colors" />
          <span className="hidden sm:inline">Search & Actions...</span>
          <kbd className="ml-3 hidden sm:inline-flex items-center px-1.5 py-0.5 text-[11px] font-semibold text-textSecondary bg-surface border border-border rounded shadow-xs">
            Ctrl+K
          </kbd>
        </button>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={onOpenCommandPalette}
            className="p-2 text-textSecondary hover:text-primary hover:bg-subtle rounded-input border border-transparent hover:border-border transition-colors relative"
            title="System notifications & alerts"
          >
            <Bell className="w-5 h-5" />
            {unreadAlertsCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-major-chart rounded-full ring-2 ring-surface" />
            )}
          </button>
        </div>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center space-x-2.5 pl-2 pr-3 py-1.5 rounded-input hover:bg-subtle border border-transparent hover:border-border transition-colors cursor-pointer"
          >
            <div className="w-8 h-8 rounded-full bg-primary-soft text-primary font-bold flex items-center justify-center text-sm">
              {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
            </div>
            <div className="hidden md:flex flex-col text-left">
              <span className="text-xs font-semibold text-textPrimary leading-tight">
                {user?.full_name || user?.email}
              </span>
              <span className="text-[11px] text-textMuted capitalize">
                {user?.role || 'User'}
              </span>
            </div>
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-surface border border-border rounded-card shadow-dropdown py-1 z-50 animate-in fade-in-50 zoom-in-95">
              <div className="px-4 py-2.5 border-b border-border">
                <p className="text-xs font-semibold text-textPrimary">{user?.full_name}</p>
                <p className="text-xs text-textMuted truncate">{user?.email}</p>
                <div className="mt-2">{getRoleBadge(user?.role)}</div>
              </div>
              <div className="py-1">
                <div className="px-4 py-2 text-xs text-textSecondary flex items-center">
                  <Shield className="w-3.5 h-3.5 mr-2 text-primary" />
                  <span>Authenticated Session</span>
                </div>
                <button
                  onClick={() => {
                    setUserMenuOpen(false);
                    logout();
                  }}
                  className="w-full text-left px-4 py-2 text-xs text-major-text hover:bg-red-50 flex items-center transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5 mr-2 text-major-chart" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
