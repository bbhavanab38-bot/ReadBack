import React, { useState } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  ArrowRight,
  EyeOff,
  Eye,
  FileText,
  Activity,
  Layers
  ,MessageCircle
} from 'lucide-react';
import { VerificationResult, DocumentDetail } from '../types';
import { VerifiedSpeechControls } from './VerifiedSpeechControls';
import { VerifiedPatientSummary } from './VerifiedPatientSummary';

interface VerificationReportProps {
  result: VerificationResult;
  document: DocumentDetail;
  onProceedToNextStep: () => void;
  onViewOriginalDoc?: () => void;
  elderMode: boolean;
  ttsEnabled: boolean;
  simplifiedLanguage: boolean;
  caregiverView: boolean;
}

export const VerificationReport: React.FC<VerificationReportProps> = ({
  result,
  document,
  onProceedToNextStep,
  onViewOriginalDoc,
  elderMode,
  ttsEnabled,
  simplifiedLanguage,
  caregiverView,
}) => {
  const isBlocked = result.overall_status === 'BLOCKED';
  const isVerified = result.overall_status === 'VERIFIED';
  const isReview = result.overall_status === 'NEEDS_REVIEW' || result.overall_status === 'PARTIALLY_VERIFIED';
  const [showSimpleExplanation, setShowSimpleExplanation] = useState(false);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner Status (Section 21 & 24) */}
      {isBlocked ? (
        /* BLOCKED STATE BANNER */
        <div className="rounded-2xl bg-rose-950/80 border-2 border-rose-500/80 p-6 sm:p-8 text-rose-100 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-60 h-60 bg-rose-500/10 rounded-full blur-2xl pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-xl bg-rose-600/30 border border-rose-500 flex items-center justify-center flex-shrink-0 text-rose-400">
                <XCircle className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                    ⚠ EXPLANATION BLOCKED
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-600 text-white uppercase tracking-wider">
                    Gate Active
                  </span>
                </div>
                <p className="text-sm text-rose-200/90 leading-relaxed max-w-2xl font-medium">
                  ReadBack detected a critical mismatch in a medically important field. The AI explanation was <strong>not approved</strong> and has been prevented from displaying as trustworthy medical guidance.
                </p>
                {result.blocked_reason && (
                  <p className="text-xs text-rose-300 font-mono bg-rose-900/50 border border-rose-700/60 p-2 rounded-lg mt-2">
                    Detection Detail: {result.blocked_reason}
                  </p>
                )}
              </div>
            </div>

            {/* Score & Actions */}
            <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-3 flex-shrink-0">
              <div className="text-left md:text-right">
                <span className="text-xs text-rose-300 uppercase tracking-wider block">Document Fidelity Score</span>
                <span className="text-3xl sm:text-4xl font-extrabold text-white font-mono">
                  {result.fidelity_score}%
                </span>
              </div>
              {onViewOriginalDoc && (
                <button
                  onClick={onViewOriginalDoc}
                  className="px-4 py-2 rounded-xl bg-rose-800/80 hover:bg-rose-700 text-white text-xs font-semibold border border-rose-600 transition-colors"
                >
                  View Original Document
                </button>
              )}
            </div>
          </div>
        </div>
      ) : isVerified ? (
        /* VERIFIED STATE BANNER */
        <div className="rounded-2xl bg-emerald-950/80 border-2 border-emerald-500/80 p-6 sm:p-8 text-emerald-100 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-60 h-60 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-600/30 border border-emerald-500 flex items-center justify-center flex-shrink-0 text-emerald-400">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                    ✓ VERIFIED
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-600 text-white uppercase tracking-wider">
                    High Fidelity
                  </span>
                </div>
                <p className="text-sm text-emerald-200/90 leading-relaxed max-w-2xl font-medium">
                  All critical fields match. ReadBack independently re-extracted facts from the AI explanation and confirmed that numbers, units, drug names, dosage, frequency, and flags are 100% faithful to your document.
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-3 flex-shrink-0">
              <div className="text-left md:text-right">
                <span className="text-xs text-emerald-300 uppercase tracking-wider block">Document Fidelity Score</span>
                <span className="text-3xl sm:text-4xl font-extrabold text-white font-mono">
                  {result.fidelity_score}%
                </span>
              </div>
              <button
                onClick={onProceedToNextStep}
                className="inline-flex items-center space-x-1.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-emerald-500/25 transition-all hover:scale-[1.02]"
              >
                <span>Check Verified Next Step</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* NEEDS REVIEW BANNER */
        <div className="rounded-2xl bg-amber-950/80 border-2 border-amber-500/80 p-6 sm:p-8 text-amber-100 shadow-2xl">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 rounded-xl bg-amber-600/30 border border-amber-500 flex items-center justify-center flex-shrink-0 text-amber-400">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <span className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                ⚠ NEEDS REVIEW / PARTIALLY VERIFIED
              </span>
              <p className="text-sm text-amber-200/90 leading-relaxed">
                Some fields had borderline confidence or missing parameters in the original report. Please review the comparison details below.
              </p>
            </div>
          </div>
        </div>
      )}

      {isVerified && result.explanation_safe_to_display && document.explanation_text ? (
        <section className="rounded-xl border border-emerald-800 bg-slate-900 p-5 space-y-3">
          <h3 className="font-bold text-white">Verified patient-friendly explanation</h3>
          <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">{document.explanation_text}</p>
          <VerifiedSpeechControls
            text={document.explanation_text}
            language={document.selected_language || 'en'}
            verificationStatus={result.overall_status}
            elderMode={elderMode}
            enabled={ttsEnabled}
          />
          <button
            type="button"
            onClick={() => setShowSimpleExplanation(value => !value)}
            aria-expanded={showSimpleExplanation || simplifiedLanguage || caregiverView}
            className={`inline-flex items-center gap-3 rounded-xl border border-sky-300/35 bg-sky-300/10 px-5 font-bold text-sky-100 hover:bg-sky-300/20 ${elderMode ? 'min-h-16 w-full justify-center text-lg' : 'min-h-12 text-sm'}`}
          >
            <MessageCircle className="h-5 w-5" aria-hidden="true" />
            {showSimpleExplanation ? 'Hide “Explain it to me”' : 'EXPLAIN IT TO ME'}
          </button>
          {(showSimpleExplanation || simplifiedLanguage || caregiverView) && (
            <VerifiedPatientSummary
              document={document}
              simpleLanguage={showSimpleExplanation || simplifiedLanguage}
              caregiverView={caregiverView}
              elderMode={elderMode}
            />
          )}
        </section>
      ) : (
        <VerifiedSpeechControls
          text=""
          language={document.selected_language || 'en'}
          verificationStatus={result.overall_status}
          elderMode={elderMode}
          enabled={ttsEnabled}
        />
      )}

      {/* Summary Scorecard (Section 22) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4">
          <span className="text-xs text-slate-400 block">Fields Checked</span>
          <span className="text-2xl font-bold text-white mt-1 block">
            {result.total_fields_checked}
          </span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4">
          <span className="text-xs text-slate-400 block">Passed Matches</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">
            {result.passed_count}
          </span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4">
          <span className="text-xs text-slate-400 block">Critical Mismatches</span>
          <span className={`text-2xl font-bold mt-1 block ${result.critical_mismatches_count > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
            {result.critical_mismatches_count}
          </span>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-4">
          <span className="text-xs text-slate-400 block">Needs Review</span>
          <span className="text-2xl font-bold text-amber-400 mt-1 block">
            {result.review_count}
          </span>
        </div>
      </div>

      {/* Field-by-Field Verification Table (Section 22) */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl overflow-hidden shadow-xl">
        <div className="px-5 py-4 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-white text-base">Field-by-Field Fidelity Verification Table</h3>
            <p className="text-xs text-slate-400">Direct comparison between original document facts and explanation facts</p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Formula: (Passed / Total) × 100 = {result.fidelity_score}%
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-slate-700/80 text-slate-400 text-xs bg-slate-950/40">
                <th className="py-3 px-4 font-semibold">Field Name</th>
                <th className="py-3 px-4 font-semibold">Original Document Fact</th>
                <th className="py-3 px-4 font-semibold">Independently Extracted Explanation Fact</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {result.field_comparisons.map((comp) => {
                const isFail = comp.status === 'MISMATCH';
                const isPass = comp.status === 'PASS';

                return (
                  <tr 
                    key={comp.field_id}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isFail ? 'bg-rose-950/20' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-semibold text-slate-200">
                      <div>
                        <span>{comp.field_name}</span>
                        <span className="block text-[10px] uppercase font-normal text-slate-500">
                          {comp.category}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-mono text-xs text-slate-200">
                      <span className="px-2 py-1 rounded bg-slate-800 border border-slate-700 block whitespace-pre-wrap">
                        {comp.original_display}
                      </span>
                      {comp.source_text && (
                        <span className="block mt-1 text-[10px] text-slate-500 whitespace-pre-wrap">
                          Source: {comp.source_text}
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4 font-mono text-xs">
                      <span className={`px-2 py-1 rounded border block whitespace-pre-wrap ${
                        isFail 
                          ? 'bg-rose-950/60 text-rose-300 border-rose-700/80 font-bold' 
                          : 'bg-slate-800 text-slate-200 border-slate-700'
                      }`}>
                        {comp.explanation_display}
                      </span>
                      {comp.explanation_source_text && (
                        <span className="block mt-1 text-[10px] text-slate-500 whitespace-pre-wrap">
                          Extracted from: {comp.explanation_source_text}
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      {isPass ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>PASS</span>
                        </span>
                      ) : isFail ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>{comp.mismatch_type || 'MISMATCH'}</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>REVIEW</span>
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-xs text-slate-400 max-w-xs">
                      {comp.details}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* "What ReadBack Could Not Verify" Core Trust Feature (Section 25) */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex items-center space-x-2 text-amber-400">
          <HelpCircle className="w-4 h-4" />
          <h3 className="font-bold text-sm uppercase tracking-wider">
            WHAT READBACK COULD NOT VERIFY
          </h3>
        </div>

        {result.what_readback_could_not_verify && result.what_readback_could_not_verify.length > 0 ? (
          <ul className="space-y-1.5 text-xs text-slate-300">
            {result.what_readback_could_not_verify.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-amber-400">⚠</span>
                <span>{item}</span>
              </li>
            ))}
            <li className="text-[11px] text-slate-500 pt-2 italic">
              ReadBack did not guess or fabricate these values.
            </li>
          </ul>
        ) : (
          <p className="text-xs text-slate-400">
            All extracted fields contained sufficient OCR confidence and defined reference parameters in the original document.
          </p>
        )}
      </div>

      {/* "Why?" Architecture Explanation Card (Section 59) */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 text-xs text-slate-400 space-y-2">
        <span className="font-semibold text-slate-200 block text-sm">
          Why was this verification performed?
        </span>
        <p className="leading-relaxed">
          Standard medical AI takes a document and generates an explanation with no second check. ReadBack independently extracted the facts directly from the generated explanation text and performed a field-by-field normalized comparison against the confirmed original document schema. 
          {isBlocked && ' Because a critical mismatch was detected, the gate blocked the unsafe explanation.'}
        </p>
      </div>
    </div>
  );
};
