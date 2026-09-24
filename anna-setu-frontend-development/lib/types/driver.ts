/**
 * AnnaSetu — Driver Types
 *
 * Types specific to the delivery partner role.
 */
import type { Location, OwnershipType, VehicleType } from './core'

export interface DriverProfile {
  userId: string
  fullName: string
  licenceNumber?: string
  licenceExpiry?: string
  vehicleType: VehicleType
  vehicleNumber?: string
  ownershipType: OwnershipType
  startingLocation: Location
  verified: boolean
  rating?: number
  totalTrips: number
}

/** Driver-side view of available/active jobs */
export interface DriverJob {
  id: string
  donorName: string
  pickupLocation: Location
  stops: DriverJobStop[]
  totalDistance: number
  estimatedDuration: number
  estimatedEarnings: number
  foodDescription: string
  quantity: number
  unit: 'kg' | 'plates'
  urgency: 'low' | 'medium' | 'high'
  expiresAt: string
  status: 'Available' | 'Accepted' | 'Pickup' | 'In transit' | 'Completed'
}

export interface DriverJobStop {
  order: number
  receiverName: string
  address: string
  quantity: number
  status: 'Pending' | 'In Progress' | 'Completed'
}

/** Driver earnings summary */
export interface DriverEarnings {
  today: number
  thisWeek: number
  thisMonth: number
  totalPaid: number
  pendingPayout: number
  history: DriverEarningEntry[]
}

export interface DriverEarningEntry {
  id: string
  deliveryId: string
  amount: number
  date: string
  status: 'Paid' | 'Pending'
}

/** Driver data for the UI */
export interface DriverData {
  name: string
  verified: boolean
  rating: number
  totalTrips: number
  vehicleType: string
  vehicleNumber: string
  activeJob?: DriverJob
  availableJobs: DriverJob[]
  earnings: DriverEarnings
  completedDeliveries: DriverJob[]
}
