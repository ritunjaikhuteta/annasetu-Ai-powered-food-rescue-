/**
 * AnnaSetu — Donor Types
 *
 * Types specific to the donor role and UI.
 * DONOR_DATA has been moved to lib/mock-data/donor.ts.
 */
import type { Location } from './core'

// ─── Donor Profile ─────────────────────────────────────────

export interface DonorProfile {
  userId: string
  businessName: string
  businessType: 'restaurant' | 'caterer' | 'hotel' | 'supermarket' | 'corporate-cafeteria' | 'food-vendor' | 'other'
  gstin?: string
  fssaiNumber?: string
  authorizedPerson?: string
  pickupLocation: Location
  verified: boolean
}

// ─── Donor UI-Specific Types ───────────────────────────────

export type DonorStatus = 'Posted' | 'Matched' | 'Allocated' | 'Picked up' | 'In transit' | 'Delivered' | 'Expired' | 'Cancelled'
export type FoodKind = 'Vegetarian' | 'Non-Vegetarian'

export interface DonorReceiver {
  name: string
  quantity: number
  address: string
}

export interface DonorDonation {
  id: string
  name: string
  type: FoodKind
  category: string
  quantity: number
  unit: 'kg' | 'plates'
  status: DonorStatus
  createdAt: string
  deadline: string
  allocation: number
  receivers: DonorReceiver[]
  image: string
  description: string
  storage: string
  packaging: string
  preparation: string
  pickupAddress: string
  priority: number
  driver?: string
  vehicle?: string
  eta?: number
  distance?: number
}

export interface DonorNotification {
  id: string
  title: string
  body: string
  time: string
  urgency?: 'urgent' | 'success' | 'info'
}

export interface DonorReport {
  id: string
  type: string
  date: string
  status: 'Ready' | 'Preparing'
}

export interface DonorCertificate {
  milestone: number
  date?: string
  achieved: boolean
}

export interface DonorImpact {
  rescued: number
  meals: number
  co2: number
  rescues: number
  monthly: { month: string; rescued: number; meals: number }[]
}

export interface DonorData {
  businessName: string
  verified: boolean
  donation: DonorDonation
  donations: DonorDonation[]
  notifications: DonorNotification[]
  impact: DonorImpact
  reports: DonorReport[]
  certificates: DonorCertificate[]
}
