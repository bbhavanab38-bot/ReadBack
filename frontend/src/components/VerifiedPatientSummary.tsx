import React from 'react';
import { CheckCircle2, ClipboardCheck } from 'lucide-react';
import { DocumentDetail, MedicalFact } from '../types';

interface VerifiedPatientSummaryProps {
  document: DocumentDetail;
  simpleLanguage: boolean;
  caregiverView: boolean;
  elderMode: boolean;
}

function factValue(fact: MedicalFact): string {
  const value = fact.value ?? fact.dosage ?? fact.strength;
  if (value !== undefined && value !== null) return `${value}${fact.unit ? ` ${fact.unit}` : ''}`;
  return fact.instruction_text || fact.source_text;
}

function simpleFactText(fact: MedicalFact): string {
  if (fact.category === 'laboratory') {
    const value = fact.value === undefined || fact.value === null ? 'not available' : `${fact.value}${fact.unit ? ` ${fact.unit}` : ''}`;
    return `Your report shows ${fact.name}: ${value}${fact.flag && fact.flag !== 'NONE' ? `. The report marks this result as ${fact.flag}` : ''}.`;
  }
  if (fact.category === 'medication') {
    const dose = fact.dosage || fact.strength;
    return `Your document lists ${fact.name}${dose ? `, ${dose}` : ''}${fact.frequency ? `, ${fact.frequency}` : ''}${fact.duration ? `, for ${fact.duration}` : ''}.`;
  }
  if (fact.category === 'instruction') return `Your document says: ${fact.instruction_text || fact.source_text}`;
  return `Your document says: ${fact.source_text}`;
}

export const VerifiedPatientSummary: React.FC<VerifiedPatientSummaryProps> = ({
  document,
  simpleLanguage,
  caregiverView,
  elderMode,
}) => {
  const isVerified = document.verification_result?.overall_status === 'VERIFIED'
    && document.verification_result.explanation_safe_to_display;
  const facts = document.confirmed_facts?.length ? document.confirmed_facts : document.extracted_facts || [];
  const nextStep = document.next_step;

  if (!isVerified) return null;

  if (caregiverView) {
    const findings = facts.filter(fact => fact.category === 'laboratory' || fact.category === 'medication' || fact.category === 'instruction');
    const hasVerifiedNextStep = !!nextStep?.has_next_step
      && nextStep.verification_status === 'VERIFIED'
      && nextStep.is_explicit
      && !!nextStep.source_text;
    return (
      <section className={`space-y-5 rounded-2xl border border-slate-600 bg-slate-800 p-5 ${elderMode ? 'sm:p-7' : ''}`} aria-labelledby="caregiver-summary-title">
        <div>
          <p className="text-xs font-bold uppercase text-sky-200">Caregiver view · verified information only</p>
          <h3 id="caregiver-summary-title" className="mt-1 text-xl font-extrabold text-white">A clear summary to review together</h3>
        </div>
        <dl className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4"><dt className="text-xs font-bold uppercase text-slate-400">Document</dt><dd className="mt-1 font-semibold capitalize text-white">{document.document_type.replace('_', ' ')}</dd></div>
          <div className="rounded-xl border border-emerald-300/30 bg-emerald-300/10 p-4"><dt className="text-xs font-bold uppercase text-emerald-100">Status</dt><dd className="mt-1 flex items-center gap-2 font-bold text-white"><CheckCircle2 className="h-5 w-5 text-emerald-200" />Information verified</dd></div>
        </dl>
        <div>
          <h4 className="font-bold text-white">Important verified findings</h4>
          <ul className="mt-2 space-y-2">
            {findings.map(fact => (
              <li key={fact.field_id} className="flex flex-wrap items-baseline justify-between gap-2 rounded-lg border border-slate-700 bg-slate-950/50 p-3">
                <span className="font-semibold text-slate-100">{fact.name}</span>
                <span className="font-mono text-slate-200">{factValue(fact)}{fact.flag && fact.flag !== 'NONE' ? ` · ${fact.flag}` : ''}</span>
                <span className="w-full text-xs text-slate-400">Source: Page {fact.page || fact.bbox?.page || 1}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4">
          <h4 className="font-bold text-white">Next verified step</h4>
          {hasVerifiedNextStep ? (
            <p className="mt-1 text-slate-200">{nextStep.source_text}<span className="block text-xs text-slate-400">Source: Page {nextStep.page || 1}</span></p>
          ) : <p className="mt-1 text-slate-400">No explicit follow-up instruction was found.</p>}
        </div>
        <p className="text-xs text-slate-400">This view repeats source facts only; it does not add medical interpretation.</p>
      </section>
    );
  }

  if (!simpleLanguage) return null;

  return (
    <section className={`space-y-4 rounded-2xl border border-sky-300/25 bg-slate-800 p-5 ${elderMode ? 'sm:p-7' : ''}`} aria-labelledby="simple-explanation-title">
      <div className="flex items-center gap-2 text-sky-100">
        <ClipboardCheck className="h-5 w-5" aria-hidden="true" />
        <h3 id="simple-explanation-title" className="text-lg font-bold">What your report says</h3>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {facts.map(fact => (
          <article key={fact.field_id} className="rounded-xl border border-slate-700 bg-slate-950/55 p-4">
            <h4 className={`font-bold text-white ${elderMode ? 'text-xl' : 'text-base'}`}>{fact.name}</h4>
            <p className={`mt-1 font-mono font-extrabold text-slate-100 ${elderMode ? 'text-2xl' : 'text-lg'}`}>{factValue(fact)}</p>
            {fact.flag && fact.flag !== 'NONE' && <p className={`mt-1 font-bold text-amber-100 ${elderMode ? 'text-lg' : 'text-sm'}`}>{fact.flag}</p>}
            <p className={`mt-3 leading-relaxed text-slate-200 ${elderMode ? 'text-lg' : 'text-sm'}`}>{simpleFactText(fact)}</p>
            <p className="mt-2 text-xs text-slate-400">Source: Page {fact.page || fact.bbox?.page || 1}</p>
          </article>
        ))}
      </div>
      <p className="text-sm font-semibold text-emerald-100">✓ ReadBack checked these facts against your document.</p>
    </section>
  );
};