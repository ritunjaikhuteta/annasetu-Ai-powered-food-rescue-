/**
 * AnnaSetu — Admin Operations Service
 *
 * Mock service for internal operations console and verification review.
 * Replace with Supabase admin role API calls when backend is connected.
 */
import { ADMIN_DATA } from '@/lib/mock-data/admin'
import type { AdminData, AdminVerificationEntry } from '@/lib/types/admin'
import type { VerificationStatus } from '@/lib/types/core'

export interface IAdminService {
  getData(): Promise<AdminData>
  reviewVerification(id: string, status: VerificationStatus, note?: string): Promise<{ ok: boolean }>
  dismissQueueItem(id: string): Promise<{ ok: boolean }>
}

export const adminService: IAdminService = {
  async getData(): Promise<AdminData> {
    return ADMIN_DATA
  },
  async reviewVerification(id: string, status: VerificationStatus, note?: string) {
    const item = ADMIN_DATA.verificationQueue.find(v => v.id === id)
    if (item) {
      item.status = status
      ADMIN_DATA.dashboard.pendingVerifications = Math.max(0, ADMIN_DATA.dashboard.pendingVerifications - 1)
      ADMIN_DATA.recentActivity.unshift({
        id: `act-${Date.now()}`,
        type: 'verification_reviewed',
        description: `${item.userName} status updated to ${status}${note ? `: ${note}` : ''}`,
        timestamp: 'Just now',
        actorName: 'Admin Operations',
        entityId: item.userId,
      })
      return { ok: true }
    }
    return { ok: false }
  },
  async dismissQueueItem(id: string) {
    const index = ADMIN_DATA.dashboard.operationsQueue.findIndex(q => q.id === id)
    if (index !== -1) {
      ADMIN_DATA.dashboard.operationsQueue.splice(index, 1)
      return { ok: true }
    }
    return { ok: false }
  },
}
