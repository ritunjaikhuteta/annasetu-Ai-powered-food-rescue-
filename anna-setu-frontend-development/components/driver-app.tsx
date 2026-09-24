'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import '@/app/driver/driver.css'
import {
  Navigation,
  MapPin,
  Clock,
  CheckCircle2,
  DollarSign,
  User,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  ArrowRight,
  Leaf,
  LogOut,
  Phone,
  AlertCircle,
  Truck,
  Sparkles,
} from 'lucide-react'
import { driverService } from '@/lib/services/driver'
import type { DriverData, DriverJob } from '@/lib/types/driver'
import { VerificationBadge } from '@/components/verification/VerificationBadge'
import { RescueStatus } from '@/components/rescue/RescueStatus'
import { FoodTypeBadge } from '@/components/rescue/FoodTypeBadge'
import { LoadingState } from '@/components/shared/LoadingState'
import { useAuth } from '@/lib/auth/context'

export default function DriverApp({ path = '/driver/dashboard' }: { path?: string }) {
  const { profile, verificationStatus, signOut } = useAuth()
  const isVerified = verificationStatus === 'VERIFIED' || verificationStatus === 'verified'
  const [data, setData] = useState<DriverData | null>(null)
  const [activeTab, setActiveTab] = useState<'mission' | 'available' | 'earnings' | 'profile'>('mission')
  const [isOnline, setIsOnline] = useState(true)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [gpsLive, setGpsLive] = useState('26.8920° N, 75.8068° E (Jaipur Central Corridor)')
  const [verifyingStop, setVerifyingStop] = useState<number | null>(null)
  const [otp, setOtp] = useState('')
  const [otpError, setOtpError] = useState('')

  useEffect(() => {
    driverService.getData().then(setData)
  }, [])

  if (!data) {
    return <LoadingState message="Loading delivery partner portal…" className="min-h-screen" />
  }

  const handleCompleteStop = async (order: number) => {
    if (!data.activeJob) return
    const res = await driverService.completeStop(data.activeJob.id, order, otp)
    if (res.ok) {
      setVerifyingStop(null)
      setOtp('')
      setOtpError('')
      const updated = await driverService.getData()
      setData({ ...updated })
    } else {
      setOtpError(res.message)
    }
  }

  const handleAcceptJob = async (jobId: string) => {
    const res = await driverService.acceptJob(jobId)
    if (res.ok) {
      const updated = await driverService.getData()
      setData({ ...updated })
      setActiveTab('mission')
    }
  }

  const activeJob = data.activeJob

  return (
    <div className="driver-shell">
      {/* Mobile Top Header */}
      <header className="driver-header">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-emerald-800 text-amber-200 flex items-center justify-center -rotate-6">
            <Leaf size={16} />
          </span>
          <div>
            <h1 className="text-sm font-bold text-stone-900 leading-none">AnnaSetu Partner</h1>
            <span className="text-[10px] text-stone-500">{data.vehicleType} · {data.vehicleNumber}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsOnline(!isOnline)}
            className={`px-3 py-1 rounded-full text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              isOnline
                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                : 'bg-stone-200 text-stone-600 border border-stone-300'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-600 animate-pulse' : 'bg-stone-400'}`} />
            {isOnline ? 'Online' : 'Offline'}
          </button>

          <div className="relative">
            <button
              type="button"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="w-8 h-8 rounded-full bg-emerald-800 text-amber-200 flex items-center justify-center font-bold text-xs hover:ring-2 hover:ring-emerald-400 transition-all cursor-pointer"
              aria-label="Partner profile menu"
              aria-expanded={userMenuOpen}
            >
              {(profile?.full_name || data.name).charAt(0).toUpperCase()}
            </button>

            {userMenuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-stone-200 py-2 z-50 text-left">
                  <div className="px-4 py-3 border-b border-stone-100">
                    <p className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">Delivery Partner</p>
                    <p className="text-sm font-bold text-stone-900 truncate">{profile?.full_name || data.name}</p>
                    <p className="text-xs text-stone-500 truncate">{data.vehicleType} · {data.vehicleNumber}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <VerificationBadge status={(verificationStatus as any) || data.verified} />
                      <span className="text-xs text-stone-500 font-medium">★ {data.rating}</span>
                    </div>
                  </div>
                  <div className="py-1">
                    <button
                      type="button"
                      onClick={() => { setActiveTab('mission'); setUserMenuOpen(false); }}
                      className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${activeTab === 'mission' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'}`}
                    >
                      <Navigation size={14} className="text-stone-400" /> Active Mission
                    </button>
                    <button
                      type="button"
                      onClick={() => { setActiveTab('available'); setUserMenuOpen(false); }}
                      className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${activeTab === 'available' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'}`}
                    >
                      <Truck size={14} className="text-stone-400" /> Available Jobs ({data.availableJobs.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => { setActiveTab('earnings'); setUserMenuOpen(false); }}
                      className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${activeTab === 'earnings' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'}`}
                    >
                      <DollarSign size={14} className="text-stone-400" /> Earnings (₹{data.earnings?.thisWeek ?? 0})
                    </button>
                    <button
                      type="button"
                      onClick={() => { setActiveTab('profile'); setUserMenuOpen(false); }}
                      className={`w-full text-left px-4 py-2 text-xs font-medium flex items-center gap-2.5 transition-colors cursor-pointer border-0 bg-transparent ${activeTab === 'profile' ? 'text-emerald-800 bg-emerald-50' : 'text-stone-700 hover:bg-stone-50'}`}
                    >
                      <User size={14} className="text-stone-400" /> Partner Profile
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

      {/* Main Container */}
      <main className="driver-content">
        {/* TAB 1: ACTIVE MISSION */}
        {activeTab === 'mission' && (
          <>
            {activeJob ? (
              <div className="space-y-4">
                {/* Active Mission Header */}
                <div className="driver-card bg-emerald-950 text-white border-none p-5">
                  <div className="flex items-center justify-between text-xs text-emerald-300">
                    <span className="uppercase tracking-wider font-semibold">Active Rescue Mission</span>
                    <span className="bg-emerald-800/80 px-2.5 py-0.5 rounded-full text-[11px] font-bold text-white">
                      ₹{activeJob.estimatedEarnings} payout
                    </span>
                  </div>
                  <h2 className="text-lg font-bold mt-2 text-white">{activeJob.foodDescription}</h2>
                  <div className="flex items-center gap-4 text-xs text-emerald-200 mt-2">
                    <span>{activeJob.quantity} {activeJob.unit}</span>
                    <span>•</span>
                    <span>{activeJob.totalDistance} km total</span>
                    <span>•</span>
                    <span>~{activeJob.estimatedDuration} mins</span>
                  </div>
                </div>

                {/* Live GPS Route Tracker */}
                <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-950">
                  <div className="flex items-center gap-2">
                    <Navigation size={15} className="text-emerald-700 animate-pulse" />
                    <div>
                      <span className="font-bold block">Live GPS Telemetry</span>
                      <span className="text-[11px] text-emerald-700 font-mono">{gpsLive}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      if (typeof window !== 'undefined' && navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                          (pos) => {
                            setGpsLive(`${pos.coords.latitude.toFixed(4)}° N, ${pos.coords.longitude.toFixed(4)}° E (±${Math.round(pos.coords.accuracy)}m)`)
                          },
                          () => {
                            setGpsLive('26.8920° N, 75.8068° E (Jaipur Central Corridor)')
                          }
                        )
                      }
                    }}
                    className="px-2.5 py-1 bg-emerald-800 hover:bg-emerald-900 text-white rounded-lg text-[10px] font-bold cursor-pointer"
                  >
                    Sync GPS
                  </button>
                </div>

                {/* Pickup Location Card */}
                <div className="driver-card space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-stone-500 uppercase tracking-wide">Step 1: Food Pickup</span>
                    <span className="text-emerald-700 font-semibold text-[11px]">✓ Picked Up</span>
                  </div>
                  <div className="font-bold text-sm text-stone-900">{activeJob.donorName}</div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-xs text-stone-600 flex items-start gap-1.5">
                      <MapPin size={14} className="shrink-0 mt-0.5 text-stone-400" />
                      <span>{activeJob.pickupLocation.address}</span>
                    </div>
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(activeJob.pickupLocation.address)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold rounded-lg shrink-0 flex items-center gap-1 transition-colors"
                    >
                      <Navigation size={13} className="text-emerald-700" /> GPS Map
                    </a>
                  </div>
                </div>

                {/* Receiver Delivery Stops */}
                <div className="driver-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-stone-500 uppercase tracking-wide">
                      Step 2: Drop-offs ({activeJob.stops.length} stops)
                    </span>
                    <span className="text-xs text-stone-500 font-medium">Safe Food Transfer</span>
                  </div>

                  <div className="space-y-3">
                    {activeJob.stops.map((stop) => {
                      const isDone = stop.status === 'Completed'
                      return (
                        <div
                          key={stop.order}
                          className={`p-3.5 rounded-xl border transition-all ${
                            isDone
                              ? 'bg-stone-50 border-stone-200 opacity-75'
                              : 'bg-white border-emerald-200 shadow-xs'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className={`w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center ${isDone ? 'bg-emerald-600 text-white' : 'bg-emerald-100 text-emerald-800'}`}>
                                  {isDone ? '✓' : stop.order}
                                </span>
                                <span className="font-bold text-sm text-stone-900">{stop.receiverName}</span>
                              </div>
                              <p className="text-xs text-stone-600 mt-1 pl-7">{stop.address}</p>
                              <span className="text-xs font-semibold text-emerald-800 pl-7 block mt-0.5">
                                Handoff: {stop.quantity} kg
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5 shrink-0 mt-1">
                              <a
                                href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(stop.address)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-2.5 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-700 text-xs font-semibold rounded-lg flex items-center gap-1 transition-colors"
                                title="Navigate using GPS"
                              >
                                <Navigation size={13} className="text-emerald-700" /> GPS
                              </a>
                              {!isDone && (
                                <button
                                  onClick={() => setVerifyingStop(stop.order)}
                                  className="px-3 py-1.5 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-bold rounded-lg shadow-xs cursor-pointer"
                                >
                                  Verify OTP
                                </button>
                              )}
                            </div>
                          </div>

                          {verifyingStop === stop.order && (
                            <div className="mt-3 pt-3 border-t border-stone-200 space-y-2">
                              <p className="text-xs text-stone-600">
                                Ask recipient at <strong>{stop.receiverName}</strong> for 4-digit code:
                              </p>
                              <div className="flex gap-2">
                                <input
                                  type="text"
                                  placeholder="1234"
                                  maxLength={4}
                                  value={otp}
                                  onChange={(e) => setOtp(e.target.value)}
                                  className="w-28 text-center font-bold tracking-widest text-base border border-stone-300 rounded-lg p-1.5"
                                />
                                <button
                                  onClick={() => handleCompleteStop(stop.order)}
                                  className="px-3 py-1.5 bg-emerald-700 text-white text-xs font-bold rounded-lg hover:bg-emerald-800"
                                >
                                  Confirm
                                </button>
                                <button
                                  onClick={() => setVerifyingStop(null)}
                                  className="px-2 py-1.5 text-xs text-stone-500"
                                >
                                  Cancel
                                </button>
                              </div>
                              {otpError && <p className="text-xs text-rose-600 font-medium">{otpError}</p>}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="driver-card text-center py-12">
                <Truck size={36} className="mx-auto text-stone-300 mb-3" />
                <h3 className="font-bold text-stone-800 text-base">No Active Mission</h3>
                <p className="text-xs text-stone-500 mt-1 mb-4">
                  Check available rescue requests nearby to start earning.
                </p>
                <button
                  onClick={() => setActiveTab('available')}
                  className="px-4 py-2 bg-emerald-800 text-white text-xs font-bold rounded-lg hover:bg-emerald-900"
                >
                  View Available Jobs
                </button>
              </div>
            )}
          </>
        )}

        {/* TAB 2: AVAILABLE JOBS */}
        {activeTab === 'available' && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-stone-900">Nearby Rescue Requests</h2>
            {data.availableJobs.length > 0 ? (
              data.availableJobs.map((job) => (
                <div key={job.id} className="driver-card space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wide">
                        {job.stops.length} Stop Rescue
                      </span>
                      <h3 className="text-sm font-bold text-stone-900 mt-0.5">{job.foodDescription}</h3>
                      <p className="text-xs text-stone-600 mt-0.5">Pickup: {job.donorName}</p>
                    </div>
                    <span className="text-base font-bold text-emerald-900 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                      ₹{job.estimatedEarnings}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-stone-500 pt-1 border-t border-stone-100">
                    <span>{job.quantity} {job.unit}</span>
                    <span>•</span>
                    <span>{job.totalDistance} km</span>
                    <span>•</span>
                    <span>~{job.estimatedDuration} mins</span>
                  </div>

                  {isVerified ? (
                    <button
                      onClick={() => handleAcceptJob(job.id)}
                      className="w-full py-2.5 bg-emerald-800 hover:bg-emerald-900 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-xs"
                    >
                      Accept Mission <ArrowRight size={14} />
                    </button>
                  ) : (
                    <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 text-center font-medium">
                      Verification required before accepting missions (Status: {verificationStatus})
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="driver-card text-center py-10 text-xs text-stone-500">
                No open jobs in your radius right now. New rescue requests appear in real time!
              </div>
            )}
          </div>
        )}

        {/* TAB 3: EARNINGS */}
        {activeTab === 'earnings' && (
          <div className="space-y-4">
            <div className="driver-card bg-stone-900 text-white p-5">
              <span className="text-xs text-stone-400 font-medium">Pending Payout</span>
              <div className="text-3xl font-extrabold text-amber-300 mt-1">₹{data.earnings.pendingPayout}</div>
              <p className="text-[11px] text-stone-400 mt-2">Transfers to your bank account weekly.</p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="driver-card p-3 text-center">
                <span className="text-[10px] text-stone-500 block font-semibold">TODAY</span>
                <span className="text-base font-bold text-stone-900 mt-1 block">₹{data.earnings.today}</span>
              </div>
              <div className="driver-card p-3 text-center">
                <span className="text-[10px] text-stone-500 block font-semibold">THIS WEEK</span>
                <span className="text-base font-bold text-stone-900 mt-1 block">₹{data.earnings.thisWeek}</span>
              </div>
              <div className="driver-card p-3 text-center">
                <span className="text-[10px] text-stone-500 block font-semibold">THIS MONTH</span>
                <span className="text-base font-bold text-stone-900 mt-1 block">₹{data.earnings.thisMonth}</span>
              </div>
            </div>

            <div className="driver-card space-y-3">
              <h3 className="text-xs font-bold text-stone-800 uppercase tracking-wide">Completed Missions</h3>
              <div className="divide-y divide-stone-100">
                {data.earnings.history.map((entry) => (
                  <div key={entry.id} className="py-2.5 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-stone-800 block">Mission {entry.deliveryId}</span>
                      <span className="text-stone-400 text-[11px]">{entry.date}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-emerald-800 block">+₹{entry.amount}</span>
                      <span className="text-[10px] text-stone-400">{entry.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: PROFILE */}
        {activeTab === 'profile' && (
          <div className="space-y-4">
            <div className="driver-card space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-emerald-800 text-amber-200 flex items-center justify-center font-bold text-lg">
                  {(profile?.full_name || data.name).charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-base text-stone-900">{profile?.full_name || data.name}</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <VerificationBadge status={(verificationStatus as any) || data.verified} />
                    <span className="text-xs text-stone-500 font-medium">★ {data.rating}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-stone-400 block">Total Rescues</span>
                  <span className="font-bold text-stone-900">{data.totalTrips} missions</span>
                </div>
                <div>
                  <span className="text-stone-400 block">Vehicle</span>
                  <span className="font-bold text-stone-900">{data.vehicleType}</span>
                </div>
              </div>
            </div>

            <div className="driver-card">
              <button
                type="button"
                onClick={() => signOut()}
                className="w-full flex items-center justify-between text-xs font-bold text-rose-700 hover:text-rose-800"
              >
                <span>Sign Out of Partner Portal</span>
                <LogOut size={14} />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Mobile Bottom Navigation Bar */}
      <nav className="driver-bottom-nav">
        <button
          onClick={() => setActiveTab('mission')}
          className={`driver-nav-btn ${activeTab === 'mission' ? 'active' : ''}`}
        >
          <Navigation size={18} />
          <span>Mission</span>
        </button>
        <button
          onClick={() => setActiveTab('available')}
          className={`driver-nav-btn ${activeTab === 'available' ? 'active' : ''}`}
        >
          <Truck size={18} />
          <span>Jobs ({data.availableJobs.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('earnings')}
          className={`driver-nav-btn ${activeTab === 'earnings' ? 'active' : ''}`}
        >
          <DollarSign size={18} />
          <span>Earnings</span>
        </button>
        <button
          onClick={() => setActiveTab('profile')}
          className={`driver-nav-btn ${activeTab === 'profile' ? 'active' : ''}`}
        >
          <User size={18} />
          <span>Profile</span>
        </button>
      </nav>
    </div>
  )
}
