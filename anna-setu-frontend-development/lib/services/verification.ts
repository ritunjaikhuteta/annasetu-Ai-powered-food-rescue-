/**
 * AnnaSetu — Verification Service
 */
import { ADMIN_DATA } from '@/lib/mock-data/admin'
import type { VerificationDocument } from '@/lib/types/verification'
import type { VerificationStatus } from '@/lib/types/core'

export interface IVerificationService {
  checkStatus(userId: string): Promise<VerificationStatus>
  uploadDocument(userId: string, document: Partial<VerificationDocument>): Promise<{ ok: boolean; documentId: string }>
}

export const verificationService: IVerificationService = {
  async checkStatus(userId: string) {
    const queueItem = ADMIN_DATA.verificationQueue.find(v => v.userId === userId)
    if (queueItem) return queueItem.status
    return 'verified'
  },
  async uploadDocument(userId: string, document: Partial<VerificationDocument>) {
    return { ok: true, documentId: `doc-${Date.now()}` }
  },
}
