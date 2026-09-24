/**
 * AnnaSetu — Donation Service
 */
import { DONOR_DATA } from '@/lib/mock-data/donor'
import type { DonorDonation } from '@/lib/types/donor'

export interface IDonationService {
  list(): Promise<DonorDonation[]>
  getById(id: string): Promise<DonorDonation | undefined>
  create(donation: Partial<DonorDonation>): Promise<{ ok: boolean; donation: DonorDonation }>
  cancel(id: string): Promise<{ ok: boolean }>
}

export const donationService: IDonationService = {
  async list() {
    return DONOR_DATA.donations
  },
  async getById(id: string) {
    return DONOR_DATA.donations.find(d => d.id === id) ?? DONOR_DATA.donation
  },
  async create(donationData) {
    const newDonation: DonorDonation = {
      id: `AS-${Math.floor(1000 + Math.random() * 9000)}`,
      name: donationData.name || 'Surplus Food',
      type: donationData.type || 'Vegetarian',
      category: donationData.category || 'Cooked Meals',
      quantity: donationData.quantity || 10,
      unit: donationData.unit || 'kg',
      status: 'Posted',
      createdAt: 'Just now',
      deadline: donationData.deadline || 'Today, 8:00 PM',
      allocation: 0,
      receivers: [],
      image: '/placeholder.jpg',
      description: donationData.description || '',
      storage: donationData.storage || 'Room temperature',
      packaging: donationData.packaging || 'Food-grade containers',
      preparation: 'Prepared today',
      pickupAddress: donationData.pickupAddress || DONOR_DATA.donation.pickupAddress,
      priority: 85,
    }
    DONOR_DATA.donations.unshift(newDonation)
    return { ok: true, donation: newDonation }
  },
  async cancel(id: string) {
    const item = DONOR_DATA.donations.find(d => d.id === id)
    if (item) {
      item.status = 'Cancelled'
      return { ok: true }
    }
    return { ok: false }
  },
}
