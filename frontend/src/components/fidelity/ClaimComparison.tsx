import React from 'react';
import { FieldComparison } from '../../types';

interface ClaimComparisonProps {
  comparisons: FieldComparison[];
  simulated: boolean;
}

export const ClaimComparison: React.FC<ClaimComparisonProps> = ({ comparisons, simulated }) => (
  <section className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-800" aria-labelledby="claim-comparison-title">
    <div className="border-b border-slate-700 px-5 py-4">
      <p className="text-xs font-bold uppercase text-slate-400">{simulated ? 'Demo output' : 'ReadBack verification'}</p>
      <h2 id="claim-comparison-title" className="mt-1 text-lg font-bold text-white">Document claim vs. AI claim</h2>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-slate-950/60 text-xs uppercase text-slate-300">
          <tr>
            <th scope="col" className="px-5 py-3">Field</th>
            <th scope="col" className="px-5 py-3">Document said</th>
            <th scope="col" className="px-5 py-3">AI output</th>
            <th scope="col" className="px-5 py-3">ReadBack result</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700">
          {comparisons.map(comparison => {
            const mismatch = comparison.status === 'MISMATCH';
            return (
              <tr key={comparison.field_id} className={mismatch ? 'bg-rose-950/30' : ''}>
                <th scope="row" className="px-5 py-4 font-semibold text-slate-100">
                  {comparison.field_name}
                  <span className="mt-1 block text-xs font-normal capitalize text-slate-400">{comparison.category}</span>
                </th>
                <td className="px-5 py-4 font-mono text-slate-200">{comparison.original_display}</td>
                <td className={`px-5 py-4 font-mono ${mismatch ? 'font-bold text-rose-200' : 'text-slate-200'}`}>{comparison.explanation_display}</td>
                <td className="px-5 py-4">
                  <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-bold ${mismatch ? 'border-rose-400/50 bg-rose-400/10 text-rose-100' : comparison.status === 'PASS' ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-100' : 'border-amber-300/40 bg-amber-300/10 text-amber-100'}`}>
                    {mismatch ? 'BLOCKED' : comparison.status === 'PASS' ? 'MATCHED' : comparison.status}
                  </span>
                  <p className="mt-1 max-w-xs text-xs text-slate-400">{comparison.mismatch_type || comparison.details}</p>
                </td>
              </tr>
            );
          })}
          {comparisons.length === 0 && (
            <tr><td colSpan={4} className="px-5 py-8 text-center text-slate-400">No field comparisons are available for this document.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  </section>
);