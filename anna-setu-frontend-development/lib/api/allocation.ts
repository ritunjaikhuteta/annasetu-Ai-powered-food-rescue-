/**
 * AnnaSetu — Donation Allocation API Client
 */

import { apiClient } from './client'

export type AllocationStatus = 'RESERVED' | 'ACCEPTED' | 'RELEASED' | 'FULFILLED' | 'CANCELLED'

export interface AllocationCreatePayload {
  donation_id: string
  need_id: string
  match_id?: string
  allocated_quantity_kg: number
}

export interface AllocationResponse {
  id: string
  donation_id: string
  need_id: string
  match_id?: string
  allocated_quantity_kg: number
  status: AllocationStatus
  created_at?: string
  updated_at?: string
}

export const allocationApi = {
  /** Atomically commit a portion of a donation to an active NGO need */
  async createAllocation(payload: AllocationCreatePayload): Promise<AllocationResponse> {
    return apiClient<AllocationResponse>('/api/v1/allocations', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
