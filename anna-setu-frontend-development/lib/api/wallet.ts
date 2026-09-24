/**
 * AnnaSetu — Digital Wallet & Financial Ledger API Client
 */

import { apiClient } from './client'

export type TransactionType =
  | 'TOP_UP'
  | 'DELIVERY_CHARGE'
  | 'PLATFORM_FEE'
  | 'DRIVER_PAYOUT'
  | 'RESERVATION'
  | 'RESERVATION_RELEASE'
  | 'REFUND'
  | 'BONUS'
  | 'ADJUSTMENT'

export type TransactionStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | 'REVERSED'

export interface Wallet {
  id: string
  user_id: string
  owner_type: 'RECEIVER' | 'DRIVER' | 'DONOR' | 'ADMIN'
  balance: number
  reserved_balance: number
  available_balance: number
  currency: 'INR'
  created_at?: string
  updated_at?: string
}

export interface Transaction {
  id: string
  wallet_id: string
  user_id: string
  type: TransactionType
  amount: number
  currency: 'INR'
  status: TransactionStatus
  reference_id?: string
  reference_type?: string
  description: string
  created_at?: string
}

export interface WalletTopUpPayload {
  amount: number
  idempotency_key?: string
}

export interface WalletTopUpResponse {
  wallet_id: string
  amount: number
  new_balance: number
  transaction_id: string
  status: string
  payment_reference?: string
  message: string
}

export interface WalletReservationResponse {
  id: string
  wallet_id: string
  delivery_id: string
  reserved_amount: number
  status: string
  created_at?: string
}

export interface PaymentRefundPayload {
  reason: string
  amount?: number
}

export interface PaymentRefundResponse {
  refund_id: string
  delivery_id: string
  refund_amount: number
  wallet_id: string
  status: string
  message: string
}

export const walletApi = {
  /**
   * Fetch current user's digital wallet and available balance
   */
  async getWallet(): Promise<Wallet> {
    return apiClient<Wallet>('/api/v1/wallet')
  },

  /**
   * Retrieve auditable transaction ledger entries
   */
  async getTransactions(): Promise<Transaction[]> {
    return apiClient<Transaction[]>('/api/v1/wallet/transactions')
  },

  /**
   * Credit wallet balance via demo mode or payment gateway
   */
  async topUp(payload: WalletTopUpPayload): Promise<WalletTopUpResponse> {
    return apiClient<WalletTopUpResponse>('/api/v1/wallet/top-up', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Reserve delivery total (charge + 12% platform fee) before mission commitment
   */
  async reserveDelivery(deliveryId: string): Promise<WalletReservationResponse> {
    return apiClient<WalletReservationResponse>(`/api/v1/deliveries/${deliveryId}/reserve`, {
      method: 'POST',
    })
  },

  /**
   * Final settlement of completed delivery mission
   */
  async settleDelivery(deliveryId: string): Promise<any> {
    return apiClient<any>(`/api/v1/deliveries/${deliveryId}/settle`, {
      method: 'POST',
    })
  },

  /**
   * Administrative refund for settled delivery
   */
  async refundDelivery(
    deliveryId: string,
    payload: PaymentRefundPayload
  ): Promise<PaymentRefundResponse> {
    return apiClient<PaymentRefundResponse>(`/api/v1/deliveries/${deliveryId}/refund`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
