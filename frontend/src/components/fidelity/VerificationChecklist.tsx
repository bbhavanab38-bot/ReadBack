import React from 'react';
import { AlertTriangle, Check, Minus } from 'lucide-react';
import { FieldComparison, VerificationResult } from '../../types';

const CHECKS: Array<{ label: string; types: string[]; categories?: string[] }> = [
  { label: 'Numeric value', types: ['NUMERIC_MISMATCH'], categories: ['laboratory'] },
  { label: 'Unit', types: ['UNIT_MISMATCH'], categories: ['laboratory'] },
  { label: 'Drug name', types: ['CRITICAL_DRUG_MISMATCH'], categories: ['medication'] },
  { label: 'Dosage', types: ['CRITICAL_DOSAGE_MISMATCH'], categories: ['medication'] },
  { label: 'Frequency', types: ['CRITICAL_FREQUENCY_MISMATCH'], categories: ['medication'] },
  { label: 'Negation', types: ['CRITICAL_NEGATION_FLIP'], categories: ['instruction'] },
  { label: 'Abnormal / critical flag', types: ['FLAG_MISMATCH'], categories: ['laboratory'] },
  { label: 'Important field omission', types: ['FIELD_OMITTED'] },
];

interface VerificationChecklistProps {
  result: VerificationResult;
}

export const VerificationChecklist: React.FC<VerificationChecklistProps> = ({ result }) => (
  <section className="rounded-2xl border border-slate-700 bg-slate-800 p-5" aria-labelledby="verification-checks-title">
    <h2 id="verification-checks-title" className="text-lg font-bold text-white">Field-level checks</h2>
    <p className="mt-1 text-sm text-slate-400">Each status below is derived from the backend comparison result.</p>
    <ul className="mt-4 grid gap-2 sm:grid-cols-2">
      {CHECKS.map(check => {
        const relevant: FieldComparison[] = result.field_comparisons.filter(comparison =>
          (!check.categories || check.categories.includes(comparison.category))
          && (check.types.includes(comparison.mismatch_type || '') || comparison.status === 'PASS')
        );
        const mismatch = relevant.find(comparison => check.types.includes(comparison.mismatch_type || ''));
        const hasRelevantComparison = relevant.length > 0;
        const Icon = mismatch ? AlertTriangle : hasRelevantComparison ? Check : Minus;
        const label = mismatch ? 'MISMATCH' : hasRelevantComparison ? 'MATCHED' : 'NOT CHECKED';
        return (
          <li key={check.label} className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-950/40 px-3 py-3">
            <span className="text-sm text-slate-200">{check.label}</span>
            <span className={`inline-flex items-center gap-1.5 text-xs font-bold ${mismatch ? 'text-rose-200' : hasRelevantComparison ? 'text-emerald-200' : 'text-slate-400'}`}>
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </span>
          </li>
        );
      })}
    </ul>
    <p className="mt-3 text-xs text-amber-100">Reference-range equality is not currently compared by the backend verifier.</p>
  </section>
);