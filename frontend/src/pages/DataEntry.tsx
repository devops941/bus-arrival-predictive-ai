import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { Route, Stop, Trip, Observation, DelayEvent, ImportValidationReport } from '../types';
import {
  Database,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Upload,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  Search,
  RefreshCw,
  Bus,
  MapPin,
  Clock,
  Download,
} from 'lucide-react';
import { toast } from 'sonner';

export const DataEntry: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'routes' | 'stops' | 'trips' | 'observations' | 'events' | 'import'>('routes');
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [delayEvents, setDelayEvents] = useState<DelayEvent[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Quick Add Modal States
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRoute, setNewRoute] = useState({ route_no: '', name: '', origin: '', destination: '', total_distance_km: 12.0 });
  const [newStop, setNewStop] = useState({ stop_code: '', name: '', latitude: 9.9252, longitude: 78.1198 });

  // Inline Edit Row State
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<any>({});

  // Import Wizard States
  const [importKind, setImportKind] = useState<'routes' | 'stops' | 'observations'>('routes');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importReport, setImportReport] = useState<ImportValidationReport | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importValidOnly, setImportValidOnly] = useState(true);

  // Load all datasets so tab count badges immediately show real database numbers
  const loadAllDatasets = async () => {
    setIsLoading(true);
    try {
      const [rData, sData, tData, oData, eData] = await Promise.all([
        api.getRoutes().catch(() => []),
        api.getStops().catch(() => []),
        api.getTrips().catch(() => []),
        api.getObservations(150).catch(() => []),
        api.getDelayEvents().catch(() => []),
      ]);
      setRoutes(rData);
      setStops(sData);
      setTrips(tData);
      setObservations(oData);
      setDelayEvents(eData);
    } catch (e: any) {
      toast.error(e.message || 'Failed to load transit datasets.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllDatasets();
  }, []);

  // Handle Quick Add
  const handleQuickAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (activeTab === 'routes') {
        await api.createRoute({
          ...newRoute,
          stops_count: 5,
          stops: [],
          status: 'active',
        });
        toast.success(`Route ${newRoute.route_no} created.`);
        setNewRoute({ route_no: '', name: '', origin: '', destination: '', total_distance_km: 12.0 });
      } else if (activeTab === 'stops') {
        await api.createStop({
          stop_code: newStop.stop_code,
          name: newStop.name,
          lat: newStop.latitude,
          lon: newStop.longitude,
          is_active: true,
        });
        toast.success(`Stop ${newStop.stop_code} added.`);
        setNewStop({ stop_code: '', name: '', latitude: 9.9252, longitude: 78.1198 });
      }
      setShowAddModal(false);
      loadAllDatasets();
    } catch (err: any) {
      toast.error(err.message || 'Failed to create record.');
    }
  };

  // Handle Delete
  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this record?')) return;
    try {
      if (activeTab === 'routes') await api.deleteRoute(id);
      if (activeTab === 'stops') await api.deleteStop(id);
      if (activeTab === 'observations') await api.deleteObservation(id);
      toast.success('Record deleted.');
      loadAllDatasets();
    } catch (e: any) {
      toast.error(e.message || 'Delete operation failed.');
    }
  };

  // Handle Inline Edit Save
  const handleSaveInline = async (id: string) => {
    try {
      if (activeTab === 'routes') {
        await api.updateRoute(id, editFormData);
      } else if (activeTab === 'stops') {
        await api.updateStop(id, editFormData);
      }
      toast.success('Record updated successfully.');
      setEditingId(null);
      loadAllDatasets();
    } catch (e: any) {
      toast.error(e.message || 'Update failed.');
    }
  };

  // Handle Import Validate & Commit
  const handleImportSubmit = async (commitAction: boolean) => {
    if (!selectedFile) {
      toast.error('Please choose a CSV or TXT file first.');
      return;
    }
    setIsImporting(true);
    try {
      const report = await api.importDataset(importKind, selectedFile, commitAction, importValidOnly);
      setImportReport(report);
      if (commitAction) {
        toast.success(`Successfully committed ${report.valid_count} valid records into database!`);
        loadAllDatasets();
      } else {
        toast.info(`Dry-run validation complete: ${report.valid_count} valid, ${report.invalid_count} flagged issues.`);
      }
    } catch (e: any) {
      toast.error(e.message || 'Import error.');
    } finally {
      setIsImporting(false);
    }
  };

  // Quick download sample CSV for testing wizard
  const downloadSampleCsv = (type: 'routes' | 'stops' | 'observations') => {
    let content = '';
    let filename = '';
    if (type === 'routes') {
      filename = 'sample_madurai_routes.csv';
      content = 'route_no,name,origin,destination,total_distance_km,scheduled_headway_min,active\n' +
        '77A,Periyar to Othakadai High Court,Periyar Bus Stand,Othakadai High Court Bench,15.8,10,true\n' +
        '88,Periyar to Madurai Airport,Periyar Bus Stand,Madurai International Airport,14.2,15,true\n' +
        '48P,Periyar to Samayanallur,Periyar Bus Stand,Samayanallur,13.6,12,true\n' +
        '700,Mattuthavani to Thiruparankundram,Mattuthavani MGR Bus Stand,Thiruparankundram Temple,15.5,15,true\n';
    } else if (type === 'stops') {
      filename = 'sample_madurai_stops.csv';
      content = 'stop_code,name,lat,lon\n' +
        'MDU-001,Periyar Bus Stand,9.9174,78.1132\n' +
        'MDU-002,Simmakkal,9.9255,78.1210\n' +
        'MDU-003,Goripalayam Junction,9.9328,78.1315\n' +
        'MDU-004,Thallakulam,9.9380,78.1382\n' +
        'MDU-005,K.Pudur,9.9452,78.1470\n' +
        'MDU-006,Mattuthavani MGR Bus Stand,9.9498,78.1638\n' +
        'MDU-015,Madurai International Airport,9.8345,78.0934\n';
    } else {
      filename = 'sample_madurai_observations.csv';
      content = 'trip_id,route_no,stop_code,scheduled_arrival,actual_arrival,delay_min,precipitation_mm,passenger_load_pct\n' +
        'TRIP-MDU-88-101,88,MDU-001,2026-11-18 15:30:00,2026-11-18 15:30:30,0.5,0.0,65\n' +
        'TRIP-MDU-88-101,88,MDU-010,2026-11-18 15:38:00,2026-11-18 15:39:15,1.2,0.0,75\n' +
        'TRIP-MDU-88-101,88,MDU-012,2026-11-18 15:52:00,2026-11-18 15:54:30,2.5,0.0,80\n' +
        'TRIP-MDU-88-101,88,MDU-015,2026-11-18 16:10:00,2026-11-18 16:14:00,4.0,0.0,55\n';
    }

    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success(`Downloaded ${filename} template`);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-black text-textPrimary tracking-tight">
            Data Entry & Transit Management
          </h1>
          <p className="text-xs text-textSecondary mt-1">
            CRUD operations, inline-editable tables, and CSV/GTFS ingestion with row-level validation.
          </p>
        </div>

        {activeTab !== 'import' && (
          <div className="flex items-center space-x-2">
            {(activeTab === 'routes' || activeTab === 'stops') && (
              <button
                onClick={() => setShowAddModal(true)}
                className="px-3.5 py-2 bg-primary hover:bg-primary-hover text-white rounded-input text-xs font-semibold flex items-center transition-colors shadow-xs cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                Quick Add Row
              </button>
            )}
            <button
              onClick={loadAllDatasets}
              className="p-2 text-textSecondary hover:bg-subtle rounded-input border border-border transition-colors cursor-pointer"
              title="Refresh all datasets"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        )}
      </div>

      {/* Dataset Tabs */}
      <div className="flex items-center space-x-1 border-b border-border overflow-x-auto pb-1 text-xs font-semibold">
        {[
          { key: 'routes', label: 'Routes', icon: Bus, count: routes.length },
          { key: 'stops', label: 'Stops', icon: MapPin, count: stops.length },
          { key: 'trips', label: 'Trips', icon: Clock, count: trips.length },
          { key: 'observations', label: 'Observations', icon: Database, count: observations.length },
          { key: 'events', label: 'Delay Events', icon: AlertTriangle, count: delayEvents.length },
          { key: 'import', label: 'CSV / GTFS Import Wizard', icon: Upload, count: null },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key as any);
                setSearch('');
                setEditingId(null);
              }}
              className={`flex items-center px-3.5 py-2 rounded-t-lg transition-all border-b-2 cursor-pointer ${
                isActive
                  ? 'border-primary text-primary bg-primary-soft/30'
                  : 'border-transparent text-textSecondary hover:text-textPrimary hover:bg-subtle'
              }`}
            >
              <Icon className="w-3.5 h-3.5 mr-1.5 shrink-0" />
              <span>{tab.label}</span>
              {tab.count !== null ? (
                <span className="ml-1.5 px-2 py-0.5 rounded-full bg-slate-200 text-[10px] font-bold text-textPrimary">
                  {tab.count}
                </span>
              ) : (
                <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-primary/10 text-[9px] font-bold text-primary">
                  Ingest
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content: Regular Data Tables */}
      {activeTab !== 'import' && (
        <div className="bg-surface border border-border rounded-card p-5 shadow-card space-y-4">
          {/* Table Search & Tools */}
          <div className="flex items-center justify-between gap-4">
            <div className="relative w-72">
              <input
                type="text"
                placeholder="Search rows..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full h-9 pl-8 pr-3 text-xs bg-subtle border border-border rounded-input text-textPrimary placeholder:text-textMuted focus:ring-1 focus:ring-primary focus:outline-none"
              />
              <Search className="w-3.5 h-3.5 text-textMuted absolute left-2.5 top-3 pointer-events-none" />
            </div>

            <div className="text-xs text-textMuted">
              Click <Edit2 className="w-3 h-3 inline mx-1" /> to inline edit any field
            </div>
          </div>

          {/* Routes Table */}
          {activeTab === 'routes' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Route #</th>
                    <th className="py-2.5 px-3">Name</th>
                    <th className="py-2.5 px-3">Origin</th>
                    <th className="py-2.5 px-3">Destination</th>
                    <th className="py-2.5 px-3">Distance (km)</th>
                    <th className="py-2.5 px-3">Stops</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium text-textPrimary">
                  {routes
                    .filter((r) => r.name.toLowerCase().includes(search.toLowerCase()) || r.route_no.includes(search))
                    .map((r) => {
                      const isEditing = editingId === r.id;
                      return (
                        <tr key={r.id} className="hover:bg-subtle/50 transition-colors">
                          <td className="py-2.5 px-3 font-mono font-bold text-primary">{r.route_no}</td>
                          <td className="py-2.5 px-3 font-semibold">
                            {isEditing ? (
                              <input
                                type="text"
                                value={editFormData.name ?? r.name}
                                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                                className="h-7 px-2 border rounded text-xs bg-white w-full"
                              />
                            ) : (
                              r.name
                            )}
                          </td>
                          <td className="py-2.5 px-3">
                            {isEditing ? (
                              <input
                                type="text"
                                value={editFormData.origin ?? r.origin}
                                onChange={(e) => setEditFormData({ ...editFormData, origin: e.target.value })}
                                className="h-7 px-2 border rounded text-xs bg-white w-full"
                              />
                            ) : (
                              r.origin
                            )}
                          </td>
                          <td className="py-2.5 px-3">
                            {isEditing ? (
                              <input
                                type="text"
                                value={editFormData.destination ?? r.destination}
                                onChange={(e) => setEditFormData({ ...editFormData, destination: e.target.value })}
                                className="h-7 px-2 border rounded text-xs bg-white w-full"
                              />
                            ) : (
                              r.destination
                            )}
                          </td>
                          <td className="py-2.5 px-3 tnum font-semibold">{r.total_distance_km} km</td>
                          <td className="py-2.5 px-3 text-textMuted">{r.stops_count || r.stops?.length || 0} stops</td>
                          <td className="py-2.5 px-3 text-right space-x-1.5">
                            {isEditing ? (
                              <>
                                <button
                                  onClick={() => handleSaveInline(r.id)}
                                  className="p-1 text-ontime-text hover:bg-green-50 rounded"
                                >
                                  <Check className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => setEditingId(null)}
                                  className="p-1 text-textMuted hover:bg-slate-100 rounded"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => {
                                    setEditingId(r.id);
                                    setEditFormData({ name: r.name, origin: r.origin, destination: r.destination });
                                  }}
                                  className="p-1 text-textSecondary hover:text-primary hover:bg-subtle rounded"
                                  title="Edit"
                                >
                                  <Edit2 className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => handleDelete(r.id)}
                                  className="p-1 text-major-chart hover:bg-red-50 rounded"
                                  title="Delete"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}

          {/* Stops Table */}
          {activeTab === 'stops' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Code</th>
                    <th className="py-2.5 px-3">Stop Name</th>
                    <th className="py-2.5 px-3">Coordinates (Lat, Lon)</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium text-textPrimary">
                  {stops
                    .filter((s) => s.name.toLowerCase().includes(search.toLowerCase()) || s.stop_code.includes(search))
                    .map((s) => {
                      const isEditing = editingId === s.id;
                      const lat = Number(s.lat ?? s.latitude ?? 0);
                      const lon = Number(s.lon ?? s.longitude ?? 0);
                      return (
                        <tr key={s.id} className="hover:bg-subtle/50 transition-colors">
                          <td className="py-2.5 px-3 font-mono font-bold text-primary">{s.stop_code}</td>
                          <td className="py-2.5 px-3 font-semibold">
                            {isEditing ? (
                              <input
                                type="text"
                                value={editFormData.name ?? s.name}
                                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                                className="h-7 px-2 border rounded text-xs bg-white w-full"
                              />
                            ) : (
                              s.name
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-textMuted tnum font-mono">
                            {lat.toFixed(4)}, {lon.toFixed(4)}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Active
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-right space-x-1.5">
                            {isEditing ? (
                              <>
                                <button
                                  onClick={() => handleSaveInline(s.id)}
                                  className="p-1 text-ontime-text hover:bg-green-50 rounded"
                                >
                                  <Check className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => setEditingId(null)}
                                  className="p-1 text-textMuted hover:bg-slate-100 rounded"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => {
                                    setEditingId(s.id);
                                    setEditFormData({ name: s.name });
                                  }}
                                  className="p-1 text-textSecondary hover:text-primary hover:bg-subtle rounded"
                                >
                                  <Edit2 className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => handleDelete(s.id)}
                                  className="p-1 text-major-chart hover:bg-red-50 rounded"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}

          {/* Observations Table */}
          {activeTab === 'observations' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Trip ID</th>
                    <th className="py-2.5 px-3">Route</th>
                    <th className="py-2.5 px-3">Stop Code</th>
                    <th className="py-2.5 px-3">Scheduled Arrival</th>
                    <th className="py-2.5 px-3">Actual Arrival</th>
                    <th className="py-2.5 px-3">Delay</th>
                    <th className="py-2.5 px-3">Conditions</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium text-textPrimary">
                  {observations.slice(0, 100).map((o) => {
                    const delay = Number(o.delay_min ?? 0);
                    const schedStr = String(o.scheduled_arrival || '');
                    const actualStr = String(o.actual_arrival || '');
                    return (
                      <tr key={o.id} className="hover:bg-subtle/50 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-[11px] text-textSecondary">{o.trip_id}</td>
                        <td className="py-2.5 px-3 font-bold text-primary">{o.route_no || o.route_id || '--'}</td>
                        <td className="py-2.5 px-3 font-semibold">{o.stop_code || o.stop_id}</td>
                        <td className="py-2.5 px-3 text-textMuted tnum">{schedStr.replace('T', ' ').slice(0, 19)}</td>
                        <td className="py-2.5 px-3 text-textPrimary tnum font-semibold">{actualStr.replace('T', ' ').slice(0, 19)}</td>
                        <td className="py-2.5 px-3 tnum">
                          <span
                            className={`px-2 py-0.5 rounded font-bold text-[11px] ${
                              delay > 2 ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {delay >= 0 ? `+${delay.toFixed(1)}m` : `${delay.toFixed(1)}m`}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-textSecondary">
                          {o.precipitation_mm && o.precipitation_mm > 0 ? (
                            <span className="text-sky-700 font-semibold">🌧 Rain</span>
                          ) : (
                            <span className="text-textMuted">Dry / Normal</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleDelete(o.id)}
                            className="p-1 text-major-chart hover:bg-red-50 rounded"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Trips Table */}
          {activeTab === 'trips' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Trip Identifier</th>
                    <th className="py-2.5 px-3">Route</th>
                    <th className="py-2.5 px-3">Direction</th>
                    <th className="py-2.5 px-3">Day Type</th>
                    <th className="py-2.5 px-3">Scheduled Start</th>
                    <th className="py-2.5 px-3">Vehicle ID</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium text-textPrimary">
                  {trips.slice(0, 100).map((t) => {
                    const startStr = String(t.scheduled_start || '');
                    return (
                      <tr key={t.id} className="hover:bg-subtle/50 transition-colors">
                        <td className="py-2.5 px-3 font-mono font-bold text-primary">{t.trip_id || t.trip_number || t.id}</td>
                        <td className="py-2.5 px-3 font-bold">{t.route_no || t.route_id}</td>
                        <td className="py-2.5 px-3 uppercase text-[10px] font-semibold">{t.direction || 'outbound'}</td>
                        <td className="py-2.5 px-3 capitalize">{t.day_type || 'weekday'}</td>
                        <td className="py-2.5 px-3 tnum">{startStr.replace('T', ' ').slice(0, 19)}</td>
                        <td className="py-2.5 px-3 font-mono text-textMuted">{t.vehicle_id || '--'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Events Table */}
          {activeTab === 'events' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Delay Cause / Incident</th>
                    <th className="py-2.5 px-3">Route #</th>
                    <th className="py-2.5 px-3">Date & Time</th>
                    <th className="py-2.5 px-3">Delay Impact</th>
                    <th className="py-2.5 px-3">Severity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium text-textPrimary">
                  {delayEvents.length > 0 ? (
                    delayEvents.map((e) => (
                      <tr key={e.id} className="hover:bg-subtle/50 transition-colors">
                        <td className="py-2.5 px-3 font-bold capitalize text-primary">{e.cause || e.incident_type || 'Incident'}</td>
                        <td className="py-2.5 px-3 font-semibold">{e.route_no || e.route_id || 'All'}</td>
                        <td className="py-2.5 px-3 tnum">{e.date ? `${e.date} ${e.time || ''}` : (e.start_time || '--')}</td>
                        <td className="py-2.5 px-3 tnum font-bold text-amber-800">+{e.minutes ?? e.impact_minutes ?? 0} min</td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-50 text-amber-700 border border-amber-200">
                            {e.severity || 'Moderate'}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-textMuted italic">
                        No active incident delay events reported.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab Content: CSV / GTFS Import Wizard */}
      {activeTab === 'import' && (
        <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-6">
          <div className="border-b border-border pb-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-textPrimary flex items-center">
                <FileSpreadsheet className="w-5 h-5 mr-2 text-primary" />
                CSV & GTFS Static Transit Import Wizard
              </h2>
              <p className="text-xs text-textSecondary mt-1">
                Upload raw transit files (e.g. routes.csv, stops.csv, observations.csv).
                Our ingestion engine parses rows, identifies missing/duplicate entries, and highlights messy rows with validation diagnostics.
              </p>
            </div>

            {/* Quick Sample Downloads */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-textMuted">Sample Templates:</span>
              <button
                type="button"
                onClick={() => downloadSampleCsv('routes')}
                className="px-2.5 py-1.5 bg-subtle hover:bg-slate-200 text-textPrimary rounded-md border border-border text-[11px] font-semibold flex items-center cursor-pointer transition-colors"
              >
                <Download className="w-3 h-3 mr-1" /> Routes
              </button>
              <button
                type="button"
                onClick={() => downloadSampleCsv('stops')}
                className="px-2.5 py-1.5 bg-subtle hover:bg-slate-200 text-textPrimary rounded-md border border-border text-[11px] font-semibold flex items-center cursor-pointer transition-colors"
              >
                <Download className="w-3 h-3 mr-1" /> Stops
              </button>
              <button
                type="button"
                onClick={() => downloadSampleCsv('observations')}
                className="px-2.5 py-1.5 bg-subtle hover:bg-slate-200 text-textPrimary rounded-md border border-border text-[11px] font-semibold flex items-center cursor-pointer transition-colors"
              >
                <Download className="w-3 h-3 mr-1" /> Observations
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Step 1: Select Type & Upload File */}
            <div className="space-y-4 md:col-span-1 border-r border-border pr-6">
              <span className="text-xs font-bold text-textMuted uppercase tracking-wider">
                Step 1: Dataset & File Selection
              </span>

              <div>
                <label className="block text-xs font-semibold text-textSecondary mb-1.5">
                  Target Dataset Kind
                </label>
                <select
                  value={importKind}
                  onChange={(e) => setImportKind(e.target.value as any)}
                  className="w-full h-10 px-3 text-xs bg-subtle border border-border rounded-input text-textPrimary font-semibold cursor-pointer"
                >
                  <option value="routes">Routes (routes.csv / routes.txt)</option>
                  <option value="stops">Stops (stops.csv / stops.txt)</option>
                  <option value="observations">Observations (observed_delays.csv)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-textSecondary mb-1.5">
                  Select CSV or TXT File
                </label>
                <input
                  type="file"
                  accept=".csv,.txt"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-textSecondary file:mr-3 file:py-2 file:px-3 file:rounded-md file:border file:border-border file:text-xs file:font-semibold file:bg-subtle hover:file:bg-slate-100 cursor-pointer"
                />
                {selectedFile && (
                  <p className="text-[11px] text-primary font-semibold mt-1">
                    Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </p>
                )}
              </div>

              <div className="pt-1">
                <label className="flex items-center space-x-2 cursor-pointer text-xs font-medium text-textSecondary">
                  <input
                    type="checkbox"
                    checked={importValidOnly}
                    onChange={(e) => setImportValidOnly(e.target.checked)}
                    className="w-3.5 h-3.5 text-primary rounded"
                  />
                  <span>Import valid rows only (isolate messy rows)</span>
                </label>
              </div>

              <div className="pt-2 flex flex-col space-y-2">
                <button
                  type="button"
                  disabled={!selectedFile || isImporting}
                  onClick={() => handleImportSubmit(false)}
                  className="w-full h-10 bg-subtle hover:bg-slate-200 border border-border text-textPrimary rounded-input text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {isImporting ? 'Validating...' : 'Validate File Only (Dry-Run)'}
                </button>
                <button
                  type="button"
                  disabled={!selectedFile || isImporting}
                  onClick={() => handleImportSubmit(true)}
                  className="w-full h-10 bg-primary hover:bg-primary-hover text-white rounded-input text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {isImporting ? 'Committing...' : 'Validate & Commit into Database'}
                </button>
              </div>
            </div>

            {/* Step 2 & 3: Validation Report & Issue Table */}
            <div className="md:col-span-2 space-y-4">
              <span className="text-xs font-bold text-textMuted uppercase tracking-wider">
                Step 2: Row-Level Validation & Ingestion Report
              </span>

              {importReport ? (
                <div className="space-y-4">
                  {/* Summary Bar */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-subtle border border-border text-center">
                      <span className="text-[11px] text-textMuted uppercase font-medium">Total Rows</span>
                      <div className="text-lg font-bold text-textPrimary tnum">{importReport.total_rows}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-green-50 border border-green-200 text-center">
                      <span className="text-[11px] text-green-700 uppercase font-medium">Valid Rows</span>
                      <div className="text-lg font-bold text-ontime-text tnum">{importReport.valid_count}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-center">
                      <span className="text-[11px] text-red-700 uppercase font-medium">Flagged Issues</span>
                      <div className="text-lg font-bold text-major-text tnum">{importReport.invalid_count}</div>
                    </div>
                  </div>

                  {/* Issues Table */}
                  <div className="border border-border rounded-lg overflow-hidden">
                    <div className="bg-subtle px-3 py-2 border-b border-border flex items-center justify-between text-xs font-bold text-textPrimary">
                      <span>Row Issues & Outlier Report ({importReport.issues.length})</span>
                      <span className="text-textMuted font-normal text-[11px]">
                        {importReport.committed ? 'Database state: COMMITTED' : 'Database state: UNCOMMITTED'}
                      </span>
                    </div>

                    <div className="max-h-64 overflow-y-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-textSecondary uppercase font-semibold border-b border-border">
                          <tr>
                            <th className="py-2 px-3">Row #</th>
                            <th className="py-2 px-3">Field</th>
                            <th className="py-2 px-3">Type</th>
                            <th className="py-2 px-3">Diagnostic Message</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border text-textPrimary">
                          {importReport.issues.length > 0 ? (
                            importReport.issues.map((iss, idx) => (
                              <tr key={idx} className="hover:bg-subtle/50">
                                <td className="py-2 px-3 font-mono font-bold">{iss.row}</td>
                                <td className="py-2 px-3 font-semibold text-primary">{iss.field}</td>
                                <td className="py-2 px-3">
                                  <span
                                    className={`px-1.5 py-0.2 rounded text-[10px] font-bold uppercase ${
                                      iss.is_fatal ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                                    }`}
                                  >
                                    {iss.issue_type}
                                  </span>
                                </td>
                                <td className="py-2 px-3 text-textSecondary">{iss.message}</td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={4} className="py-6 text-center text-xs text-ontime-text font-semibold">
                                <CheckCircle2 className="w-5 h-5 mx-auto mb-1 text-ontime-chart" />
                                All rows passed schema validation rules!
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center border border-dashed border-border rounded-lg text-center p-6 text-xs text-textMuted space-y-2">
                  <Upload className="w-8 h-8 text-textMuted" />
                  <p className="font-semibold text-textPrimary">No Import Validation Run Yet</p>
                  <p className="max-w-xs">
                    Choose a file or click one of the sample template buttons above, then click "Validate File" to preview detected duplicates and schema diagnostics.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-textPrimary/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md bg-surface border border-border rounded-card p-6 shadow-dropdown space-y-4 animate-in fade-in-50 zoom-in-95">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary capitalize">Quick Add {activeTab}</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 text-textMuted hover:text-textPrimary cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleQuickAdd} className="space-y-3">
              {activeTab === 'routes' && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-textSecondary mb-1">Route #</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 77A"
                      value={newRoute.route_no}
                      onChange={(e) => setNewRoute({ ...newRoute, route_no: e.target.value })}
                      className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-textSecondary mb-1">Route Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Periyar to Othakadai"
                      value={newRoute.name}
                      onChange={(e) => setNewRoute({ ...newRoute, name: e.target.value })}
                      className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-textSecondary mb-1">Origin</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Periyar Bus Stand"
                        value={newRoute.origin}
                        onChange={(e) => setNewRoute({ ...newRoute, origin: e.target.value })}
                        className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-textSecondary mb-1">Destination</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Othakadai"
                        value={newRoute.destination}
                        onChange={(e) => setNewRoute({ ...newRoute, destination: e.target.value })}
                        className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                      />
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'stops' && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-textSecondary mb-1">Stop Code</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. MDU-050"
                      value={newStop.stop_code}
                      onChange={(e) => setNewStop({ ...newStop, stop_code: e.target.value })}
                      className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-textSecondary mb-1">Stop Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Meenakshi Amman Temple"
                      value={newStop.name}
                      onChange={(e) => setNewStop({ ...newStop, name: e.target.value })}
                      className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-semibold text-textSecondary mb-1">Latitude</label>
                      <input
                        type="number"
                        step="0.0001"
                        required
                        value={newStop.latitude}
                        onChange={(e) => setNewStop({ ...newStop, latitude: parseFloat(e.target.value) })}
                        className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-textSecondary mb-1">Longitude</label>
                      <input
                        type="number"
                        step="0.0001"
                        required
                        value={newStop.longitude}
                        onChange={(e) => setNewStop({ ...newStop, longitude: parseFloat(e.target.value) })}
                        className="w-full h-9 px-3 text-xs bg-subtle border border-border rounded-input"
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 text-xs text-textSecondary hover:bg-subtle rounded-input border border-border cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-primary hover:bg-primary-hover rounded-input shadow-xs cursor-pointer"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
