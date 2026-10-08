import React from 'react';
import { Play } from 'lucide-react';
import { FidelityFailureType, MedicalFact } from '../../types';

const FAILURE_OPTIONS: Array<{ value: FidelityFailureType; label: string; category: MedicalFact['category'] }> = [
  { value: 'numeric_value_changed', label: 'Numeric value changed', category: 'laboratory' },
  { value: 'unit_changed', label: 'Unit changed', category: 'laboratory' },
  { value: 'drug_name_changed', label: 'Drug name changed', category: 'medication' },
  { value: 'dosage_changed', label: 'Dosage changed', category: 'medication' },
  { value: 'frequency_changed', label: 'Frequency changed', category: 'medication' },
  { value: 'negation_flipped', label: 'Negation flipped', category: 'instruction' },
  { value: 'abnormal_flag_changed', label: 'Abnormal flag changed', category: 'laboratory' },
  { value: 'important_fact_omitted', label: 'Important fact omitted', category: 'general' },
];

interface FailureSimulatorProps {
  facts: MedicalFact[];
  failureType: FidelityFailureType;
  onFailureTypeChange: (failureType: FidelityFailureType) => void;
  onSimulate: () => void;
  disabled: boolean;
  loading: boolean;
}

function supportsFailure(facts: MedicalFact[], option: typeof FAILURE_OPTIONS[number]): boolean {
  if (option.value === 'important_fact_omitted') {
    return facts.some(fact => fact.category === 'laboratory' || fact.category === 'medication' || (fact.category === 'instruction' && fact.negation));
  }
  if (option.value === 'numeric_value_changed') return facts.some(fact => fact.category === 'laboratory' && fact.value !== null && fact.value !== undefined);
  if (option.value === 'unit_changed') return facts.some(fact => fact.category === 'laboratory' && !!fact.unit);
  if (option.value === 'abnormal_flag_changed') return facts.some(fact => fact.category === 'laboratory' && !!fact.flag && fact.flag !== 'NONE');
  if (option.value === 'drug_name_changed') return facts.some(fact => fact.category === 'medication');
  if (option.value === 'dosage_changed') return facts.some(fact => fact.category === 'medication' && !!(fact.dosage || fact.strength));
  if (option.value === 'frequency_changed') return facts.some(fact => fact.category === 'medication' && !!fact.frequency);
  return facts.some(fact => fact.category === 'instruction');
}

export const FailureSimulator: React.FC<FailureSimulatorProps> = ({
  facts,
  failureType,
  onFailureTypeChange,
  onSimulate,
  disabled,
  loading,
}) => (
  <section className="rounded-2xl border border-slate-700 bg-slate-800 p-5 shadow-inner sm:p-6" aria-labelledby="failure-simulator-title">
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="max-w-xl">
        <p className="text-xs font-bold uppercase text-amber-200">Demo / research only</p>
        <h2 id="failure-simulator-title" className="mt-1 text-lg font-bold text-white">Simulate an AI error</h2>
        <p className="mt-1 text-sm text-slate-300">Creates a separate corrupted output from these confirmed facts. It never edits the source document or saved explanation.</p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <label className="flex min-w-64 flex-col gap-1 text-sm font-medium text-slate-200">
          Failure type
          <select
            value={failureType}
            onChange={event => onFailureTypeChange(event.target.value as FidelityFailureType)}
            disabled={disabled || loading}
            className="min-h-11 rounded-lg border border-slate-600 bg-slate-950 px-3 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-300 disabled:opacity-60"
          >
            {FAILURE_OPTIONS.map(option => (
              <option key={option.value} value={option.value} disabled={!supportsFailure(facts, option)}>
                {option.label}{supportsFailure(facts, option) ? '' : ' — not in this document'}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={onSimulate}
          disabled={disabled || loading || !supportsFailure(facts, FAILURE_OPTIONS.find(option => option.value === failureType)!)}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-400 px-5 font-bold text-slate-950 hover:bg-amber-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play className="h-4 w-4" />
          {loading ? 'Rechecking…' : 'Simulate AI Error'}
        </button>
      </div>
    </div>
  </section>
);