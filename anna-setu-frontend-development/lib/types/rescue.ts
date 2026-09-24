/**
 * AnnaSetu — Rescue Domain Types
 *
 * Donation, Need, Match, Allocation, Delivery — the core product flow.
 */
import type { FoodCategory, FoodType, Location, MealPeriod, StorageCondition } from './core'

// ─── Donation ──────────────────────────────────────────────

export type DonationStatus =
  | 'POSTED'
  | 'MATCHING'
  | 'MATCHED'
  | 'ALLOCATED'
  | 'DRIVER_ASSIGNED'
  | 'PICKUP_VERIFIED'
  | 'IN_TRANSIT'
  | 'DELIVERED'
  | 'EXPIRED'
  | 'CANCELLED'

export interface Donation {
  id: string
  donorId: string
  foodType: FoodType
  category: FoodCategory
  name: string
  description: string
  quantity: number
  unit: 'kg' | 'plates' | 'servings'
  preparationTime: string
  availableFrom: string
  deadline: string
  pickupLocation: Location
  storageCondition: StorageCondition
  storageInfo: string
  packaging: string
  allergenInfo?: string
  image?: string
  aiInsight?: FoodAIInsight
  status: DonationStatus
  priority?: number
  createdAt: string
  updatedAt?: string
}

export interface FoodAIInsight {
  foodDescription: string
  confidence: number
  estimatedQuantity: {
    min: number
    max: number
  }
  suggestedCategory?: FoodCategory
}

// ─── NGO Need ──────────────────────────────────────────────

export type NeedStatus =
  | 'OPEN'
  | 'MATCHING'
  | 'MATCHED'
  | 'PARTIALLY_FULFILLED'
  | 'FULFILLED'
  | 'EXPIRED'
  | 'CANCELLED'

export interface NGONeed {
  id: string
  receiverId: string
  mealPeriod: MealPeriod
  foodType: FoodType
  categories: FoodCategory[]
  requiredQuantity: number
  minimumQuantity: number
  requiredBy: string
  currentCapacity: number
  location: Location
  receivingHours: {
    open: string
    close: string
  }
  notes?: string
  status: NeedStatus
  createdAt: string
  updatedAt?: string
}

// ─── Match & Allocation ────────────────────────────────────

export type MatchStatus = 'PROPOSED' | 'CONFIRMED' | 'REJECTED' | 'EXPIRED'

export interface Match {
  id: string
  donationId: string
  needId: string
  score: number
  factors: RescuePriorityFactors
  status: MatchStatus
  createdAt: string
}

export interface RescuePriorityFactors {
  distance: number
  eta: number
  expiryBuffer: number
  quantityFulfillment: number
  capacity: number
  routeFeasibility: number
}

export interface DonationAllocation {
  id: string
  donationId: string
  receiverId: string
  receiverName: string
  receiverAddress: string
  quantity: number
  status: 'PENDING' | 'CONFIRMED' | 'PICKED_UP' | 'DELIVERED' | 'CANCELLED'
}

// ─── Delivery ──────────────────────────────────────────────

export type DeliveryStatus =
  | 'PENDING'
  | 'DRIVER_ASSIGNED'
  | 'PICKUP_IN_PROGRESS'
  | 'PICKUP_VERIFIED'
  | 'IN_TRANSIT'
  | 'DELIVERY_IN_PROGRESS'
  | 'DELIVERED'
  | 'FAILED'

export interface DeliveryStop {
  order: number
  type: 'pickup' | 'delivery'
  location: Location
  entityName: string
  entityId: string
  quantity: number
  status: 'PENDING' | 'ARRIVED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'SKIPPED'
  arrivedAt?: string
  completedAt?: string
}

export interface Delivery {
  id: string
  donationId: string
  driverId: string
  allocations: string[]  // allocation IDs
  status: DeliveryStatus
  stops: DeliveryStop[]
  route?: {
    distance: number
    estimatedDuration: number
    eta: number
  }
  pickupVerification?: HandoffVerification
  deliveryVerifications: HandoffVerification[]
  earnings?: number
  createdAt: string
  completedAt?: string
}

export interface HandoffVerification {
  type: 'pickup' | 'delivery'
  gpsVerified: boolean
  gpsLocation?: Location
  otpVerified: boolean
  otp?: string
  packageSealed: boolean
  packageImage?: string
  sealId?: string
  timestamp?: string
  notes?: string
}

export interface FoodIntegrityCheck {
  id: string
  deliveryId: string
  pickupImage?: string
  deliveryImage?: string
  sealIntact: boolean
  aiResult?: {
    discrepancyDetected: boolean
    confidence: number
    description: string
  }
  timestamp: string
}
