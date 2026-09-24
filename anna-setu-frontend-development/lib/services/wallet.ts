/**
 * AnnaSetu — Wallet & Financial Service
 */
import { DRIVER_DATA } from '@/lib/mock-data/driver'
import type { Wallet, Transaction } from '@/lib/types/wallet'

export interface IWalletService {
  getDriverEarnings(): Promise<typeof DRIVER_DATA.earnings>
  requestPayout(amount: number): Promise<{ ok: boolean; message: string }>
}

export const walletService: IWalletService = {
  async getDriverEarnings() {
    return DRIVER_DATA.earnings
  },
  async requestPayout(amount: number) {
    if (amount <= 0 || amount > DRIVER_DATA.earnings.pendingPayout) {
      return { ok: false, message: 'Invalid payout amount requested' }
    }
    DRIVER_DATA.earnings.pendingPayout -= amount
    DRIVER_DATA.earnings.totalPaid += amount
    return { ok: true, message: `Payout request of ₹${amount} initiated successfully` }
  },
}
