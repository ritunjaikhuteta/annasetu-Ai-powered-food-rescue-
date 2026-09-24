/**
 * AnnaSetu — Authoritative Backend API Data Types (FastAPI Models)
 */

export type UserRole = 'DONOR' | 'RECEIVER' | 'DRIVER' | 'ADMIN'

export type VerificationStatus = 'PENDING' | 'UNDER_REVIEW' | 'VERIFIED' | 'REJECTED'

export type DietType = 'VEGETARIAN' | 'NON_VEGETARIAN' | 'VEGAN' | 'MIXED'

export type MealPeriod = 'BREAKFAST' | 'LUNCH' | 'DINNER' | 'SNACKS'

export type StorageCondition = 'AMBIENT' | 'CHILLED' | 'FROZEN' | 'HOT'

export type PackagingType = 'SEALED_CONTAINERS' | 'FOIL_PACKS' | 'BULK_VESSELS' | 'INDIVIDUAL_TRAYS' | 'OTHER'

export type DonationStatus = 'DRAFT' | 'POSTED' | 'MATCHED' | 'PARTIALLY_ALLOCATED' | 'ALLOCATED' | 'COMPLETED' | 'CANCELLED' | 'EXPIRED'

export type NeedStatus = 'DRAFT' | 'ACTIVE' | 'PARTIALLY_FULFILLED' | 'FULFILLED' | 'CANCELLED' | 'EXPIRED'

export type MatchStatus = 'SUGGESTED' | 'ALLOCATED' | 'REJECTED' | 'EXPIRED'

export type AllocationStatus = 'RESERVED' | 'CONFIRMED' | 'IN_TRANSIT' | 'DELIVERED' | 'CANCELLED'

export type DeliveryStatus =
  | 'OPEN'
  | 'OFFERED'
  | 'ACCEPTED'
  | 'ASSIGNED'
  | 'ARRIVING_PICKUP'
  | 'PICKED_UP'
  | 'IN_TRANSIT'
  | 'AT_STOP'
  | 'DELIVERED'
  | 'FAILED_PICKUP'
  | 'FAILED_DELIVERY'
  | 'REASSIGNMENT_REQUIRED'
  | 'CANCELLED'

export type SealStatus = 'INTACT' | 'BROKEN' | 'MISSING' | 'DISPUTED'

export type ManualReviewStatus = 'PENDING' | 'CLEARED' | 'REQUIRES_ACTION' | 'DISPUTED'

export type TransactionType = 'CREDIT' | 'DEBIT' | 'TOPUP' | 'CHARGE' | 'PAYOUT' | 'REFUND' | 'PLATFORM_FEE' | 'ADJUSTMENT' | 'SUBSCRIPTION_PAYMENT'

export type TransactionStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | 'REVERSED'

export interface UserSummary {
  id: string
  full_name?: string | null
  email?: string | null
  phone?: string | null
  role: UserRole
  is_active: boolean
  verification_status?: VerificationStatus
  created_at?: string
  updated_at?: string
}

export interface MeResponse {
  user: {
    id: string
    email?: string
    phone?: string
    user_metadata?: Record<string, any>
  }
  role: UserRole
  profile: UserSummary
  verification_status: VerificationStatus
  is_verified: boolean
}

export interface DonationItem {
  id: string
  donor_id: string
  food_name: string
  description?: string | null
  food_category_id: string
  diet_type: DietType
  quantity_kg: number
  remaining_quantity_kg: number
  status: DonationStatus
  preparation_time?: string | null
  available_from: string
  rescue_deadline: string
  storage_condition?: StorageCondition | null
  packaging_type?: PackagingType | null
  pickup_location_id: string
  allergens?: string[]
  created_at: string
  updated_at: string
}

export interface DonationCreatePayload {
  food_name: string
  description?: string
  food_category_id: string
  diet_type: DietType
  quantity_kg: number
  preparation_time?: string
  available_from: string
  rescue_deadline: string
  storage_condition?: StorageCondition
  packaging_type?: PackagingType
  pickup_location_id?: string
  allergens?: string[]
}

export interface NeedItem {
  id: string
  receiver_id: string
  food_category_id: string
  diet_type: DietType
  required_quantity_kg: number
  remaining_quantity_kg: number
  minimum_quantity_kg: number
  capacity_kg: number
  status: NeedStatus
  meal_period: MealPeriod
  required_by: string
  receiving_window_start?: string | null
  receiving_window_end?: string | null
  location_id?: string | null
  special_instructions?: string | null
  created_at: string
  updated_at: string
}

export interface NeedCreatePayload {
  food_category_id: string
  diet_type: DietType
  required_quantity_kg: number
  minimum_quantity_kg?: number
  capacity_kg?: number
  meal_period: MealPeriod
  required_by: string
  receiving_window_start?: string
  receiving_window_end?: string
  location_id?: string
  special_instructions?: string
}

export interface MatchItem {
  id: string
  donation_id: string
  need_id: string
  priority_score: number
  priority_label: 'HIGH' | 'MEDIUM' | 'LOW'
  distance_km: number
  estimated_travel_minutes: number
  shelf_life_buffer_hours: number
  fulfillment_ratio: number
  route_feasibility_score: number
  status: MatchStatus
  explanation?: string | null
  created_at: string
}

export interface AllocationItem {
  id: string
  match_id: string
  donation_id: string
  need_id: string
  allocated_quantity_kg: number
  status: AllocationStatus
  delivery_id?: string | null
  created_at: string
  accepted_at?: string | null
  fulfilled_at?: string | null
}

export interface DeliveryItem {
  id: string
  donation_id: string
  driver_id?: string | null
  status: DeliveryStatus
  total_quantity_kg: number
  pickup_location_id: string
  vehicle_type?: string | null
  estimated_eta?: string | null
  actual_pickup_time?: string | null
  actual_delivery_time?: string | null
  handoff_status: string
  integrity_status: string
  created_at: string
  updated_at: string
}

export interface DeliveryStopItem {
  id: string
  delivery_id: string
  need_id: string
  stop_sequence: number
  dropoff_location_id: string
  allocated_quantity_kg: number
  status: 'PENDING' | 'ARRIVED' | 'COMPLETED' | 'FAILED'
  otp_verified: boolean
  handoff_status: string
  seal_id?: string | null
  seal_status?: SealStatus
  created_at: string
  updated_at: string
}

export interface DeliveryOfferItem {
  id: string
  delivery_id: string
  driver_id: string
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED'
  expires_at: string
  created_at: string
}

export interface WalletItem {
  id: string
  user_id: string
  balance: number
  reserved_balance: number
  available_balance: number
  currency: string
  is_frozen: boolean
}

export interface TransactionItem {
  id: string
  wallet_id: string
  type: TransactionType
  amount: number
  balance_after?: number | null
  status: TransactionStatus
  delivery_id?: string | null
  reference_id?: string | null
  description?: string | null
  created_at: string
  updated_at: string
}

export interface DeliveryPricingBreakdown {
  delivery_id: string
  distance_km: number
  estimated_minutes: number
  stop_count: number
  base_fare: number
  per_km_rate: number
  per_min_rate: number
  delivery_charge: number
  platform_fee_percent: number
  platform_fee: number
  ngo_total: number
  driver_payout: number
}

export interface SubscriptionPlanItem {
  id: string
  plan_code: string
  name: string
  description?: string | null
  price_monthly_inr: number
  price_yearly_inr: number
  features: string[]
  is_active: boolean
}

export interface SubscriptionItem {
  id: string
  user_id: string
  plan_id: string
  status: 'ACTIVE' | 'CANCELLED' | 'EXPIRED' | 'PAST_DUE'
  billing_cycle: 'MONTHLY' | 'YEARLY'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  plan?: SubscriptionPlanItem
}
