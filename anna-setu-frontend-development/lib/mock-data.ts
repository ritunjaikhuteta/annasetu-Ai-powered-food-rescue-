/**
 * AnnaSetu — Canonical Mock Data
 *
 * ONE coherent demo dataset. All screens reference the same rescue scenario.
 *
 * SCENARIO (Phase 19 — Golden Demo):
 * - DONOR: Green Leaf Catering (Sector 17, Gurugram)
 * - DONATION: 40 kg vegetarian cooked meals
 * - RECEIVERS:
 *     · Seva Community Kitchen — 20 kg need · 12 kg allocated
 *     · Anna Sadan Charitable Trust — 15 kg need · 8 kg allocated
 *     · Sahara Community Home — 18 kg allocated (compatible 3rd stop)
 * - DRIVER: Arjun Sharma, Insulated Van DL 12 CA 4455
 * - DELIVERY: 3 stops, 9.1 km · IN_TRANSIT · Pickup verified, Stop 2 next
 *
 * Matches backend/services/demo_service.py canonical seed.
 * Namespace-tagged for safe reset when DEMO_MODE=true.
 */

import type { User, Location } from '@/lib/types/core'
import type { Donation, NGONeed, Delivery, DonationAllocation, Match, HandoffVerification, FoodIntegrityCheck } from '@/lib/types/rescue'
import type { VerificationRecord } from '@/lib/types/verification'
import type { ImpactMetrics } from '@/lib/types/impact'

// ─── Canonical Locations (matches Gurugram demo seed) ─────

export const LOCATIONS = {
  greenLeafCatering: {
    lat: 28.4660,
    lng: 77.0328,
    address: '14 Sector 17, Gurugram, Haryana',
    city: 'Gurugram',
    state: 'Haryana',
    postalCode: '122001',
  } satisfies Location,
  sevaCommunity: {
    lat: 28.4595,
    lng: 77.0665,
    address: 'Community Hall, Sector 29, Gurugram, Haryana',
    city: 'Gurugram',
    state: 'Haryana',
    postalCode: '122001',
  } satisfies Location,
  annaSadan: {
    lat: 28.4730,
    lng: 77.0015,
    address: 'Old Delhi Road, Sector 12, Gurugram, Haryana',
    city: 'Gurugram',
    state: 'Haryana',
    postalCode: '122001',
  } satisfies Location,
  saharaCommunity: {
    lat: 28.4510,
    lng: 77.0885,
    address: 'Sector 46, Near Leisure Valley, Gurugram, Haryana',
    city: 'Gurugram',
    state: 'Haryana',
    postalCode: '122003',
  } satisfies Location,
  driverHome: {
    lat: 28.6139,
    lng: 77.2090,
    address: 'Central Delhi Base',
    city: 'New Delhi',
    state: 'Delhi',
    postalCode: '110001',
  } satisfies Location,
} as const

// ─── Mock Users ────────────────────────────────────────────

export const MOCK_DONOR: User = {
  id: 'demo_donor_green_leaf',
  name: 'Green Leaf Catering',
  email: 'operations@greenleafcatering.demo',
  role: 'donor',
  verified: true,
  verificationStatus: 'VERIFIED',
  phone: '+91-98765-00001',
  location: LOCATIONS.greenLeafCatering,
  avatar: '/placeholder-user.jpg',
  createdAt: '2024-01-10T10:00:00Z',
}

export const MOCK_RECEIVER: User = {
  id: 'demo_receiver_seva_kitchen',
  name: 'Seva Community Kitchen',
  email: 'team@sevakitchen.demo',
  role: 'receiver',
  verified: true,
  verificationStatus: 'VERIFIED',
  phone: '+91-98765-00002',
  location: LOCATIONS.sevaCommunity,
  avatar: '/placeholder-user.jpg',
  createdAt: '2024-01-12T10:00:00Z',
}

export const MOCK_RECEIVER_B: User = {
  id: 'demo_receiver_anna_sadan',
  name: 'Anna Sadan Charitable Trust',
  email: 'trust@annasadan.demo',
  role: 'receiver',
  verified: true,
  verificationStatus: 'VERIFIED',
  phone: '+91-98765-00003',
  location: LOCATIONS.annaSadan,
  createdAt: '2024-02-05T10:00:00Z',
}

export const MOCK_RECEIVER_C: User = {
  id: 'demo_receiver_sahara',
  name: 'Sahara Community Home',
  email: 'info@saharacommunity.demo',
  role: 'receiver',
  verified: true,
  verificationStatus: 'VERIFIED',
  phone: '+91-98765-00005',
  location: LOCATIONS.saharaCommunity,
  createdAt: '2024-03-01T10:00:00Z',
}

export const MOCK_DRIVER: User = {
  id: 'demo_driver_arjun_sharma',
  name: 'Arjun Sharma',
  email: 'arjun.delivery@annasetu.demo',
  role: 'driver',
  verified: true,
  verificationStatus: 'VERIFIED',
  phone: '+91-98765-00004',
  location: LOCATIONS.driverHome,
  avatar: '/placeholder-user.jpg',
  createdAt: '2024-02-01T10:00:00Z',
}

export const MOCK_ADMIN: User = {
  id: 'demo_admin_ops',
  name: 'AnnaSetu Demo Admin',
  email: 'demo-admin@annasetu.demo',
  role: 'admin',
  verified: true,
  verificationStatus: 'VERIFIED',
  phone: '+91-98765-00009',
  location: { lat: 28.6139, lng: 77.2090, address: 'Operations Center, New Delhi' },
  createdAt: '2024-01-01T10:00:00Z',
}

// ─── Canonical Donation (40 kg · 20 allocated · 20 remaining) ──

export const MOCK_DONATION: Donation = {
  id: 'AS-GL-0001',
  donorId: MOCK_DONOR.id,
  foodType: 'vegetarian',
  category: 'cooked-meals',
  name: 'Vegetarian Cooked Meals',
  description: 'Freshly prepared North Indian thali — roti, dal, sabzi, rice. Refrigerated pickup available from 2:15 PM.',
  quantity: 40,
  unit: 'kg',
  preparationTime: 'Today, 2:00 PM',
  availableFrom: 'Today, 2:15 PM',
  deadline: 'Today, 6:00 PM',
  pickupLocation: LOCATIONS.greenLeafCatering,
  storageCondition: 'refrigerated',
  storageInfo: 'Insulated containers · 4 °C',
  packaging: 'Sealed food-grade stainless steel containers',
  allergenInfo: 'Contains dairy, wheat, mustard oil. Verify before serving.',
  image: '/placeholder.jpg',
  aiInsight: {
    foodDescription: 'Cooked rice + vegetables + roti',
    confidence: 94,
    estimatedQuantity: { min: 28, max: 42 },
    suggestedCategory: 'cooked-meals',
  },
  status: 'IN_TRANSIT',
  priority: 94,
  createdAt: 'Today, 2:10 PM',
}

// ─── Canonical Need (Seva Community: 20 kg lunch need) ─────

export const MOCK_NEED: NGONeed = {
  id: 'need-seva-001',
  receiverId: MOCK_RECEIVER.id,
  mealPeriod: 'lunch',
  foodType: 'vegetarian',
  categories: ['cooked-meals'],
  requiredQuantity: 20,
  minimumQuantity: 10,
  requiredBy: 'Today, 8:00 PM',
  currentCapacity: 30,
  location: LOCATIONS.sevaCommunity,
  receivingHours: { open: '18:00', close: '20:00' },
  status: 'PARTIALLY_FULFILLED',
  createdAt: 'Today, 1:50 PM',
}

// ─── Canonical Allocation — 12 + 8 + 20? wait → consistent with 40 kg
// Allocation breakdown that sums to 40 (12 + 8 + 20 = 40):
//   Seva Community Kitchen: 12 kg of 20 kg need (partially fulfilled)
//   Anna Sadan: 8 kg of 15 kg need
//   Sahara Community: 20 kg (3rd stop)
// ──────────────────────────────────────────────────────────

export const MOCK_ALLOCATIONS: DonationAllocation[] = [
  { id: 'alloc-seva', donationId: MOCK_DONATION.id, receiverId: MOCK_RECEIVER.id, receiverName: 'Seva Community Kitchen', receiverAddress: LOCATIONS.sevaCommunity.address, quantity: 12, status: 'CONFIRMED' },
  { id: 'alloc-anna', donationId: MOCK_DONATION.id, receiverId: MOCK_RECEIVER_B.id, receiverName: 'Anna Sadan Charitable Trust', receiverAddress: LOCATIONS.annaSadan.address, quantity: 8, status: 'CONFIRMED' },
  { id: 'alloc-sahara', donationId: MOCK_DONATION.id, receiverId: MOCK_RECEIVER_C.id, receiverName: 'Sahara Community Home', receiverAddress: LOCATIONS.saharaCommunity.address, quantity: 20, status: 'CONFIRMED' },
]

// ─── Canonical Delivery ────────────────────────────────────

export const MOCK_DELIVERY: Delivery = {
  id: 'demo_del_001',
  donationId: MOCK_DONATION.id,
  driverId: MOCK_DRIVER.id,
  allocations: MOCK_ALLOCATIONS.map(a => a.id),
  status: 'IN_TRANSIT',
  stops: [
    { order: 1, type: 'pickup', location: LOCATIONS.greenLeafCatering, entityName: 'Green Leaf Catering', entityId: MOCK_DONOR.id, quantity: 40, status: 'COMPLETED', completedAt: 'Today, 2:45 PM' },
    { order: 2, type: 'delivery', location: LOCATIONS.sevaCommunity, entityName: 'Seva Community Kitchen', entityId: MOCK_RECEIVER.id, quantity: 12, status: 'IN_PROGRESS' },
    { order: 3, type: 'delivery', location: LOCATIONS.annaSadan, entityName: 'Anna Sadan Charitable Trust', entityId: MOCK_RECEIVER_B.id, quantity: 8, status: 'PENDING' },
    { order: 4, type: 'delivery', location: LOCATIONS.saharaCommunity, entityName: 'Sahara Community Home', entityId: MOCK_RECEIVER_C.id, quantity: 20, status: 'PENDING' },
  ],
  route: { distance: 9.1, estimatedDuration: 35, eta: 11 },
  pickupVerification: {
    type: 'pickup',
    gpsVerified: true,
    otpVerified: true,
    otp: '4729',
    packageSealed: true,
    sealId: 'AS-GL-000047',
    timestamp: 'Today, 2:45 PM',
  },
  deliveryVerifications: [],
  earnings: 264,
  createdAt: 'Today, 2:30 PM',
}

// ─── Canonical Match ───────────────────────────────────────

export const MOCK_MATCH: Match = {
  id: 'match-seva-001',
  donationId: MOCK_DONATION.id,
  needId: MOCK_NEED.id,
  score: 94,
  factors: {
    distance: 3.9,
    eta: 15,
    expiryBuffer: 3.6,
    quantityFulfillment: 60,
    capacity: 30,
    routeFeasibility: 96,
  },
  status: 'CONFIRMED',
  createdAt: 'Today, 2:20 PM',
}

// ─── Mock Verification ─────────────────────────────────────

export const MOCK_VERIFICATION: VerificationRecord = {
  id: 'verif-greenleaf',
  userId: MOCK_DONOR.id,
  role: 'donor',
  status: 'VERIFIED',
  documents: [
    { id: 'doc-1', type: 'business_registration', label: 'Business Registration', verified: true, verifiedAt: '2024-01-16T10:00:00Z' },
    { id: 'doc-2', type: 'fssai_license', label: 'FSSAI License (11223009900099)', verified: true, verifiedAt: '2024-01-16T10:00:00Z' },
  ],
  submittedAt: '2024-01-15T10:00:00Z',
  reviewedAt: '2024-01-16T10:00:00Z',
  reviewedBy: MOCK_ADMIN.id,
}

// ─── Mock Impact ───────────────────────────────────────────

export const MOCK_IMPACT: ImpactMetrics = {
  foodRescued: 1240,
  mealsEquivalent: 3720,
  co2Saved: 2480,
  money: 24800,
  beneficiaries: 1850,
}

// ─── Data Service (backward compat) ────────────────────────

export const mockDataService = {
  getCurrentUser: (role: string) => {
    switch (role) {
      case 'donor': return MOCK_DONOR
      case 'receiver': return MOCK_RECEIVER
      case 'driver': return MOCK_DRIVER
      case 'admin': return MOCK_ADMIN
      default: return null
    }
  },
  getDonation: () => MOCK_DONATION,
  getNeed: () => MOCK_NEED,
  getDelivery: () => MOCK_DELIVERY,
  getImpact: () => MOCK_IMPACT,
  getAllocations: () => MOCK_ALLOCATIONS,
  getDonations: () => [MOCK_DONATION],
  getNeeds: () => [MOCK_NEED],
  getDeliveries: () => [MOCK_DELIVERY],
}
