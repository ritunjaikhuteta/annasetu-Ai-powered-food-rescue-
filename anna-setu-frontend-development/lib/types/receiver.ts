/**
 * AnnaSetu — Receiver Types
 *
 * Types specific to the receiver (NGO/organization) role.
 */
import type { FoodCategory, FoodType, Location } from './core'

export interface ReceiverProfile {
  userId: string
  organizationName: string
  registrationNumber?: string
  ngoDarpanId?: string
  pan?: string
  organizationAddress: Location
  receivingLocation: Location
  receivingHours: {
    open: string
    close: string
  }
  acceptedFoodTypes: FoodType[]
  acceptedCategories: FoodCategory[]
  currentCapacity: number
  verified: boolean
}

/** Receiver-side view of an incoming delivery */
export interface ReceiverDelivery {
  id: string
  donorName: string
  foodName: string
  quantity: number
  unit: 'kg' | 'plates'
  driverName: string
  status: 'Arriving' | 'Arrived' | 'Received'
  eta?: number
  arrivalTime?: string
}

/** Receiver data for the UI */
export interface ReceiverData {
  organizationName: string
  verified: boolean
  openCapacity: number
  activeNeeds: ReceiverNeedSummary[]
  incomingDeliveries: ReceiverDelivery[]
  receivedHistory: ReceiverDelivery[]
  impact: {
    mealsReceived: number
    totalQuantity: number
    deliveriesCompleted: number
    monthly: { month: string; received: number; meals: number }[]
  }
}

export interface ReceiverNeedSummary {
  id: string
  mealPeriod: string
  foodType: string
  quantity: number
  requiredBy: string
  status: 'Open' | 'Matched' | 'Fulfilled' | 'Expired'
}

export type ReceiverNeed = ReceiverNeedSummary
