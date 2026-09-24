/**
 * AnnaSetu — Core Domain Types
 *
 * Foundational types shared across all roles and modules.
 */

// ─── User & Roles ──────────────────────────────────────────

export type UserRole = 'donor' | 'receiver' | 'driver' | 'admin'

/** Roles available for public registration (admin is internal-only) */
export type AuthRole = Exclude<UserRole, 'admin'>

export interface Location {
  lat?: number
  lng?: number
  address: string
  city?: string
  state?: string
  postalCode?: string
}

export interface UserProfile {
  id: string
  full_name: string | null
  phone: string | null
  role: string
  is_active: boolean
  verification_status?: VerificationStatus
  created_at?: string
  updated_at?: string
}

export interface User {
  id: string
  name: string
  email: string
  phone: string
  role: UserRole
  verified: boolean
  verificationStatus: VerificationStatus
  location: Location
  avatar?: string
  createdAt: string
  updatedAt?: string
}

// ─── Verification ──────────────────────────────────────────

export type VerificationStatus =
  | 'PENDING'
  | 'UNDER_REVIEW'
  | 'VERIFIED'
  | 'REJECTED'
  | 'pending'
  | 'under_review'
  | 'verified'
  | 'rejected'

// ─── Food ──────────────────────────────────────────────────

export type FoodType = 'vegetarian' | 'non-vegetarian' | 'mixed'

export type FoodCategory =
  | 'cooked-meals'
  | 'rice-dal'
  | 'roti-sabzi'
  | 'fruits'
  | 'vegetables'
  | 'bakery'
  | 'dairy'
  | 'packaged-food'
  | 'chicken'
  | 'mutton'
  | 'fish-seafood'
  | 'egg-based'
  | 'other'

export type MealPeriod = 'breakfast' | 'lunch' | 'dinner' | 'snacks'

export type StorageCondition = 'ambient' | 'refrigerated' | 'frozen' | 'hot-held'

// ─── Vehicle ───────────────────────────────────────────────

export type VehicleType =
  | 'motorcycle'
  | 'scooter'
  | 'auto'
  | 'car'
  | 'van'
  | 'pickup'
  | 'small-truck'
  | 'truck'

export type OwnershipType = 'self-owned' | 'authorized'
