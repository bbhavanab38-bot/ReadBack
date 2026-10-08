import React, { useMemo, useState } from 'react';
import { ArrowLeft, BadgeCheck, FlaskConical, RotateCcw, ShieldCheck } from 'lucide-react';
import { DocumentDetail, FidelityFailureType, FidelitySimulationResponse, VerificationStatus } from '../types';
import { api } from '../services/api';
import { BlockedExplanation } from '../components/fidelity/BlockedExplanation';
import { ClaimComparison } from '../components/fidelity/ClaimComparison';
import { ClaimProvenance } from '../components/fidelity/ClaimProvenance';
import { FailureSimulator } from '../components/fidelity/FailureSimulator';
import { FidelityPipeline } from '../components/fidelity/FidelityPipeline';
import { VerificationChecklist } from '../components/fidelity/VerificationChecklist';

type DemoFixture = 'cbc' | 'prescription';

interface FidelityLabProps {
  onBackToOverview: () => void;
}

export const FidelityLab: React.FC<FidelityLabProps> = ({ onBackToOverview }) => {
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [simulation, setSimulation] = useState<FidelitySimulationResponse | null>(null);
  const [failureType, setFailureType] = useState<FidelityFailureType>('numeric_value_changed');
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState(0);

  const loadSyntheticDemo = async (fixture: DemoFixture = 'cbc') => {
    setLoading(true);
    setError(null);
    setSimulation(null);
    setDocument(null);
    setStage(0);
    try {
      const uploaded = await api.loadFidelityLabDemo(fixture);
      setDocument(uploaded);
      setStage(1);

      await api.explainDocument(uploaded.id, 'en');
      setStage(2);
      await api.verifyDocument(uploaded.id);
      setStage(4);

      const verifiedDocument = await api.getDocument(uploaded.id);
      setDocument(verifiedDocument);
      if (
        verifiedDocument.verification_result?.overall_status !== 'VERIFIED'
        || !verifiedDocument.verification_result.explanation_safe_to_display
      ) {
        setError('The existing synthetic example did not pass ReadBack verification. Simulations are disabled.');
        setStage(5);
        return;
      }
      setFailureType(fixture === 'cbc' ? 'numeric_value_changed' : 'drug_name_changed');
      setStage(5);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unable to load the synthetic document.');
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    if (!document || document.verification_result?.overall_status !== 'VERIFIED') return;
    setSimulating(true);
    setError(null);
    try {
      const result = await api.simulateFidelityFailure(document.id, failureType);
      setSimulation(result);
      setStage(5);
    } catch (simulationError) {
      setError(simulationError instanceof Error ? simulationError.message : 'The demonstration could not be run.');
    } finally {
      setSimulating(false);
    }
  };

  const activeResult = simulation?.verification_result || document?.verification_result || null;
  const comparisons = activeResult?.field_comparisons || [];
  const criticalComparison = comparisons.find(comparison => comparison.status === 'MISMATCH' && comparison.is_critical);
  const sourceFact = useMemo(() => {
    if (!document || !criticalComparison) return document?.confirmed_facts?.[0] || document?.extracted_facts?.[0];
    return document.confirmed_facts?.find(fact => fact.field_id === criticalComparison.field_id)
      || document.extracted_facts?.find(fact => fact.field_id === criticalComparison.field_id);
  }, [document, criticalComparison]);

  const backToVerified = () => {
    setSimulation(null);
    setError(null);
    setStage(5);
  };

  const chooseAnotherFixture = () => {
    setDocument(null);
    setSimulation(null);
    setError(null);
    setStage(0);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <header className="flex flex-col gap-4 rounded-2xl border border-slate-700 bg-slate-900 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div className="flex items-start gap-3">
          <span className="rounded-xl border border-sky-300/20 bg-sky-300/10 p-2.5 text-sky-200">
            <FlaskConical className="h-6 w-6" aria-hidden="true" />
          </span>
          <div>
            <p className="text-xs font-bold uppercase text-sky-200">Fidelity Lab</p>
            <h1 className="mt-1 text-2xl font-extrabold text-white">Does the explanation preserve the facts?</h1>
            <p className="mt-1 text-sm text-slate-300">See how ReadBack detects changes in AI-generated medical explanations.</p>
          </div>
        </div>
        <button type="button" onClick={onBackToOverview} className="inline-flex min-h-11 items-center gap-2 self-start rounded-xl border border-slate-600 bg-slate-800 px-4 text-sm font-semibold text-slate-100 hover:bg-slate-700 sm:self-auto">
          <ArrowLeft className="h-4 w-4" />
          Overview
        </button>
      </header>

      <FidelityPipeline activeStage={stage} verdict={activeResult?.overall_status} />

      {!document && (
        <section className="rounded-2xl border border-slate-700 bg-slate-800 p-6 sm:p-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-bold uppercase text-sky-200">Synthetic data · demonstration only</p>
            <h2 className="mt-2 text-xl font-bold text-white">Test how ReadBack catches explanation errors.</h2>
            <p className="mt-2 text-sm text-slate-300">Load a checked-in synthetic document. Facts and verification results come from the existing ReadBack pipeline.</p>
            {error && <p role="alert" className="mt-4 text-sm text-rose-200">{error}</p>}
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button type="button" onClick={() => void loadSyntheticDemo('cbc')} disabled={loading} className="inline-flex min-h-12 items-center gap-2 rounded-xl bg-sky-400 px-5 font-bold text-slate-950 hover:bg-sky-300 disabled:opacity-50">
                <FlaskConical className="h-5 w-5" />
                {loading ? 'Loading verified example…' : 'Load Synthetic CBC Demo'}
              </button>
              <button type="button" onClick={() => void loadSyntheticDemo('prescription')} disabled={loading} className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-slate-500 bg-slate-700 px-5 font-semibold text-white hover:bg-slate-600 disabled:opacity-50">
                <BadgeCheck className="h-5 w-5" />
                Load Synthetic Prescription
              </button>
            </div>
          </div>
        </section>
      )}

      {document && (
        <>
          <section className="rounded-2xl border border-slate-700 bg-slate-800 p-5 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-bold text-white">{document.filename}</h2>
                  <span className="rounded-full border border-amber-300/30 bg-amber-300/10 px-3 py-1 text-xs font-bold text-amber-100">SYNTHETIC DEMO</span>
                </div>
                <p className="mt-1 text-sm capitalize text-slate-300">{document.document_type.replace('_', ' ')} · {document.page_count} page(s)</p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <div className="rounded-xl border border-emerald-300/30 bg-emerald-300/10 px-4 py-3 text-right">
                  <p className="text-xs font-bold uppercase text-emerald-100">{document.verification_result?.overall_status || 'NOT VERIFIED'}</p>
                  <p className="mt-1 text-xl font-extrabold text-white">{document.verification_result?.fidelity_score ?? '—'}{document.verification_result ? '%' : ''} <span className="text-xs font-medium text-emerald-100">field fidelity</span></p>
                </div>
                <button type="button" onClick={chooseAnotherFixture} className="min-h-11 rounded-xl border border-slate-600 px-4 text-sm font-semibold text-slate-200 hover:bg-slate-700">Choose another fixture</button>
              </div>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {(document.confirmed_facts?.length ? document.confirmed_facts : document.extracted_facts || []).map(fact => (
                <div key={fact.field_id} className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-white">{fact.name}</p>
                      <p className="mt-1 font-mono text-lg font-bold text-slate-100">
                        {fact.value ?? fact.dosage ?? fact.strength ?? fact.instruction_text ?? '—'} {fact.unit || ''}
                      </p>
                      {fact.reference_range && <p className="mt-1 text-sm text-slate-300">Reference: {fact.reference_range}</p>}
                      {fact.frequency && <p className="mt-1 text-sm text-slate-300">Frequency: {fact.frequency}</p>}
                    </div>
                    {fact.flag && fact.flag !== 'NONE' && <span className="rounded-full border border-amber-200/30 bg-amber-200/10 px-3 py-1 text-xs font-bold text-amber-100">{fact.flag}</span>}
                  </div>
                  <p className="mt-2 text-xs text-slate-400">Source · p. {fact.page || 1}: {fact.source_text}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950/60 p-4">
              <div className="flex items-center gap-2 text-emerald-100">
                <ShieldCheck className="h-5 w-5" aria-hidden="true" />
                <h3 className="font-bold">Verified AI explanation</h3>
                <span className="rounded-full border border-emerald-300/30 px-2.5 py-1 text-xs font-bold">VERIFIED</span>
              </div>
              <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-100">{document.explanation_text}</p>
            </div>
          </section>

          <FailureSimulator
            facts={document.confirmed_facts?.length ? document.confirmed_facts : document.extracted_facts || []}
            failureType={failureType}
            onFailureTypeChange={value => { setFailureType(value); setSimulation(null); }}
            onSimulate={() => void runSimulation()}
            disabled={document.verification_result?.overall_status !== 'VERIFIED'}
            loading={simulating}
          />

          {error && <p role="alert" className="rounded-xl border border-rose-400/30 bg-rose-950/30 p-4 text-sm text-rose-100">{error}</p>}

          {simulation && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-300/30 bg-amber-300/10 p-4">
                <div>
                  <p className="text-xs font-extrabold uppercase text-amber-100">{simulation.demo_label}</p>
                  <p className="mt-1 text-sm text-slate-100">This corrupted text exists only in this demo result; the saved document was not changed.</p>
                </div>
                <button type="button" onClick={backToVerified} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-slate-500 bg-slate-800 px-4 font-semibold text-white hover:bg-slate-700">
                  <RotateCcw className="h-4 w-4" />
                  Return to verified state
                </button>
              </div>
              <div className="rounded-xl border border-slate-700 bg-slate-950/60 p-4">
                <p className="text-xs font-bold uppercase text-amber-100">Intentionally corrupted demo output</p>
                <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-100">{simulation.simulated_explanation}</p>
              </div>
              <ClaimComparison comparisons={simulation.verification_result.field_comparisons} simulated />
              {simulation.verification_result.overall_status === 'BLOCKED' && (
                <BlockedExplanation comparison={criticalComparison || simulation.verification_result.field_comparisons.find(item => item.status === 'MISMATCH')} blockedReason={simulation.verification_result.blocked_reason} />
              )}
              <VerificationChecklist result={simulation.verification_result} />
              <ClaimProvenance
                document={document}
                comparison={criticalComparison || simulation.verification_result.field_comparisons.find(item => item.status === 'MISMATCH')}
                verdict={simulation.verification_result.overall_status}
                explanation={simulation.simulated_explanation}
              />
            </div>
          )}

          {!simulation && document.verification_result && (
            <div className="space-y-4">
              <ClaimComparison comparisons={document.verification_result.field_comparisons} simulated={false} />
              <VerificationChecklist result={document.verification_result} />
              <ClaimProvenance
                document={document}
                comparison={document.verification_result.field_comparisons[0]}
                verdict={document.verification_result.overall_status}
                explanation={document.explanation_text || ''}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};