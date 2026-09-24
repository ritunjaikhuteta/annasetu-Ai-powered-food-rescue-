/**
 * Driver (Delivery Partner) API Client
 */

import { apiClient } from './client'
import { VerificationStatus } from '@/lib/types/core'

export interface DriverProfile {
  id: string
  user_id: string
  driving_license_number?: string
  vehicle_type?: string
  vehicle_number?: string
  vehicle_capacity_kg?: number
  has_refrigeration?: boolean
  is_online?: boolean
  current_latitude?: number
  current_longitude?: number
  verification_status: VerificationStatus
  created_at?: string
  updated_at?: string
}

export interface DriverProfileUpdatePayload {
  vehicle_type?: string
  vehicle_number?: string
  vehicle_capacity_kg?: number
  has_refrigeration?: boolean
  is_online?: boolean
  current_latitude?: number
  current_longitude?: number
}

export interface DriverLocationUpdatePayload {
  latitude: number
  longitude: number
  accuracy_meters?: number
}

export interface DriverLocationRecord {
  id: string
  driver_id: string
  latitude: number
  longitude: number
  accuracy_meters?: number
  recorded_at: string
}

export const driverApi = {
  /**
   * Fetch driver profile
   */
  async getProfile(): Promise<DriverProfile> {
    return apiClient<DriverProfile>('/api/v1/driver/profile')
  },

  /**
   * Update driver operational fields
   */
  async updateProfile(payload: DriverProfileUpdatePayload): Promise<DriverProfile> {
    return apiClient<DriverProfile>('/api/v1/driver/profile', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Submit driver live GPS telemetry
   */
  async updateLocation(payload: DriverLocationUpdatePayload): Promise<DriverLocationRecord> {
    return apiClient<DriverLocationRecord>('/api/v1/driver/location', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Fetch active and completed deliveries assigned to the authenticated driver
   */
  async getMyDeliveries(): Promise<any[]> {
    return apiClient<any[]>('/api/v1/driver/deliveries')
  },
}

