/**
 * AnnaSetu — Domain Types (Legacy re-export)
 *
 * This file re-exports from the organized types/ directory
 * to maintain backward compatibility with existing imports.
 *
 * New code should import from '@/lib/types/core', '@/lib/types/rescue', etc.
 */

export type { UserRole, AuthRole, User, Location, FoodType, FoodCategory, MealPeriod, VehicleType, VerificationStatus } from './types/core'
export type { DonationStatus, Donation, NeedStatus, NGONeed, DeliveryStatus, Delivery, HandoffVerification, FoodIntegrityCheck, DonationAllocation, Match, MatchStatus, RescuePriorityFactors } from './types/rescue'
export type { VerificationRecord, VerificationDocument } from './types/verification'
export type { ImpactMetrics, ImpactRecord, Certificate } from './types/impact'
export type { Wallet, Transaction, Subscription } from './types/wallet'
export type { Notification } from './types/notification'
export type { AuditLog } from './types/admin'
