/**
 * AnnaSetu — NGO Need API Client
 */

import { apiClient } from './client'

export type MealPeriod = 'BREAKFAST' | 'LUNCH' | 'DINNER' | 'SNACKS'
export type DietType = 'VEGETARIAN' | 'NON_VEGETARIAN' | 'MIXED'
export type NeedStatus = 'DRAFT' | 'ACTIVE' | 'PARTIALLY_FULFILLED' | 'FULFILLED' | 'CANCELLED' | 'EXPIRED'

export interface NeedResponse {
  id: string
  receiver_id: string
  meal_period: MealPeriod
  diet_type: DietType
  food_category_id: string
  required_quantity_kg: number
  minimum_quantity_kg: number
  remaining_quantity_kg: number
  receiving_capacity_kg: number
  required_by: string
  receiving_start_time: string
  receiving_end_time: string
  special_requirements?: string
  location_id: string
  status: NeedStatus
  created_at?: string
  updated_at?: string
}

export interface NeedCreatePayload {
  meal_period: MealPeriod
  diet_type: DietType
  food_category_id: string
  required_quantity_kg: number
  minimum_quantity_kg: number
  receiving_capacity_kg: number
  required_by: string
  receiving_start_time?: string
  receiving_end_time?: string
  special_requirements?: string
  location_id: string
}

export interface NeedUpdatePayload {
  meal_period?: MealPeriod
  diet_type?: DietType
  food_category_id?: string
  required_quantity_kg?: number
  minimum_quantity_kg?: number
  receiving_capacity_kg?: number
  required_by?: string
  receiving_start_time?: string
  receiving_end_time?: string
  special_requirements?: string
  location_id?: string
}

export const needApi = {
  /** Create a new NGO food need in DRAFT state */
  async createNeed(payload: NeedCreatePayload): Promise<NeedResponse> {
    return apiClient<NeedResponse>('/api/v1/needs', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /** List needs created by authenticated receiver */
  async listNeeds(status?: NeedStatus): Promise<NeedResponse[]> {
    const query = status ? `?status_filter=${status}` : ''
    return apiClient<NeedResponse[]>(`/api/v1/needs${query}`)
  },

  /** Get details of a specific need */
  async getNeed(needId: string): Promise<NeedResponse> {
    return apiClient<NeedResponse>(`/api/v1/needs/${needId}`)
  },

  /** Update an editable need */
  async updateNeed(needId: string, payload: NeedUpdatePayload): Promise<NeedResponse> {
    return apiClient<NeedResponse>(`/api/v1/needs/${needId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  /** Activate a draft need for surplus matching */
  async activateNeed(needId: string): Promise<NeedResponse> {
    return apiClient<NeedResponse>(`/api/v1/needs/${needId}/activate`, {
      method: 'POST',
    })
  },

  /** Cancel an active or draft need */
  async cancelNeed(needId: string): Promise<NeedResponse> {
    return apiClient<NeedResponse>(`/api/v1/needs/${needId}/cancel`, {
      method: 'POST',
    })
  },
}
