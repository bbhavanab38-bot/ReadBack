import React from 'react';
import { ArrowDown } from 'lucide-react';
import { DocumentDetail, FieldComparison, VerificationStatus } from '../../types';

interface ClaimProvenanceProps {
  document: DocumentDetail;
  comparison?: FieldComparison;
  verdict: VerificationStatus;
  explanation: string;
}

export const ClaimProvenance: React.FC<ClaimProvenanceProps> = ({ document, comparison, verdict, explanation }) => {
  const fact = document.confirmed_facts?.find(item => item.field_id === comparison?.field_id)
    || document.extracted_facts?.find(item => item.field_id === comparison?.field_id);
  const source = comparison?.source_text || fact?.source_text || 'Source text is not available.';
  const claim = comparison?.explanation_source_text || explanation || 'Explanation claim is not available.';
  const steps = [
    { label: 'Source document', value: document.filename },
    { label: `Page ${fact?.page || fact?.bbox?.page || 1} · Parsed source`, value: source },
    { label: 'Structured fact', value: comparison?.original_display || 'No field selected' },
    { label: 'AI explanation claim', value: claim },
    { label: 'Independent re-extraction', value: comparison?.explanation_display || 'No extracted claim' },
    { label: 'Field-level verification', value: comparison?.details || verdict },
    { label: 'Final verdict', value: verdict },
  ];

  return (
    <section className="rounded-2xl border border-slate-700 bg-slate-800 p-5" aria-labelledby="claim-provenance-title">
      <h2 id="claim-provenance-title" className="text-lg font-bold text-white">Claim provenance</h2>
      <ol className="mt-4 space-y-2">
        {steps.map((step, index) => (
          <li key={step.label}>
            <div className="rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2.5">
              <p className="text-xs font-bold uppercase text-sky-200">{step.label}</p>
              <p className="mt-1 break-words text-sm text-slate-200">{step.value}</p>
            </div>
            {index < steps.length - 1 && <ArrowDown className="mx-auto my-1 h-4 w-4 text-slate-500" aria-hidden="true" />}
          </li>
        ))}
      </ol>
    </section>
  );
};