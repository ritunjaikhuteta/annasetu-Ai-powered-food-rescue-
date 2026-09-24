/**
 * Donor API Client
 */

import { apiClient } from './client'
import { VerificationStatus } from '@/lib/types/core'

export interface DonorProfile {
  id: string
  user_id: string
  business_name: string
  business_type?: string
  fssai_license_number?: string
  gstin?: string
  contact_person_name?: string
  pickup_instructions?: string
  operating_hours?: Record<string, any>
  verification_status: VerificationStatus
  subscription_plan?: string
  created_at?: string
  updated_at?: string
}

export interface DonorProfileUpdatePayload {
  business_name?: string
  business_type?: string
  fssai_license_number?: string
  gstin?: string
  contact_person_name?: string
  pickup_instructions?: string
  operating_hours?: Record<string, any>
}

export const donorApi = {
  /**
   * Fetch donor business profile
   */
  async getProfile(): Promise<DonorProfile> {
    return apiClient<DonorProfile>('/api/v1/donor/profile')
  },

  /**
   * Update donor business profile
   */
  async updateProfile(payload: DonorProfileUpdatePayload): Promise<DonorProfile> {
    return apiClient<DonorProfile>('/api/v1/donor/profile', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
}
