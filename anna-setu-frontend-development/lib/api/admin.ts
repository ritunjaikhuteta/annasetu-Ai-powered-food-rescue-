/**
 * AnnaSetu — Admin & Operations Command Center API Client (Phase 17)
 */

import { apiClient } from './client'

export interface PlatformOperationalHealth {
  ai_provider: 'AVAILABLE' | 'DEGRADED' | 'DISABLED'
  routing_provider: 'AVAILABLE' | 'FALLBACK' | 'DISABLED'
  payment_provider: 'AVAILABLE' | 'MOCK' | 'DEGRADED'
  database: 'AVAILABLE' | 'ERROR'
}

export interface AdminOverviewResponse {
  active_donors: number
  active_receivers: number
  verified_drivers: number
  posted_donations: number
  active_needs: number
  open_deliveries: number
  in_transit_deliveries: number
  completed_deliveries_today: number
  pending_verifications: number
  integrity_reviews_pending: number
  failed_deliveries: number
  reassignment_required: number
  total_food_rescued_kg: number
  total_meal_equivalent: number
  total_co2e_avoided_kg: number
  financial_exception_count: number
  operational_health: PlatformOperationalHealth
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SystemNotification {
  id: string
  type: string
  title: string
  message: string
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  created_at: string
  metadata: Record<string, any>
}

export interface AuditLogEntry {
  id: string
  timestamp: string
  actor: string
  action: string
  entity_type: string
  entity_id?: string | null
  user_id?: string | null
  details: Record<string, any>
}

export interface VerificationItemResponse {
  id: string
  user_id: string
  role: string
  verification_type: string
  status: string
  created_at: string
  submitted_documents_count: number
  user_full_name?: string | null
  organization_or_business?: string | null
}

export interface VerificationDetailResponse {
  id: string
  user_id: string
  role: string
  verification_type: string
  status: string
  created_at: string
  verified_at?: string | null
  verified_by?: string | null
  rejection_reason?: string | null
  user_profile: Record<string, any>
  role_profile: Record<string, any>
  documents: Record<string, any>[]
}

export interface ActiveRescueDelivery {
  delivery_id: string
  status: string
  driver_id?: string | null
  driver_name?: string | null
  vehicle_type?: string | null
  donation_id: string
  food_name?: string | null
  quantity_kg: number
  pickup_location_ref: string
  delivery_stops_count: number
  current_stop?: string | null
  estimated_eta?: string | null
  deadline?: string | null
  route_status: string
  handoff_status: string
  integrity_status: string
  urgency_level: 'NORMAL' | 'ELEVATED' | 'AT_RISK'
}

export interface DeliveryExceptionItem {
  delivery_id: string
  status: string
  exception_type: string
  urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM'
  reason: string
  driver_id?: string | null
  created_at: string
  deadline?: string | null
}

export interface AdminUserItem {
  id: string
  full_name?: string | null
  email?: string | null
  phone?: string | null
  role: string
  is_active: boolean
  verification_status?: string | null
  created_at?: string | null
  business_or_org_name?: string | null
}

export interface FinancialExceptionItem {
  id: string
  exception_type: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  related_entity_id: string
  description: string
  amount?: number | null
  created_at: string
}

export interface ImpactAnalyticsResponse {
  period: string
  total_food_rescued_kg: number
  meal_equivalents: number
  co2e_avoided_kg: number
  active_donor_count: number
  active_receiver_count: number
  trends: Array<{ label: string; value: number }>
}

export interface OperationsAnalyticsResponse {
  period: string
  donations_posted: number
  donations_delivered: number
  delivery_completion_rate: number
  failure_rate: number
  average_delivery_time_minutes: number
  reassignment_count: number
  average_rescue_lead_time_hours: number
}

export interface FinancialAnalyticsResponse {
  period: string
  delivery_charges_total: number
  platform_fees_total: number
  driver_payouts_total: number
  refunds_total: number
  subscription_revenue_total: number
}

// ============================================================================
// API CLIENT CALLS
// ============================================================================

export async function getAdminOverview(): Promise<AdminOverviewResponse> {
  return apiClient<AdminOverviewResponse>('/api/v1/admin/overview')
}

export async function getSystemNotifications(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<SystemNotification>> {
  return apiClient<PaginatedResponse<SystemNotification>>(
    `/api/v1/admin/notifications/system?page=${page}&page_size=${pageSize}`
  )
}

export async function getAdminAuditLogs(
  filters?: { actor?: string; action?: string; entity_type?: string },
  page: number = 1,
  pageSize: number = 50
): Promise<PaginatedResponse<AuditLogEntry>> {
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  if (filters?.actor) params.set('actor', filters.actor)
  if (filters?.action) params.set('action', filters.action)
  if (filters?.entity_type) params.set('entity_type', filters.entity_type)
  return apiClient<PaginatedResponse<AuditLogEntry>>(`/api/v1/admin/audit-logs?${params.toString()}`)
}

export async function getAdminVerifications(
  filters?: { role?: string; status?: string; verification_type?: string },
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<VerificationItemResponse>> {
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  if (filters?.role) params.set('role', filters.role)
  if (filters?.status) params.set('status', filters.status)
  if (filters?.verification_type) params.set('verification_type', filters.verification_type)
  return apiClient<PaginatedResponse<VerificationItemResponse>>(
    `/api/v1/admin/verifications?${params.toString()}`
  )
}

export async function getAdminVerificationDetail(
  verificationId: string
): Promise<VerificationDetailResponse> {
  return apiClient<VerificationDetailResponse>(`/api/v1/admin/verifications/${verificationId}`)
}

export async function approveVerification(
  verificationId: string,
  reviewNotes?: string
): Promise<VerificationDetailResponse> {
  return apiClient<VerificationDetailResponse>(
    `/api/v1/admin/verifications/${verificationId}/approve`,
    {
      method: 'POST',
      body: JSON.stringify({ review_notes: reviewNotes }),
    }
  )
}

export async function rejectVerification(
  verificationId: string,
  rejectionReason: string
): Promise<VerificationDetailResponse> {
  return apiClient<VerificationDetailResponse>(
    `/api/v1/admin/verifications/${verificationId}/reject`,
    {
      method: 'POST',
      body: JSON.stringify({ rejection_reason: rejectionReason }),
    }
  )
}

export async function requestVerificationReview(
  verificationId: string,
  reviewNotes: string
): Promise<VerificationDetailResponse> {
  return apiClient<VerificationDetailResponse>(
    `/api/v1/admin/verifications/${verificationId}/request-review`,
    {
      method: 'POST',
      body: JSON.stringify({ review_notes: reviewNotes }),
    }
  )
}

export async function getActiveRescueOperations(): Promise<ActiveRescueDelivery[]> {
  return apiClient<ActiveRescueDelivery[]>('/api/v1/admin/operations/active')
}

export async function getDeliveryExceptions(): Promise<DeliveryExceptionItem[]> {
  return apiClient<DeliveryExceptionItem[]>('/api/v1/admin/operations/exceptions')
}

export async function reassignDelivery(
  deliveryId: string,
  newDriverId: string,
  reason: string
): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>(`/api/v1/admin/deliveries/${deliveryId}/reassign`, {
    method: 'POST',
    body: JSON.stringify({ new_driver_id: newDriverId, reason }),
  })
}

export async function getAdminUsers(
  filters?: { role?: string; verification_status?: string; is_active?: boolean; search?: string },
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<AdminUserItem>> {
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('page_size', String(pageSize))
  if (filters?.role) params.set('role', filters.role)
  if (filters?.verification_status) params.set('verification_status', filters.verification_status)
  if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active))
  if (filters?.search) params.set('search', filters.search)
  return apiClient<PaginatedResponse<AdminUserItem>>(`/api/v1/admin/users?${params.toString()}`)
}

export async function activateUser(userId: string, reason: string): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>(`/api/v1/admin/users/${userId}/activate`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function deactivateUser(userId: string, reason: string): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>(`/api/v1/admin/users/${userId}/deactivate`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function getAdminIntegrityReviews(status?: string): Promise<any[]> {
  const q = status ? `?status=${status}` : ''
  return apiClient<any[]>(`/api/v1/admin/integrity/reviews${q}`)
}

export async function submitAdminIntegrityReview(
  checkId: string,
  status: 'CLEARED' | 'REQUIRES_ACTION' | 'DISPUTED',
  notes?: string
): Promise<any> {
  return apiClient<any>(`/api/v1/admin/integrity/${checkId}/review`, {
    method: 'POST',
    body: JSON.stringify({ status, notes }),
  })
}

export async function getAdminFinancialExceptions(): Promise<FinancialExceptionItem[]> {
  return apiClient<FinancialExceptionItem[]>('/api/v1/admin/financial/exceptions')
}

export async function createFinancialAdjustment(
  walletId: string,
  amount: number,
  adjustmentType: 'CREDIT' | 'DEBIT',
  reason: string,
  originalReferenceId?: string
): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>('/api/v1/admin/financial/adjust', {
    method: 'POST',
    body: JSON.stringify({
      wallet_id: walletId,
      amount,
      adjustment_type: adjustmentType,
      reason,
      original_reference_id: originalReferenceId,
    }),
  })
}

export async function getImpactAnalytics(period: string = '30d'): Promise<ImpactAnalyticsResponse> {
  return apiClient<ImpactAnalyticsResponse>(`/api/v1/admin/analytics/impact?period=${period}`)
}

export async function getOperationsAnalytics(period: string = '30d'): Promise<OperationsAnalyticsResponse> {
  return apiClient<OperationsAnalyticsResponse>(`/api/v1/admin/analytics/operations?period=${period}`)
}

export async function getFinancialAnalytics(period: string = '30d'): Promise<FinancialAnalyticsResponse> {
  return apiClient<FinancialAnalyticsResponse>(`/api/v1/admin/analytics/financial?period=${period}`)
}
