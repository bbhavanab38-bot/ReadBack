import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  ShieldCheck, 
  ShieldAlert, 
  AlertCircle, 
  TrendingUp, 
  ArrowRight, 
  Clock, 
  Upload, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Accessibility,
  RefreshCw,
  Trash2
} from 'lucide-react';
import { DocumentSummary, DashboardMetrics } from '../types';
import { api } from '../services/api';

interface DashboardViewProps {
  onSelectDocument: (documentId: string) => void;
  onStartAnalysis: () => void;
  onLoadDemo: (demoType: string) => void;
  onOpenFidelityLab: () => void;
  onTryElderMode: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onSelectDocument,
  onStartAnalysis,
  onLoadDemo,
  onOpenFidelityLab,
  onTryElderMode,
}) => {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docsData, metricsData] = await Promise.all([
        api.getDocuments(),
        api.getMetrics(),
      ]);
      setDocuments(docsData);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this document and all associated extracted data?')) return;
    setDeletingId(id);
    try {
      await api.deleteDocument(id);
      await loadData();
    } catch (err) {
      alert('Delete failed');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Human-centered overview */}
      <section className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="grid lg:grid-cols-12">
          <div className="flex flex-col justify-center p-6 sm:p-9 lg:col-span-6">
            <p className="text-xs font-bold uppercase text-sky-200">Medical information, easier to access</p>
            <h1 className="mt-3 text-3xl font-extrabold leading-tight text-white sm:text-4xl">
              Understand your medical documents.<br />
              <span className="text-sky-300">Verify what AI says.</span><br />
              Hear it in your language.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-300">
              Built to make medical information easier to understand — especially when reading a medical report feels difficult.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={onStartAnalysis} className="inline-flex min-h-12 items-center gap-2 rounded-xl bg-sky-400 px-5 font-bold text-slate-950 hover:bg-sky-300">
                <Upload className="h-5 w-5" /> Analyze a Document
              </button>
              <button type="button" onClick={onTryElderMode} className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-sky-300/40 bg-sky-300/10 px-5 font-bold text-sky-100 hover:bg-sky-300/20">
                <Accessibility className="h-5 w-5" /> Try Elder Mode
              </button>
            </div>
          </div>
          <div className="relative min-h-[25rem] bg-slate-800 lg:col-span-6">
            <img
              src="https://images.unsplash.com/photo-1782906187500-b57299d96aa8?q=80&w=1547&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
              alt="Older adult reviewing a printed document at home"
              className="absolute inset-0 h-full w-full object-cover object-center"
            />
            <div className="absolute inset-x-0 bottom-0 grid gap-3 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent p-5 pt-16 sm:grid-cols-2 sm:p-6 sm:pt-20">
              <div className="rounded-xl border border-white/15 bg-slate-950/85 p-4 backdrop-blur-sm">
                <p className="text-xs font-bold uppercase text-slate-300">Before</p>
                <p className="mt-1 text-sm font-semibold text-white">A dense report. Values, units and flags are hard to find.</p>
              </div>
              <div className="rounded-xl border border-emerald-300/35 bg-slate-950/90 p-4 backdrop-blur-sm">
                <p className="text-xs font-bold uppercase text-emerald-100">After · verified</p>
                <p className="mt-1 text-sm font-semibold text-white">Key facts checked against the source, ready to read or hear.</p>
                <p className="mt-2 text-xs font-semibold text-sky-100">Simple · Verified · Spoken locally</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Row (Prompt Section 10) */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 sm:gap-4">
        {/* Documents Analyzed */}
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Documents Analyzed</span>
            <FileText className="w-4 h-4 text-brand-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-extrabold text-white">
              {metrics?.documents_analyzed ?? 0}
            </span>
          </div>
        </div>

        {/* Verified Explanations */}
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Verified Explanations</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
              {metrics?.verified_explanations ?? 0}
            </span>
          </div>
        </div>

        {/* Blocked Explanations */}
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Blocked Explanations</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-extrabold text-rose-400">
              {metrics?.blocked_explanations ?? 0}
            </span>
          </div>
        </div>

        {/* Needs Review */}
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Needs Review</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-extrabold text-amber-400">
              {metrics?.needs_review ?? 0}
            </span>
          </div>
        </div>

        {/* Average Document Fidelity */}
        <div className="col-span-2 md:col-span-1 bg-slate-800/50 border border-slate-700/60 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Average Fidelity</span>
            <TrendingUp className="w-4 h-4 text-brand-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-1">
            <span className="text-2xl sm:text-3xl font-extrabold text-white">
              {metrics?.average_document_fidelity ?? 0}%
            </span>
          </div>
        </div>
      </div>

      <section className="flex flex-col gap-4 rounded-2xl border border-sky-300/20 bg-slate-800/80 p-5 shadow-inner sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="rounded-xl bg-sky-300/10 p-2.5 text-sky-200"><ShieldCheck className="h-5 w-5" aria-hidden="true" /></span>
          <div>
            <h2 className="font-bold text-white">AI explanation fidelity</h2>
            <p className="mt-1 text-sm text-slate-300">ReadBack verifies critical medical claims before showing them as trusted.</p>
          </div>
        </div>
        <button type="button" onClick={onOpenFidelityLab} className="inline-flex min-h-11 items-center justify-center gap-2 self-start rounded-xl border border-sky-300/30 bg-sky-300/10 px-4 text-sm font-semibold text-sky-100 hover:bg-sky-300/20 sm:self-auto">
          Open Fidelity Lab <ArrowRight className="h-4 w-4" />
        </button>
      </section>

      {/* Recent Analyses Section (Section 10) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-800/40 border border-slate-700/60 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-base text-white">Recent Medical Document Analyses</h2>
              <p className="text-xs text-slate-400">Field-level fidelity verification history</p>
            </div>
            <button
              onClick={loadData}
              className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-700 text-slate-400 hover:text-white"
              title="Refresh analyses"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="py-12 text-center rounded-lg border border-dashed border-slate-700">
              <FileText className="w-10 h-10 text-slate-500 mx-auto mb-2" />
              <p className="text-sm font-medium text-slate-300">No analyses yet.</p>
              <p className="text-xs text-slate-500 mt-1">Upload a medical document or choose a demo to begin.</p>
              <button
                onClick={onStartAnalysis}
                className="mt-4 inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Upload Document</span>
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-slate-700/80 text-slate-400 text-xs">
                    <th className="pb-3 font-semibold">Document</th>
                    <th className="pb-3 font-semibold">Type</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 font-semibold">Fidelity</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/40">
                  {documents.slice(0, 8).map((doc) => {
                    const vr = doc.verification_result;
                    const status = vr?.overall_status || 'NEEDS_REVIEW';
                    const score = vr?.fidelity_score !== undefined ? `${vr.fidelity_score}%` : 'Pending';

                    return (
                      <tr
                        key={doc.id}
                        onClick={() => onSelectDocument(doc.id)}
                        className="hover:bg-slate-700/30 cursor-pointer transition-colors group"
                      >
                        <td className="py-3 font-medium text-slate-200">
                          <div className="flex items-center space-x-2">
                            <FileText className="w-4 h-4 text-brand-400 flex-shrink-0" />
                            <span className="truncate max-w-[180px] sm:max-w-[240px]">{doc.filename}</span>
                          </div>
                        </td>
                        <td className="py-3 text-slate-400 capitalize">
                          {doc.document_type.replace('_', ' ')}
                        </td>
                        <td className="py-3">
                          {status === 'VERIFIED' && (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>✓ VERIFIED</span>
                            </span>
                          )}
                          {status === 'BLOCKED' && (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                              <XCircle className="w-3 h-3" />
                              <span>✕ BLOCKED</span>
                            </span>
                          )}
                          {(status === 'NEEDS_REVIEW' || status === 'PARTIALLY_VERIFIED') && (
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                              <AlertTriangle className="w-3 h-3" />
                              <span>⚠ REVIEW</span>
                            </span>
                          )}
                        </td>
                        <td className="py-3 font-semibold text-slate-200">
                          {score}
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={(e) => handleDelete(e, doc.id)}
                              className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                              title="Delete document (Privacy)"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              aria-label={`Open ${doc.filename} for review`}
                              onClick={(event) => {
                                event.stopPropagation();
                                onSelectDocument(doc.id);
                              }}
                              className="text-brand-400 group-hover:translate-x-0.5 transition-transform inline-flex items-center"
                            >
                              <ArrowRight className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Audit Log Trail (Prompt Section 43) */}
        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-base text-white">System Audit Events</h2>
              <p className="text-xs text-slate-400">Minimal, privacy-compliant event log</p>
            </div>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto max-h-[380px] pr-1">
            {metrics?.recent_audit_events && metrics.recent_audit_events.length > 0 ? (
              metrics.recent_audit_events.map((evt) => (
                <div 
                  key={evt.id}
                  className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-700/40 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-brand-300">
                      {evt.event_type}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {evt.timestamp}
                    </span>
                  </div>
                  {evt.document_id && (
                    <p className="text-[10px] text-slate-400 truncate">
                      Doc ID: {evt.document_id.slice(0, 8)}...
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500 py-6 text-center">No audit events recorded.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
