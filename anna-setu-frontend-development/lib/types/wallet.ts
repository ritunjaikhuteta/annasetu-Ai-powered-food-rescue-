/**
 * AnnaSetu — Wallet & Subscription Types
 */

export interface Wallet {
  id: string
  userId: string
  balance: number
  currency: 'INR'
  lastUpdated: string
}

export interface Transaction {
  id: string
  walletId: string
  type: 'credit' | 'debit' | 'payout' | 'refund'
  amount: number
  description: string
  referenceId?: string
  referenceType?: 'delivery' | 'subscription' | 'donation' | 'manual'
  status: 'PENDING' | 'COMPLETED' | 'FAILED'
  createdAt: string
}

export type SubscriptionPlan = 'starter' | 'business' | 'enterprise'
export type BillingCycle = 'monthly' | 'yearly'

export interface Subscription {
  id: string
  userId: string
  plan: SubscriptionPlan
  billingCycle: BillingCycle
  amount: number
  status: 'ACTIVE' | 'CANCELLED' | 'EXPIRED' | 'TRIAL'
  currentPeriodStart: string
  currentPeriodEnd: string
  createdAt: string
}
