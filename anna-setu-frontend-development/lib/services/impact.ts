/**
 * AnnaSetu — Impact Service
 */
import { DONOR_DATA } from '@/lib/mock-data/donor'
import type { DonorImpact, DonorCertificate } from '@/lib/types/donor'

export interface IImpactService {
  getDonorImpact(): Promise<DonorImpact>
  getCertificates(): Promise<DonorCertificate[]>
}

export const impactService: IImpactService = {
  async getDonorImpact() {
    return DONOR_DATA.impact
  },
  async getCertificates() {
    return DONOR_DATA.certificates
  },
}
