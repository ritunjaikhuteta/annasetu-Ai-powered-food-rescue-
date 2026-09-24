/**
 * AnnaSetu — Donor Subscriptions & Entitlements API Client
 */

import { apiClient } from './client'

export type BillingCycle = 'MONTHLY' | 'YEARLY'

export type SubscriptionStatus =
  | 'TRIAL'
  | 'ACTIVE'
  | 'PAUSED'
  | 'EXPIRED'
  | 'CANCELLED'

export interface SubscriptionPlan {
  id: string
  name: string
  code: string
  monthly_price: number
  yearly_price: number
  currency: 'INR'
  features: Record<string, any>
  is_active: boolean
}

export interface Subscription {
  id: string
  user_id: string
  plan_id: string
  plan_name: string
  billing_cycle: BillingCycle
  amount: number
  status: SubscriptionStatus
  current_period_start: string
  current_period_end: string
  created_at?: string
  updated_at?: string
}

export interface SubscriptionCheckoutPayload {
  plan_id: string
  billing_cycle?: BillingCycle
}

export const subscriptionApi = {
  /**
   * List available subscription plans
   */
  async getPlans(): Promise<SubscriptionPlan[]> {
    return apiClient<SubscriptionPlan[]>('/api/v1/subscription-plans')
  },

  /**
   * Get active subscription for the authenticated donor
   */
  async getCurrentSubscription(): Promise<Subscription | null> {
    return apiClient<Subscription | null>('/api/v1/subscription')
  },

  /**
   * Subscribe to a plan (monthly or yearly)
   */
  async checkout(payload: SubscriptionCheckoutPayload): Promise<Subscription> {
    return apiClient<Subscription>('/api/v1/subscriptions/checkout', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Cancel active subscription
   */
  async cancel(): Promise<Subscription> {
    return apiClient<Subscription>('/api/v1/subscriptions/cancel', {
      method: 'POST',
    })
  },
}
