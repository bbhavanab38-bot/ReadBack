import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  FileCheck,
  Languages
} from 'lucide-react';
import { api } from '../services/api';
import { DocumentDetail } from '../types';

interface UploadSectionProps {
  onDocumentReady: (doc: DocumentDetail) => void;
  onCancel?: () => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({ onDocumentReady, onCancel }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [processingStage, setProcessingStage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setUploadError(null);
    const stages = file.name.toLowerCase().endsWith('.txt')
      ? ['Uploading...', 'Extracting text...', 'Building structured facts...']
      : ['Uploading...', 'Extracting text...', 'Running OCR...', 'Building structured facts...'];
    let stageIndex = 0;
    setProcessingStage(stages[stageIndex]);
    const stageTimer = window.setInterval(() => {
      stageIndex = Math.min(stageIndex + 1, stages.length - 1);
      setProcessingStage(stages[stageIndex]);
    }, 1100);
    try {
      const doc = await api.uploadDocument(file);
      setProcessingStage('Ready for verification.');
      onDocumentReady(doc);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Document extraction failed.');
    } finally {
      window.clearInterval(stageTimer);
      setUploading(false);
      setProcessingStage(null);
    }
  };

  const handleDemo = async (demoType: string) => {
    setUploading(true);
    setUploadError(null);
    setProcessingStage('Building structured facts...');
    try {
      const doc = await api.uploadDocument(undefined, demoType);
      setProcessingStage('Ready for verification.');
      onDocumentReady(doc);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Demo failed to load.');
    } finally {
      setUploading(false);
      setProcessingStage(null);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload Header */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          Upload Medical Document
        </h2>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          ReadBack extracts typed facts, requests your confirmation, translates into simple language, and field-by-field verifies the AI explanation before showing it to you.
        </p>
      </div>

      {uploadError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* Drag & Drop Zone (Section 11) */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
          isDragging 
            ? 'border-brand-400 bg-brand-500/10 scale-[1.01]' 
            : 'border-slate-700 hover:border-slate-600 bg-slate-800/40 hover:bg-slate-800/60'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          accept=".pdf,.png,.jpg,.jpeg,.txt"
          className="hidden"
        />

        <div className="w-14 h-14 mx-auto rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 mb-4">
          <Upload className={`w-7 h-7 ${uploading ? 'animate-bounce' : ''}`} />
        </div>

        <h3 className="text-base font-semibold text-slate-200">
          {processingStage || 'Drop your medical document here, or browse'}
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Supports PDF, PNG, JPG, JPEG, and TXT files. Untrusted text is sanitized and protected against prompt injection.
        </p>

        <div className="mt-4 flex items-center justify-center space-x-4 text-[11px] text-slate-500">
          <span>✓ Privacy Mode Protected</span>
          <span>•</span>
          <span>✓ Local OCR Processing</span>
          <span>•</span>
          <span>✓ No Diagnosis Advice</span>
        </div>
      </div>

      {/* Quick Demo Pre-loaded Test Cases */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Or select a synthetic test case (No file needed):
          </span>
          <span className="text-[11px] px-2 py-0.5 rounded bg-brand-500/20 text-brand-400 font-mono">
            Demo Mode Ready
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Demo 1: Clean CBC */}
          <button
            type="button"
            disabled={uploading}
            onClick={() => handleDemo('lab_report')}
            className="p-3.5 rounded-xl text-left bg-slate-900/60 hover:bg-slate-800 border border-slate-700/70 hover:border-emerald-500/40 transition-all group"
          >
            <div className="flex items-center space-x-2 text-emerald-400 mb-1">
              <FileCheck className="w-4 h-4" />
              <span className="font-semibold text-xs text-slate-200 group-hover:text-emerald-400">
                Blood Report (CBC)
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Hemoglobin 10.2 g/dL (LOW), WBC 7800, explicit 2-week follow-up. Demonstrates 100% verified flow.
            </p>
          </button>

          {/* Demo 2: Blocked Mismatch */}
          <button
            type="button"
            disabled={uploading}
            onClick={() => handleDemo('corrupted_test')}
            className="p-3.5 rounded-xl text-left bg-slate-900/60 hover:bg-slate-800 border border-slate-700/70 hover:border-rose-500/40 transition-all group"
          >
            <div className="flex items-center space-x-2 text-rose-400 mb-1">
              <ShieldAlert className="w-4 h-4" />
              <span className="font-semibold text-xs text-slate-200 group-hover:text-rose-400">
                Deliberate Mismatch
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Original: 10.2 g/dL. Hallucination test: 12.2 g/dL. Demonstrates instant verification blocking.
            </p>
          </button>

          {/* Demo 3: Prescription */}
          <button
            type="button"
            disabled={uploading}
            onClick={() => handleDemo('prescription')}
            className="p-3.5 rounded-xl text-left bg-slate-900/60 hover:bg-slate-800 border border-slate-700/70 hover:border-brand-500/40 transition-all group"
          >
            <div className="flex items-center space-x-2 text-brand-400 mb-1">
              <FileText className="w-4 h-4" />
              <span className="font-semibold text-xs text-slate-200 group-hover:text-brand-400">
                Prescription (Rx)
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-snug">
              Metformin 500 mg, Atorvastatin 20 mg, negation warnings ("Do NOT take on empty stomach").
            </p>
          </button>
        </div>
      </div>
    </div>
  );
};
