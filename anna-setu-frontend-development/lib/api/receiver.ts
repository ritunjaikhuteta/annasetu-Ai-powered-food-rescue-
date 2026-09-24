/**
 * Receiver (NGO) API Client
 */

import { apiClient } from './client'
import { VerificationStatus } from '@/lib/types/core'

export interface ReceiverProfile {
  id: string
  user_id: string
  organization_name: string
  organization_type?: string
  registration_number?: string
  darpan_id?: string
  pan_number?: string
  contact_person_name?: string
  beneficiary_count?: number
  storage_capacity_liters?: number
  has_refrigeration?: boolean
  operating_hours?: Record<string, any>
  verification_status: VerificationStatus
  created_at?: string
  updated_at?: string
}

export interface ReceiverProfileUpdatePayload {
  organization_name?: string
  organization_type?: string
  registration_number?: string
  darpan_id?: string
  pan_number?: string
  contact_person_name?: string
  beneficiary_count?: number
  storage_capacity_liters?: number
  has_refrigeration?: boolean
  operating_hours?: Record<string, any>
}

export const receiverApi = {
  /**
   * Fetch receiver NGO profile
   */
  async getProfile(): Promise<ReceiverProfile> {
    return apiClient<ReceiverProfile>('/api/v1/receiver/profile')
  },

  /**
   * Update receiver NGO profile
   */
  async updateProfile(payload: ReceiverProfileUpdatePayload): Promise<ReceiverProfile> {
    return apiClient<ReceiverProfile>('/api/v1/receiver/profile', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
}
