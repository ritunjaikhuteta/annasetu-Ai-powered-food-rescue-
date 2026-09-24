import React from 'react'
import { ShieldCheck, Clock, AlertCircle } from 'lucide-react'
import type { VerificationStatus } from '@/lib/types/core'

export interface VerificationBadgeProps {
  status: VerificationStatus | boolean
  className?: string
}

export function VerificationBadge({ status, className = '' }: VerificationBadgeProps) {
  const isVerified = status === true || status === 'verified'
  const isPending = status === 'pending' || status === 'under_review'

  if (isVerified) {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 ${className}`}>
        <ShieldCheck size={13} className="text-emerald-600" />
        Verified Account
      </span>
    )
  }

  if (isPending) {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 ${className}`}>
        <Clock size={13} className="text-amber-600" />
        Verification Pending
      </span>
    )
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200 ${className}`}>
      <AlertCircle size={13} className="text-rose-600" />
      Unverified
    </span>
  )
}
