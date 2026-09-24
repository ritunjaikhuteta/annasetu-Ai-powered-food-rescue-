/**
 * AnnaSetu — Matching Service Interface
 *
 * Simulates the AI-driven matching algorithm that distributes donations
 * to multiple verified receivers based on need urgency, capacity, and distance.
 */
import type { DonorDonation } from '@/lib/types/donor'
import type { ReceiverNeed } from '@/lib/types/receiver'

export interface IMatchRecommendation {
  receiverId: string
  receiverName: string
  allocatedQuantity: number
  distanceKm: number
  score: number
  rationale: string
}

export interface IMatchingService {
  findMatchesForDonation(donation: DonorDonation): Promise<IMatchRecommendation[]>
}

export const matchingService: IMatchingService = {
  async findMatchesForDonation(donation: DonorDonation): Promise<IMatchRecommendation[]> {
    // Canonical match allocation for Green Leaf Catering: 12kg Seva Community, 8kg Anna Sadan, 20kg Sahara
    return [
      {
        receiverId: 'user-receiver-1',
        receiverName: 'Seva Community Kitchen',
        allocatedQuantity: 12,
        distanceKm: 2.4,
        score: 96,
        rationale: 'High urgency lunch requirement within 3 km',
      },
      {
        receiverId: 'user-receiver-2',
        receiverName: 'Anna Sadan Charitable Trust',
        allocatedQuantity: 8,
        distanceKm: 4.1,
        score: 92,
        rationale: 'Verified capacity, aligns with vegetarian meal preference',
      },
      {
        receiverId: 'user-receiver-3',
        receiverName: 'Sahara Community Home',
        allocatedQuantity: 20,
        distanceKm: 5.8,
        score: 89,
        rationale: 'Active evening food need for 50+ residents',
      },
    ]
  },
}
