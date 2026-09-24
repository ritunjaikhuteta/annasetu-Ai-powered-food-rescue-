/**
 * AnnaSetu — Notification Types
 */
import type { UserRole } from './core'

export type NotificationChannel = 'in_app' | 'push' | 'email' | 'sms'
export type NotificationUrgency = 'info' | 'success' | 'warning' | 'urgent'

export interface Notification {
  id: string
  userId: string
  title: string
  body: string
  urgency: NotificationUrgency
  channel: NotificationChannel
  read: boolean
  actionUrl?: string
  entityType?: string
  entityId?: string
  createdAt: string
  readAt?: string
}
