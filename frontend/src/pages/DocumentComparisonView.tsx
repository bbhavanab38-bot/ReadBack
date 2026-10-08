import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  AlertTriangle, 
  CheckCircle2, 
  Calendar, 
  TrendingUp, 
  Clock, 
  FileText,
  Search
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from 'recharts';
import { DocumentSummary, DocumentComparisonResult } from '../types';
import { api } from '../services/api';

export const DocumentComparisonView: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<DocumentComparisonResult | null>(null);
  const [timelineData, setTimelineData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchInit = async () => {
      try {
        const [docs, timeline] = await Promise.all([
          api.getDocuments(),
          api.getTimeline(),
        ]);
        setDocuments(docs);
        setTimelineData(timeline);
        if (docs.length >= 2) {
          setSelectedDocIds([docs[0].id, docs[1].id]);
        }
      } catch (err) {
        console.error('Failed to load comparison data:', err);
      }
    };
    fetchInit();
  }, []);

  const handleRunComparison = async () => {
    if (selectedDocIds.length < 2) {
      alert('Please select at least 2 documents to compare.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.compareDocuments(selectedDocIds);
      setComparisonResult(res);
    } catch (err: any) {
      alert(err.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectDoc = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  // Prepare chart data for lab tests over time
  const chartData = timelineData.map((t) => ({
    date: t.date,
    ...t.values,
  }));

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex items-center space-x-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Multi-Document Comparison & Timeline
            </h1>
            <p className="text-xs sm:text-sm text-slate-400">
              Cross-document conflict detection and historical health timeline
            </p>
          </div>
        </div>
      </div>

      {/* Document Selection Grid */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <span className="font-bold text-sm text-white">
            Select Documents to Compare (Select 2 or more)
          </span>
          <button
            onClick={handleRunComparison}
            disabled={selectedDocIds.length < 2 || loading}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:bg-slate-800 text-white font-semibold text-xs transition-colors shadow-md"
          >
            {loading ? 'Analyzing Conflicts...' : `Compare ${selectedDocIds.length} Documents`}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                onClick={() => toggleSelectDoc(doc.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-brand-500/15 border-brand-500 text-white'
                    : 'bg-slate-800/40 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs truncate max-w-[200px]">{doc.filename}</span>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}}
                    className="rounded text-brand-500 focus:ring-0"
                  />
                </div>
                <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
                  <span className="capitalize">{doc.document_type.replace('_', ' ')}</span>
                  <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparison Conflict Alerts (Prompt Section 27) */}
      {comparisonResult && (
        <div className="space-y-4">
          {comparisonResult.has_conflicts ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm">
                <AlertTriangle className="w-5 h-5" />
                <span>⚠ DOCUMENT CONFLICT DETECTED</span>
              </div>

              {comparisonResult.conflicts.map((conflict, idx) => (
                <div
                  key={idx}
                  className="rounded-xl bg-rose-950/70 border-2 border-rose-600/80 p-5 text-rose-100 shadow-xl space-y-3"
                >
                  <div className="flex items-center justify-between border-b border-rose-800/60 pb-2">
                    <span className="font-bold text-sm text-white">
                      Conflicting Parameter: {conflict.field_name}
                    </span>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-600 text-white">
                      {conflict.conflict_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-3 rounded-lg bg-rose-900/50 border border-rose-700">
                      <span className="text-rose-300 block text-[10px] uppercase">{conflict.doc_a_name}</span>
                      <span className="text-base font-bold text-white mt-1 block">{conflict.doc_a_value}</span>
                    </div>
                    <div className="p-3 rounded-lg bg-rose-900/50 border border-rose-700">
                      <span className="text-rose-300 block text-[10px] uppercase">{conflict.doc_b_name}</span>
                      <span className="text-base font-bold text-white mt-1 block">{conflict.doc_b_value}</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-black/40 border border-rose-800/60 text-xs text-rose-200 leading-relaxed font-sans">
                    {conflict.warning_message}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 flex items-center space-x-3">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
              <div>
                <span className="font-bold text-sm block">No Cross-Document Discrepancies Found</span>
                <p className="text-xs text-emerald-200/80 mt-0.5">
                  The selected documents do not contain conflicting dosage or laboratory parameters.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Health Document Timeline (Prompt Section 28) */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <Calendar className="w-5 h-5 text-brand-400" />
            <div>
              <h2 className="text-lg font-bold text-white">HEALTH DOCUMENT TIMELINE</h2>
              <p className="text-xs text-slate-400">Extracted numerical lab parameters plotted chronologically</p>
            </div>
          </div>
          <span className="text-[11px] text-slate-400 italic">
            Strictly displays extracted data • No automated diagnostic interpretation
          </span>
        </div>

        {chartData.length > 0 ? (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '0.75rem',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line
                  type="monotone"
                  dataKey="Hemoglobin"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="Fasting Blood Glucose"
                  stroke="#34d399"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="WBC"
                  stroke="#fbbf24"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-10 text-xs text-slate-500">
            No chronological laboratory records available.
          </div>
        )}
      </div>
    </div>
  );
};
