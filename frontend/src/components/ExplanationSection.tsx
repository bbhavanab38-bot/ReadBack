import React, { useState } from 'react';
import { 
  Languages, 
  Sparkles, 
  BookOpen, 
  ShieldCheck, 
  ShieldAlert, 
  FileCheck2,
  RefreshCw,
  MessageCircle
} from 'lucide-react';
import { DocumentDetail } from '../types';
import { api } from '../services/api';
import { VerifiedSpeechControls } from './VerifiedSpeechControls';
import { VerifiedPatientSummary } from './VerifiedPatientSummary';
import { ReadBackLanguage } from '../hooks/useAccessibilityPreferences';

interface ExplanationSectionProps {
  document: DocumentDetail;
  onExplanationGenerated: (updatedDoc: DocumentDetail) => void;
  onProceedToVerify: () => void;
  elderMode: boolean;
  ttsEnabled: boolean;
  simplifiedLanguage: boolean;
  caregiverView: boolean;
  selectedLanguage: ReadBackLanguage;
  setSelectedLanguage: (language: ReadBackLanguage) => void;
}

export const ExplanationSection: React.FC<ExplanationSectionProps> = ({
  document,
  onExplanationGenerated,
  onProceedToVerify,
  elderMode,
  ttsEnabled,
  simplifiedLanguage,
  caregiverView,
  selectedLanguage,
  setSelectedLanguage,
}) => {
  const [corruptMode, setCorruptMode] = useState<string>('none');
  const [loading, setLoading] = useState(false);
  const [glossary, setGlossary] = useState<Record<string, string>>({});
  const [showSimpleExplanation, setShowSimpleExplanation] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const mode = corruptMode === 'none' ? null : corruptMode;
      const res = await api.explainDocument(document.id, selectedLanguage, mode);
      setGlossary(res.term_definitions || {});
      
      // Refresh document
      const updated = await api.getDocument(document.id);
      onExplanationGenerated(updated);
    } catch (err: any) {
      alert(err.message || 'Explanation generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const hasExplanation = !!document.explanation_text || document.explanation_pending_verification === true;
  const canDisplayExplanation = document.verification_result?.overall_status === 'VERIFIED'
    && document.verification_result.explanation_safe_to_display === true;
  const explanationWasBlocked = document.verification_result?.overall_status === 'BLOCKED';
  const verifiedLanguageMatches = selectedLanguage === (document.selected_language || selectedLanguage);
  const speechVerificationStatus = verifiedLanguageMatches
    ? document.verification_result?.overall_status
    : undefined;

  return (
    <div className="space-y-6">
      {/* Configuration Header */}
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-brand-400" />
              <span>Step 2: Simple-Language AI Explanation</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              ReadBack translates verified facts into your preferred language without changing numbers, units, drug names, dosage, or flags.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Language Selector (Section 18) */}
            <div className="flex flex-wrap items-center gap-2" aria-label="Explanation language">
              <Languages className="h-5 w-5 text-brand-300" aria-hidden="true" />
              {elderMode ? (
                <div className="grid grid-cols-2 gap-2">
                  {([
                    ['en', 'English', 'Listen in English'],
                    ['kn', 'ಕನ್ನಡ', 'ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ'],
                    ['hi', 'हिन्दी', 'हिन्दी में सुनें'],
                    ['ta', 'தமிழ்', 'தமிழில் கேளுங்கள்'],
                  ] as const).map(([code, label, helper]) => (
                    <button key={code} type="button" aria-pressed={selectedLanguage === code} onClick={() => setSelectedLanguage(code)} className={`min-h-[4.5rem] rounded-xl border px-4 py-2 text-left ${selectedLanguage === code ? 'border-sky-300 bg-sky-300/15 text-white' : 'border-slate-600 bg-slate-900 text-slate-200'}`}>
                      <span className="block text-base font-bold">{label}</span><span className="block text-xs text-slate-300">{helper}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <select aria-label="Explanation language" value={selectedLanguage} onChange={(event) => setSelectedLanguage(event.target.value as ReadBackLanguage)} className="min-h-11 rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-300">
                  <option value="en">English</option><option value="kn">ಕನ್ನಡ (Kannada)</option><option value="hi">हिन्दी (Hindi)</option><option value="ta">தமிழ் (Tamil)</option>
                </select>
              )}
            </div>

            {/* Deliberate Corruption Testing Dropdown (Demonstration Feature) */}
            <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5">
              <span className="text-[11px] text-slate-400">Test Gate:</span>
              <select
                value={corruptMode}
                onChange={(e) => setCorruptMode(e.target.value)}
                className="bg-transparent text-slate-300 text-xs font-medium focus:outline-none cursor-pointer"
              >
                <option value="none" className="bg-slate-900 text-white">Clean (Faithful)</option>
                <option value="number" className="bg-slate-900 text-rose-300">Simulate Numeric Hallucination (12.2 vs 10.2)</option>
                <option value="drug" className="bg-slate-900 text-rose-300">Simulate Drug Name Swap (Metoprolol)</option>
                <option value="dosage" className="bg-slate-900 text-rose-300">Simulate Dosage Mismatch (1000 mg)</option>
                <option value="negation" className="bg-slate-900 text-rose-300">Simulate Negation Flip</option>
                <option value="flag" className="bg-slate-900 text-rose-300">Simulate Flag Flip (LOW to NORMAL)</option>
              </select>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs sm:text-sm shadow-md transition-all"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Generating...' : hasExplanation ? 'Regenerate' : 'Generate Explanation'}</span>
            </button>
          </div>
        </div>

        {corruptMode !== 'none' && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <span>
              <strong>Research Demonstration Mode:</strong> You selected a deliberate corruption ({corruptMode}). When you run verification, ReadBack should catch and <strong>BLOCK</strong> this unfaithful explanation.
            </span>
          </div>
        )}
      </div>

      {/* Generated Explanation Display */}
      {hasExplanation && !canDisplayExplanation ? (
        <div className={`p-6 rounded-xl border text-center space-y-3 ${explanationWasBlocked ? 'border-rose-700 bg-rose-950/40' : 'border-amber-700 bg-amber-950/30'}`}>
          <ShieldAlert className={`w-8 h-8 mx-auto ${explanationWasBlocked ? 'text-rose-400' : 'text-amber-400'}`} />
          <h3 className="font-bold text-white">
            {explanationWasBlocked ? 'Explanation blocked' : 'Explanation hidden until verification'}
          </h3>
          <p className="text-xs text-slate-300">
            {explanationWasBlocked
              ? 'A critical field changed. The explanation is hidden; review the verification report before continuing.'
              : 'ReadBack will independently re-extract and compare the critical fields before displaying the explanation.'}
          </p>
          {!explanationWasBlocked && (
            <button
              onClick={onProceedToVerify}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Run Field-Level Verification</span>
            </button>
          )}
          <VerifiedSpeechControls
            text=""
            language={selectedLanguage}
            verificationStatus={undefined}
              elderMode={elderMode}
              enabled={ttsEnabled}
          />
        </div>
      ) : hasExplanation ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                <FileCheck2 className="w-4 h-4 text-brand-400" />
                <span>Patient-Friendly Medical Explanation ({selectedLanguage.toUpperCase()})</span>
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                Verified for Display
              </span>
            </div>

            <div className="text-sm sm:text-base text-slate-200 leading-relaxed font-sans whitespace-pre-line p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              {document.explanation_text}
            </div>

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

            <VerifiedSpeechControls
              text={document.explanation_text || ''}
              language={selectedLanguage}
              verificationStatus={speechVerificationStatus}
              unavailableReason={verifiedLanguageMatches ? undefined : 'Generate and verify this language before listening.'}
              elderMode={elderMode}
              enabled={ttsEnabled}
            />

            <div className="pt-2 flex items-center justify-between">
              <p className="text-xs text-slate-400">
                Next: ReadBack independently re-extracts facts from this text and performs field-by-field verification.
              </p>
              <button
                onClick={onProceedToVerify}
                className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold text-sm shadow-lg shadow-emerald-500/25 transition-all hover:scale-[1.02]"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Run Field-Level Verification</span>
              </button>
            </div>
          </div>

          {/* Medical Glossary / Term Definitions (Section 52) */}
          <div className="lg:col-span-4 bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
              <BookOpen className="w-4 h-4 text-brand-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                What These Terms Mean
              </span>
            </div>

            <div className="space-y-3">
              {Object.keys(glossary).length > 0 ? (
                Object.entries(glossary).map(([term, def]) => (
                  <div key={term} className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 text-xs space-y-1">
                    <span className="font-bold text-brand-300">{term}</span>
                    <p className="text-slate-300 leading-relaxed">{def}</p>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 space-y-2">
                  <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 space-y-1">
                    <span className="font-bold text-brand-300">Hemoglobin</span>
                    <p className="text-slate-300">A protein in red blood cells that carries oxygen from your lungs to the rest of your body.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 space-y-1">
                    <span className="font-bold text-brand-300">Reference Range</span>
                    <p className="text-slate-300">The expected set of numbers that most healthy people fall into for this test.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center rounded-2xl border border-dashed border-slate-700 bg-slate-800/30">
          <Sparkles className="w-10 h-10 text-brand-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">Generate Patient-Friendly Explanation</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Choose your preferred language (English, Kannada, Hindi, or Tamil) and click Generate Explanation to begin.
          </p>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="mt-4 inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm shadow-md"
          >
            <span>{loading ? 'Generating...' : 'Generate Explanation'}</span>
          </button>
        </div>
      )}
    </div>
  );
};
