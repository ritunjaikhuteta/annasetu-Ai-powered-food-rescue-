/**
 * Profile API Client
 */

import { apiClient } from './client'
import { UserProfile } from '@/lib/types/core'

export interface ProfileUpdatePayload {
  full_name?: string
  phone?: string
}

export const profileApi = {
  /**
   * Fetch current user's profile
   */
  async getMyProfile(): Promise<UserProfile> {
    return apiClient<UserProfile>('/api/v1/me/profile')
  },

  /**
   * Update allowed profile fields
   */
  async updateMyProfile(payload: ProfileUpdatePayload): Promise<UserProfile> {
    return apiClient<UserProfile>('/api/v1/me/profile', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
}
