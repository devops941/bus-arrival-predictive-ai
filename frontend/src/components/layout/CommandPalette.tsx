import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Command } from 'cmdk';
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
  LogOut,
  Bus,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useFilters } from '../../context/FilterContext';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ open, onOpenChange }) => {
  const navigate = useNavigate();
  const { logout, role } = useAuth();
  const { routes, setSelectedRouteId } = useFilters();
  const [search, setSearch] = useState('');

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [open, onOpenChange]);

  const runCommand = (command: () => void) => {
    command();
    onOpenChange(false);
    setSearch('');
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-textPrimary/40 backdrop-blur-xs p-4">
      <div
        className="w-full max-w-xl bg-surface border border-border rounded-card shadow-dropdown overflow-hidden animate-in fade-in-50 zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        <Command
          value={search}
          onValueChange={setSearch}
          className="w-full"
        >
          <div className="flex items-center border-b border-border px-3.5">
            <Bus className="w-4 h-4 text-primary mr-2.5 shrink-0" />
            <Command.Input
              autoFocus
              placeholder="Type a command, route number, or page..."
              className="w-full h-12 text-sm bg-transparent outline-none placeholder:text-textMuted text-textPrimary"
            />
            <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-xs text-textMuted bg-subtle rounded border border-border">
              ESC
            </kbd>
          </div>

          <Command.List className="max-h-80 overflow-y-auto p-2 text-sm">
            <Command.Empty className="py-6 text-center text-sm text-textMuted">
              No matching pages or routes found.
            </Command.Empty>

            <Command.Group heading="Navigation" className="text-xs font-semibold text-textMuted px-2 py-1.5 uppercase tracking-wider">
              <Command.Item
                onSelect={() => runCommand(() => navigate('/dashboard'))}
                className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
              >
                <LayoutDashboard className="w-4 h-4 mr-2.5 text-primary" />
                Dashboard Overview
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => navigate('/eta'))}
                className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
              >
                <Navigation className="w-4 h-4 mr-2.5 text-prediction-chart" />
                ETA Arrival Predictor
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => navigate('/trends'))}
                className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
              >
                <LineChart className="w-4 h-4 mr-2.5 text-minor-chart" />
                Delay Trends & Heatmap
              </Command.Item>

              {role && role !== 'passenger' && (
                <>
                  <Command.Item
                    onSelect={() => runCommand(() => navigate('/data-entry'))}
                    className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                  >
                    <Database className="w-4 h-4 mr-2.5 text-emerald-600" />
                    Data Entry & CSV Import
                  </Command.Item>
                  <Command.Item
                    onSelect={() => runCommand(() => navigate('/features'))}
                    className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                  >
                    <SlidersHorizontal className="w-4 h-4 mr-2.5 text-sky-600" />
                    Feature Engineering
                  </Command.Item>
                  <Command.Item
                    onSelect={() => runCommand(() => navigate('/models'))}
                    className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                  >
                    <Cpu className="w-4 h-4 mr-2.5 text-indigo-600" />
                    Model Training & Registry
                  </Command.Item>
                  <Command.Item
                    onSelect={() => runCommand(() => navigate('/accuracy'))}
                    className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2.5 text-teal" />
                    Accuracy & Error Analysis
                  </Command.Item>
                  <Command.Item
                    onSelect={() => runCommand(() => navigate('/reports'))}
                    className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                  >
                    <FileSpreadsheet className="w-4 h-4 mr-2.5 text-orange-600" />
                    Generate & Download Reports
                  </Command.Item>
                </>
              )}

              <Command.Item
                onSelect={() => runCommand(() => navigate('/alerts'))}
                className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
              >
                <Bell className="w-4 h-4 mr-2.5 text-major-chart" />
                System Alerts & Drift Monitoring
              </Command.Item>

              {role === 'admin' && (
                <Command.Item
                  onSelect={() => runCommand(() => navigate('/admin'))}
                  className="flex items-center px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                >
                  <Settings className="w-4 h-4 mr-2.5 text-textSecondary" />
                  Admin & User Management
                </Command.Item>
              )}
            </Command.Group>

            {routes.length > 0 && (
              <Command.Group heading="Switch Transit Route" className="text-xs font-semibold text-textMuted px-2 py-1.5 uppercase tracking-wider mt-2">
                {routes.slice(0, 7).map((r) => (
                  <Command.Item
                    key={r.id}
                    onSelect={() => {
                      runCommand(() => {
                        setSelectedRouteId(r.id);
                        navigate('/dashboard');
                      });
                    }}
                    className="flex items-center justify-between px-3 py-2 text-textPrimary hover:bg-subtle rounded-md cursor-pointer transition-colors"
                  >
                    <div className="flex items-center">
                      <span className="w-7 h-5 rounded bg-primary-soft text-primary font-bold text-xs flex items-center justify-center mr-2.5">
                        {r.route_no}
                      </span>
                      <span className="text-sm font-medium">{r.name}</span>
                    </div>
                    <span className="text-xs text-textMuted">{r.stops_count} stops</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            <Command.Group heading="Account" className="text-xs font-semibold text-textMuted px-2 py-1.5 uppercase tracking-wider mt-2">
              <Command.Item
                onSelect={() => runCommand(() => logout())}
                className="flex items-center px-3 py-2 text-major-text hover:bg-red-50 rounded-md cursor-pointer transition-colors"
              >
                <LogOut className="w-4 h-4 mr-2.5 text-major-chart" />
                Sign Out
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
      <div
        className="fixed inset-0 -z-10"
        onClick={() => onOpenChange(false)}
      />
    </div>
  );
};
