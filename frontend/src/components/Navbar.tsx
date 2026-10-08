import React from 'react';
import { 
  ShieldCheck, 
  FileText, 
  BarChart3, 
  Layers, 
  Eye, 
  Lock,
  Upload,
  ClipboardCheck,
  Sparkles,
  BadgeCheck,
  ArrowRight
  ,Accessibility, Settings2, Volume2, Type, Languages
} from 'lucide-react';
import { ReadBackLanguage, ReadBackFontSize } from '../hooks/useAccessibilityPreferences';

interface NavbarProps {
  activeTab: 'dashboard' | 'analyze' | 'compare' | 'fidelity' | 'evaluation';
  setActiveTab: (tab: 'dashboard' | 'analyze' | 'compare' | 'fidelity' | 'evaluation') => void;
  workflowStep: number;
  setWorkflowStep: (step: number) => void;
  hasDocument: boolean;
  verified: boolean;
  highContrast: boolean;
  setHighContrast: (val: boolean) => void;
  fontSize: ReadBackFontSize;
  setFontSize: (size: ReadBackFontSize) => void;
  elderMode: boolean;
  setElderMode: (enabled: boolean) => void;
  ttsEnabled: boolean;
  setTtsEnabled: (enabled: boolean) => void;
  simplifiedLanguage: boolean;
  setSimplifiedLanguage: (enabled: boolean) => void;
  caregiverView: boolean;
  setCaregiverView: (enabled: boolean) => void;
  selectedLanguage: ReadBackLanguage;
  setSelectedLanguage: (language: ReadBackLanguage) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  workflowStep,
  setWorkflowStep,
  hasDocument,
  verified,
  highContrast,
  setHighContrast,
  fontSize,
  setFontSize,
  elderMode,
  setElderMode,
  ttsEnabled,
  setTtsEnabled,
  simplifiedLanguage,
  setSimplifiedLanguage,
  caregiverView,
  setCaregiverView,
  selectedLanguage,
  setSelectedLanguage,
}) => {
  return (
    <header className={`sticky top-0 z-50 border-b backdrop-blur-md transition-colors ${
      highContrast && !elderMode
        ? 'bg-black border-yellow-400 text-yellow-300' 
        : 'bg-slate-900/95 border-slate-600 text-white'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <button
            type="button"
            className="flex items-center space-x-3 cursor-pointer group text-left"
            onClick={() => setActiveTab('dashboard')}
            aria-label="ReadBack overview"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-500 flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-slate-400">
                  READBACK
                </span>
                <span className="hidden sm:inline text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700">
                  Health document workspace
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Understand. Verify what AI says. Know your verified next step.
              </p>
            </div>
          </button>

          {/* Navigation Links */}
          <nav aria-label={activeTab === 'analyze' ? 'Document workflow' : 'Main navigation'} className="flex items-center gap-1 overflow-x-auto whitespace-nowrap px-1">
            {activeTab === 'analyze' ? (
              [
                { num: 1, label: 'Upload', Icon: Upload },
                { num: 2, label: 'Facts', Icon: ClipboardCheck },
                { num: 3, label: 'Explanation', Icon: Sparkles },
                { num: 4, label: 'Verification', Icon: ShieldCheck },
                { num: 5, label: 'Next step', Icon: BadgeCheck },
              ].map(({ num, label, Icon }) => {
                const accessible = num === 1 || (hasDocument && num <= workflowStep) || (num === 5 && verified);
                const active = workflowStep === num;
                return (
                  <button
                    key={num}
                    type="button"
                    disabled={!accessible}
                    aria-current={active ? 'step' : undefined}
                    onClick={() => {
                      setWorkflowStep(num);
                      setActiveTab('analyze');
                    }}
                    className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-35 ${
                      active ? 'bg-sky-400/15 text-sky-300 ring-1 ring-sky-400/30' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden xl:inline">{label}</span>
                    {num < 5 && <ArrowRight className="hidden 2xl:block h-3 w-3 text-slate-600" />}
                  </button>
                );
              })
            ) : (
              <>
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                activeTab === 'dashboard'
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => setActiveTab('analyze')}
              className="flex items-center space-x-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800/60 hover:text-white sm:text-sm"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Upload</span>
            </button>

            <button
              onClick={() => setActiveTab('compare')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                activeTab === 'compare'
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span className="hidden md:inline">Multi-Doc</span>
              <span>Compare</span>
            </button>

            <button
              onClick={() => setActiveTab('fidelity')}
              aria-current={activeTab === 'fidelity' ? 'page' : undefined}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                activeTab === 'fidelity'
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Fidelity Lab</span>
            </button>

            <button
              onClick={() => setActiveTab('evaluation')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                activeTab === 'evaluation'
                  ? 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Evaluation</span>
            </button>
              </>
            )}
          </nav>

          {/* Accessibility & Safety Badges */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-pressed={elderMode}
              onClick={() => setElderMode(!elderMode)}
              className={`inline-flex min-h-11 items-center gap-2 rounded-xl border px-3 text-sm font-bold transition-colors ${elderMode ? 'border-sky-300 bg-sky-300 text-slate-950' : 'border-slate-700 bg-slate-800 text-slate-100 hover:bg-slate-700'} ${elderMode ? 'min-h-12 sm:px-4' : ''}`}
            >
              <Accessibility className="h-5 w-5" aria-hidden="true" />
              <span className="hidden sm:inline">Elder Mode</span>
            </button>

            <details className="relative">
              <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-3 text-sm font-semibold text-slate-100 hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-300">
                <Settings2 className="h-5 w-5" aria-hidden="true" />
                <span className="hidden lg:inline">Accessibility</span>
              </summary>
              <div role="region" aria-label="Accessibility settings" className="absolute right-0 z-50 mt-2 w-[min(22rem,calc(100vw-2rem))] space-y-5 rounded-2xl border border-slate-600 bg-slate-900 p-5 shadow-2xl">
                <div>
                  <h2 className="flex items-center gap-2 text-sm font-bold text-white"><Type className="h-4 w-4" /> Text size</h2>
                  <div className="mt-2 grid grid-cols-3 gap-2" role="group" aria-label="Text size">
                    {(['normal', 'large', 'xlarge'] as const).map(size => (
                      <button key={size} type="button" aria-pressed={fontSize === size} onClick={() => setFontSize(size)} className={`min-h-11 rounded-lg border px-2 text-sm font-semibold capitalize ${fontSize === size ? 'border-sky-300 bg-sky-300/15 text-sky-100' : 'border-slate-700 bg-slate-800 text-slate-200'}`}>
                        {size === 'xlarge' ? 'Extra large' : size}
                      </button>
                    ))}
                  </div>
                </div>
                <button type="button" aria-pressed={highContrast} onClick={() => setHighContrast(!highContrast)} className="flex min-h-11 w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-800 px-3 text-sm font-semibold text-white">
                  <span className="flex items-center gap-2"><Eye className="h-4 w-4" /> High contrast</span><span>{highContrast ? 'On' : 'Off'}</span>
                </button>
                <button type="button" aria-pressed={ttsEnabled} onClick={() => setTtsEnabled(!ttsEnabled)} className="flex min-h-11 w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-800 px-3 text-sm font-semibold text-white">
                  <span className="flex items-center gap-2"><Volume2 className="h-4 w-4" /> Voice</span><span>{ttsEnabled ? 'On' : 'Off'}</span>
                </button>
                <button type="button" aria-pressed={simplifiedLanguage} onClick={() => setSimplifiedLanguage(!simplifiedLanguage)} className="flex min-h-11 w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-800 px-3 text-sm font-semibold text-white">
                  <span>Simplified language</span><span>{simplifiedLanguage ? 'On' : 'Off'}</span>
                </button>
                <button type="button" aria-pressed={caregiverView} onClick={() => setCaregiverView(!caregiverView)} className="flex min-h-11 w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-800 px-3 text-sm font-semibold text-white">
                  <span>Caregiver view</span><span>{caregiverView ? 'On' : 'Off'}</span>
                </button>
                <div>
                  <h2 className="flex items-center gap-2 text-sm font-bold text-white"><Languages className="h-4 w-4" /> Language</h2>
                  {elderMode ? (
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      {([
                        ['en', 'English', 'Listen in English'],
                        ['kn', 'ಕನ್ನಡ', 'ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ'],
                        ['hi', 'हिन्दी', 'हिन्दी में सुनें'],
                        ['ta', 'தமிழ்', 'தமிழில் கேளுங்கள்'],
                      ] as const).map(([code, label, hint]) => (
                        <button key={code} type="button" aria-pressed={selectedLanguage === code} onClick={() => setSelectedLanguage(code)} className={`min-h-[4.5rem] rounded-xl border p-3 text-left ${selectedLanguage === code ? 'border-sky-300 bg-sky-300/15 text-white' : 'border-slate-700 bg-slate-800 text-slate-200'}`}>
                          <span className="block text-base font-bold">{label}</span><span className="mt-1 block text-xs text-slate-300">{hint}</span>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <select aria-label="Preferred language" value={selectedLanguage} onChange={event => setSelectedLanguage(event.target.value as ReadBackLanguage)} className="mt-2 min-h-11 w-full rounded-lg border border-slate-600 bg-slate-950 px-3 text-white">
                      <option value="en">English</option><option value="kn">ಕನ್ನಡ (Kannada)</option><option value="hi">हिन्दी (Hindi)</option><option value="ta">தமிழ் (Tamil)</option>
                    </select>
                  )}
                </div>
              </div>
            </details>

            {/* Privacy Shield Indicator */}
            <div title="ReadBack verifies generated explanations against extracted document facts." className="hidden md:flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1.5 text-[11px] font-medium text-emerald-200">
              <Lock className="h-3.5 w-3.5 text-emerald-400" />
              <span>Responsible AI &amp; Verification Active</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
