/**
 * AnnaSetu — Impact Types
 *
 * Types for tracking and displaying rescue impact.
 */

export interface ImpactRecord {
  id: string
  donationId: string
  deliveryId: string
  foodRescuedKg: number
  mealEquivalents: number
  co2eAvoidedKg: number
  beneficiaries: number
  recordedAt: string
}

export interface ImpactFactor {
  label: string
  value: number
  unit: string
  methodology?: string
}

export interface ImpactMetrics {
  foodRescued: number
  mealsEquivalent: number
  co2Saved: number
  money: number
  beneficiaries: number
}

export interface Certificate {
  id: string
  userId: string
  milestoneKg: number
  achievedAt?: string
  achieved: boolean
  certificateUrl?: string
}
