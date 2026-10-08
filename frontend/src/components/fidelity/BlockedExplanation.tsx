import React from 'react';
import { AlertTriangle, ShieldX } from 'lucide-react';
import { FieldComparison } from '../../types';

interface BlockedExplanationProps {
  comparison?: FieldComparison;
  blockedReason?: string | null;
}

function numericDifference(comparison?: FieldComparison): string | null {
  if (!comparison || comparison.mismatch_type !== 'NUMERIC_MISMATCH') return null;
  const original = comparison.original_display.match(/-?\d+(?:\.\d+)?/);
  const attempted = comparison.explanation_display.match(/-?\d+(?:\.\d+)?/);
  if (!original || !attempted) return null;
  const delta = Number(attempted[0]) - Number(original[0]);
  return `${delta > 0 ? '+' : ''}${delta.toFixed(1)}`;
}

export const BlockedExplanation: React.FC<BlockedExplanationProps> = ({ comparison, blockedReason }) => (
  <section role="alert" className="rounded-2xl border border-rose-400/50 bg-rose-950/30 p-5 sm:p-6" aria-labelledby="blocked-explanation-title">
    <div className="flex items-start gap-3">
      <ShieldX className="mt-0.5 h-6 w-6 shrink-0 text-rose-200" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-bold uppercase text-rose-200">Explanation not approved</p>
        <h2 id="blocked-explanation-title" className="mt-1 text-xl font-extrabold text-white">WHY READBACK BLOCKED THIS</h2>
        <p className="mt-2 text-sm leading-relaxed text-rose-100">
          ReadBack independently extracted the medical claim from the generated explanation and compared it with the confirmed document fact. Because this is a medically important field, the explanation was not approved.
        </p>
      </div>
    </div>
    {comparison ? (
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-600 bg-slate-950/60 p-4">
          <p className="text-xs font-bold uppercase text-slate-400">Field</p>
          <p className="mt-1 font-semibold text-white">{comparison.field_name}</p>
          <p className="mt-1 text-xs text-rose-200">{comparison.mismatch_type || 'CRITICAL MISMATCH'}</p>
        </div>
        <div className="rounded-xl border border-slate-600 bg-slate-950/60 p-4">
          <p className="text-xs font-bold uppercase text-slate-400">Document said</p>
          <p className="mt-1 font-mono text-sm text-slate-100">{comparison.original_display}</p>
        </div>
        <div className="rounded-xl border border-rose-400/40 bg-rose-950/50 p-4">
          <p className="text-xs font-bold uppercase text-rose-200">AI output · demo corruption</p>
          <p className="mt-1 font-mono text-sm text-white">{comparison.explanation_display}</p>
          {numericDifference(comparison) && <p className="mt-2 text-sm font-bold text-rose-200">Difference: {numericDifference(comparison)}</p>}
        </div>
      </div>
    ) : (
      <p className="mt-4 flex items-start gap-2 text-sm text-rose-100"><AlertTriangle className="h-4 w-4 shrink-0" />{blockedReason || 'A critical field did not match.'}</p>
    )}
  </section>
);