/**
 * AnnaSetu — Notification Service
 */
import { DONOR_DATA } from '@/lib/mock-data/donor'
import type { DonorNotification } from '@/lib/types/donor'

export interface INotificationService {
  list(): Promise<DonorNotification[]>
  dismiss(id: string): Promise<{ ok: boolean }>
}

export const notificationService: INotificationService = {
  async list() {
    return DONOR_DATA.notifications
  },
  async dismiss(id: string) {
    const idx = DONOR_DATA.notifications.findIndex(n => n.id === id)
    if (idx !== -1) {
      DONOR_DATA.notifications.splice(idx, 1)
      return { ok: true }
    }
    return { ok: false }
  },
}
