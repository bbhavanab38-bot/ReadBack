import React from 'react';
import { Check, FileText, ListChecks, Sparkles, ScanSearch, GitCompareArrows, ShieldCheck } from 'lucide-react';

const STAGES = [
  { label: 'Document', Icon: FileText },
  { label: 'Structured facts', Icon: ListChecks },
  { label: 'AI explanation', Icon: Sparkles },
  { label: 'Independent re-extraction', Icon: ScanSearch },
  { label: 'Field-level diff', Icon: GitCompareArrows },
  { label: 'Verdict', Icon: ShieldCheck },
];

interface FidelityPipelineProps {
  activeStage: number;
  verdict?: 'VERIFIED' | 'BLOCKED' | 'NEEDS_REVIEW' | 'PARTIALLY_VERIFIED';
}

export const FidelityPipeline: React.FC<FidelityPipelineProps> = ({ activeStage, verdict }) => (
  <ol aria-label="ReadBack verification pipeline" className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
    {STAGES.map(({ label, Icon }, index) => {
      const complete = index < activeStage;
      const active = index === activeStage;
      const verdictColor = index === 5 && verdict === 'BLOCKED'
        ? 'border-rose-400/50 bg-rose-400/10 text-rose-100'
        : index === 5 && verdict === 'VERIFIED'
          ? 'border-emerald-400/50 bg-emerald-400/10 text-emerald-100'
          : active
            ? 'border-sky-400/60 bg-sky-400/10 text-sky-100'
            : complete
              ? 'border-emerald-400/30 bg-slate-800 text-emerald-100'
              : 'border-slate-700 bg-slate-800/60 text-slate-400';
      return (
        <li key={label} aria-current={active ? 'step' : undefined} className={`flex min-h-20 items-center gap-3 rounded-xl border p-3 ${verdictColor}`}>
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-950/50">
            {complete ? <Check className="h-5 w-5" aria-hidden="true" /> : <Icon className="h-5 w-5" aria-hidden="true" />}
          </span>
          <span className="text-sm font-semibold leading-snug">{label}</span>
        </li>
      );
    })}
  </ol>
);