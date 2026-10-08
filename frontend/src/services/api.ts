import {
  DocumentDetail,
  DocumentSummary,
  MedicalFact,
  VerificationResult,
  VerifiedNextStep,
  ProviderContact,
  DocumentComparisonResult,
  DashboardMetrics,
  EvaluationRunResponse
} from '../types';
import { FidelityFailureType, FidelitySimulationResponse } from '../types';

const API_BASE = '/api';

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getDocuments(): Promise<DocumentSummary[]> {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async getDocument(id: string): Promise<DocumentDetail> {
    const res = await fetch(`${API_BASE}/documents/${id}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Unable to load document (${res.status}).`);
    }
    return res.json();
  },

  async simulateFidelityFailure(id: string, failureType: FidelityFailureType): Promise<FidelitySimulationResponse> {
    const res = await fetch(`${API_BASE}/documents/${id}/simulate-ai-error`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ failure_type: failureType }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Simulation failed (${res.status}).`);
    }
    return res.json();
  },

  async loadFidelityLabDemo(fixture: 'cbc' | 'prescription' = 'cbc'): Promise<DocumentDetail> {
    return api.uploadDocument(undefined, fixture === 'cbc' ? 'fidelity_lab_cbc' : 'fidelity_lab_prescription');
  },

  async extractDocumentFacts(id: string): Promise<DocumentDetail> {
    const res = await fetch(`${API_BASE}/documents/${id}/extract`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Extraction failed (${res.status}).`);
    }
    await res.json();
    return api.getDocument(id);
  },

  async uploadDocument(file?: File, demoType?: string): Promise<DocumentDetail> {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    }
    if (demoType) {
      formData.append('demo_type', demoType);
    }

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async deleteDocument(id: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  },

  async confirmFacts(id: string, confirmedFacts: MedicalFact[]): Promise<DocumentDetail> {
    const res = await fetch(`${API_BASE}/documents/${id}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirmed_facts: confirmedFacts }),
    });
    if (!res.ok) throw new Error('Failed to confirm facts');
    return res.json();
  },

  async explainDocument(
    id: string,
    language: string = 'en',
    corruptForTesting?: string | null
  ): Promise<{
    document_id: string;
    language: string;
    explanation_text: string;
    summary_bullet_points: string[];
    term_definitions: Record<string, string>;
  }> {
    const res = await fetch(`${API_BASE}/documents/${id}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language,
        corrupt_for_testing: corruptForTesting || null,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Explanation failed');
    }
    return res.json();
  },

  async verifyDocument(id: string): Promise<VerificationResult> {
    const res = await fetch(`${API_BASE}/documents/${id}/verify`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Verification failed');
    }
    return res.json();
  },

  async getVerification(id: string): Promise<VerificationResult> {
    const res = await fetch(`${API_BASE}/documents/${id}/verification`);
    if (!res.ok) throw new Error('Failed to fetch verification');
    return res.json();
  },

  async getNextStep(id: string): Promise<VerifiedNextStep> {
    const res = await fetch(`${API_BASE}/documents/${id}/next-step`);
    if (!res.ok) throw new Error('Failed to fetch next step');
    return res.json();
  },

  async saveProvider(id: string, provider: ProviderContact): Promise<VerifiedNextStep> {
    const res = await fetch(`${API_BASE}/documents/${id}/provider`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(provider),
    });
    if (!res.ok) throw new Error('Failed to save provider');
    return res.json();
  },

  async compareDocuments(docIds: string[]): Promise<DocumentComparisonResult> {
    const res = await fetch(`${API_BASE}/documents/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(docIds),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Comparison failed');
    }
    return res.json();
  },

  async getTimeline(): Promise<Array<{ document_id: string; filename: string; date: string; values: Record<string, number> }>> {
    const res = await fetch(`${API_BASE}/documents/timeline`);
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
  },

  async getMetrics(): Promise<DashboardMetrics> {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  },

  async getEvaluationResults(): Promise<EvaluationRunResponse> {
    const res = await fetch(`${API_BASE}/evaluation/results`);
    if (!res.ok) throw new Error('Failed to fetch evaluation results');
    return res.json();
  },

  async runEvaluation(): Promise<EvaluationRunResponse> {
    const res = await fetch(`${API_BASE}/evaluation/run`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Evaluation benchmark execution failed');
    return res.json();
  },
};
