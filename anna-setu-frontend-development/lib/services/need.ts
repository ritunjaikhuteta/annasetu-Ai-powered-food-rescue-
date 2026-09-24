/**
 * AnnaSetu — Need Service
 */
import { RECEIVER_DATA } from '@/lib/mock-data/receiver'
import type { ReceiverNeed } from '@/lib/types/receiver'

export interface INeedService {
  list(): Promise<ReceiverNeed[]>
  create(need: Omit<ReceiverNeed, 'id' | 'status'>): Promise<{ ok: boolean; need: ReceiverNeed }>
  cancel(id: string): Promise<{ ok: boolean }>
}

export const needService: INeedService = {
  async list() {
    return RECEIVER_DATA.activeNeeds
  },
  async create(data) {
    const need: ReceiverNeed = {
      id: `need-${Date.now()}`,
      status: 'Open',
      ...data,
    }
    RECEIVER_DATA.activeNeeds.unshift(need)
    return { ok: true, need }
  },
  async cancel(id: string) {
    const idx = RECEIVER_DATA.activeNeeds.findIndex(n => n.id === id)
    if (idx !== -1) {
      RECEIVER_DATA.activeNeeds.splice(idx, 1)
      return { ok: true }
    }
    return { ok: false }
  },
}
