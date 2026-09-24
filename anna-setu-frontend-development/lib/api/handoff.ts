/**
 * AnnaSetu — Trust, Handoff Verification, Tamper Seals, and Evidence API Client
 */

import { apiClient } from './client'
import { Delivery } from './delivery'

export type HandoffType = 'PICKUP' | 'DELIVERY'

export type HandoffStatus =
  | 'PENDING'
  | 'VERIFIED'
  | 'EXPIRED'
  | 'FAILED'
  | 'MANUAL_REVIEW'

export type SealStatus =
  | 'NOT_RECORDED'
  | 'INTACT'
  | 'BROKEN'
  | 'MISSING'
  | 'DISPUTED'

export type EvidenceType =
  | 'PACKAGE_PHOTO'
  | 'SEAL_PHOTO'
  | 'LOCATION_PROOF'
  | 'OTHER'

export type ManualReviewStatus =
  | 'PENDING'
  | 'CLEARED'
  | 'REQUIRES_ACTION'
  | 'DISPUTED'

export interface OTPGenerationResponse {
  delivery_id: string
  stop_id?: string
  handoff_type: HandoffType
  otp: string
  expires_at: string
  message: string
}

export interface HandoffVerificationPayload {
  otp: string
  latitude: number
  longitude: number
  accuracy_meters?: number
}

export interface PickupEvidencePayload {
  package_image: string
  seal_image: string
  latitude?: number
  longitude?: number
  metadata?: Record<string, any>
}

export interface DeliveryEvidencePayload {
  package_image: string
  seal_image: string
  seal_condition?: SealStatus
  latitude?: number
  longitude?: number
  metadata?: Record<string, any>
}

export interface HandoffEvidence {
  id: string
  delivery_id: string
  stop_id?: string
  handoff_id?: string
  evidence_type: EvidenceType
  storage_path: string
  captured_by: string
  latitude?: number
  longitude?: number
  metadata?: Record<string, any>
  captured_at?: string
}

export interface FoodIntegrityCheck {
  id: string
  delivery_id: string
  stop_id?: string
  check_type: string
  pickup_image_path?: string
  delivery_image_path?: string
  seal_id?: string
  pickup_seal_status?: string
  delivery_seal_status?: string
  ai_integrity_score?: number
  tampering_signal: boolean
  ai_reason?: string
  manual_review_status: ManualReviewStatus
  reviewed_by?: string
  reviewed_at?: string
  created_at?: string
  updated_at?: string
}

export const handoffApi = {
  /**
   * Donor requests single-use pickup verification OTP to share with driver
   */
  async requestPickupOtp(deliveryId: string): Promise<OTPGenerationResponse> {
    return apiClient<OTPGenerationResponse>(`/api/v1/deliveries/${deliveryId}/pickup-otp`, {
      method: 'POST',
    })
  },

  /**
   * Assigned driver verifies pickup handoff using donor OTP with GPS proximity
   */
  async verifyPickup(
    deliveryId: string,
    payload: HandoffVerificationPayload
  ): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/verify-pickup`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Driver uploads package photo and applied tamper seal photo
   */
  async uploadPickupEvidence(
    deliveryId: string,
    payload: PickupEvidencePayload
  ): Promise<HandoffEvidence[]> {
    return apiClient<HandoffEvidence[]>(`/api/v1/deliveries/${deliveryId}/pickup-evidence`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Receiver requests single-use delivery stop OTP to share with driver
   */
  async requestDeliveryOtp(
    deliveryId: string,
    stopId: string
  ): Promise<OTPGenerationResponse> {
    return apiClient<OTPGenerationResponse>(
      `/api/v1/deliveries/${deliveryId}/stops/${stopId}/delivery-otp`,
      { method: 'POST' }
    )
  },

  /**
   * Driver verifies delivery stop using receiver OTP with GPS proximity and seal status
   */
  async verifyDelivery(
    deliveryId: string,
    stopId: string,
    payload: HandoffVerificationPayload,
    sealCondition: SealStatus = 'INTACT'
  ): Promise<Delivery> {
    const url = `/api/v1/deliveries/${deliveryId}/stops/${stopId}/verify-delivery?seal_condition=${sealCondition}`
    return apiClient<Delivery>(url, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Driver uploads delivery package and seal photos upon arrival at stop
   */
  async uploadDeliveryEvidence(
    deliveryId: string,
    stopId: string,
    payload: DeliveryEvidencePayload
  ): Promise<HandoffEvidence[]> {
    return apiClient<HandoffEvidence[]>(
      `/api/v1/deliveries/${deliveryId}/stops/${stopId}/delivery-evidence`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    )
  },

  /**
   * Retrieve access-controlled handoff evidence photos for authorized delivery participants
   */
  async getDeliveryEvidence(deliveryId: string): Promise<HandoffEvidence[]> {
    return apiClient<HandoffEvidence[]>(`/api/v1/deliveries/${deliveryId}/evidence`)
  },

  /**
   * Retrieve visual integrity check results for a delivery
   */
  async getIntegrityChecks(deliveryId: string): Promise<FoodIntegrityCheck[]> {
    return apiClient<FoodIntegrityCheck[]>(`/api/v1/integrity/deliveries/${deliveryId}`)
  },

  /**
   * Admin lists integrity checks requiring manual operational review
   */
  async listIntegrityReviews(
    status?: ManualReviewStatus
  ): Promise<FoodIntegrityCheck[]> {
    const query = status ? `?status=${status}` : ''
    return apiClient<FoodIntegrityCheck[]>(`/api/v1/integrity/reviews${query}`)
  },

  /**
   * Admin submits manual review outcome for an integrity check
   */
  async submitManualReview(
    checkId: string,
    reviewStatus: ManualReviewStatus,
    notes?: string
  ): Promise<FoodIntegrityCheck> {
    return apiClient<FoodIntegrityCheck>(`/api/v1/integrity/${checkId}/review`, {
      method: 'POST',
      body: JSON.stringify({ status: reviewStatus, notes }),
    })
  },
}
