/**
 * Auth API Client
 */

import { apiClient } from './client'
import { VerificationStatus } from '@/lib/types/core'

export interface MeResponse {
  user: {
    id: string
    email?: string
    phone?: string
    user_metadata?: Record<string, any>
  }
  role: 'DONOR' | 'RECEIVER' | 'DRIVER' | 'ADMIN'
  profile: {
    id: string
    full_name?: string
    phone?: string
    role: string
    is_active: boolean
    created_at?: string
    updated_at?: string
  }
  verification_status: VerificationStatus
  is_verified: boolean
}

export const authApi = {
  /**
   * Get current authenticated user identity and authoritative profile from FastAPI
   */
  async getMe(): Promise<MeResponse> {
    return apiClient<MeResponse>('/api/v1/me')
  },
}
