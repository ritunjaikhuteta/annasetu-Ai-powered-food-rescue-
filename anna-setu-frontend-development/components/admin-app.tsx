'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import '@/app/admin/admin.css'
import {
  Activity,
  FileCheck2,
  Users,
  Truck,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Leaf,
  LogOut,
  Clock,
  Sparkles,
  Search,
  Filter,
  DollarSign,
  BarChart3,
  ShieldCheck,
  RefreshCw,
  Eye,
  UserCheck,
  UserX,
  FileText,
} from 'lucide-react'
import {
  AdminOverviewResponse,
  ActiveRescueDelivery,
  DeliveryExceptionItem,
  VerificationItemResponse,
  VerificationDetailResponse,
  FinancialExceptionItem,
  AdminUserItem,
  AuditLogEntry,
  ImpactAnalyticsResponse,
  OperationsAnalyticsResponse,
  FinancialAnalyticsResponse,
  getAdminOverview,
  getAdminVerifications,
  getAdminVerificationDetail,
  approveVerification,
  rejectVerification,
  requestVerificationReview,
  getActiveRescueOperations,
  getDeliveryExceptions,
  reassignDelivery,
  getAdminUsers,
  activateUser,
  deactivateUser,
  getAdminIntegrityReviews,
  submitAdminIntegrityReview,
  getAdminFinancialExceptions,
  createFinancialAdjustment,
  getAdminAuditLogs,
  getImpactAnalytics,
  getOperationsAnalytics,
  getFinancialAnalytics,
} from '@/lib/api/admin'
import { LoadingState } from '@/components/shared/LoadingState'

type AdminTab =
  | 'overview'
  | 'verifications'
  | 'operations'
  | 'integrity'
  | 'financial'
  | 'users'
  | 'analytics'
  | 'audit'

export default function AdminApp({ path = '/admin/dashboard' }: { path?: string }) {
  const [activeTab, setActiveTab] = useState<AdminTab>('overview')
  const [overview, setOverview] = useState<AdminOverviewResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Verifications State
  const [verifications, setVerifications] = useState<VerificationItemResponse[]>([])
  const [selectedVerif, setSelectedVerif] = useState<VerificationDetailResponse | null>(null)
  const [verifModalAction, setVerifModalAction] = useState<'approve' | 'reject' | 'review' | null>(null)
  const [verifNote, setVerifNote] = useState<string>('')

  // Operations State
  const [activeRescues, setActiveRescues] = useState<ActiveRescueDelivery[]>([])
  const [exceptions, setExceptions] = useState<DeliveryExceptionItem[]>([])
  const [selectedReassignDelivery, setSelectedReassignDelivery] = useState<string | null>(null)
  const [newDriverId, setNewDriverId] = useState<string>('')
  const [reassignReason, setReassignReason] = useState<string>('')

  // Integrity State
  const [integrityReviews, setIntegrityReviews] = useState<any[]>([])
  const [selectedIntegrityCheck, setSelectedIntegrityCheck] = useState<any | null>(null)
  const [integrityNote, setIntegrityNote] = useState<string>('')

  // Financial State
  const [financialExceptions, setFinancialExceptions] = useState<FinancialExceptionItem[]>([])
  const [showAdjustModal, setShowAdjustModal] = useState<boolean>(false)
  const [adjWalletId, setAdjWalletId] = useState<string>('')
  const [adjAmount, setAdjAmount] = useState<string>('')
  const [adjType, setAdjType] = useState<'CREDIT' | 'DEBIT'>('CREDIT')
  const [adjReason, setAdjReason] = useState<string>('')

  // Users State
  const [usersList, setUsersList] = useState<AdminUserItem[]>([])
  const [userSearch, setUserSearch] = useState<string>('')
  const [userActionModal, setUserActionModal] = useState<{ user: AdminUserItem; type: 'activate' | 'deactivate' } | null>(null)
  const [userActionReason, setUserActionReason] = useState<string>('')

  // Analytics State
  const [analyticsPeriod, setAnalyticsPeriod] = useState<string>('30d')
  const [impactData, setImpactData] = useState<ImpactAnalyticsResponse | null>(null)
  const [opsData, setOpsData] = useState<OperationsAnalyticsResponse | null>(null)
  const [finData, setFinData] = useState<FinancialAnalyticsResponse | null>(null)

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([])

  // Load Overview Data
  const loadOverview = async () => {
    try {
      setRefreshing(true)
      const data = await getAdminOverview()
      setOverview(data)
      setErrorMsg(null)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load administrative overview.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadOverview()
  }, [])

  // Tab change effect
  useEffect(() => {
    if (activeTab === 'verifications') {
      getAdminVerifications().then((res) => setVerifications(res.items)).catch(() => {})
    } else if (activeTab === 'operations') {
      getActiveRescueOperations().then(setActiveRescues).catch(() => {})
      getDeliveryExceptions().then(setExceptions).catch(() => {})
    } else if (activeTab === 'integrity') {
      getAdminIntegrityReviews().then(setIntegrityReviews).catch(() => {})
    } else if (activeTab === 'financial') {
      getAdminFinancialExceptions().then(setFinancialExceptions).catch(() => {})
    } else if (activeTab === 'users') {
      getAdminUsers({ search: userSearch }).then((res) => setUsersList(res.items)).catch(() => {})
    } else if (activeTab === 'analytics') {
      getImpactAnalytics(analyticsPeriod).then(setImpactData).catch(() => {})
      getOperationsAnalytics(analyticsPeriod).then(setOpsData).catch(() => {})
      getFinancialAnalytics(analyticsPeriod).then(setFinData).catch(() => {})
    } else if (activeTab === 'audit') {
      getAdminAuditLogs().then((res) => setAuditLogs(res.items)).catch(() => {})
    }
  }, [activeTab, analyticsPeriod])

  if (loading && !overview) {
    return <LoadingState message="Connecting to AnnaSetu Operations Command Center…" className="min-h-screen" />
  }

  return (
    <div className="admin-shell">
      {/* Sidebar Navigation */}
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <Link href="/" className="flex items-center gap-2 text-white font-bold text-lg">
            <span className="w-8 h-8 rounded-lg bg-emerald-700 text-amber-200 flex items-center justify-center font-bold">
              AS
            </span>
            <span>AnnaSetu Ops</span>
          </Link>
          <div className="mt-2 text-[11px] text-emerald-300 font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Command Center
          </div>
        </div>

        <nav className="admin-nav">
          <button
            onClick={() => setActiveTab('overview')}
            className={`admin-nav-item w-full text-left ${activeTab === 'overview' ? 'active' : ''}`}
          >
            <Activity size={16} />
            Command Center
          </button>
          <button
            onClick={() => setActiveTab('operations')}
            className={`admin-nav-item w-full text-left ${activeTab === 'operations' ? 'active' : ''}`}
          >
            <Truck size={16} />
            Live Rescues ({overview?.in_transit_deliveries || 0})
          </button>
          <button
            onClick={() => setActiveTab('verifications')}
            className={`admin-nav-item w-full text-left ${activeTab === 'verifications' ? 'active' : ''}`}
          >
            <FileCheck2 size={16} />
            Verification Queue ({overview?.pending_verifications || 0})
          </button>
          <button
            onClick={() => setActiveTab('integrity')}
            className={`admin-nav-item w-full text-left ${activeTab === 'integrity' ? 'active' : ''}`}
          >
            <ShieldCheck size={16} />
            Integrity Reviews ({overview?.integrity_reviews_pending || 0})
          </button>
          <button
            onClick={() => setActiveTab('financial')}
            className={`admin-nav-item w-full text-left ${activeTab === 'financial' ? 'active' : ''}`}
          >
            <DollarSign size={16} />
            Financial Exceptions ({overview?.financial_exception_count || 0})
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`admin-nav-item w-full text-left ${activeTab === 'users' ? 'active' : ''}`}
          >
            <Users size={16} />
            User & Driver Directory
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`admin-nav-item w-full text-left ${activeTab === 'analytics' ? 'active' : ''}`}
          >
            <BarChart3 size={16} />
            Rescue Analytics
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`admin-nav-item w-full text-left ${activeTab === 'audit' ? 'active' : ''}`}
          >
            <Clock size={16} />
            Append-Only Audit Trail
          </button>
        </nav>

        <div className="p-4 border-t border-white/10 text-xs text-emerald-400/80">
          <div>Authoritative Mode: SERVER</div>
          <div className="text-[10px] text-emerald-500/60 mt-0.5">Admin Security Enforced</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="admin-main">
        {/* Topbar */}
        <header className="admin-topbar">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-gray-900 tracking-tight">AnnaSetu Operations</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
              Live Monitor
            </span>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={loadOverview}
              disabled={refreshing}
              className="flex items-center gap-1.5 text-xs text-gray-600 hover:text-emerald-800 transition py-1.5 px-3 rounded-md border border-gray-200 hover:border-emerald-300 bg-white"
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              Sync
            </button>
            <Link
              href="/"
              className="text-xs text-gray-600 hover:text-gray-900 flex items-center gap-1"
            >
              <LogOut size={14} /> Exit
            </Link>
          </div>
        </header>

        {/* Dynamic Workspace Container */}
        <div className="admin-content">
          {errorMsg && (
            <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 1: OVERVIEW */}
          {/* ================================================================= */}
          {activeTab === 'overview' && overview && (
            <div className="space-y-6">
              {/* System Operational Health */}
              <div className="admin-card border-l-4 border-l-emerald-700">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Platform Operational Health
                  </h3>
                  <span className="text-xs font-semibold text-emerald-800">Deterministic Authorities Online</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
                    <span className="text-gray-500 block text-[11px]">AI Assistance Layer</span>
                    <span className="font-bold text-gray-900">{overview.operational_health.ai_provider}</span>
                  </div>
                  <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
                    <span className="text-gray-500 block text-[11px]">Routing Engine</span>
                    <span className="font-bold text-gray-900">{overview.operational_health.routing_provider}</span>
                  </div>
                  <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
                    <span className="text-gray-500 block text-[11px]">Payment Gateway</span>
                    <span className="font-bold text-gray-900">{overview.operational_health.payment_provider}</span>
                  </div>
                  <div className="p-2.5 rounded bg-gray-50 border border-gray-200">
                    <span className="text-gray-500 block text-[11px]">Database Ledger</span>
                    <span className="font-bold text-gray-900">{overview.operational_health.database}</span>
                  </div>
                </div>
              </div>

              {/* Dense Operational Summary Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="admin-card">
                  <span className="text-xs text-gray-500 font-medium">In-Transit Rescues</span>
                  <div className="text-2xl font-bold text-gray-900 mt-1">{overview.in_transit_deliveries}</div>
                  <span className="text-[11px] text-emerald-700 mt-1 block">{overview.open_deliveries} open missions</span>
                </div>

                <div className="admin-card">
                  <span className="text-xs text-gray-500 font-medium">Pending Verification</span>
                  <div className="text-2xl font-bold text-amber-700 mt-1">{overview.pending_verifications}</div>
                  <span className="text-[11px] text-gray-500 mt-1 block">Awaiting human review</span>
                </div>

                <div className="admin-card">
                  <span className="text-xs text-gray-500 font-medium">Delivery Exceptions</span>
                  <div className="text-2xl font-bold text-red-600 mt-1">
                    {overview.failed_deliveries + overview.reassignment_required}
                  </div>
                  <span className="text-[11px] text-red-700 mt-1 block">{overview.reassignment_required} need driver</span>
                </div>

                <div className="admin-card">
                  <span className="text-xs text-gray-500 font-medium">Integrity Discrepancies</span>
                  <div className="text-2xl font-bold text-amber-700 mt-1">{overview.integrity_reviews_pending}</div>
                  <span className="text-[11px] text-gray-500 mt-1 block">Seal/Package alerts</span>
                </div>

                <div className="admin-card">
                  <span className="text-xs text-gray-500 font-medium">Food Rescued (kg)</span>
                  <div className="text-2xl font-bold text-emerald-800 mt-1">
                    {overview.total_food_rescued_kg.toLocaleString()}
                  </div>
                  <span className="text-[11px] text-gray-500 mt-1 block">~{overview.total_meal_equivalent.toLocaleString()} meals</span>
                </div>
              </div>

              {/* Quick Actions & Live Queues */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="admin-card">
                  <h3 className="font-bold text-sm text-gray-900 mb-3 flex items-center justify-between">
                    <span>Active Entity Footprint</span>
                    <button
                      onClick={() => setActiveTab('users')}
                      className="text-xs text-emerald-700 hover:underline font-semibold"
                    >
                      Inspect All →
                    </button>
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between p-2 rounded bg-gray-50 border border-gray-100">
                      <span className="text-gray-600">Active Donor Businesses</span>
                      <span className="font-bold text-gray-900">{overview.active_donors}</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-gray-50 border border-gray-100">
                      <span className="text-gray-600">Active Hunger Relief NGOs</span>
                      <span className="font-bold text-gray-900">{overview.active_receivers}</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-gray-50 border border-gray-100">
                      <span className="text-gray-600">Verified Logistics Drivers</span>
                      <span className="font-bold text-gray-900">{overview.verified_drivers}</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-gray-50 border border-gray-100">
                      <span className="text-gray-600">Deliveries Completed Today</span>
                      <span className="font-bold text-emerald-800">{overview.completed_deliveries_today}</span>
                    </div>
                  </div>
                </div>

                <div className="admin-card">
                  <h3 className="font-bold text-sm text-gray-900 mb-3 flex items-center justify-between">
                    <span>Urgent Action Requirements</span>
                    <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">Action Queue</span>
                  </h3>
                  <div className="space-y-2 text-xs">
                    {overview.reassignment_required > 0 ? (
                      <div className="p-3 rounded bg-red-50 border border-red-200 text-red-800 flex justify-between items-center">
                        <div>
                          <strong className="block">Delivery Reassignment Required</strong>
                          <span>{overview.reassignment_required} missions currently lack active drivers.</span>
                        </div>
                        <button
                          onClick={() => setActiveTab('operations')}
                          className="px-2.5 py-1 bg-red-600 text-white rounded text-xs font-semibold hover:bg-red-700"
                        >
                          Reassign
                        </button>
                      </div>
                    ) : (
                      <div className="p-2.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs">
                        No critical delivery reassignment backlogs detected.
                      </div>
                    )}

                    {overview.pending_verifications > 0 && (
                      <div className="p-3 rounded bg-amber-50 border border-amber-200 text-amber-900 flex justify-between items-center">
                        <div>
                          <strong className="block">Pending Document Verifications</strong>
                          <span>{overview.pending_verifications} organization or driver applications waiting.</span>
                        </div>
                        <button
                          onClick={() => setActiveTab('verifications')}
                          className="px-2.5 py-1 bg-amber-700 text-white rounded text-xs font-semibold hover:bg-amber-800"
                        >
                          Review Queue
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 2: VERIFICATION QUEUE */}
          {/* ================================================================= */}
          {activeTab === 'verifications' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-base font-bold text-gray-900">Verification Review Queue</h2>
                  <p className="text-xs text-gray-500">Human-in-the-loop review of submitted licenses, PAN, and credentials.</p>
                </div>
              </div>

              {selectedVerif ? (
                <div className="admin-card space-y-4">
                  <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                    <div>
                      <button
                        onClick={() => setSelectedVerif(null)}
                        className="text-xs text-emerald-700 font-semibold hover:underline mb-1 block"
                      >
                        ← Back to Queue
                      </button>
                      <h3 className="font-bold text-sm text-gray-900">
                        Verification Case: {selectedVerif.id} ({selectedVerif.role})
                      </h3>
                      <span className="text-xs text-gray-500">User: {selectedVerif.user_profile?.full_name || selectedVerif.user_id}</span>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded bg-amber-100 text-amber-800 font-bold">
                      {selectedVerif.status}
                    </span>
                  </div>

                  {/* Submitted Documents & OCR Extractions */}
                  <div>
                    <h4 className="text-xs font-bold uppercase text-gray-600 mb-2">Submitted Documents & Extracted OCR</h4>
                    {selectedVerif.documents.length === 0 ? (
                      <p className="text-xs text-gray-500 italic">No document attachments uploaded.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedVerif.documents.map((doc, idx) => (
                          <div key={idx} className="p-3 rounded border border-gray-200 bg-gray-50 text-xs space-y-1.5">
                            <div className="flex justify-between font-bold">
                              <span>{doc.document_type || 'Document'}</span>
                              <span className="text-gray-500">{doc.verification_status || 'PENDING'}</span>
                            </div>
                            {doc.extracted_data ? (
                              <div className="p-2 rounded bg-white border border-gray-200 text-[11px] space-y-1">
                                <span className="font-semibold text-emerald-800 block">AI Suggestion & Extracted Info:</span>
                                <div>Doc Number: {doc.extracted_data.document_number || 'N/A'}</div>
                                <div>Holder: {doc.extracted_data.holder_name || 'N/A'}</div>
                                <div>Vehicle: {doc.extracted_data.vehicle_number || 'N/A'}</div>
                                <div>Expiry: {doc.extracted_data.expiry_date || 'N/A'}</div>
                                <div className="text-gray-400 text-[10px]">Confidence: {doc.extracted_data.extraction_confidence}%</div>
                              </div>
                            ) : (
                              <span className="text-gray-400 italic">No OCR extraction recorded.</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-4 border-t border-gray-200 flex gap-3">
                    <button
                      onClick={() => setVerifModalAction('approve')}
                      className="px-4 py-2 bg-emerald-700 text-white rounded text-xs font-bold hover:bg-emerald-800 transition"
                    >
                      Approve Verification
                    </button>
                    <button
                      onClick={() => setVerifModalAction('reject')}
                      className="px-4 py-2 bg-red-600 text-white rounded text-xs font-bold hover:bg-red-700 transition"
                    >
                      Reject with Reason
                    </button>
                    <button
                      onClick={() => setVerifModalAction('review')}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded text-xs font-bold hover:bg-gray-300 transition"
                    >
                      Request Further Review
                    </button>
                  </div>
                </div>
              ) : (
                <div className="admin-card overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-gray-200 text-gray-500 uppercase text-[10px] tracking-wider font-bold">
                        <th className="py-2.5 px-3">Role</th>
                        <th className="py-2.5 px-3">Applicant / Organization</th>
                        <th className="py-2.5 px-3">Type</th>
                        <th className="py-2.5 px-3">Docs</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3">Created</th>
                        <th className="py-2.5 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-gray-700">
                      {verifications.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-6 text-center text-gray-400 italic">
                            No verification requests currently pending.
                          </td>
                        </tr>
                      ) : (
                        verifications.map((v) => (
                          <tr key={v.id} className="hover:bg-gray-50 transition">
                            <td className="py-3 px-3 font-semibold text-gray-900">{v.role}</td>
                            <td className="py-3 px-3">
                              <span className="font-bold block text-gray-900">{v.user_full_name || v.user_id}</span>
                              <span className="text-[11px] text-gray-500">{v.organization_or_business || '—'}</span>
                            </td>
                            <td className="py-3 px-3">{v.verification_type}</td>
                            <td className="py-3 px-3">{v.submitted_documents_count}</td>
                            <td className="py-3 px-3">
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                                {v.status}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-gray-500">{v.created_at ? v.created_at.slice(0, 10) : '—'}</td>
                            <td className="py-3 px-3 text-right">
                              <button
                                onClick={async () => {
                                  const detail = await getAdminVerificationDetail(v.id)
                                  setSelectedVerif(detail)
                                }}
                                className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 font-semibold hover:bg-emerald-100 transition border border-emerald-200"
                              >
                                Inspect
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 3: OPERATIONS & LIVE RESCUES */}
          {/* ================================================================= */}
          {activeTab === 'operations' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-bold text-gray-900">Live Rescue Operations & Logistics</h2>
                <p className="text-xs text-gray-500">Track active driver routes, transit progress, and resolve delivery exceptions.</p>
              </div>

              {/* Delivery Exceptions Section */}
              {exceptions.length > 0 && (
                <div className="admin-card border-l-4 border-l-red-600 space-y-3">
                  <h3 className="font-bold text-sm text-red-900 flex items-center gap-1.5">
                    <AlertTriangle size={16} className="text-red-600" />
                    Delivery Exceptions Requiring Action ({exceptions.length})
                  </h3>
                  <div className="space-y-2">
                    {exceptions.map((exc) => (
                      <div key={exc.delivery_id} className="p-3 rounded bg-red-50 border border-red-200 text-xs flex justify-between items-center">
                        <div>
                          <strong className="text-red-900 block">{exc.exception_type} — Delivery {exc.delivery_id}</strong>
                          <span className="text-red-700">{exc.reason}</span>
                        </div>
                        <button
                          onClick={() => {
                            setSelectedReassignDelivery(exc.delivery_id)
                          }}
                          className="px-3 py-1.5 bg-red-700 text-white rounded font-bold hover:bg-red-800 transition"
                        >
                          Reassign Driver
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Active Deliveries Table */}
              <div className="admin-card overflow-x-auto">
                <h3 className="font-bold text-sm text-gray-900 mb-3">Active Rescue Missions</h3>
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500 uppercase text-[10px] tracking-wider font-bold">
                      <th className="py-2.5 px-3">Mission ID</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Driver / Vehicle</th>
                      <th className="py-2.5 px-3">Quantity</th>
                      <th className="py-2.5 px-3">Current Stop</th>
                      <th className="py-2.5 px-3">ETA</th>
                      <th className="py-2.5 px-3">Urgency</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {activeRescues.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="py-6 text-center text-gray-400 italic">
                          No active rescue missions in transit at this moment.
                        </td>
                      </tr>
                    ) : (
                      activeRescues.map((del) => (
                        <tr key={del.delivery_id} className="hover:bg-gray-50 transition">
                          <td className="py-3 px-3 font-semibold text-gray-900">{del.delivery_id}</td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                              {del.status}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className="font-bold block">{del.driver_name || del.driver_id || 'Unassigned'}</span>
                            <span className="text-[11px] text-gray-500">{del.vehicle_type || 'Vehicle pending'}</span>
                          </td>
                          <td className="py-3 px-3 font-bold text-gray-900">{del.quantity_kg} kg</td>
                          <td className="py-3 px-3">{del.current_stop || 'Pickup Point'}</td>
                          <td className="py-3 px-3">{del.estimated_eta || '—'}</td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                del.urgency_level === 'AT_RISK'
                                  ? 'bg-red-100 text-red-800'
                                  : del.urgency_level === 'ELEVATED'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-emerald-100 text-emerald-800'
                              }`}
                            >
                              {del.urgency_level}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => setSelectedReassignDelivery(del.delivery_id)}
                              className="px-2 py-1 text-[11px] font-semibold text-gray-700 hover:text-emerald-800 border border-gray-200 rounded hover:bg-gray-100"
                            >
                              Reassign
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 4: INTEGRITY REVIEWS */}
          {/* ================================================================= */}
          {activeTab === 'integrity' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-bold text-gray-900">Package Integrity & Seal Verification Queue</h2>
                <p className="text-xs text-gray-500">Examine visual consistency between pickup and delivery checkpoints.</p>
              </div>

              <div className="admin-card overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500 uppercase text-[10px] tracking-wider font-bold">
                      <th className="py-2.5 px-3">Check ID</th>
                      <th className="py-2.5 px-3">Delivery</th>
                      <th className="py-2.5 px-3">Pickup Seal</th>
                      <th className="py-2.5 px-3">Delivery Seal</th>
                      <th className="py-2.5 px-3">AI Visual Signal</th>
                      <th className="py-2.5 px-3">Review Status</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {integrityReviews.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-6 text-center text-gray-400 italic">
                          No pending package integrity discrepancies detected.
                        </td>
                      </tr>
                    ) : (
                      integrityReviews.map((chk) => (
                        <tr key={chk.id} className="hover:bg-gray-50 transition">
                          <td className="py-3 px-3 font-semibold text-gray-900">{chk.id}</td>
                          <td className="py-3 px-3">{chk.delivery_id}</td>
                          <td className="py-3 px-3 font-mono">{chk.pickup_seal_status || 'INTACT'}</td>
                          <td className="py-3 px-3 font-mono text-red-600 font-bold">{chk.delivery_seal_status || 'BROKEN'}</td>
                          <td className="py-3 px-3">
                            <span className="text-xs">{chk.ai_reason || 'Score: ' + (chk.ai_integrity_score || 'N/A')}</span>
                          </td>
                          <td className="py-3 px-3 font-bold text-amber-800">{chk.manual_review_status}</td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => setSelectedIntegrityCheck(chk)}
                              className="px-2.5 py-1 bg-emerald-50 text-emerald-800 rounded font-bold hover:bg-emerald-100 border border-emerald-200"
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 5: FINANCIAL EXCEPTIONS */}
          {/* ================================================================= */}
          {activeTab === 'financial' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-base font-bold text-gray-900">Financial Exceptions & Ledger Audits</h2>
                  <p className="text-xs text-gray-500">Inspect failed transactions, stale reservations, and execute controlled adjustments.</p>
                </div>
                <button
                  onClick={() => setShowAdjustModal(true)}
                  className="px-3 py-1.5 bg-emerald-700 text-white rounded text-xs font-bold hover:bg-emerald-800 transition"
                >
                  + Create Controlled Adjustment
                </button>
              </div>

              <div className="admin-card overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500 uppercase text-[10px] tracking-wider font-bold">
                      <th className="py-2.5 px-3">Exception ID</th>
                      <th className="py-2.5 px-3">Type</th>
                      <th className="py-2.5 px-3">Severity</th>
                      <th className="py-2.5 px-3">Related Reference</th>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3">Amount</th>
                      <th className="py-2.5 px-3">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {financialExceptions.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-6 text-center text-gray-400 italic">
                          No financial exceptions or balance invariant violations found.
                        </td>
                      </tr>
                    ) : (
                      financialExceptions.map((exc) => (
                        <tr key={exc.id} className="hover:bg-gray-50 transition">
                          <td className="py-3 px-3 font-semibold text-gray-900">{exc.id}</td>
                          <td className="py-3 px-3 font-bold">{exc.exception_type}</td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800">
                              {exc.severity}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-mono text-gray-600">{exc.related_entity_id}</td>
                          <td className="py-3 px-3">{exc.description}</td>
                          <td className="py-3 px-3 font-bold text-gray-900">
                            {exc.amount !== null && exc.amount !== undefined ? `₹${exc.amount}` : '—'}
                          </td>
                          <td className="py-3 px-3 text-gray-500">{exc.created_at ? exc.created_at.slice(0, 16) : '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 6: USERS & DRIVERS */}
          {/* ================================================================= */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-base font-bold text-gray-900">User & Driver Directory</h2>
                  <p className="text-xs text-gray-500">Inspect registered donors, NGOs, and delivery partners.</p>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Search name, phone, business..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        getAdminUsers({ search: userSearch }).then((res) => setUsersList(res.items))
                      }
                    }}
                    className="px-3 py-1.5 border border-gray-300 rounded text-xs w-64"
                  />
                  <button
                    onClick={() => getAdminUsers({ search: userSearch }).then((res) => setUsersList(res.items))}
                    className="px-3 py-1.5 bg-gray-100 border border-gray-300 rounded text-xs font-semibold hover:bg-gray-200"
                  >
                    Search
                  </button>
                </div>
              </div>

              <div className="admin-card overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500 uppercase text-[10px] tracking-wider font-bold">
                      <th className="py-2.5 px-3">Name</th>
                      <th className="py-2.5 px-3">Role</th>
                      <th className="py-2.5 px-3">Organization / Vehicle</th>
                      <th className="py-2.5 px-3">Phone</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Verification</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {usersList.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-6 text-center text-gray-400 italic">
                          No users matched search criteria.
                        </td>
                      </tr>
                    ) : (
                      usersList.map((u) => (
                        <tr key={u.id} className="hover:bg-gray-50 transition">
                          <td className="py-3 px-3 font-bold text-gray-900">{u.full_name || u.id}</td>
                          <td className="py-3 px-3 font-semibold">{u.role}</td>
                          <td className="py-3 px-3">{u.business_or_org_name || '—'}</td>
                          <td className="py-3 px-3 font-mono">{u.phone || '—'}</td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                u.is_active ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-800'
                              }`}
                            >
                              {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className="font-semibold text-gray-600">{u.verification_status || 'PENDING'}</span>
                          </td>
                          <td className="py-3 px-3 text-right">
                            {u.is_active ? (
                              <button
                                onClick={() => setUserActionModal({ user: u, type: 'deactivate' })}
                                className="px-2 py-1 text-[11px] text-red-700 border border-red-200 rounded hover:bg-red-50 font-semibold"
                              >
                                Deactivate
                              </button>
                            ) : (
                              <button
                                onClick={() => setUserActionModal({ user: u, type: 'activate' })}
                                className="px-2 py-1 text-[11px] text-emerald-700 border border-emerald-200 rounded hover:bg-emerald-50 font-semibold"
                              >
                                Reactivate
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 7: RESCUE ANALYTICS */}
          {/* ================================================================= */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-base font-bold text-gray-900">Rescue Logistics & Impact Analytics</h2>
                  <p className="text-xs text-gray-500">Grounded in recorded ledger transactions and environmental factors.</p>
                </div>
                <div className="flex gap-1.5 bg-gray-100 p-1 rounded-lg border border-gray-200">
                  {['today', '7d', '30d', '90d'].map((p) => (
                    <button
                      key={p}
                      onClick={() => setAnalyticsPeriod(p)}
                      className={`px-2.5 py-1 text-xs rounded font-semibold transition ${
                        analyticsPeriod === p ? 'bg-white shadow text-gray-900 font-bold' : 'text-gray-500 hover:text-gray-900'
                      }`}
                    >
                      {p.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* Impact Metrics */}
              {impactData && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="admin-card border-t-4 border-t-emerald-700">
                    <span className="text-xs font-bold uppercase text-gray-500">Food Rescued</span>
                    <div className="text-3xl font-bold text-emerald-800 mt-1">
                      {impactData.total_food_rescued_kg.toLocaleString()} kg
                    </div>
                    <span className="text-xs text-gray-500 mt-1 block">In timeframe: {analyticsPeriod}</span>
                  </div>
                  <div className="admin-card border-t-4 border-t-emerald-700">
                    <span className="text-xs font-bold uppercase text-gray-500">Meal Equivalents</span>
                    <div className="text-3xl font-bold text-gray-900 mt-1">
                      {impactData.meal_equivalents.toLocaleString()}
                    </div>
                    <span className="text-xs text-gray-500 mt-1 block">0.4 kg per meal equivalent</span>
                  </div>
                  <div className="admin-card border-t-4 border-t-emerald-700">
                    <span className="text-xs font-bold uppercase text-gray-500">Avoided CO2e</span>
                    <div className="text-3xl font-bold text-gray-900 mt-1">
                      {impactData.co2e_avoided_kg.toLocaleString()} kg
                    </div>
                    <span className="text-xs text-gray-500 mt-1 block">2.5 kg CO2e per kg saved</span>
                  </div>
                </div>
              )}

              {/* Operational & Financial Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {opsData && (
                  <div className="admin-card space-y-3">
                    <h3 className="font-bold text-sm text-gray-900">Operational Delivery Logistics</h3>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Delivery Completion Rate</span>
                        <strong className="text-emerald-800">{opsData.delivery_completion_rate}%</strong>
                      </div>
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Failure Rate</span>
                        <strong className="text-red-700">{opsData.failure_rate}%</strong>
                      </div>
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Average Transit Duration</span>
                        <strong>{opsData.average_delivery_time_minutes} minutes</strong>
                      </div>
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Reassignments Required</span>
                        <strong>{opsData.reassignment_count}</strong>
                      </div>
                    </div>
                  </div>
                )}

                {finData && (
                  <div className="admin-card space-y-3">
                    <h3 className="font-bold text-sm text-gray-900">Financial Ledger Breakdown</h3>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Total Delivery Charges</span>
                        <strong className="text-gray-900">₹{finData.delivery_charges_total.toLocaleString()}</strong>
                      </div>
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>AnnaSetu Platform Fees (12%)</span>
                        <strong className="text-emerald-800">₹{finData.platform_fees_total.toLocaleString()}</strong>
                      </div>
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Driver Payouts</span>
                        <strong>₹{finData.driver_payouts_total.toLocaleString()}</strong>
                      </div>
                      <div className="flex justify-between p-2 rounded bg-gray-50">
                        <span>Subscription Revenue</span>
                        <strong>₹{finData.subscription_revenue_total.toLocaleString()}</strong>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* TAB 8: AUDIT TRAIL */}
          {/* ================================================================= */}
          {activeTab === 'audit' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-base font-bold text-gray-900">Append-Only System Audit Trail</h2>
                <p className="text-xs text-gray-500">Auditable mutation records. Redacted credentials, immutable log history.</p>
              </div>

              <div className="admin-card overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-500 uppercase text-[10px] tracking-wider font-bold">
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Actor</th>
                      <th className="py-2.5 px-3">Action</th>
                      <th className="py-2.5 px-3">Entity Type</th>
                      <th className="py-2.5 px-3">Entity ID</th>
                      <th className="py-2.5 px-3">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {auditLogs.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-6 text-center text-gray-400 italic">
                          No audit trail records found.
                        </td>
                      </tr>
                    ) : (
                      auditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-gray-50 transition">
                          <td className="py-3 px-3 text-gray-500 font-mono text-[11px]">{log.timestamp.slice(0, 19).replace('T', ' ')}</td>
                          <td className="py-3 px-3 font-semibold">{log.actor}</td>
                          <td className="py-3 px-3 font-bold text-gray-900">{log.action}</td>
                          <td className="py-3 px-3">{log.entity_type}</td>
                          <td className="py-3 px-3 font-mono text-[11px] text-gray-600">{log.entity_id || '—'}</td>
                          <td className="py-3 px-3 text-gray-500 font-mono text-[11px]">
                            {JSON.stringify(log.details).slice(0, 50)}...
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ===================================================================== */}
      {/* CONFIRMATION MODALS FOR PRIVILEGED ACTIONS */}
      {/* ===================================================================== */}

      {/* 1. Verification Decision Modal */}
      {verifModalAction && selectedVerif && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-gray-900">
              Confirm {verifModalAction.toUpperCase()}: Case {selectedVerif.id}
            </h3>
            <p className="text-xs text-gray-600">
              {verifModalAction === 'approve' && 'This action grants authoritative VERIFIED status to the applicant profile.'}
              {verifModalAction === 'reject' && 'This action rejects the verification. Documented rejection reason is mandatory.'}
              {verifModalAction === 'review' && 'This action escalates the case into UNDER_REVIEW status with your notes.'}
            </p>

            <div>
              <label className="text-xs font-bold text-gray-700 block mb-1">
                {verifModalAction === 'reject' ? 'Rejection Reason (Required)' : 'Review Notes (Audited)'}
              </label>
              <textarea
                value={verifNote}
                onChange={(e) => setVerifNote(e.target.value)}
                rows={3}
                placeholder="Enter auditable notes..."
                className="w-full text-xs p-2.5 border border-gray-300 rounded-md"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  setVerifModalAction(null)
                  setVerifNote('')
                }}
                className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (verifModalAction === 'approve') {
                    await approveVerification(selectedVerif.id, verifNote)
                  } else if (verifModalAction === 'reject') {
                    if (!verifNote.trim()) return alert('Rejection reason required.')
                    await rejectVerification(selectedVerif.id, verifNote)
                  } else if (verifModalAction === 'review') {
                    await requestVerificationReview(selectedVerif.id, verifNote)
                  }
                  setVerifModalAction(null)
                  setVerifNote('')
                  const updated = await getAdminVerificationDetail(selectedVerif.id)
                  setSelectedVerif(updated)
                  loadOverview()
                }}
                className={`px-4 py-1.5 text-xs font-bold text-white rounded ${
                  verifModalAction === 'approve'
                    ? 'bg-emerald-700 hover:bg-emerald-800'
                    : verifModalAction === 'reject'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-gray-800 hover:bg-gray-900'
                }`}
              >
                Confirm Action
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Reassign Delivery Modal */}
      {selectedReassignDelivery && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-gray-900">
              Reassign Delivery: {selectedReassignDelivery}
            </h3>
            <p className="text-xs text-gray-600">
              Specify the target verified driver ID and the auditable reason for operational reassignment.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">New Driver ID</label>
                <input
                  type="text"
                  placeholder="e.g. user-driver-2"
                  value={newDriverId}
                  onChange={(e) => setNewDriverId(e.target.value)}
                  className="w-full text-xs p-2 border border-gray-300 rounded"
                />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">Reason for Reassignment</label>
                <textarea
                  placeholder="e.g. Previous driver mechanical breakdown"
                  value={reassignReason}
                  onChange={(e) => setReassignReason(e.target.value)}
                  rows={2}
                  className="w-full text-xs p-2 border border-gray-300 rounded"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  setSelectedReassignDelivery(null)
                  setNewDriverId('')
                  setReassignReason('')
                }}
                className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!newDriverId.trim() || !reassignReason.trim()) {
                    return alert('Driver ID and reason are both required.')
                  }
                  await reassignDelivery(selectedReassignDelivery, newDriverId, reassignReason)
                  setSelectedReassignDelivery(null)
                  setNewDriverId('')
                  setReassignReason('')
                  getActiveRescueOperations().then(setActiveRescues)
                  getDeliveryExceptions().then(setExceptions)
                  loadOverview()
                }}
                className="px-4 py-1.5 text-xs font-bold text-white bg-red-700 hover:bg-red-800 rounded"
              >
                Confirm Reassignment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. User Activation / Deactivation Modal */}
      {userActionModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-gray-900">
              Confirm {userActionModal.type === 'activate' ? 'Activation' : 'Deactivation'}
            </h3>
            <p className="text-xs text-gray-600">
              User: {userActionModal.user.full_name} ({userActionModal.user.id}). This action is auditable.
            </p>

            <div>
              <label className="text-xs font-bold text-gray-700 block mb-1">Mandatory Reason</label>
              <textarea
                value={userActionReason}
                onChange={(e) => setUserActionReason(e.target.value)}
                placeholder="Document administrative justification..."
                rows={2}
                className="w-full text-xs p-2 border border-gray-300 rounded"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  setUserActionModal(null)
                  setUserActionReason('')
                }}
                className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!userActionReason.trim()) return alert('Reason is required.')
                  if (userActionModal.type === 'activate') {
                    await activateUser(userActionModal.user.id, userActionReason)
                  } else {
                    await deactivateUser(userActionModal.user.id, userActionReason)
                  }
                  setUserActionModal(null)
                  setUserActionReason('')
                  getAdminUsers({ search: userSearch }).then((res) => setUsersList(res.items))
                  loadOverview()
                }}
                className={`px-4 py-1.5 text-xs font-bold text-white rounded ${
                  userActionModal.type === 'activate' ? 'bg-emerald-700 hover:bg-emerald-800' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                Confirm {userActionModal.type === 'activate' ? 'Activation' : 'Deactivation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4. Financial Adjustment Modal */}
      {showAdjustModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-gray-900">Create Controlled Ledger Adjustment</h3>
            <p className="text-xs text-gray-600">
              Creates an auditable ADJUSTMENT transaction without altering historical transactions in-place.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">Target Wallet ID</label>
                <input
                  type="text"
                  placeholder="e.g. w-admin-test"
                  value={adjWalletId}
                  onChange={(e) => setAdjWalletId(e.target.value)}
                  className="w-full text-xs p-2 border border-gray-300 rounded"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Type</label>
                  <select
                    value={adjType}
                    onChange={(e: any) => setAdjType(e.target.value)}
                    className="w-full text-xs p-2 border border-gray-300 rounded"
                  >
                    <option value="CREDIT">CREDIT</option>
                    <option value="DEBIT">DEBIT</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-700 block mb-1">Amount (INR)</label>
                  <input
                    type="number"
                    placeholder="100.00"
                    value={adjAmount}
                    onChange={(e) => setAdjAmount(e.target.value)}
                    className="w-full text-xs p-2 border border-gray-300 rounded"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-gray-700 block mb-1">Auditable Reason</label>
                <textarea
                  placeholder="Document reason for balance adjustment..."
                  value={adjReason}
                  onChange={(e) => setAdjReason(e.target.value)}
                  rows={2}
                  className="w-full text-xs p-2 border border-gray-300 rounded"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  setShowAdjustModal(false)
                  setAdjWalletId('')
                  setAdjAmount('')
                  setAdjReason('')
                }}
                className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  const amt = parseFloat(adjAmount)
                  if (!adjWalletId.trim() || isNaN(amt) || amt <= 0 || !adjReason.trim()) {
                    return alert('Wallet ID, valid positive amount, and reason are required.')
                  }
                  await createFinancialAdjustment(adjWalletId, amt, adjType, adjReason)
                  setShowAdjustModal(false)
                  setAdjWalletId('')
                  setAdjAmount('')
                  setAdjReason('')
                  getAdminFinancialExceptions().then(setFinancialExceptions)
                  loadOverview()
                }}
                className="px-4 py-1.5 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 rounded"
              >
                Apply Adjustment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 5. Package Integrity Review Modal */}
      {selectedIntegrityCheck && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="font-bold text-base text-gray-900">
              Review Integrity Check: {selectedIntegrityCheck.id}
            </h3>
            <div className="text-xs space-y-1 text-gray-700 bg-gray-50 p-3 rounded border border-gray-200">
              <div>Pickup Seal: <strong>{selectedIntegrityCheck.pickup_seal_status || 'INTACT'}</strong></div>
              <div>Delivery Seal: <strong className="text-red-600">{selectedIntegrityCheck.delivery_seal_status || 'BROKEN'}</strong></div>
              <div>AI Visual Signal: {selectedIntegrityCheck.ai_reason || 'Score: ' + (selectedIntegrityCheck.ai_integrity_score || 'N/A')}</div>
            </div>

            <div className="p-2.5 rounded bg-emerald-50/60 border border-emerald-200 text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#2f5536] flex items-center gap-1">
                  <Sparkles size={13} /> Visual Food Quality / Integrity AI
                </span>
                <span className="text-[10px] text-gray-500 uppercase font-semibold">Non-Authoritative</span>
              </div>
              <p className="text-[11px] text-gray-600">
                Visual inspection signals aid review. AI does not certify food safety or compliance.
              </p>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-700 block mb-1">Review Outcome Notes</label>
              <textarea
                value={integrityNote}
                onChange={(e) => setIntegrityNote(e.target.value)}
                placeholder="Enter review findings..."
                rows={2}
                className="w-full text-xs p-2 border border-gray-300 rounded"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => {
                  setSelectedIntegrityCheck(null)
                  setIntegrityNote('')
                }}
                className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  await submitAdminIntegrityReview(selectedIntegrityCheck.id, 'REQUIRES_ACTION', integrityNote)
                  setSelectedIntegrityCheck(null)
                  setIntegrityNote('')
                  getAdminIntegrityReviews().then(setIntegrityReviews)
                  loadOverview()
                }}
                className="px-3 py-1.5 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 rounded"
              >
                Action Required
              </button>
              <button
                onClick={async () => {
                  await submitAdminIntegrityReview(selectedIntegrityCheck.id, 'CLEARED', integrityNote)
                  setSelectedIntegrityCheck(null)
                  setIntegrityNote('')
                  getAdminIntegrityReviews().then(setIntegrityReviews)
                  loadOverview()
                }}
                className="px-3 py-1.5 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 rounded"
              >
                Clear Check
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
