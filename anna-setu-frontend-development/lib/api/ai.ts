/**
 * AnnaSetu — AI Assistance, Document OCR, and Operational Explanations API Client (Phase 16)
 *
 * IMPORTANT:
 * - AI results are suggestions only ("AI suggestion", "Extracted information", "Needs review").
 * - Deterministic backend rules remain authoritative for eligibility, matching, allocation, routing, pricing, payment, and verification.
 * - AI never independently approves or rejects verification, donations, or operations.
 */

import { apiClient } from './client'

export const AI_UI_LABELS = {
  SUGGESTION: 'AI suggestion',
  EXTRACTED_INFO: 'Extracted information',
  NEEDS_REVIEW: 'Needs review',
} as const

export interface ExtractedDocumentFields {
  document_type?: string | null
  document_number?: string | null
  holder_name?: string | null
  organization_name?: string | null
  vehicle_number?: string | null
  issue_date?: string | null
  expiry_date?: string | null
  issuing_authority?: string | null
  raw_snippet?: string | null
}

export interface DocumentExtractionResult {
  document_id: string
  document_type: string
  fields: ExtractedDocumentFields
  confidence: number
  uncertainties: string[]
  method: 'DETERMINISTIC' | 'AI_ASSISTED' | 'FALLBACK'
  review_status: 'EXTRACTED_SUCCESSFULLY' | 'EXTRACTION_UNCERTAIN' | 'DOCUMENT_MISMATCH' | 'EXPIRED_DOCUMENT' | 'MANUAL_REVIEW_REQUIRED'
  stored_in_db: boolean
}

export interface ConsistencyCheckDetail {
  field_name: string
  extracted_value?: string | null
  profile_value?: string | null
  status: 'MATCH' | 'MISMATCH' | 'PARTIAL_MATCH' | 'NOT_CHECKED'
  reason: string
}

export interface DocumentConsistencyResponse {
  document_id: string
  overall_status: 'MATCH' | 'MISMATCH' | 'PARTIAL_MATCH' | 'NOT_CHECKED'
  is_expired: boolean
  review_recommendation: string
  details: ConsistencyCheckDetail[]
  audit_note: string
}

export interface FoodNormalizationResponse {
  raw_description: string
  normalized_description: string
  possible_category?: string | null
  possible_diet_type?: string | null
  estimated_quantity_kg?: number | null
  meal_period?: string | null
  possible_allergens: string[]
  uncertainties: string[]
  is_ai_generated: boolean
}

export interface DonationAIAssistResponse {
  donation_id: string
  declared_quantity_kg: number
  normalized_description?: string | null
  category_suggestion?: string | null
  diet_suggestion?: string | null
  meal_period_suggestion?: string | null
  quantity_consistency_signal: 'CONSISTENT' | 'DISCREPANCY' | 'NOT_ESTIMATED'
  estimated_quantity_kg?: number | null
  missing_information_suggestions: string[]
  allergen_suggestions: string[]
  disclaimer: string
}

export interface NeedAIAssistResponse {
  need_id: string
  suggested_meal_period?: string | null
  suggested_diet_type?: string | null
  suggested_quantity_kg?: number | null
  special_requirements_suggestions: string[]
  uncertainties: string[]
  disclaimer: string
}

export interface ExplanationResponse {
  entity_id: string
  explanation_type: string
  explanation_text: string
  is_ai_generated: boolean
  facts: Record<string, any>
}

/**
 * Normalizes free-text food descriptions using deterministic parsing first, with AI fallback.
 */
export async function normalizeFoodDescription(
  raw_description: string
): Promise<FoodNormalizationResponse> {
  return apiClient<FoodNormalizationResponse>('/api/v1/ai/normalize-food', {
    method: 'POST',
    body: JSON.stringify({ raw_description }),
  })
}

/**
 * Retrieves AI-assisted suggestions for a surplus donation.
 * Note: Donor-declared quantity remains authoritative.
 */
export async function assistDonation(
  donation_id: string
): Promise<DonationAIAssistResponse> {
  return apiClient<DonationAIAssistResponse>(`/api/v1/donations/${donation_id}/ai-assist`, {
    method: 'POST',
  })
}

/**
 * Retrieves candidate suggestions for an NGO hunger relief need from free-text requirements.
 */
export async function assistNeed(
  need_id: string,
  free_text_requirement?: string
): Promise<NeedAIAssistResponse> {
  return apiClient<NeedAIAssistResponse>(`/api/v1/needs/${need_id}/ai-assist`, {
    method: 'POST',
    body: free_text_requirement ? JSON.stringify({ free_text_requirement }) : undefined,
  })
}

/**
 * Retrieves human-readable natural language explanation for a deterministic match priority score.
 */
export async function getMatchExplanation(
  match_id: string
): Promise<ExplanationResponse> {
  return apiClient<ExplanationResponse>(`/api/v1/matches/${match_id}/explanation`)
}

/**
 * Retrieves human-readable explanation for operational delivery status.
 */
export async function getDeliveryExplanation(
  delivery_id: string
): Promise<ExplanationResponse> {
  return apiClient<ExplanationResponse>(`/api/v1/deliveries/${delivery_id}/explanation`)
}

/**
 * Extracts candidate fields from verification document text/image and stores in verification_documents.extracted_data.
 */
export async function processVerificationDocument(
  document_id: string,
  ocr_text?: string,
  document_type?: string
): Promise<DocumentExtractionResult> {
  return apiClient<DocumentExtractionResult>(`/api/v1/documents/${document_id}/process-ocr`, {
    method: 'POST',
    body: JSON.stringify({
      document_id,
      ocr_text,
      document_type,
    }),
  })
}

/**
 * Performs deterministic consistency check between document candidates and registered entity/profile.
 */
export async function checkDocumentConsistency(
  document_id: string
): Promise<DocumentConsistencyResponse> {
  return apiClient<DocumentConsistencyResponse>(`/api/v1/documents/${document_id}/consistency-check`)
}

/**
 * Retrieves visual integrity analysis for a delivery (reusing Phase 14 integrity checks).
 */
export async function getIntegrityAnalysis(
  delivery_id: string
): Promise<any[]> {
  return apiClient<any[]>(`/api/v1/integrity/deliveries/${delivery_id}`)
}

/**
 * Retrieves human-readable environmental and meal impact explanation based on recorded data.
 */
export async function getImpactExplanation(
  entity_id: string,
  donation_id?: string
): Promise<ExplanationResponse> {
  const query = donation_id ? `?donation_id=${encodeURIComponent(donation_id)}` : ''
  return apiClient<ExplanationResponse>(`/api/v1/impact/${entity_id}/explanation${query}`)
}
