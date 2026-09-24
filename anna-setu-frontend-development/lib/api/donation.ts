/**
 * AnnaSetu — Surplus Food Donation API Client
 */

import { apiClient } from './client'
import type { DietType } from './need'

export type StorageCondition = 'ambient' | 'refrigerated' | 'frozen' | 'hot-held'
export type DonationStatus = 'DRAFT' | 'POSTED' | 'MATCHING' | 'MATCHED' | 'ALLOCATED' | 'CANCELLED' | 'EXPIRED'

export interface DonationResponse {
  id: string
  donor_id: string
  diet_type: DietType
  food_category_id: string
  declared_quantity_kg: number
  remaining_quantity_kg: number
  preparation_at: string
  available_from: string
  rescue_deadline: string
  storage_condition: StorageCondition
  packaging_type: string
  allergen_information?: string
  raw_description: string
  normalized_description?: string
  image_path?: string
  pickup_location_id: string
  status: DonationStatus
  created_at?: string
  updated_at?: string
}

export interface DonationCreatePayload {
  diet_type: DietType
  food_category_id: string
  declared_quantity_kg: number
  preparation_at: string
  available_from: string
  rescue_deadline: string
  storage_condition?: StorageCondition
  packaging_type: string
  allergen_information?: string
  raw_description: string
  normalized_description?: string
  image_path?: string
  pickup_location_id: string
}

export interface DonationUpdatePayload {
  diet_type?: DietType
  food_category_id?: string
  declared_quantity_kg?: number
  preparation_at?: string
  available_from?: string
  rescue_deadline?: string
  storage_condition?: StorageCondition
  packaging_type?: string
  allergen_information?: string
  raw_description?: string
  normalized_description?: string
  image_path?: string
  pickup_location_id?: string
}

export const donationApi = {
  /** Create a new surplus food donation in DRAFT status (min 5 kg) */
  async createDonation(payload: DonationCreatePayload): Promise<DonationResponse> {
    return apiClient<DonationResponse>('/api/v1/donations', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /** List donations owned by the donor */
  async listDonations(status?: DonationStatus): Promise<DonationResponse[]> {
    const query = status ? `?status_filter=${status}` : ''
    return apiClient<DonationResponse[]>(`/api/v1/donations${query}`)
  },

  /** Get specific donation details */
  async getDonation(donationId: string): Promise<DonationResponse> {
    return apiClient<DonationResponse>(`/api/v1/donations/${donationId}`)
  },

  /** Update editable donation details */
  async updateDonation(donationId: string, payload: DonationUpdatePayload): Promise<DonationResponse> {
    return apiClient<DonationResponse>(`/api/v1/donations/${donationId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  /** Post surplus food donation for matching */
  async postDonation(donationId: string): Promise<DonationResponse> {
    return apiClient<DonationResponse>(`/api/v1/donations/${donationId}/post`, {
      method: 'POST',
    })
  },

  /** Cancel donation */
  async cancelDonation(donationId: string): Promise<DonationResponse> {
    return apiClient<DonationResponse>(`/api/v1/donations/${donationId}/cancel`, {
      method: 'POST',
    })
  },
}
