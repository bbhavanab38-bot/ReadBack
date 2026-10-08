import React, { useState } from 'react';
import { 
  Calendar, 
  MapPin, 
  CheckCircle2, 
  AlertCircle, 
  Phone, 
  Mail, 
  Building2, 
  Save, 
  Plus, 
  ShieldCheck,
  Stethoscope,
  Info
} from 'lucide-react';
import { VerifiedNextStep, ProviderContact, DocumentDetail } from '../types';
import { api } from '../services/api';
import { VerifiedSpeechControls } from './VerifiedSpeechControls';

interface VerifiedNextStepCardProps {
  document: DocumentDetail;
  nextStep: VerifiedNextStep;
  onProviderSaved: (updatedStep: VerifiedNextStep) => void;
  elderMode: boolean;
  ttsEnabled: boolean;
}

export const VerifiedNextStepCard: React.FC<VerifiedNextStepCardProps> = ({
  document,
  nextStep,
  onProviderSaved,
  elderMode,
  ttsEnabled,
}) => {
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [providerForm, setProviderForm] = useState<ProviderContact>(
    nextStep.saved_provider || {
      provider_name: '',
      phone: '',
      email: '',
      clinic_or_hospital: '',
      notes: '',
    }
  );
  const [saving, setSaving] = useState(false);

  const handleSaveProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!providerForm.provider_name.trim()) {
      alert('Please enter a provider name.');
      return;
    }

    setSaving(true);
    try {
      const updated = await api.saveProvider(document.id, providerForm);
      onProviderSaved(updated);
      setShowProviderModal(false);
    } catch (err) {
      alert('Failed to save provider contact information.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">VERIFIED NEXT STEP</h2>
              <p className="text-xs text-slate-400">Grounded healthcare-services navigation</p>
            </div>
          </div>

          {nextStep.has_next_step ? (
            <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Instruction Verified</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
              <span>No Instruction Stated</span>
            </span>
          )}
        </div>

        {nextStep.has_next_step ? (
          /* Explicit follow-up detected */
          <div className="space-y-6">
            <VerifiedSpeechControls
              text={nextStep.source_text || ''}
              language="en"
              label="verified next step"
              elderMode={elderMode}
              enabled={ttsEnabled}
              verificationStatus={
                document.verification_result?.overall_status === 'VERIFIED'
                  && nextStep.verification_status === 'VERIFIED'
                    && nextStep.is_explicit
                  ? 'VERIFIED'
                  : undefined
              }
                  unavailableReason="Audio is unavailable until the next step is explicitly verified."
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                  <span className="text-xs text-slate-400 flex items-center space-x-1.5 mb-1">
                  <Stethoscope className="w-3.5 h-3.5 text-brand-400" />
                  <span>Healthcare Service</span>
                </span>
                  <span className="text-base font-bold text-white block">
                  {nextStep.service_name}
                </span>
                {nextStep.department_or_specialty && (
                  <span className="text-xs text-slate-400 mt-1 block">
                    {nextStep.department_or_specialty}
                  </span>
                )}
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                <span className="text-xs text-slate-400 flex items-center space-x-1.5 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-brand-400" />
                  <span>Timing in document</span>
                </span>
                <span className="text-base font-bold text-emerald-400 block font-mono">
                  {nextStep.timing || 'Not stated'}
                </span>
                <span className="text-xs text-slate-400 mt-1 block">
                  {nextStep.timing ? 'Explicitly stated in source' : 'No timing stated in source'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                <span className="text-xs text-slate-400 flex items-center space-x-1.5 mb-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Grounding Source</span>
                </span>
                <span className="text-xs text-slate-300 font-mono italic block line-clamp-2">
                  "{nextStep.source_text}"
                </span>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Page {nextStep.page || 1} • Verified explicit instruction
                </span>
              </div>
            </div>

            {/* Provider Contact Section (Section 31) */}
            <div className="p-5 rounded-xl bg-slate-800/30 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="font-bold text-sm text-white block">
                  Healthcare Provider Follow-up Details
                </span>
                <p className="text-xs text-slate-400 mt-0.5">
                  Save your clinic, hospital, or doctor details for this verified follow-up step.
                </p>
                {nextStep.saved_provider && (
                  <div className="mt-2 text-xs text-emerald-300 flex items-center space-x-3">
                    <span><strong>Provider:</strong> {nextStep.saved_provider.provider_name}</span>
                    {nextStep.saved_provider.phone && <span><strong>Phone:</strong> {nextStep.saved_provider.phone}</span>}
                    {nextStep.saved_provider.clinic_or_hospital && <span><strong>Clinic:</strong> {nextStep.saved_provider.clinic_or_hospital}</span>}
                  </div>
                )}
              </div>

              <button
                onClick={() => setShowProviderModal(true)}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition-colors flex-shrink-0"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{nextStep.saved_provider ? 'Edit Provider Contact' : 'Find / Contact Healthcare Provider'}</span>
              </button>
            </div>
          </div>
        ) : (
          /* No explicit instruction */
          <div className="p-6 rounded-xl bg-slate-800/40 border border-slate-800 text-center space-y-2">
            <Info className="w-8 h-8 text-slate-500 mx-auto" />
            <h3 className="font-bold text-sm text-slate-200">
              No verified healthcare-service instruction was found in this document.
            </h3>
            <p className="text-xs text-slate-400 max-w-lg mx-auto">
              ReadBack strictly adheres to safety boundaries and will <strong>never independently infer</strong> or hypothesize unstated specialist consultations, scans, or tests.
            </p>
          </div>
        )}

        {/* Safety Boundary Notice (Section 30) */}
        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 flex items-start space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
          <span>
            <strong>Verified Next Step Boundary:</strong> ReadBack only displays next-step recommendations that are explicitly printed in the verified medical document. It will not advise you to see a cardiologist, order an MRI, or modify medication unless explicitly written by your doctor.
          </span>
        </div>
      </div>

      {/* Provider Contact Modal / Drawer (Section 31) */}
      {showProviderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-base text-white">Save Healthcare Provider</h3>
              <button
                onClick={() => setShowProviderModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveProvider} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Doctor / Provider Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Sarah Jenkins"
                  value={providerForm.provider_name}
                  onChange={(e) => setProviderForm({ ...providerForm, provider_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-brand-500"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Clinic / Hospital</label>
                <input
                  type="text"
                  placeholder="e.g. Metropolitan Medical Center"
                  value={providerForm.clinic_or_hospital || ''}
                  onChange={(e) => setProviderForm({ ...providerForm, clinic_or_hospital: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-slate-300 block mb-1 font-semibold">Phone Number</label>
                  <input
                    type="tel"
                    placeholder="e.g. +1 555-0192"
                    value={providerForm.phone || ''}
                    onChange={(e) => setProviderForm({ ...providerForm, phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="text-slate-300 block mb-1 font-semibold">Email</label>
                  <input
                    type="email"
                    placeholder="clinic@example.com"
                    value={providerForm.email || ''}
                    onChange={(e) => setProviderForm({ ...providerForm, email: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Appointment Notes</label>
                <textarea
                  rows={2}
                  placeholder="Bring prior lab reports and insurance card"
                  value={providerForm.notes || ''}
                  onChange={(e) => setProviderForm({ ...providerForm, notes: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:border-brand-500"
                />
              </div>

              <div className="pt-3 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowProviderModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow"
                >
                  {saving ? 'Saving...' : 'Save Provider Contact'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
