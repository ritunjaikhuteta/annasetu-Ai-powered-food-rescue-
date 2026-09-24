/**
 * AnnaSetu — Auth Types
 *
 * Types specific to the authentication flow.
 * VerificationStatus and UserProfile are imported from the central types.
 */
import type { AuthRole, VerificationStatus, UserProfile } from '@/lib/types/core'

export type { AuthRole, VerificationStatus, UserProfile } from '@/lib/types/core'

export type AuthMode = 'login' | 'register'

export interface AuthResult {
  ok: boolean
  message: string
  redirect?: string
  verificationStatus?: VerificationStatus
  requiresEmailConfirmation?: boolean
  profile?: UserProfile
}

export interface RegisterPayload {
  email: string
  password: string
  fullName: string
  phone: string
  // Donor specific
  businessName?: string
  businessType?: string
  gstin?: string
  fssaiNumber?: string
  pickupAddress?: string
  // Receiver specific
  organizationName?: string
  registrationNumber?: string
  ngoDarpanId?: string
  pan?: string
  receivingAddress?: string
  acceptedFoodType?: string
  acceptedCategories?: string[]
  // Driver specific
  licenceNumber?: string
  licenceExpiry?: string
  vehicleType?: string
  vehicleNumber?: string
  ownershipType?: string
  startingAddress?: string
  city?: string
  state?: string
  postalCode?: string
}

export const roleMeta: Record<AuthRole, { label: string; shortLabel: string; description: string }> = {
  donor: {
    label: 'Donor',
    shortLabel: 'Share surplus food',
    description: 'Restaurants, caterers, hotels, supermarkets, and food businesses.',
  },
  receiver: {
    label: 'Receiver',
    shortLabel: 'Raise a food need',
    description: 'NGOs and community organizations serving people nearby.',
  },
  driver: {
    label: 'Delivery partner',
    shortLabel: 'Deliver food where it matters',
    description: 'People who can move safe food from a donor to a receiver.',
  },
}

export const rolePath = (role: AuthRole) => `/auth/${role}`
export const dashboardPath = (role: AuthRole) =>
  role === 'driver' ? '/driver/dashboard' : `/${role}/dashboard`
export const isAuthRole = (value: string): value is AuthRole =>
  value === 'donor' || value === 'receiver' || value === 'driver'
