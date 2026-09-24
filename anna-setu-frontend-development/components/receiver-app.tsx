'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import '@/app/receiver/receiver.css'
import {
  Utensils,
  Plus,
  Truck,
  History,
  TrendingUp,
  ShieldCheck,
  Bell,
  Clock,
  MapPin,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Leaf,
  LogOut,
  Navigation,
  X,
  Search,
  Filter,
  Download,
  Award,
  FileText,
  Check,
  Phone,
  Thermometer,
  AlertCircle,
  Calendar,
  ArrowRight,
  ExternalLink,
  FileSpreadsheet,
  CheckCircle,
  Sparkles,
  Radio,
} from 'lucide-react'
import { receiverService } from '@/lib/services/receiver'
import type { ReceiverData, ReceiverDelivery, ReceiverNeedSummary } from '@/lib/types/receiver'
import { VerificationBadge } from '@/components/verification/VerificationBadge'
import { RescueStatus } from '@/components/rescue/RescueStatus'
import { FoodTypeBadge } from '@/components/rescue/FoodTypeBadge'
import { AIInsight } from '@/components/shared/AIInsight'
import { LoadingState } from '@/components/shared/LoadingState'
import { useAuth } from '@/lib/auth/context'

export default function ReceiverApp({ path = '/receiver/dashboard' }: { path?: string }) {
  const { user, profile, verificationStatus, signOut } = useAuth()
  const isVerified = verificationStatus === 'VERIFIED' || verificationStatus === 'verified'
  const [data, setData] = useState<ReceiverData | null>(null)

  // Initialize active tab from URL path if applicable
  const getInitialTab = (): 'overview' | 'needs' | 'incoming' | 'history' => {
    if (path.includes('/needs')) return 'needs'
    if (path.includes('/incoming') || path.includes('/deliveries')) return 'incoming'
    if (path.includes('/history')) return 'history'
    return 'overview'
  }

  const [activeTab, setActiveTab] = useState<'overview' | 'needs' | 'incoming' | 'history'>(getInitialTab())
  const [showNeedModal, setShowNeedModal] = useState(false)
  const [showHandoffModal, setShowHandoffModal] = useState(false)
  const [selectedCertificate, setSelectedCertificate] = useState<ReceiverDelivery | null>(null)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [otp, setOtp] = useState('')
  const [otpMessage, setOtpMessage] = useState('')
  const [gpsReceiverStatus, setGpsReceiverStatus] = useState('')
  const [driverContactStatus, setDriverContactStatus] = useState<string | null>(null)

  // Search & Filter States
  const [needsFilter, setNeedsFilter] = useState<'ALL' | 'OPEN' | 'MATCHED'>('ALL')
  const [needsSearch, setNeedsSearch] = useState('')
  const [historySearch, setHistorySearch] = useState('')

  const [needForm, setNeedForm] = useState({
    mealPeriod: 'Dinner',
    foodType: 'Vegetarian',
    quantity: 25,
    requiredBy: 'Today, 8:00 PM',
    location: 'Sector 3 Community Kitchen, Malviya Nagar, Jaipur',
  })

  useEffect(() => {
    receiverService.getData().then(setData)
  }, [])

  if (!data) {
    return <LoadingState message="Loading receiver workspace…" className="min-h-screen" />
  }

  const handleCreateNeed = async (e: React.FormEvent) => {
    e.preventDefault()
    await receiverService.createNeed(needForm)
    const updated = await receiverService.getData()
    setData({ ...updated })
    setShowNeedModal(false)
  }

  const handleVerifyHandoff = async () => {
    const res = await receiverService.confirmDelivery('delivery-1', otp)
    setOtpMessage(res.message)
    if (res.ok) {
      setTimeout(() => {
        // Move delivery-1 to history if present
        if (data.incomingDeliveries.length > 0) {
          const verifiedDelivery = data.incomingDeliveries[0]
          const nowStr = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
          const updatedHistory = [
            {
              ...verifiedDelivery,
              status: 'Received' as const,
              arrivalTime: `Today, ${nowStr}`,
            },
            ...data.receivedHistory,
          ]
          setData({
            ...data,
            incomingDeliveries: data.incomingDeliveries.slice(1),
            receivedHistory: updatedHistory,
            impact: {
              ...data.impact,
              deliveriesCompleted: data.impact.deliveriesCompleted + 1,
              mealsReceived: data.impact.mealsReceived + (verifiedDelivery.quantity * 3),
              totalQuantity: data.impact.totalQuantity + verifiedDelivery.quantity,
            },
          })
        }
        setShowHandoffModal(false)
        setOtpMessage('')
        setOtp('')
      }, 1500)
    }
  }

  const exportHistoryCSV = () => {
    const headers = ['ID', 'Food Name', 'Quantity (kg)', 'Donor Organization', 'Driver', 'Arrival Time', 'Verification Status']
    const rows = data.receivedHistory.map((item) => [
      item.id,
      `"${item.foodName}"`,
      item.quantity,
      `"${item.donorName}"`,
      `"${item.driverName}"`,
      `"${item.arrivalTime || 'Delivered'}"`,
      '"Verified Received (OTP Confirmed)"',
    ])
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `annasetu-rescue-history-${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const downloadReportPDF = () => {
    const dummyWindow = window.open('', '_blank')
    if (dummyWindow) {
      dummyWindow.document.write(`
        <html>
          <head>
            <title>AnnaSetu - Community Food Rescue Impact Report</title>
            <style>
              body { font-family: system-ui, -apple-system, sans-serif; padding: 40px; color: #1c1917; }
              h1 { color: #166534; font-size: 24px; margin-bottom: 4px; }
              .meta { font-size: 13px; color: #78716c; margin-bottom: 24px; }
              .stats { display: flex; gap: 20px; margin-bottom: 30px; }
              .stat-box { border: 1px solid #e7e5e4; border-radius: 10px; padding: 16px; min-width: 140px; background: #fafaf9; }
              .stat-val { font-size: 22px; font-weight: bold; color: #166534; }
              .stat-lbl { font-size: 12px; color: #78716c; }
              table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }
              th, td { border: 1px solid #e7e5e4; padding: 10px 12px; text-align: left; }
              th { background: #f5f5f4; font-weight: 600; }
              .footer { margin-top: 40px; font-size: 11px; color: #a8a29e; border-top: 1px solid #e7e5e4; padding-top: 12px; }
            </style>
          </head>
          <body>
            <h1>AnnaSetu — Verified Food Rescue & Shelter Impact Report</h1>
            <div class="meta">
              Organization: <strong>${profile?.full_name || data.organizationName}</strong> | Generated on: ${new Date().toLocaleDateString('en-IN', { dateStyle: 'full' })}
            </div>
            <div class="stats">
              <div class="stat-box"><div class="stat-val">${data.impact.mealsReceived}</div><div class="stat-lbl">Meals Served</div></div>
              <div class="stat-box"><div class="stat-val">${data.impact.totalQuantity} kg</div><div class="stat-lbl">Food Rescued</div></div>
              <div class="stat-box"><div class="stat-val">${data.impact.deliveriesCompleted}</div><div class="stat-lbl">Handoffs Completed</div></div>
              <div class="stat-box"><div class="stat-val">${(data.impact.totalQuantity * 2.5).toFixed(0)} kg</div><div class="stat-lbl">CO₂e Avoided</div></div>
            </div>
            <h3>Historical Handoff Log</h3>
            <table>
              <thead>
                <tr>
                  <th>Food Item</th>
                  <th>Quantity</th>
                  <th>Donor Organization</th>
                  <th>Delivery Partner</th>
                  <th>Arrival Time</th>
                  <th>Chain of Custody</th>
                </tr>
              </thead>
              <tbody>
                ${data.receivedHistory
                  .map(
                    (item) => `
                  <tr>
                    <td><strong>${item.foodName}</strong></td>
                    <td>${item.quantity} ${item.unit}</td>
                    <td>${item.donorName}</td>
                    <td>${item.driverName}</td>
                    <td>${item.arrivalTime || 'Delivered'}</td>
                    <td><span style="color:#166534; font-weight:600;">✓ OTP Verified</span></td>
                  </tr>
                `
                  )
                  .join('')}
              </tbody>
            </table>
            <div class="footer">
              AnnaSetu Zero-Waste Network · Certified under Good Samaritan Food Donation Standards.
            </div>
          </body>
        </html>
      `)
      dummyWindow.document.close()
      setTimeout(() => dummyWindow.print(), 500)
    }
  }

  // Filtered Needs
  const filteredNeeds = data.activeNeeds.filter((need) => {
    if (needsFilter === 'OPEN' && need.status !== 'Open') return false
    if (needsFilter === 'MATCHED' && need.status !== 'Matched') return false
    if (needsSearch) {
      const q = needsSearch.toLowerCase()
      return (
        need.mealPeriod.toLowerCase().includes(q) ||
        need.foodType.toLowerCase().includes(q) ||
        need.status.toLowerCase().includes(q)
      )
    }
    return true
  })

  // Filtered History
  const filteredHistory = data.receivedHistory.filter((item) => {
    if (!historySearch) return true
    const q = historySearch.toLowerCase()
    return (
      item.foodName.toLowerCase().includes(q) ||
      item.donorName.toLowerCase().includes(q) ||
      item.driverName.toLowerCase().includes(q)
    )
  })

  return (
    <div className="receiver-shell">
      {/* Sidebar Navigation */}
      <aside className="receiver-sidebar">
        <div className="receiver-sidebar-header">
          <Link href="/" className="flex items-center gap-2 text-emerald-950 font-bold text-lg">
            <span className="w-8 h-8 rounded-lg bg-emerald-800 text-amber-200 flex items-center justify-center -rotate-6">
              <Leaf size={18} />
            </span>
            <span>AnnaSetu</span>
          </Link>
          <div className="mt-4">
            <div className="text-sm font-semibold text-stone-900 truncate">
              {profile?.full_name || data.organizationName}
            </div>
            <div className="mt-1">
              <VerificationBadge status={verificationStatus} />
            </div>
          </div>
        </div>

        <nav className="receiver-nav">
          <button
            onClick={() => setActiveTab('overview')}
            className={`receiver-nav-item w-full text-left cursor-pointer border-0 ${activeTab === 'overview' ? 'active' : ''}`}
          >
            <TrendingUp size={16} />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab('needs')}
            className={`receiver-nav-item w-full text-left cursor-pointer border-0 ${activeTab === 'needs' ? 'active' : ''}`}
          >
            <Utensils size={16} />
            <span>Active Needs</span>
            <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-stone-200 text-stone-700">
              {data.activeNeeds.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('incoming')}
            className={`receiver-nav-item w-full text-left cursor-pointer border-0 ${activeTab === 'incoming' ? 'active' : ''}`}
          >
            <Truck size={16} />
            <span>Incoming Deliveries</span>
            {data.incomingDeliveries.length > 0 && (
              <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-blue-600 text-white animate-pulse">
                {data.incomingDeliveries.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`receiver-nav-item w-full text-left cursor-pointer border-0 ${activeTab === 'history' ? 'active' : ''}`}
          >
            <History size={16} />
            <span>Rescue History</span>
            <span className="ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-stone-200 text-stone-700">
              {data.receivedHistory.length}
            </span>
          </button>
        </nav>

        <div className="p-4 border-t border-stone-200 mt-auto">
          <button
            onClick={() => signOut()}
            className="flex items-center gap-2 text-xs font-semibold text-stone-500 hover:text-stone-800 transition-colors bg-transparent border-0 cursor-pointer p-0 w-full"
          >
            <LogOut size={14} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <div className="receiver-main">
        {/* Topbar */}
        <header className="receiver-topbar">
          <div>
            <h1 className="text-lg font-bold text-stone-900">
              {activeTab === 'overview' && 'Community Food Hub — Overview'}
              {activeTab === 'needs' && 'Active Food Requirements'}
              {activeTab === 'incoming' && 'Incoming Food Handoffs'}
              {activeTab === 'history' && 'Food Rescue Records & Certifications'}
            </h1>
            <p className="text-xs text-stone-500">
              {activeTab === 'overview' && 'Executive summary of shelter capacity, real-time incoming meals, and hunger relief impact'}
              {activeTab === 'needs' && 'Manage dietary requirements and meal quantities for AI automated surplus routing'}
              {activeTab === 'incoming' && 'Real-time vehicle telemetry, cold-chain monitoring, and OTP verification'}
              {activeTab === 'history' && 'Audited ledger of completed food rescues and safe handoff certificates'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowNeedModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white rounded-full text-xs font-bold transition-all shadow-sm cursor-pointer"
            >
              <Plus size={15} />
              Raise Food Need
            </button>

            <div className="relative">
              <button
                type="button"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 p-1.5 pl-3 rounded-full hover:bg-stone-100 transition-colors border border-stone-200 bg-white cursor-pointer"
                aria-label="Receiver profile menu"
                aria-expanded={userMenuOpen}
              >
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-bold text-stone-900 leading-tight">
                    {profile?.full_name || data.organizationName}
                  </div>
                  <div className="text-[10px] text-emerald-700 font-medium">Receiver Hub</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-emerald-800 text-amber-200 flex items-center justify-center font-bold text-xs">
                  {(profile?.full_name || data.organizationName).slice(0, 2).toUpperCase()}
                </div>
                <ChevronDown
                  size={14}
                  className={`text-stone-400 transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {userMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-stone-200 py-2 z-50 text-left">
                    <div className="px-4 py-3 border-b border-stone-100">
                      <p className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">Signed in as</p>
                      <p className="text-sm font-bold text-stone-900 truncate">
                        {profile?.full_name || data.organizationName}
                      </p>
                      <p className="text-xs text-stone-500 truncate">{user?.email || 'receiver@hopehaven.demo'}</p>
                      <div className="mt-2">
                        <VerificationBadge status={verificationStatus} />
                      </div>
                    </div>
                    <div className="py-1">
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab('overview')
                          setUserMenuOpen(false)
                        }}
                        className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${
                          activeTab === 'overview' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'
                        }`}
                      >
                        <TrendingUp size={14} className="text-stone-400" /> Overview & Capacity
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab('needs')
                          setUserMenuOpen(false)
                        }}
                        className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${
                          activeTab === 'needs' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'
                        }`}
                      >
                        <Utensils size={14} className="text-stone-400" /> Active Food Needs
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab('incoming')
                          setUserMenuOpen(false)
                        }}
                        className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${
                          activeTab === 'incoming' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'
                        }`}
                      >
                        <Truck size={14} className="text-stone-400" /> Incoming Deliveries
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab('history')
                          setUserMenuOpen(false)
                        }}
                        className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${
                          activeTab === 'history' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'
                        }`}
                      >
                        <History size={14} className="text-stone-400" /> Rescue History
                      </button>
                    </div>
                    <div className="pt-1 border-t border-stone-100">
                      <button
                        type="button"
                        onClick={() => {
                          setUserMenuOpen(false)
                          signOut()
                        }}
                        className="w-full flex items-center gap-2 px-4 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer border-0 bg-transparent text-left"
                      >
                        <LogOut size={14} /> Sign out
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Dynamic Tab Body */}
        <main className="receiver-content space-y-6">
          {/* ========================================================= */}
          {/* TAB 1: OVERVIEW                                           */}
          {/* ========================================================= */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* AI Dispatch Insight Banner */}
              <AIInsight
                title="Smart Allocation Alert"
                text="Your open lunch capacity was automatically matched to surplus vegetarian meals from Green Leaf Catering (2.4 km away). Driver is currently en route."
                metric="Optimal Match 96%"
              />

              {/* 4 Primary Metric Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="receiver-card p-4">
                  <div className="flex items-center justify-between text-stone-500 mb-1">
                    <span className="text-xs font-medium">Open Capacity</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold">Active</span>
                  </div>
                  <div className="text-2xl font-bold text-stone-900">
                    {data.openCapacity} <span className="text-xs font-normal text-stone-500">kg</span>
                  </div>
                  <span className="text-[11px] text-emerald-700 mt-1 block font-medium">Ready for immediate intake</span>
                </div>

                <div className="receiver-card p-4">
                  <div className="flex items-center justify-between text-stone-500 mb-1">
                    <span className="text-xs font-medium">Active Needs</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-semibold">Live</span>
                  </div>
                  <div className="text-2xl font-bold text-stone-900">{data.activeNeeds.length}</div>
                  <span className="text-[11px] text-purple-700 mt-1 block font-medium">
                    {data.activeNeeds.filter((n) => n.status === 'Matched').length} matched ·{' '}
                    {data.activeNeeds.filter((n) => n.status === 'Open').length} open
                  </span>
                </div>

                <div className="receiver-card p-4">
                  <div className="flex items-center justify-between text-stone-500 mb-1">
                    <span className="text-xs font-medium">Incoming Today</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold animate-pulse">En route</span>
                  </div>
                  <div className="text-2xl font-bold text-stone-900">
                    {data.incomingDeliveries.reduce((sum, d) => sum + d.quantity, 0)}{' '}
                    <span className="text-xs font-normal text-stone-500">kg</span>
                  </div>
                  <span className="text-[11px] text-blue-700 mt-1 block font-medium">
                    {data.incomingDeliveries.length > 0 ? `ETA ${data.incomingDeliveries[0].eta || 11} mins` : 'No batches en route'}
                  </span>
                </div>

                <div className="receiver-card p-4">
                  <div className="flex items-center justify-between text-stone-500 mb-1">
                    <span className="text-xs font-medium">Meals Served</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 font-semibold">Total</span>
                  </div>
                  <div className="text-2xl font-bold text-stone-900">{data.impact.mealsReceived}</div>
                  <span className="text-[11px] text-stone-500 mt-1 block font-medium">
                    {data.impact.deliveriesCompleted} verified handoffs
                  </span>
                </div>
              </div>

              {/* Quick Actions Action Callout */}
              <div className="bg-gradient-to-r from-emerald-800 to-teal-900 text-white rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Sparkles size={16} className="text-amber-300" />
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-200">Surplus Routing Network</span>
                  </div>
                  <h3 className="text-base font-bold text-white mt-1">Expecting a community meal surge tonight?</h3>
                  <p className="text-xs text-emerald-100/90 mt-0.5">
                    Raise an active food requirement with your required meal period, dietary preference, and location.
                  </p>
                </div>
                <button
                  onClick={() => setShowNeedModal(true)}
                  className="px-4 py-2.5 bg-amber-400 hover:bg-amber-300 text-emerald-950 font-bold text-xs rounded-xl transition-all shadow shrink-0 cursor-pointer flex items-center gap-2"
                >
                  <Plus size={15} /> Post New Food Need
                </button>
              </div>

              {/* Two Column Grid: Incoming Deliveries Snapshot & Active Needs Snapshot */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Incoming Deliveries Card */}
                <div className="receiver-card space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                        <Truck size={16} className="text-blue-600" /> Incoming Deliveries
                      </h2>
                      <p className="text-xs text-stone-500">Live batches arriving at your facility</p>
                    </div>
                    <button
                      onClick={() => setActiveTab('incoming')}
                      className="text-xs font-bold text-emerald-800 hover:text-emerald-900 flex items-center gap-1 cursor-pointer bg-transparent border-0 p-0"
                    >
                      Track All <ChevronRight size={14} />
                    </button>
                  </div>

                  {data.incomingDeliveries.length > 0 ? (
                    <div className="space-y-3">
                      {data.incomingDeliveries.map((del) => (
                        <div
                          key={del.id}
                          className="p-3.5 rounded-xl border border-blue-100 bg-blue-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-stone-900">{del.foodName}</span>
                              <FoodTypeBadge type="Vegetarian" />
                            </div>
                            <p className="text-xs text-stone-600 mt-1">
                              From <strong>{del.donorName}</strong> · Driver <strong>{del.driverName}</strong>
                            </p>
                            <div className="flex items-center gap-3 text-xs text-blue-800 mt-1.5 font-medium">
                              <span className="inline-flex items-center gap-1">
                                <Clock size={12} /> ETA {del.eta || 11} mins
                              </span>
                              <span>•</span>
                              <span>
                                {del.quantity} {del.unit} (~{del.quantity * 3} meals)
                              </span>
                            </div>
                          </div>

                          <button
                            onClick={() => setShowHandoffModal(true)}
                            className="px-3.5 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-bold rounded-lg transition-colors shadow-sm shrink-0 cursor-pointer"
                          >
                            Verify OTP
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-8 text-center border border-dashed border-stone-200 rounded-xl bg-stone-50/60">
                      <Truck size={24} className="mx-auto text-stone-400 mb-2" />
                      <p className="text-xs font-semibold text-stone-600">No active deliveries en route right now</p>
                      <p className="text-[11px] text-stone-400 mt-0.5">Matched donations will appear here automatically.</p>
                    </div>
                  )}
                </div>

                {/* Active Requirements Snapshot */}
                <div className="receiver-card space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                        <Utensils size={16} className="text-emerald-700" /> Active Demands
                      </h2>
                      <p className="text-xs text-stone-500">Requirements queued for surplus matching</p>
                    </div>
                    <button
                      onClick={() => setActiveTab('needs')}
                      className="text-xs font-bold text-emerald-800 hover:text-emerald-900 flex items-center gap-1 cursor-pointer bg-transparent border-0 p-0"
                    >
                      Manage Needs <ChevronRight size={14} />
                    </button>
                  </div>

                  <div className="space-y-3">
                    {data.activeNeeds.slice(0, 3).map((need) => (
                      <div
                        key={need.id}
                        className="p-3 rounded-xl border border-stone-200 bg-white flex items-center justify-between gap-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-stone-900">{need.mealPeriod} Need</span>
                            <FoodTypeBadge type={need.foodType} />
                          </div>
                          <p className="text-[11px] text-stone-500 mt-1">
                            Target: <strong>{need.quantity} kg</strong> · By <strong>{need.requiredBy}</strong>
                          </p>
                        </div>
                        <RescueStatus status={need.status} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Monthly Relief Progression */}
              <div className="receiver-card space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-bold text-stone-900 flex items-center gap-2">
                      <History size={16} className="text-stone-600" /> Community Relief Trend
                    </h2>
                    <p className="text-xs text-stone-500">Monthly surplus food rescued & meals distributed</p>
                  </div>
                  <button
                    onClick={() => setActiveTab('history')}
                    className="text-xs font-bold text-emerald-800 hover:text-emerald-900 flex items-center gap-1 cursor-pointer bg-transparent border-0 p-0"
                  >
                    View All Records <ChevronRight size={14} />
                  </button>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {data.impact.monthly.map((m) => (
                    <div key={m.month} className="p-3 rounded-xl border border-stone-100 bg-stone-50/70 text-center">
                      <span className="text-xs font-semibold text-stone-500 uppercase">{m.month}</span>
                      <div className="text-base font-bold text-emerald-950 mt-1">{m.meals}</div>
                      <span className="text-[10px] text-stone-400 block">meals served</span>
                      <span className="text-[10px] font-semibold text-emerald-700 block mt-1">{m.received} kg</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 2: ACTIVE FOOD NEEDS                                  */}
          {/* ========================================================= */}
          {activeTab === 'needs' && (
            <div className="space-y-6">
              {/* Needs Tab Top Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-stone-900">Shelter Food Demands & Dietary Needs</h2>
                  <p className="text-xs text-stone-500">
                    Define your shelter's meal requirements so local caterers and restaurants can be matched automatically.
                  </p>
                </div>
                <button
                  onClick={() => setShowNeedModal(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white rounded-xl text-xs font-bold transition-all shadow-sm shrink-0 cursor-pointer"
                >
                  <Plus size={15} /> Raise New Need
                </button>
              </div>

              {/* Hub Capacity & Receiving Info Card */}
              <div className="receiver-card bg-gradient-to-r from-emerald-50/60 to-white border border-emerald-100 p-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-800">
                      Receiving Facility Status
                    </span>
                    <h3 className="text-base font-bold text-stone-900">
                      Current Intake Capacity: {data.openCapacity} kg Available
                    </h3>
                    <p className="text-xs text-stone-600 flex items-center gap-1.5">
                      <MapPin size={13} className="text-emerald-700 shrink-0" />
                      Sector 3 Community Kitchen, Malviya Nagar, Jaipur · Receiving Hours: 08:00 AM – 10:00 PM
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs font-semibold text-emerald-800 bg-emerald-100/70 px-3 py-1.5 rounded-lg border border-emerald-200 flex items-center gap-1.5">
                      <CheckCircle2 size={14} /> Intake Ready
                    </span>
                    <button
                      onClick={() => setShowNeedModal(true)}
                      className="text-xs font-bold text-stone-700 hover:text-stone-900 bg-white border border-stone-300 px-3 py-1.5 rounded-lg cursor-pointer"
                    >
                      Update Capacity
                    </button>
                  </div>
                </div>
              </div>

              {/* Search & Filter Bar */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2 bg-white border border-stone-200 rounded-xl px-3 py-1.5 flex-1 max-w-md">
                  <Search size={15} className="text-stone-400 shrink-0" />
                  <input
                    type="text"
                    placeholder="Search needs by meal period, diet type..."
                    value={needsSearch}
                    onChange={(e) => setNeedsSearch(e.target.value)}
                    className="w-full text-xs text-stone-800 outline-hidden bg-transparent"
                  />
                  {needsSearch && (
                    <button onClick={() => setNeedsSearch('')} className="text-stone-400 hover:text-stone-600">
                      <X size={13} />
                    </button>
                  )}
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <button
                    onClick={() => setNeedsFilter('ALL')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer border ${
                      needsFilter === 'ALL'
                        ? 'bg-emerald-800 text-white border-emerald-800'
                        : 'bg-white text-stone-600 border-stone-200 hover:bg-stone-50'
                    }`}
                  >
                    All Needs ({data.activeNeeds.length})
                  </button>
                  <button
                    onClick={() => setNeedsFilter('OPEN')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer border ${
                      needsFilter === 'OPEN'
                        ? 'bg-emerald-800 text-white border-emerald-800'
                        : 'bg-white text-stone-600 border-stone-200 hover:bg-stone-50'
                    }`}
                  >
                    Open ({data.activeNeeds.filter((n) => n.status === 'Open').length})
                  </button>
                  <button
                    onClick={() => setNeedsFilter('MATCHED')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer border ${
                      needsFilter === 'MATCHED'
                        ? 'bg-emerald-800 text-white border-emerald-800'
                        : 'bg-white text-stone-600 border-stone-200 hover:bg-stone-50'
                    }`}
                  >
                    Matched ({data.activeNeeds.filter((n) => n.status === 'Matched').length})
                  </button>
                </div>
              </div>

              {/* Needs List */}
              <div className="space-y-3">
                {filteredNeeds.length > 0 ? (
                  filteredNeeds.map((need) => (
                    <div
                      key={need.id}
                      className="receiver-card p-5 border border-stone-200 hover:border-emerald-200 transition-colors space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-xl bg-emerald-100/70 text-emerald-800 flex items-center justify-center shrink-0">
                            <Utensils size={18} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-stone-900">{need.mealPeriod} Requirement</span>
                              <FoodTypeBadge type={need.foodType} />
                              <RescueStatus status={need.status} />
                            </div>
                            <div className="flex flex-wrap items-center gap-4 text-xs text-stone-500 mt-1">
                              <span>
                                Target: <strong>{need.quantity} kg</strong> (~{need.quantity * 3} portions)
                              </span>
                              <span>•</span>
                              <span>
                                Required By: <strong>{need.requiredBy}</strong>
                              </span>
                              <span>•</span>
                              <span>ID: #{need.id}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 self-end sm:self-center">
                          {need.status === 'Matched' ? (
                            <button
                              onClick={() => setActiveTab('incoming')}
                              className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors shadow-sm flex items-center gap-1.5 cursor-pointer"
                            >
                              <Truck size={14} /> View Delivery
                            </button>
                          ) : (
                            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 flex items-center gap-1.5">
                              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                              Broadcasting to Donors
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Matching Detail Banner */}
                      <div
                        className={`text-xs p-3 rounded-lg flex items-center justify-between ${
                          need.status === 'Matched'
                            ? 'bg-blue-50/80 text-blue-900 border border-blue-100'
                            : 'bg-stone-50 text-stone-600 border border-stone-200'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {need.status === 'Matched' ? (
                            <>
                              <CheckCircle size={15} className="text-blue-700 shrink-0" />
                              <span>
                                <strong>Matched:</strong> 12 kg allocated from Green Leaf Catering. Driver Arjun Sharma in
                                transit.
                              </span>
                            </>
                          ) : (
                            <>
                              <Radio size={15} className="text-emerald-700 shrink-0" />
                              <span>
                                <strong>Awaiting Match:</strong> Surplus within 10 km radius is automatically routed to this need.
                              </span>
                            </>
                          )}
                        </div>
                        <span className="text-[11px] text-stone-500 hidden sm:inline">Priority: Standard</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="receiver-card text-center py-12 space-y-3">
                    <Utensils size={32} className="mx-auto text-stone-400" />
                    <h3 className="text-sm font-bold text-stone-800">No Food Requirements Found</h3>
                    <p className="text-xs text-stone-500 max-w-sm mx-auto">
                      No needs match your search or filter criteria. Create a new need to request surplus food.
                    </p>
                    <button
                      onClick={() => setShowNeedModal(true)}
                      className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-xs font-bold hover:bg-emerald-900 cursor-pointer"
                    >
                      + Raise Food Need
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 3: INCOMING DELIVERIES                                */}
          {/* ========================================================= */}
          {activeTab === 'incoming' && (
            <div className="space-y-6">
              {/* Incoming Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-stone-900">Incoming Deliveries & Live Handoff</h2>
                  <p className="text-xs text-stone-500">
                    Track delivery vehicles, verify cold storage temperature, and confirm handoff using single-use OTP.
                  </p>
                </div>
                {data.incomingDeliveries.length > 0 && (
                  <button
                    onClick={() => setShowHandoffModal(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white rounded-xl text-xs font-bold transition-all shadow-sm shrink-0 cursor-pointer"
                  >
                    <ShieldCheck size={16} /> Confirm Handoff (OTP)
                  </button>
                )}
              </div>

              {/* Real-time Tracking Stepper Card */}
              {data.incomingDeliveries.length > 0 ? (
                <div className="space-y-6">
                  {data.incomingDeliveries.map((del) => (
                    <div key={del.id} className="receiver-card p-6 border-blue-200 bg-white space-y-6">
                      {/* Delivery Top Bar */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-stone-100">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                              Mission #AS-1042
                            </span>
                            <span className="text-xs font-bold text-stone-900">{del.foodName}</span>
                          </div>
                          <p className="text-xs text-stone-500 mt-1">
                            Dispatched from <strong>{del.donorName}</strong> · Delivered by Driver{' '}
                            <strong>{del.driverName}</strong>
                          </p>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-lg font-extrabold text-blue-700 flex items-center gap-1.5 justify-end">
                              <Clock size={16} /> {del.eta || 11} mins
                            </div>
                            <span className="text-[10px] text-stone-400 font-medium">Estimated Arrival</span>
                          </div>
                        </div>
                      </div>

                      {/* Visual Stepper / Progress Route */}
                      <div className="bg-stone-50/70 p-4 rounded-xl border border-stone-200">
                        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-center sm:text-left">
                          {/* Step 1 */}
                          <div className="flex sm:flex-col items-center sm:items-start gap-2">
                            <div className="w-7 h-7 rounded-full bg-emerald-800 text-white flex items-center justify-center font-bold text-xs shrink-0">
                              <Check size={14} />
                            </div>
                            <div>
                              <div className="text-xs font-bold text-stone-900">Food Packed</div>
                              <div className="text-[11px] text-stone-500">12:40 PM · Quality checked</div>
                            </div>
                          </div>

                          {/* Step 2 */}
                          <div className="flex sm:flex-col items-center sm:items-start gap-2">
                            <div className="w-7 h-7 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-xs shrink-0 animate-pulse">
                              <Truck size={14} />
                            </div>
                            <div>
                              <div className="text-xs font-bold text-blue-800">In Transit</div>
                              <div className="text-[11px] text-stone-500">Temp: 4.2°C · Distance: 1.8 km</div>
                            </div>
                          </div>

                          {/* Step 3 */}
                          <div className="flex sm:flex-col items-center sm:items-start gap-2">
                            <div className="w-7 h-7 rounded-full bg-stone-200 text-stone-600 flex items-center justify-center font-bold text-xs shrink-0">
                              3
                            </div>
                            <div>
                              <div className="text-xs font-bold text-stone-600">Shelter Arrival</div>
                              <div className="text-[11px] text-stone-400">Incoming at Gate 2</div>
                            </div>
                          </div>

                          {/* Step 4 */}
                          <div className="flex sm:flex-col items-center sm:items-start gap-2">
                            <div className="w-7 h-7 rounded-full bg-stone-200 text-stone-600 flex items-center justify-center font-bold text-xs shrink-0">
                              4
                            </div>
                            <div>
                              <div className="text-xs font-bold text-stone-600">OTP Confirmation</div>
                              <div className="text-[11px] text-stone-400">Seal verification</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Vehicle & Telemetry Split */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Driver Card */}
                        <div className="p-4 rounded-xl border border-stone-200 bg-white space-y-2">
                          <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">
                            Assigned Driver
                          </span>
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-stone-100 border border-stone-200 flex items-center justify-center font-bold text-stone-800 text-sm">
                              AS
                            </div>
                            <div>
                              <div className="text-xs font-bold text-stone-900">{del.driverName}</div>
                              <div className="text-[11px] text-stone-500">⭐ 4.9 · 142 food rescues</div>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setDriverContactStatus('Connecting driver Arjun Sharma (+91 98765 43210)…')
                              setTimeout(() => setDriverContactStatus(null), 4000)
                            }}
                            className="w-full mt-2 py-1.5 text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-lg transition-colors flex items-center justify-center gap-1.5 cursor-pointer border-0"
                          >
                            <Phone size={13} /> Call Driver
                          </button>
                          {driverContactStatus && (
                            <span className="text-[10px] text-emerald-700 font-semibold block text-center">
                              {driverContactStatus}
                            </span>
                          )}
                        </div>

                        {/* Vehicle & Storage Card */}
                        <div className="p-4 rounded-xl border border-stone-200 bg-white space-y-2">
                          <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">
                            Vehicle & Cold Chain
                          </span>
                          <div className="flex items-center gap-2">
                            <Truck size={16} className="text-emerald-700" />
                            <span className="text-xs font-bold text-stone-900">Tata Ace EV (RJ 14 GC 4281)</span>
                          </div>
                          <div className="text-xs text-stone-600 flex items-center gap-1.5">
                            <Thermometer size={14} className="text-blue-600" />
                            <span>Storage Chamber: <strong>4.2°C (Optimal)</strong></span>
                          </div>
                          <span className="text-[11px] text-emerald-700 font-medium block">
                            ✓ Insulated container tamper-sealed
                          </span>
                        </div>

                        {/* Verification & Action Card */}
                        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-2 flex flex-col justify-between">
                          <div>
                            <span className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
                              Handoff Protocol
                            </span>
                            <div className="text-xs font-bold text-stone-900 mt-1">
                              Quantity: {del.quantity} {del.unit} (~{del.quantity * 3} meals)
                            </div>
                            <p className="text-[11px] text-stone-600 mt-0.5">
                              Ask driver for the 4-digit verification code to complete intake.
                            </p>
                          </div>
                          <button
                            onClick={() => setShowHandoffModal(true)}
                            className="w-full py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-bold rounded-lg transition-colors shadow-sm flex items-center justify-center gap-1.5 cursor-pointer border-0"
                          >
                            <ShieldCheck size={14} /> Enter Verification OTP
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="receiver-card text-center py-12 space-y-3">
                  <Truck size={36} className="mx-auto text-stone-400" />
                  <h3 className="text-sm font-bold text-stone-800">No Active Deliveries En Route</h3>
                  <p className="text-xs text-stone-500 max-w-sm mx-auto">
                    When nearby donors have surplus matched to your shelter's needs, live delivery missions will appear here.
                  </p>
                  <button
                    onClick={() => setActiveTab('needs')}
                    className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-xs font-bold hover:bg-emerald-900 cursor-pointer"
                  >
                    View Active Needs
                  </button>
                </div>
              )}

              {/* Safe Food Handoff Checklist */}
              <div className="receiver-card p-5 bg-stone-50/60 border border-stone-200 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-2">
                  <ShieldCheck size={16} className="text-emerald-700" /> Safe Food Intake Checklist
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-stone-600">
                  <div className="p-3 bg-white rounded-lg border border-stone-200">
                    <strong>1. Inspect Tamper Seal</strong>
                    <p className="text-[11px] text-stone-500 mt-0.5">
                      Ensure food packaging seals are unbroken and labeled with preparation time.
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-stone-200">
                    <strong>2. Check Food Temperature</strong>
                    <p className="text-[11px] text-stone-500 mt-0.5">
                      Hot items should be ≥ 60°C; chilled cooked items must be maintained ≤ 5°C.
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-stone-200">
                    <strong>3. Confirm OTP with Driver</strong>
                    <p className="text-[11px] text-stone-500 mt-0.5">
                      Entering the OTP closes the custody loop and generates your tax/rescue certificate.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB 4: RESCUE HISTORY & RECORDS                           */}
          {/* ========================================================= */}
          {activeTab === 'history' && (
            <div className="space-y-6">
              {/* History Top Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-stone-900">Food Rescue Records & Impact History</h2>
                  <p className="text-xs text-stone-500">
                    Audited ledger of all received surplus food, certified weights, and community meal equivalents.
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={exportHistoryCSV}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-stone-50 text-stone-700 rounded-xl text-xs font-bold border border-stone-300 transition-all cursor-pointer"
                  >
                    <FileSpreadsheet size={15} className="text-emerald-700" /> Export CSV
                  </button>
                  <button
                    onClick={downloadReportPDF}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-800 hover:bg-emerald-900 text-white rounded-xl text-xs font-bold transition-all shadow-sm cursor-pointer"
                  >
                    <Download size={15} /> Impact Report (PDF)
                  </button>
                </div>
              </div>

              {/* 4 Impact Summary Highlights */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="receiver-card p-4">
                  <span className="text-xs text-stone-500 font-medium">Meals Provided</span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">{data.impact.mealsReceived}</div>
                  <span className="text-[11px] text-emerald-700 mt-1 block font-medium">Nutritious portions distributed</span>
                </div>
                <div className="receiver-card p-4">
                  <span className="text-xs text-stone-500 font-medium">Total Food Rescued</span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    {data.impact.totalQuantity} <span className="text-xs font-normal text-stone-500">kg</span>
                  </div>
                  <span className="text-[11px] text-blue-700 mt-1 block font-medium">Saved from landfill</span>
                </div>
                <div className="receiver-card p-4">
                  <span className="text-xs text-stone-500 font-medium">Missions Completed</span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">{data.impact.deliveriesCompleted}</div>
                  <span className="text-[11px] text-stone-500 mt-1 block font-medium">Verified handoffs</span>
                </div>
                <div className="receiver-card p-4">
                  <span className="text-xs text-stone-500 font-medium">CO₂ Emissions Avoided</span>
                  <div className="mt-2 text-2xl font-bold text-stone-900">
                    {(data.impact.totalQuantity * 2.5).toFixed(0)}{' '}
                    <span className="text-xs font-normal text-stone-500">kg CO₂e</span>
                  </div>
                  <span className="text-[11px] text-emerald-700 mt-1 block font-medium">Environmental benefit</span>
                </div>
              </div>

              {/* Search History Bar */}
              <div className="flex items-center gap-2 bg-white border border-stone-200 rounded-xl px-3 py-2 max-w-md">
                <Search size={15} className="text-stone-400 shrink-0" />
                <input
                  type="text"
                  placeholder="Search history by donor, food name, or driver..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="w-full text-xs text-stone-800 outline-hidden bg-transparent"
                />
                {historySearch && (
                  <button onClick={() => setHistorySearch('')} className="text-stone-400 hover:text-stone-600">
                    <X size={13} />
                  </button>
                )}
              </div>

              {/* History Table / Records */}
              <div className="receiver-card overflow-hidden p-0">
                <div className="p-4 border-b border-stone-100 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-stone-900">Verified Rescue Deliveries</h3>
                  <span className="text-xs text-stone-500">{filteredHistory.length} total entries</span>
                </div>

                <div className="divide-y divide-stone-100">
                  {filteredHistory.map((item) => (
                    <div
                      key={item.id}
                      className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-stone-50/50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center shrink-0">
                          <CheckCircle2 size={18} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-stone-900">{item.foodName}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Verified
                            </span>
                          </div>
                          <p className="text-xs text-stone-600 mt-0.5">
                            Donor: <strong>{item.donorName}</strong> · Delivered by Driver <strong>{item.driverName}</strong>
                          </p>
                          <div className="flex items-center gap-3 text-[11px] text-stone-500 mt-1.5">
                            <span className="inline-flex items-center gap-1">
                              <Calendar size={12} /> {item.arrivalTime || 'Recent'}
                            </span>
                            <span>•</span>
                            <span>Quantity: <strong>{item.quantity} {item.unit}</strong> (~{item.quantity * 3} meals)</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => setSelectedCertificate(item)}
                          className="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer border-0"
                        >
                          <Award size={13} className="text-emerald-700" /> View Certificate
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Monthly Summary Table */}
              <div className="receiver-card p-5 space-y-4">
                <h3 className="text-sm font-bold text-stone-900">Monthly Food Rescue Breakdown</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="text-[11px] font-bold text-stone-400 uppercase bg-stone-50 border-y border-stone-200">
                      <tr>
                        <th className="py-2.5 px-3">Month</th>
                        <th className="py-2.5 px-3">Quantity Received (kg)</th>
                        <th className="py-2.5 px-3">Meals Provided</th>
                        <th className="py-2.5 px-3">Est. CO₂ Prevented</th>
                        <th className="py-2.5 px-3">Safety Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100 text-stone-700">
                      {data.impact.monthly.map((m) => (
                        <tr key={m.month} className="hover:bg-stone-50/50">
                          <td className="py-2.5 px-3 font-semibold text-stone-900">{m.month}</td>
                          <td className="py-2.5 px-3">{m.received} kg</td>
                          <td className="py-2.5 px-3 font-bold text-emerald-800">{m.meals}</td>
                          <td className="py-2.5 px-3">~{(m.received * 2.5).toFixed(0)} kg CO₂</td>
                          <td className="py-2.5 px-3 text-emerald-700 font-semibold">100% Verified</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ========================================================= */}
      {/* MODAL 1: RAISE FOOD NEED                                  */}
      {/* ========================================================= */}
      {showNeedModal && (
        <div className="fixed inset-0 bg-stone-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-stone-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-stone-900">Raise Food Requirement</h3>
                <p className="text-xs text-stone-500">Queued for automated AI surplus allocation</p>
              </div>
              <button
                onClick={() => setShowNeedModal(false)}
                className="text-stone-400 hover:text-stone-700 cursor-pointer p-1"
              >
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateNeed} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-stone-700 block mb-1">Meal Period</label>
                <select
                  value={needForm.mealPeriod}
                  onChange={(e) => setNeedForm({ ...needForm, mealPeriod: e.target.value })}
                  className="w-full border border-stone-300 rounded-lg p-2.5 text-sm outline-hidden focus:border-emerald-800"
                >
                  <option>Breakfast</option>
                  <option>Lunch</option>
                  <option>Evening Snack</option>
                  <option>Dinner</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-stone-700 block mb-1">Accepted Food Type</label>
                <select
                  value={needForm.foodType}
                  onChange={(e) => setNeedForm({ ...needForm, foodType: e.target.value })}
                  className="w-full border border-stone-300 rounded-lg p-2.5 text-sm outline-hidden focus:border-emerald-800"
                >
                  <option>Vegetarian</option>
                  <option>Non-Vegetarian</option>
                  <option>Both</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-stone-700 block mb-1">Estimated Quantity (kg)</label>
                <input
                  type="number"
                  min="5"
                  max="500"
                  value={needForm.quantity}
                  onChange={(e) => setNeedForm({ ...needForm, quantity: Number(e.target.value) })}
                  className="w-full border border-stone-300 rounded-lg p-2.5 text-sm outline-hidden focus:border-emerald-800"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-stone-700 block mb-1">Required By</label>
                <input
                  type="text"
                  value={needForm.requiredBy}
                  onChange={(e) => setNeedForm({ ...needForm, requiredBy: e.target.value })}
                  className="w-full border border-stone-300 rounded-lg p-2.5 text-sm outline-hidden focus:border-emerald-800"
                  placeholder="e.g. Today, 8:00 PM"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-stone-700">Delivery / Shelter Location</label>
                  <button
                    type="button"
                    onClick={() => {
                      if (typeof window === 'undefined' || !navigator.geolocation) {
                        setNeedForm({ ...needForm, location: 'Sector 3 Shelter, Malviya Nagar (GPS: 26.8524° N, 75.8194° E)' })
                        setGpsReceiverStatus('GPS calibrated to Malviya Nagar Hub, Jaipur')
                        return
                      }
                      setGpsReceiverStatus('Detecting GPS location…')
                      navigator.geolocation.getCurrentPosition(
                        (pos) => {
                          const lat = Number(pos.coords.latitude.toFixed(5))
                          const lng = Number(pos.coords.longitude.toFixed(5))
                          setNeedForm({ ...needForm, location: `Community Shelter GPS (${lat}° N, ${lng}° E)` })
                          setGpsReceiverStatus(`🛰️ GPS fix locked: ${lat}° N, ${lng}° E`)
                        },
                        () => {
                          setNeedForm({ ...needForm, location: 'Sector 3 Shelter, Malviya Nagar (GPS: 26.8524° N, 75.8194° E)' })
                          setGpsReceiverStatus('GPS fallback calibrated to Malviya Nagar, Jaipur')
                        },
                        { enableHighAccuracy: true, timeout: 8000 }
                      )
                    }}
                    className="text-[11px] font-bold text-emerald-800 flex items-center gap-1 hover:underline cursor-pointer bg-transparent border-0 p-0"
                  >
                    <Navigation size={12} /> Use GPS
                  </button>
                </div>
                <input
                  type="text"
                  value={needForm.location}
                  onChange={(e) => setNeedForm({ ...needForm, location: e.target.value })}
                  className="w-full border border-stone-300 rounded-lg p-2.5 text-sm outline-hidden focus:border-emerald-800"
                  placeholder="e.g. Sector 3 Community Kitchen, Malviya Nagar, Jaipur"
                />
                {gpsReceiverStatus && (
                  <span className="text-[10px] text-emerald-700 font-semibold block mt-1">{gpsReceiverStatus}</span>
                )}
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNeedModal(false)}
                  className="px-4 py-2 border border-stone-300 rounded-lg text-xs font-semibold text-stone-700 hover:bg-stone-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-xs font-bold hover:bg-emerald-900 cursor-pointer"
                >
                  Publish Need
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 2: HANDOFF OTP VERIFICATION                         */}
      {/* ========================================================= */}
      {showHandoffModal && (
        <div className="fixed inset-0 bg-stone-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-stone-200 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto mb-3">
              <ShieldCheck size={24} />
            </div>
            <h3 className="text-base font-bold text-stone-900">Food Handoff Verification</h3>
            <p className="text-xs text-stone-500 mt-1 mb-4">
              Enter the 4-digit code provided by driver Arjun Sharma to confirm safe food receipt and close the custody loop.
            </p>
            <input
              type="text"
              maxLength={4}
              placeholder="1234"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              className="text-center tracking-widest text-2xl font-bold border border-stone-300 rounded-xl p-3 w-40 mx-auto block mb-3 focus:outline-emerald-800"
            />
            {otpMessage && (
              <p
                className={`text-xs font-medium mb-3 ${
                  otpMessage.includes('Invalid') ? 'text-rose-600' : 'text-emerald-700'
                }`}
              >
                {otpMessage}
              </p>
            )}
            <div className="flex gap-2">
              <button
                onClick={() => setShowHandoffModal(false)}
                className="flex-1 py-2 border border-stone-300 rounded-lg text-xs font-semibold text-stone-700 hover:bg-stone-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleVerifyHandoff}
                className="flex-1 py-2 bg-emerald-800 text-white rounded-lg text-xs font-bold hover:bg-emerald-900 cursor-pointer"
              >
                Confirm Handoff
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 3: FOOD RESCUE CERTIFICATE MODAL                    */}
      {/* ========================================================= */}
      {selectedCertificate && (
        <div className="fixed inset-0 bg-stone-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-stone-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-800 text-amber-200 flex items-center justify-center">
                  <Award size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-stone-900">AnnaSetu Food Rescue Certificate</h3>
                  <span className="text-[10px] text-stone-500">Verified Chain of Custody</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedCertificate(null)}
                className="text-stone-400 hover:text-stone-700 cursor-pointer p-1"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200/80 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Certificate ID:</span>
                <span className="font-mono font-bold text-emerald-900">
                  AS-CERT-{selectedCertificate.id.toUpperCase()}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Receiving Organization:</span>
                <span className="font-bold text-stone-900">{profile?.full_name || data.organizationName}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Source Donor:</span>
                <span className="font-bold text-stone-900">{selectedCertificate.donorName}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Food Item:</span>
                <span className="font-bold text-stone-900">{selectedCertificate.foodName}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Verified Weight:</span>
                <span className="font-bold text-emerald-800">
                  {selectedCertificate.quantity} {selectedCertificate.unit} (~{selectedCertificate.quantity * 3} meals)
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Delivery Partner:</span>
                <span className="text-stone-700">{selectedCertificate.driverName}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-500">Receipt Timestamp:</span>
                <span className="text-stone-700">{selectedCertificate.arrivalTime || 'Completed'}</span>
              </div>
              <div className="pt-2 border-t border-amber-200/60 flex items-center justify-between text-[11px] text-emerald-800 font-semibold">
                <span>✓ Tamper Seal Intact</span>
                <span>✓ Cold-Chain 4.2°C Logged</span>
                <span>✓ OTP Confirmed</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedCertificate(null)}
                className="px-4 py-2 border border-stone-300 rounded-lg text-xs font-semibold text-stone-700 hover:bg-stone-50 cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  window.print()
                }}
                className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-xs font-bold hover:bg-emerald-900 cursor-pointer flex items-center gap-1.5"
              >
                <Download size={14} /> Print Certificate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
