import React, { useState } from 'react';
import { 
  Check, 
  Edit3, 
  AlertTriangle, 
  CheckCircle2, 
  FileText, 
  Sparkles, 
  ArrowRight,
  ShieldCheck,
  Search,
  CheckCheck,
  RefreshCw
} from 'lucide-react';
import { DocumentDetail, MedicalFact } from '../types';
import { api } from '../services/api';

interface ExtractionReviewProps {
  document: DocumentDetail;
  onConfirmed: (updatedDoc: DocumentDetail) => void;
  onDocumentUpdated: (updatedDoc: DocumentDetail) => void;
  activeSourceHighlight?: string | null;
  setActiveSourceHighlight?: (text: string | null) => void;
}

export const ExtractionReview: React.FC<ExtractionReviewProps> = ({
  document,
  onConfirmed,
  onDocumentUpdated,
  activeSourceHighlight,
  setActiveSourceHighlight,
}) => {
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const initialFacts = document.confirmed_facts?.length
    ? document.confirmed_facts
    : document.extracted_facts ?? [];
  const [facts, setFacts] = useState<MedicalFact[]>(initialFacts);

  // Confidence counting
  const highConfidenceCount = facts.filter((f) => f.confidence >= 0.80).length;
  const lowConfidenceCount = facts.length - highConfidenceCount;

  const handleFactValueChange = (fieldId: string, key: keyof MedicalFact, value: any) => {
    setFacts((prev) =>
      prev.map((f) => {
        if (f.field_id === fieldId) {
          return { ...f, [key]: value, edited: true };
        }
        return f;
      })
    );
  };

  const handleConfirmAll = async () => {
    setSaving(true);
    try {
      const updatedDoc = await api.confirmFacts(document.id, facts);
      onConfirmed(updatedDoc);
    } catch (err) {
      alert('Failed to save confirmed facts.');
    } finally {
      setSaving(false);
    }
  };

  const handleRunExtraction = async () => {
    setExtracting(true);
    setExtractionError(null);
    try {
      const updatedDocument = await api.extractDocumentFacts(document.id);
      const extractedFacts = updatedDocument.confirmed_facts?.length
        ? updatedDocument.confirmed_facts
        : updatedDocument.extracted_facts ?? [];
      setFacts(extractedFacts);
      onDocumentUpdated(updatedDocument);
    } catch (error) {
      setExtractionError(error instanceof Error ? error.message : 'Extraction failed. Please try again.');
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Status Bar */}
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-white text-base">Step 1: Structured Fact Review</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand-500/20 text-brand-400 border border-brand-500/30">
              OCR Quality: {Math.round(document.ocr_quality * 100)}%
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {facts.length} facts extracted • {highConfidenceCount} high confidence • {lowConfidenceCount} require confirmation
          </p>
        </div>

        {facts.length > 0 && (
          <button
            onClick={handleConfirmAll}
            disabled={saving}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.02]"
          >
            <CheckCheck className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Confirm Facts & Proceed to Explanation'}</span>
          </button>
        )}
      </div>

      {/* Split-Screen Interface (Section 12) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT: Original Document Viewer */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-700/80 rounded-2xl overflow-hidden flex flex-col h-[650px] shadow-xl">
          <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
              <FileText className="w-4 h-4 text-brand-400" />
              <span>ORIGINAL DOCUMENT TEXT</span>
            </div>
            <span className="text-[11px] text-slate-400">Page 1 of {document.page_count}</span>
          </div>

          <div className="p-4 flex-1 overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed bg-slate-950/60 divide-y divide-slate-800/40">
            {document.raw_text?.trim() ? document.raw_text.split('\n').map((line, idx) => {
              const isHighlighted = activeSourceHighlight && line.toLowerCase().includes(activeSourceHighlight.toLowerCase());

              return (
                <div
                  key={idx}
                  className={`py-1 px-2 rounded transition-colors ${
                    isHighlighted
                      ? 'bg-brand-500/30 text-brand-200 border border-brand-500/50 font-semibold'
                      : 'hover:bg-slate-800/40'
                  }`}
                >
                  <span className="inline-block w-6 text-slate-600 select-none mr-2">{idx + 1}</span>
                  <span>{line}</span>
                </div>
              );
            }) : (
              <p className="p-4 text-sm font-sans text-slate-400">Original document text preview is not available.</p>
            )}
          </div>

          <div className="p-3 bg-slate-900 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Click any fact on the right to locate its source evidence</span>
            <Search className="w-3.5 h-3.5 text-slate-500" />
          </div>
        </div>

        {/* RIGHT: Structured Extracted Information (Section 13) */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-700/80 rounded-2xl overflow-hidden flex flex-col h-[650px] shadow-xl">
          <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>STRUCTURED EXTRACTED FACTS ({facts.length})</span>
            </div>
            <span className="text-[11px] text-slate-400">Typed JSON Schema</span>
          </div>

          <div className="p-4 flex-1 overflow-y-auto space-y-3">
            {facts.length === 0 ? (
              <div className="flex min-h-64 flex-col items-center justify-center text-center">
                <FileText className="mb-3 h-9 w-9 text-slate-500" />
                <h3 className="font-semibold text-white">Extraction data is not available yet.</h3>
                <p className="mt-1 max-w-md text-sm text-slate-400">Run extraction for this selected document to load structured facts.</p>
                {extractionError && <p role="alert" className="mt-3 text-sm text-rose-300">{extractionError}</p>}
                <button
                  type="button"
                  onClick={handleRunExtraction}
                  disabled={extracting}
                  className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl bg-sky-500 px-5 font-semibold text-slate-950 hover:bg-sky-400 disabled:cursor-wait disabled:opacity-60"
                >
                  <RefreshCw className={`h-4 w-4 ${extracting ? 'animate-spin' : ''}`} />
                  {extracting ? 'Running Extraction…' : 'Run Extraction'}
                </button>
              </div>
            ) : (
              <>
                {lowConfidenceCount > 0 && (
                  <p role="status" className="rounded-lg border border-amber-400/25 bg-amber-400/10 px-3 py-2 text-sm text-amber-100">
                    Some fields need your confirmation before an explanation can be generated.
                  </p>
                )}
                {extractionError && <p role="alert" className="text-sm text-rose-300">{extractionError}</p>}
                {facts.map((fact) => {
              const isEditing = editingFieldId === fact.field_id;
              const isHighConf = fact.confidence >= 0.80;

              return (
                <div
                  key={fact.field_id}
                  onClick={() => setActiveSourceHighlight && setActiveSourceHighlight(fact.source_text)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    activeSourceHighlight && fact.source_text.includes(activeSourceHighlight)
                      ? 'border-brand-500 bg-brand-500/10'
                      : 'border-slate-800 bg-slate-800/40 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white text-sm">{fact.name}</span>
                        <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-slate-700/80 text-slate-300">
                          {fact.category}
                        </span>

                        {/* Flag Badge */}
                        {fact.flag && fact.flag !== 'NONE' && (
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              fact.flag === 'LOW' || fact.flag === 'HIGH' || fact.flag === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            }`}
                          >
                            {fact.flag}
                          </span>
                        )}

                        {fact.negation && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                            NEGATION PRESERVED (DO NOT)
                          </span>
                        )}
                      </div>

                      {/* Fact Value & Details */}
                      {!isEditing ? (
                        <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1 text-xs">
                          {fact.value !== undefined && (
                            <span className="font-mono text-base font-bold text-white">
                              {fact.value} {fact.unit || ''}
                            </span>
                          )}
                          {fact.dosage && (
                            <span className="font-mono text-sm font-semibold text-white">
                              Dosage: {fact.dosage}
                            </span>
                          )}
                          {fact.frequency && (
                            <span className="text-slate-400">
                              Frequency: <span className="text-slate-200">{fact.frequency}</span>
                            </span>
                          )}
                          {fact.reference_range && (
                            <span className="text-slate-400">
                              Ref Range: <span className="text-slate-300">{fact.reference_range}</span>
                            </span>
                          )}
                          {fact.condition && (
                            <span className="text-slate-400">
                              Condition: <span className="text-slate-300">{fact.condition}</span>
                            </span>
                          )}
                        </div>
                      ) : (
                        /* Inline Editor */
                        <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-0.5">Value</label>
                            <input
                              type="text"
                              value={fact.value ?? fact.dosage ?? ''}
                              onChange={(e) => handleFactValueChange(fact.field_id, 'value', e.target.value)}
                              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-0.5">Unit / Range</label>
                            <input
                              type="text"
                              value={fact.unit ?? fact.frequency ?? ''}
                              onChange={(e) => handleFactValueChange(fact.field_id, 'unit', e.target.value)}
                              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono"
                            />
                          </div>
                          <div>
                            <label className="text-[10px] text-slate-400 block mb-0.5">Flag</label>
                            <select
                              value={fact.flag || 'NORMAL'}
                              onChange={(e) => handleFactValueChange(fact.field_id, 'flag', e.target.value)}
                              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white"
                            >
                              <option value="NORMAL">NORMAL</option>
                              <option value="LOW">LOW</option>
                              <option value="HIGH">HIGH</option>
                              <option value="CRITICAL">CRITICAL</option>
                            </select>
                          </div>
                        </div>
                      )}

                      {/* Source Text citation */}
                      <p className="mt-2 text-[11px] text-slate-400 italic">
                        Source: "{fact.source_text}"
                      </p>
                    </div>

                    {/* Actions & Confidence */}
                    <div className="flex flex-col items-end space-y-2">
                      <div className="flex items-center space-x-1.5">
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                            isHighConf
                              ? 'bg-emerald-500/15 text-emerald-400'
                              : 'bg-amber-500/15 text-amber-400'
                          }`}
                        >
                          {Math.round(fact.confidence * 100)}% {isHighConf ? '✓' : '⚠'}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingFieldId(isEditing ? null : fact.field_id);
                          }}
                          className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-white"
                          title="Edit extracted fact"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {!isHighConf && (
                        <span className="text-[10px] text-amber-400 flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3" />
                          <span>Requires review</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
                })}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
