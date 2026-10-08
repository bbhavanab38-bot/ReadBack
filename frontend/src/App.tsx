import React, { useRef, useState } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardView } from './pages/DashboardView';
import { DocumentAnalyzerView } from './pages/DocumentAnalyzerView';
import { DocumentComparisonView } from './pages/DocumentComparisonView';
import { EvaluationDashboardView } from './pages/EvaluationDashboardView';
import { FidelityLab } from './pages/FidelityLab';
import { DocumentDetail } from './types';
import { api } from './services/api';
import { useAccessibilityPreferences } from './hooks/useAccessibilityPreferences';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analyze' | 'compare' | 'fidelity' | 'evaluation'>('dashboard');
  const [currentDocument, setCurrentDocument] = useState<DocumentDetail | null>(null);
  const [workflowStep, setWorkflowStep] = useState(1);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [documentLoadError, setDocumentLoadError] = useState(false);
  const documentRequestSequence = useRef(0);

  const [accessibility, setAccessibility] = useAccessibilityPreferences();
  const elderMode = accessibility.elderMode;
  const highContrast = elderMode || accessibility.highContrast;
  const fontSize = elderMode ? 'xlarge' : accessibility.fontSize;
  const updateAccessibility = <K extends keyof typeof accessibility>(key: K, value: (typeof accessibility)[K]) => {
    setAccessibility(current => ({ ...current, [key]: value }));
  };

  const handleSelectDocument = async (documentId: string) => {
    const requestSequence = ++documentRequestSequence.current;
    setSelectedDocumentId(documentId);
    setCurrentDocument(null);
    setDocumentLoadError(false);
    setDocumentLoading(true);
    setWorkflowStep(2);
    setActiveTab('analyze');

    try {
      const document = await api.getDocument(documentId);
      if (requestSequence !== documentRequestSequence.current) return;
      if (document.id !== documentId) throw new Error('The document response did not match the selected ID.');
      setCurrentDocument(document);
      const status = document.verification_result?.overall_status;
      setWorkflowStep(status === 'VERIFIED' || status === 'BLOCKED' ? 4 : 2);
    } catch (error) {
      if (requestSequence !== documentRequestSequence.current) return;
      console.error(`Unable to load selected document ${documentId}:`, error);
      setDocumentLoadError(true);
    } finally {
      if (requestSequence === documentRequestSequence.current) setDocumentLoading(false);
    }
  };

  const handleRetryDocumentLoad = () => {
    if (selectedDocumentId) void handleSelectDocument(selectedDocumentId);
  };

  const handleStartAnalysis = () => {
    documentRequestSequence.current += 1;
    setSelectedDocumentId(null);
    setCurrentDocument(null);
    setDocumentLoadError(false);
    setDocumentLoading(false);
    setWorkflowStep(1);
    setActiveTab('analyze');
  };

  const handleLoadDemo = async (demoType: string) => {
    try {
      const doc = await api.uploadDocument(undefined, demoType);
      documentRequestSequence.current += 1;
      setSelectedDocumentId(doc.id);
      setCurrentDocument(doc);
      setDocumentLoadError(false);
      setDocumentLoading(false);
      setWorkflowStep(2);
      setActiveTab('analyze');
    } catch (err) {
      console.error('Failed to load demo:', err);
    }
  };

  // Font sizing style mapping
  const fontSizeClass = fontSize === 'large' 
    ? 'text-lg' 
    : fontSize === 'xlarge' 
    ? 'text-xl' 
    : 'text-sm';

  return (
    <div className={`min-h-screen flex flex-col transition-colors ${
      elderMode
        ? 'elder-mode bg-slate-950 text-white'
        : highContrast
          ? 'bg-black text-yellow-300'
          : 'bg-slate-950 text-slate-100'
    } ${fontSizeClass}`}>
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        workflowStep={workflowStep}
        setWorkflowStep={setWorkflowStep}
        hasDocument={!!currentDocument}
        verified={currentDocument?.verification_result?.overall_status === 'VERIFIED'}
        highContrast={accessibility.highContrast}
        setHighContrast={(value) => updateAccessibility('highContrast', value)}
        fontSize={fontSize}
        setFontSize={(value) => updateAccessibility('fontSize', value)}
        elderMode={elderMode}
        setElderMode={(value) => updateAccessibility('elderMode', value)}
        ttsEnabled={accessibility.ttsEnabled}
        setTtsEnabled={(value) => updateAccessibility('ttsEnabled', value)}
        simplifiedLanguage={accessibility.simplifiedLanguage}
        setSimplifiedLanguage={(value) => updateAccessibility('simplifiedLanguage', value)}
        caregiverView={accessibility.caregiverView}
        setCaregiverView={(value) => updateAccessibility('caregiverView', value)}
        selectedLanguage={accessibility.language}
        setSelectedLanguage={(value) => updateAccessibility('language', value)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Dynamic Page Views */}
        {activeTab === 'dashboard' && (
          <DashboardView
            onSelectDocument={handleSelectDocument}
            onStartAnalysis={handleStartAnalysis}
            onLoadDemo={handleLoadDemo}
            onOpenFidelityLab={() => setActiveTab('fidelity')}
            onTryElderMode={() => {
              updateAccessibility('elderMode', true);
              updateAccessibility('simplifiedLanguage', true);
              setActiveTab('analyze');
              setWorkflowStep(1);
            }}
          />
        )}

        {activeTab === 'analyze' && (
          <DocumentAnalyzerView
            currentDocument={currentDocument}
            setCurrentDocument={setCurrentDocument}
            documentLoading={documentLoading}
            documentLoadError={documentLoadError}
            onRetryDocumentLoad={handleRetryDocumentLoad}
            elderMode={elderMode}
            ttsEnabled={accessibility.ttsEnabled}
            simplifiedLanguage={accessibility.simplifiedLanguage}
            caregiverView={accessibility.caregiverView}
            selectedLanguage={accessibility.language}
            setSelectedLanguage={(value) => updateAccessibility('language', value)}
            step={workflowStep}
            setStep={setWorkflowStep}
            onBackToDashboard={() => setActiveTab('dashboard')}
          />
        )}

        {activeTab === 'compare' && (
          <DocumentComparisonView />
        )}

        {activeTab === 'fidelity' && (
          <FidelityLab onBackToOverview={() => setActiveTab('dashboard')} />
        )}

        {activeTab === 'evaluation' && (
          <EvaluationDashboardView />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>
            <strong>ReadBack</strong> — AI-Powered Medical Document Understanding, Fidelity Verification & Care Navigation.
          </p>
          <p className="text-[11px] text-slate-600">
            Research & Educational Prototype • Field-Level Fidelity Engine • Privacy-Conscious
          </p>
        </div>
      </footer>
    </div>
  );
};
