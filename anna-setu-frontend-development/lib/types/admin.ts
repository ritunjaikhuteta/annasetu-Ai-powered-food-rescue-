/**
 * AnnaSetu — Admin Types
 *
 * Types specific to the internal operations console.
 */
import type { UserRole, VerificationStatus } from './core'

/** Admin dashboard summary data */
export interface AdminDashboard {
  activeDonations: number
  openNeeds: number
  liveRoutes: number
  pendingVerifications: number
  healthyMatchRate: number
  dailyGoalKg: number
  dailyRescuedKg: number
  operationsQueue: OperationsQueueItem[]
}

export interface OperationsQueueItem {
  id: string
  type: 'verification' | 'route_risk' | 'new_request' | 'dispute' | 'expiring_donation'
  title: string
  description: string
  urgency: 'low' | 'medium' | 'high' | 'critical'
  createdAt: string
  entityId?: string
}

/** Admin verification queue entry */
export interface AdminVerificationEntry {
  id: string
  userId: string
  userName: string
  role: UserRole
  status: VerificationStatus
  documentsCount: number
  submittedAt: string
  assignedTo?: string
}

/** Admin data for the UI */
export interface AdminData {
  dashboard: AdminDashboard
  verificationQueue: AdminVerificationEntry[]
  recentActivity: AdminActivityEntry[]
}

export interface AdminActivityEntry {
  id: string
  type: string
  description: string
  timestamp: string
  actorName?: string
  entityId?: string
}

export interface AuditLog {
  id: string
  action: string
  performedBy: string
  performedByRole: UserRole
  entityType: 'user' | 'donation' | 'need' | 'delivery' | 'verification' | 'wallet' | 'system'
  entityId: string
  details: string
  timestamp: string
  ipAddress?: string
}
