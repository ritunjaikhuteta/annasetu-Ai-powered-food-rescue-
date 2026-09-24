/**
 * AnnaSetu — Rescue Matching API Client
 */

import { apiClient } from './client'

export type PriorityLabel = 'HIGH' | 'MEDIUM' | 'LOW'
export type MatchStatus = 'PROPOSED' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED'

export interface PriorityBreakdown {
  distance_km: number
  estimated_travel_minutes: number
  expiry_buffer_minutes: number
  fulfillment_percent: number
  capacity_available_kg: number
  route_feasible: boolean
  expiry_score: number
  eta_score: number
  distance_score: number
  fulfillment_score: number
  route_score: number
  priority_score: number
}

export interface MatchResponse {
  id: string
  donation_id: string
  need_id: string
  priority_score: number
  priority_label: PriorityLabel
  distance_km: number
  estimated_travel_minutes: number
  estimated_arrival_at: string
  expiry_buffer_minutes: number
  fulfillable_quantity_kg: number
  fulfillment_percent: number
  priority_breakdown: PriorityBreakdown
  explanation: string
  status: MatchStatus
  created_at?: string
  updated_at?: string
}

export const matchApi = {
  /** Generate matches for a posted donation */
  async generateMatches(donationId: string): Promise<MatchResponse[]> {
    return apiClient<MatchResponse[]>(`/api/v1/donations/${donationId}/generate-matches`, {
      method: 'POST',
    })
  },

  /** Get matches discovered for a donation */
  async getDonationMatches(donationId: string): Promise<MatchResponse[]> {
    return apiClient<MatchResponse[]>(`/api/v1/donations/${donationId}/matches`)
  },

  /** Get incoming matches for an NGO need */
  async getNeedMatches(needId: string): Promise<MatchResponse[]> {
    return apiClient<MatchResponse[]>(`/api/v1/needs/${needId}/matches`)
  },
}
