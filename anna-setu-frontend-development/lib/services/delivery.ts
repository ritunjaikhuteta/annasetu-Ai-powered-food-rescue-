/**
 * AnnaSetu — Delivery Service
 */
import { DRIVER_DATA } from '@/lib/mock-data/driver'
import type { DriverJob } from '@/lib/types/driver'

export interface IDeliveryService {
  getActiveDelivery(): Promise<DriverJob | undefined>
  getDeliveryHistory(): Promise<DriverJob[]>
  updateLocation(deliveryId: string, lat: number, lng: number): Promise<{ ok: boolean }>
}

export const deliveryService: IDeliveryService = {
  async getActiveDelivery() {
    return DRIVER_DATA.activeJob
  },
  async getDeliveryHistory() {
    return DRIVER_DATA.completedDeliveries
  },
  async updateLocation(deliveryId, lat, lng) {
    return { ok: true }
  },
}
