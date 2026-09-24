/**
 * AnnaSetu — Payments, Pricing, and Delivery Settlement API Client
 */

import { apiClient } from './client'
import type { DeliveryPricingBreakdown } from './types'

export interface WalletReservationResponse {
  id: string
  wallet_id: string
  delivery_id: string
  amount: number
  status: 'RESERVED' | 'SETTLED' | 'CANCELLED'
  created_at: string
}

export interface PaymentRefundResponse {
  delivery_id: string
  refund_amount: number
  wallet_id: string
  refund_transaction_id: string
  status: string
}

/**
 * Calculates delivery pricing, 12% platform fee, and driver payout using backend Decimal arithmetic.
 */
export async function getDeliveryPricing(deliveryId: string): Promise<DeliveryPricingBreakdown> {
  return apiClient<DeliveryPricingBreakdown>(`/api/v1/pricing/delivery/${deliveryId}`)
}

/**
 * Reserves delivery charge and 12% platform fee from NGO wallet before delivery commitment.
 */
export async function reserveDeliveryFunds(deliveryId: string): Promise<WalletReservationResponse> {
  return apiClient<WalletReservationResponse>(`/api/v1/deliveries/${deliveryId}/reserve`, {
    method: 'POST',
  })
}

/**
 * Settles completed delivery mission, capturing NGO reserved funds, recording 12% platform fee, and crediting driver payout.
 */
export async function settleDeliveryMission(deliveryId: string): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>(`/api/v1/deliveries/${deliveryId}/settle`, {
    method: 'POST',
  })
}

/**
 * Admin refund for a settled delivery mission back to NGO wallet.
 */
export async function refundDeliveryMission(
  deliveryId: string,
  reason: string,
  amount?: number
): Promise<PaymentRefundResponse> {
  return apiClient<PaymentRefundResponse>(`/api/v1/deliveries/${deliveryId}/refund`, {
    method: 'POST',
    body: JSON.stringify({ reason, amount }),
  })
}
