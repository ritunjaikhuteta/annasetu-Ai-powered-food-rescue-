/**
 * AnnaSetu — Verification Documents & Intelligence API Client
 */

import { apiClient } from './client'
import type { VerificationStatus } from './types'

export interface DocumentExtractionResult {
  document_id: string
  document_type: string
  fields: Record<string, any>
  confidence: number
  uncertainties: string[]
  method: string
  review_status: string
  stored_in_db: boolean
}

export interface DocumentConsistencyResponse {
  document_id: string
  overall_status: 'MATCH' | 'MISMATCH' | 'PARTIAL_MATCH' | 'NOT_CHECKED'
  is_expired: boolean
  review_recommendation: string
  details: Array<{
    field_name: string
    extracted_value?: string | null
    profile_value?: string | null
    status: string
    reason: string
  }>
  audit_note: string
}

export async function processVerificationDocument(
  documentId: string,
  ocrText?: string,
  documentType?: string
): Promise<DocumentExtractionResult> {
  return apiClient<DocumentExtractionResult>(`/api/v1/documents/${documentId}/process-ocr`, {
    method: 'POST',
    body: JSON.stringify({
      document_id: documentId,
      ocr_text: ocrText,
      document_type: documentType,
    }),
  })
}

export async function checkDocumentConsistency(
  documentId: string
): Promise<DocumentConsistencyResponse> {
  return apiClient<DocumentConsistencyResponse>(`/api/v1/documents/${documentId}/consistency-check`)
}
