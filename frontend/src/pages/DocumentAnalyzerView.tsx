import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowLeft, FileText, RefreshCw } from 'lucide-react';
import { DocumentDetail } from '../types';
import { ReadBackLanguage } from '../hooks/useAccessibilityPreferences';
import { UploadSection } from '../components/UploadSection';
import { ExtractionReview } from '../components/ExtractionReview';
import { ExplanationSection } from '../components/ExplanationSection';
import { VerificationReport } from '../components/VerificationReport';
import { VerifiedNextStepCard } from '../components/VerifiedNextStepCard';
import { api } from '../services/api';

interface DocumentAnalyzerViewProps {
  currentDocument: DocumentDetail | null;
  setCurrentDocument: (doc: DocumentDetail | null) => void;
  documentLoading: boolean;
  documentLoadError: boolean;
  onRetryDocumentLoad: () => void;
  elderMode: boolean;
  ttsEnabled: boolean;
  simplifiedLanguage: boolean;
  caregiverView: boolean;
  selectedLanguage: ReadBackLanguage;
  setSelectedLanguage: (language: ReadBackLanguage) => void;
  step: number;
  setStep: (step: number) => void;
  onBackToDashboard: () => void;
}

export const DocumentAnalyzerView: React.FC<DocumentAnalyzerViewProps> = ({
  currentDocument,
  setCurrentDocument,
  documentLoading,
  documentLoadError,
  onRetryDocumentLoad,
  elderMode,
  ttsEnabled,
  simplifiedLanguage,
  caregiverView,
  selectedLanguage,
  setSelectedLanguage,
  step,
  setStep,
  onBackToDashboard,
}) => {
  const [activeSourceHighlight, setActiveSourceHighlight] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    setActiveSourceHighlight(null);
  }, [currentDocument?.id]);

  const handleDocumentUploaded = (doc: DocumentDetail) => {
    setCurrentDocument(doc);
    setStep(2);
  };

  const handleConfirmed = (updatedDoc: DocumentDetail) => {
    setCurrentDocument(updatedDoc);
    setStep(3);
  };

  const handleExplanationReady = (updatedDoc: DocumentDetail) => {
    setCurrentDocument(updatedDoc);
  };

  const handleRunVerification = async () => {
    if (!currentDocument) return;
    setVerifying(true);
    try {
      const vr = await api.verifyDocument(currentDocument.id);
      const updated = await api.getDocument(currentDocument.id);
      setCurrentDocument(updated);
      setStep(4);
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Breadcrumb & Step Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-slate-700 bg-slate-800/80 p-4 shadow-inner">
        <div className="flex items-center space-x-3">
          <button
            onClick={onBackToDashboard}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Back to Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <span className="font-bold text-white text-sm">
              {currentDocument ? 'Document Review' : documentLoading ? 'Loading document…' : 'New Medical Document Analysis'}
            </span>
            <p className="text-xs text-slate-400">
              {currentDocument
                ? `${currentDocument.filename} · ${currentDocument.document_type.replace('_', ' ')} · ${currentDocument.verification_result?.overall_status || 'NEEDS REVIEW'} · ${currentDocument.verification_result ? `${currentDocument.verification_result.fidelity_score}% fidelity` : 'Fidelity pending'}`
                : 'End-to-End Document Understanding & Verification Pipeline'}
            </p>
          </div>
        </div>

      </div>

      {/* Main Step Render */}
      <div>
        {documentLoading && (
          <div role="status" aria-live="polite" className="rounded-2xl border border-slate-700 bg-slate-800/70 p-8 text-center text-slate-200">
            Loading document…
          </div>
        )}

        {documentLoadError && (
          <div role="alert" className="rounded-2xl border border-rose-500/40 bg-rose-950/30 p-8 text-center">
            <AlertTriangle className="mx-auto mb-3 h-8 w-8 text-rose-300" />
            <h2 className="text-lg font-bold text-white">Unable to load this document.</h2>
            <p className="mt-1 text-sm text-slate-300">Please try again.</p>
            <button
              type="button"
              onClick={onRetryDocumentLoad}
              className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl bg-sky-500 px-5 font-semibold text-slate-950 hover:bg-sky-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </button>
          </div>
        )}

        {!documentLoading && !documentLoadError && step === 1 && (
          <UploadSection onDocumentReady={handleDocumentUploaded} />
        )}

        {!documentLoading && !documentLoadError && step === 2 && currentDocument && (
          <ExtractionReview
            key={currentDocument.id}
            document={currentDocument}
            onConfirmed={handleConfirmed}
            onDocumentUpdated={setCurrentDocument}
            activeSourceHighlight={activeSourceHighlight}
            setActiveSourceHighlight={setActiveSourceHighlight}
          />
        )}

        {!documentLoading && !documentLoadError && step > 1 && !currentDocument && (
          <div role="status" className="rounded-2xl border border-amber-400/30 bg-amber-950/20 p-8 text-center text-slate-200">
            Select a document to review, or start a new analysis.
          </div>
        )}

        {!documentLoading && !documentLoadError && step === 3 && currentDocument && (
          <ExplanationSection
            document={currentDocument}
            onExplanationGenerated={handleExplanationReady}
            onProceedToVerify={handleRunVerification}
            elderMode={elderMode}
            ttsEnabled={ttsEnabled}
            simplifiedLanguage={simplifiedLanguage}
            caregiverView={caregiverView}
            selectedLanguage={selectedLanguage}
            setSelectedLanguage={setSelectedLanguage}
          />
        )}

        {!documentLoading && !documentLoadError && step === 4 && currentDocument && currentDocument.verification_result && (
          <VerificationReport
            result={currentDocument.verification_result}
            document={currentDocument}
            onProceedToNextStep={() => setStep(5)}
            onViewOriginalDoc={() => setStep(2)}
            elderMode={elderMode}
            ttsEnabled={ttsEnabled}
            simplifiedLanguage={simplifiedLanguage}
            caregiverView={caregiverView}
          />
        )}

        {!documentLoading && !documentLoadError && step === 4 && currentDocument && !currentDocument.verification_result && (
          <div role="status" className="rounded-2xl border border-amber-400/30 bg-amber-950/20 p-8 text-center">
            <h2 className="text-lg font-bold text-white">Verification has not been run yet.</h2>
            <p className="mt-1 text-sm text-slate-300">
              Generate an explanation and verify it before viewing the verification report.
            </p>
            <button
              type="button"
              onClick={() => setStep(3)}
              className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-sky-500 px-5 font-semibold text-slate-950 hover:bg-sky-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
            >
              Back to Explanation
            </button>
          </div>
        )}

        {!documentLoading && !documentLoadError && step === 5 && currentDocument && currentDocument.next_step && (
          <VerifiedNextStepCard
            document={currentDocument}
            nextStep={currentDocument.next_step}
            elderMode={elderMode}
            ttsEnabled={ttsEnabled}
            onProviderSaved={(updatedStep) => {
              setCurrentDocument({
                ...currentDocument,
                next_step: updatedStep,
              });
            }}
          />
        )}

        {!documentLoading && !documentLoadError && step === 5 && currentDocument && !currentDocument.next_step && (
          <div role="status" className="rounded-2xl border border-amber-400/30 bg-amber-950/20 p-8 text-center">
            <h2 className="text-lg font-bold text-white">No verified next step is available.</h2>
            <p className="mt-1 text-sm text-slate-300">
              This document does not contain a next step that ReadBack could verify.
            </p>
            <button
              type="button"
              onClick={() => setStep(4)}
              className="mt-5 inline-flex min-h-11 items-center rounded-xl bg-sky-500 px-5 font-semibold text-slate-950 hover:bg-sky-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
            >
              Back to Verification Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
