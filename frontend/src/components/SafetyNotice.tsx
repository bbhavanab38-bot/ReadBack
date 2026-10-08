import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

export const SafetyNotice: React.FC = () => {
  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 my-4 flex items-start space-x-3 text-amber-200">
      <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
      <div className="text-xs sm:text-sm space-y-1">
        <p className="font-semibold text-amber-300">
          Responsible AI Safety Notice & Medical Disclaimer:
        </p>
        <p className="text-amber-200/90 leading-relaxed">
          <strong>ReadBack</strong> helps you understand and verify information contained in printed medical documents. 
          It does <strong>not</strong> provide medical diagnosis or treatment advice. Always consult a qualified healthcare professional for medical decisions.
        </p>
        <p className="text-[11px] text-amber-300/70 pt-1">
          If you believe you are experiencing a medical emergency, contact your local emergency service immediately (e.g. 911 / 112 / 108).
        </p>
      </div>
    </div>
  );
};
