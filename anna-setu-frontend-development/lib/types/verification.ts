/**
 * AnnaSetu — Verification Types
 *
 * Types for identity, document, and business verification.
 */
import type { UserRole, VerificationStatus } from './core'

export interface VerificationDocument {
  id: string
  type: DocumentType
  label: string
  fileUrl?: string
  fileName?: string
  fileSize?: number
  verified: boolean
  verifiedAt?: string
  rejectionReason?: string
}

/** All possible document types across roles */
export type DocumentType =
  // Donor
  | 'gstin'
  | 'fssai_license'
  | 'business_registration'
  | 'authorized_person_id'
  // Receiver
  | 'registration_certificate'
  | 'government_document'
  | 'ngo_darpan'
  | 'representative_id'
  | 'pan'
  // Driver
  | 'identity_document'
  | 'driving_licence'
  | 'vehicle_rc'
  | 'vehicle_insurance'
  | 'puc_certificate'
  | 'fitness_permit'
  | 'vehicle_authorization'

export interface VerificationRecord {
  id: string
  userId: string
  role: UserRole
  status: VerificationStatus
  documents: VerificationDocument[]
  submittedAt: string
  reviewedAt?: string
  reviewedBy?: string
  notes?: string
  rejectionReason?: string
}
