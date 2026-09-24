/**
 * AnnaSetu — Delivery Pricing & Fee Breakdown API Client
 */

import { apiClient } from './client'

export interface DeliveryPricing {
  delivery_id: string
  base_fare: number
  distance_km: number
  distance_charge: number
  duration_minutes: number
  time_charge: number
  stop_count: number
  stop_fees: number
  delivery_charge: number
  platform_fee_percent: number
  platform_fee: number
  ngo_total: number
  driver_payout: number
  currency: 'INR'
}

export const pricingApi = {
  /**
   * Calculate exact pricing breakdown for a delivery mission
   */
  async getDeliveryPricing(deliveryId: string): Promise<DeliveryPricing> {
    return apiClient<DeliveryPricing>(`/api/v1/pricing/delivery/${deliveryId}`)
  },
}
