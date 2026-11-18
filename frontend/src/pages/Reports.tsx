import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useFilters } from '../context/FilterContext';
import type { ReportItem } from '../types';
import { FileSpreadsheet, Plus, Download, FileText, X } from 'lucide-react';
import { toast } from 'sonner';

export const Reports: React.FC = () => {
  const { routes } = useFilters();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [title, setTitle] = useState('Corridor Performance & Reliability Audit');
  const [format, setFormat] = useState<'pdf' | 'xlsx' | 'csv' | 'html'>('xlsx');
  const [selectedRoute, setSelectedRoute] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const loadReports = async () => {
    setIsLoading(true);
    try {
      const data = await api.getReports();
      setReports(data);
    } catch (e: any) {
      toast.error(e.message || 'Failed to load reports.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    try {
      await api.createReport({
        title,
        format,
        route_id: selectedRoute || undefined,
      });
      toast.success(`Report generated in ${format.toUpperCase()} format.`);
      setShowGenerateModal(false);
      loadReports();
    } catch (err: any) {
      toast.error(err.message || 'Report generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (r: any) => {
    const targetId = r.report_id || r.id;
    const url = api.getReportDownloadUrl(targetId);
    try {
      const res = await fetch(url);
      if (!res.ok) {
        toast.error(`Download failed: HTTP ${res.status}`);
        return;
      }
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      const ext = (r.file_format || r.format || 'csv').toLowerCase();
      const safeExt = ext === 'excel' ? 'xlsx' : ext;
      link.download = `${(r.title || 'report').replace(/[^a-zA-Z0-9_-]/g, '_')}_${targetId}.${safeExt}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      toast.success('Report downloaded successfully!');
    } catch (err: any) {
      window.open(url, '_blank');
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-black text-textPrimary tracking-tight">
            Corridor & Model Performance Reports
          </h1>
          <p className="text-xs text-textSecondary mt-1">
            Export comprehensive PDF, formatted Excel spreadsheets (.xlsx), and raw CSV audit data.
          </p>
        </div>

        <button
          onClick={() => setShowGenerateModal(true)}
          className="inline-flex items-center px-4 py-2 bg-primary hover:bg-primary-hover text-white text-xs font-semibold rounded-input shadow-xs transition-colors cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          Generate New Report
        </button>
      </div>

      {/* Reports Table */}
      <div className="bg-surface border border-border rounded-card p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-primary" />
            <h2 className="text-base font-bold text-textPrimary">Generated Report Archive</h2>
          </div>
          <span className="text-xs text-textMuted">{reports.length} Reports Ready</span>
        </div>

        <div className="overflow-x-auto border border-border rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-subtle text-textSecondary uppercase font-semibold border-b border-border">
              <tr>
                <th className="py-3 px-4">Report Title</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4">Created Date</th>
                <th className="py-3 px-4">File Size</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-medium text-textPrimary">
              {reports.length > 0 ? (
                reports.map((r) => (
                  <tr key={r.id} className="hover:bg-subtle/50 transition-colors">
                    <td className="py-3 px-4 font-bold text-textPrimary flex items-center">
                      <FileText className="w-4 h-4 mr-2 text-primary shrink-0" />
                      {r.title}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-800 border border-slate-200">
                        {r.file_format || r.format || 'CSV'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-textMuted tnum">
                      {r.created_at?.slice(0, 10)}
                    </td>
                    <td className="py-3 px-4 text-textSecondary tnum">
                      {r.file_size_kb ? `${r.file_size_kb} KB` : '18.4 KB'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Available
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleDownload(r)}
                        className="inline-flex items-center px-3 py-1 bg-subtle hover:bg-slate-200 border border-border text-textPrimary rounded-md text-xs font-semibold transition-colors cursor-pointer"
                      >
                        <Download className="w-3.5 h-3.5 mr-1 text-primary" />
                        Download
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-textMuted italic">
                    {isLoading ? 'Loading report index...' : 'No reports generated yet. Click "Generate New Report" to create one.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generate Report Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-textPrimary/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-md bg-surface border border-border rounded-card p-6 shadow-dropdown space-y-4 animate-in fade-in-50 zoom-in-95">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-textPrimary">Generate Transit Report</h3>
              <button
                onClick={() => setShowGenerateModal(false)}
                className="p-1 text-textMuted hover:text-textPrimary cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-textSecondary mb-1">Report Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full h-9 px-3 bg-subtle border border-border rounded-input text-textPrimary"
                />
              </div>

              <div>
                <label className="block font-semibold text-textSecondary mb-1">Target Format</label>
                <div className="grid grid-cols-4 gap-2">
                  {(['xlsx', 'pdf', 'csv', 'html'] as const).map((fmt) => (
                    <button
                      type="button"
                      key={fmt}
                      onClick={() => setFormat(fmt)}
                      className={`py-2 rounded-md font-bold uppercase transition-all cursor-pointer ${
                        format === fmt
                          ? 'bg-primary text-white shadow-xs'
                          : 'bg-subtle text-textSecondary border border-border hover:bg-slate-100'
                      }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block font-semibold text-textSecondary mb-1">Corridor Filter (Optional)</label>
                <select
                  value={selectedRoute}
                  onChange={(e) => setSelectedRoute(e.target.value)}
                  className="w-full h-9 px-3 bg-subtle border border-border rounded-input cursor-pointer"
                >
                  <option value="">All Transit Corridors</option>
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>
                      Route {r.route_no} - {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="px-3 py-1.5 text-textSecondary hover:bg-subtle rounded-input border border-border cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="px-4 py-1.5 font-semibold text-white bg-primary hover:bg-primary-hover rounded-input shadow-xs disabled:opacity-50 cursor-pointer"
                >
                  {isGenerating ? 'Compiling File...' : 'Generate File'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
