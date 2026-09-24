/**
 * AnnaSetu — Delivery & Logistics API Client (FastAPI Backend)
 */

import { apiClient } from './client'

export type DeliveryStatus =
  | 'OPEN'
  | 'ACCEPTED'
  | 'ARRIVING_PICKUP'
  | 'PICKED_UP'
  | 'IN_TRANSIT'
  | 'AT_STOP'
  | 'DELIVERED'
  | 'CANCELLED'
  | 'FAILED_PICKUP'
  | 'FAILED_DELIVERY'
  | 'REASSIGNMENT_REQUIRED'

export type DeliveryStopType = 'PICKUP' | 'DELIVERY'

export type DeliveryStopStatus =
  | 'PENDING'
  | 'ARRIVING'
  | 'ARRIVED'
  | 'IN_PROGRESS'
  | 'VERIFIED'
  | 'COMPLETED'
  | 'FAILED'
  | 'SKIPPED'

export type DeliveryOfferStatus =
  | 'OFFERED'
  | 'VIEWED'
  | 'ACCEPTED'
  | 'DECLINED'
  | 'EXPIRED'
  | 'CANCELLED'

export interface DeliveryStop {
  id: string
  delivery_id: string
  sequence_number: number
  stop_type: DeliveryStopType
  location_id: string
  receiver_id?: string
  allocation_id?: string
  quantity_kg: number
  distance_from_prev_km: number
  estimated_arrival?: string
  status: DeliveryStopStatus
  arrived_at?: string
  completed_at?: string
}

export interface Delivery {
  id: string
  donation_id: string
  driver_id?: string
  vehicle_type?: string
  total_quantity_kg: number
  total_distance_km?: number
  estimated_duration_minutes?: number
  status: DeliveryStatus
  accepted_at?: string
  picked_up_at?: string
  completed_at?: string
  stops: DeliveryStop[]
  created_at?: string
  updated_at?: string
}

export interface DeliveryCreatePayload {
  donation_id: string
  allocation_ids: string[]
}

export interface DeliveryOffer {
  id: string
  delivery_id: string
  driver_id: string
  vehicle_type?: string
  offered_delivery_charge: number
  estimated_driver_payout: number
  estimated_distance_km?: number
  estimated_duration_minutes?: number
  expires_at: string
  status: DeliveryOfferStatus
  created_at?: string
}

export interface EligibleDriver {
  id: string
  driver_user_id: string
  name: string
  phone?: string
  vehicle_type: string
  vehicle_number?: string
  vehicle_capacity_kg: number
  has_refrigeration: boolean
  distance_to_pickup_km: number
  pickup_eta_minutes: number
  availability_status: string
  verification_status: string
}

export interface ProximityPayload {
  latitude: number
  longitude: number
  accuracy_meters?: number
}

export const deliveryApi = {
  /**
   * Create a delivery mission from accepted or reserved donation allocations
   */
  async createDelivery(payload: DeliveryCreatePayload): Promise<Delivery> {
    return apiClient<Delivery>('/api/v1/deliveries', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Get delivery mission details with ordered stops
   */
  async getDelivery(deliveryId: string): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}`)
  },

  /**
   * Discover and rank eligible drivers for a delivery
   */
  async getEligibleDrivers(deliveryId: string): Promise<EligibleDriver[]> {
    return apiClient<EligibleDriver[]>(`/api/v1/deliveries/${deliveryId}/eligible-drivers`)
  },

  /**
   * Dispatch delivery offers to drivers
   */
  async createOffers(deliveryId: string, driverIds?: string[]): Promise<DeliveryOffer[]> {
    return apiClient<DeliveryOffer[]>(`/api/v1/deliveries/${deliveryId}/offers`, {
      method: 'POST',
      body: JSON.stringify(driverIds ? { driver_ids: driverIds } : {}),
    })
  },

  /**
   * Driver marks offer as viewed
   */
  async viewOffer(offerId: string): Promise<DeliveryOffer> {
    return apiClient<DeliveryOffer>(`/api/v1/delivery-offers/${offerId}/view`, {
      method: 'POST',
    })
  },

  /**
   * Driver atomically accepts an offer (CAS protected)
   */
  async acceptOffer(offerId: string): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/delivery-offers/${offerId}/accept`, {
      method: 'POST',
    })
  },

  /**
   * Driver declines an offer
   */
  async declineOffer(offerId: string): Promise<DeliveryOffer> {
    return apiClient<DeliveryOffer>(`/api/v1/delivery-offers/${offerId}/decline`, {
      method: 'POST',
    })
  },

  /**
   * Cancel delivery or initiate reassignment if driver cancels
   */
  async cancelDelivery(deliveryId: string): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/cancel`, {
      method: 'POST',
    })
  },

  /**
   * Driver reports arrival at pickup with GPS proximity validation
   */
  async arrivePickup(deliveryId: string, proximity?: ProximityPayload): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/arrive-pickup`, {
      method: 'POST',
      body: proximity ? JSON.stringify(proximity) : undefined,
    })
  },

  /**
   * Driver confirms loading and marks food picked up
   */
  async markPickedUp(deliveryId: string): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/mark-picked-up`, {
      method: 'POST',
    })
  },

  /**
   * Driver starts transit to destination
   */
  async startTransit(deliveryId: string): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/start-transit`, {
      method: 'POST',
    })
  },

  /**
   * Driver arrives at delivery stop with GPS proximity validation
   */
  async arriveStop(deliveryId: string, proximity?: ProximityPayload): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/arrive-stop`, {
      method: 'POST',
      body: proximity ? JSON.stringify(proximity) : undefined,
    })
  },

  /**
   * Driver completes dropoff at current stop or final mission
   */
  async completeStop(deliveryId: string): Promise<Delivery> {
    return apiClient<Delivery>(`/api/v1/deliveries/${deliveryId}/complete-stop`, {
      method: 'POST',
    })
  },
}
