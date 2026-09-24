import React from 'react'

export type RescueStatusToken =
  | 'posted'
  | 'open'
  | 'available'
  | 'matched'
  | 'allocated'
  | 'assigned'
  | 'pickup'
  | 'in_transit'
  | 'in_progress'
  | 'arriving'
  | 'completed'
  | 'delivered'
  | 'received'
  | 'verified'
  | 'expired'
  | 'cancelled'
  | 'reassignment_required'
  | 'review_required'
  | 'under_review'
  | 'pending'
  | 'neutral'

export interface StatusStyle {
  label: string
  badge: string
  dot: string
  ring: string
  iconA11y: string
}

export const STATUS_TOKENS: Record<RescueStatusToken, StatusStyle> = {
  posted: {
    label: 'Posted',
    badge: 'bg-amber-50 text-amber-800 border-amber-200',
    dot: 'bg-amber-500',
    ring: 'ring-amber-100',
    iconA11y: 'Donation posted, awaiting matches',
  },
  open: {
    label: 'Open',
    badge: 'bg-amber-50 text-amber-800 border-amber-200',
    dot: 'bg-amber-500',
    ring: 'ring-amber-100',
    iconA11y: 'Open for matching',
  },
  available: {
    label: 'Available',
    badge: 'bg-amber-50 text-amber-800 border-amber-200',
    dot: 'bg-amber-500',
    ring: 'ring-amber-100',
    iconA11y: 'Delivery offer available',
  },
  matched: {
    label: 'Matched',
    badge: 'bg-purple-50 text-purple-700 border-purple-200',
    dot: 'bg-purple-500',
    ring: 'ring-purple-100',
    iconA11y: 'Receiver match found',
  },
  allocated: {
    label: 'Allocated',
    badge: 'bg-purple-50 text-purple-700 border-purple-200',
    dot: 'bg-purple-500',
    ring: 'ring-purple-100',
    iconA11y: 'Quantity allocated',
  },
  assigned: {
    label: 'Driver Assigned',
    badge: 'bg-sky-50 text-sky-700 border-sky-200',
    dot: 'bg-sky-500',
    ring: 'ring-sky-100',
    iconA11y: 'Driver assigned to route',
  },
  pickup: {
    label: 'At Pickup',
    badge: 'bg-sky-50 text-sky-700 border-sky-200',
    dot: 'bg-sky-500',
    ring: 'ring-sky-100',
    iconA11y: 'Driver at pickup location',
  },
  in_transit: {
    label: 'In Transit',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    ring: 'ring-blue-100',
    iconA11y: 'En route to receiver',
  },
  in_progress: {
    label: 'In Progress',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    ring: 'ring-blue-100',
    iconA11y: 'Delivery in progress',
  },
  arriving: {
    label: 'Arriving',
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    ring: 'ring-blue-100',
    iconA11y: 'Driver arriving shortly',
  },
  completed: {
    label: 'Completed',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-100',
    iconA11y: 'Delivery completed',
  },
  delivered: {
    label: 'Delivered',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-100',
    iconA11y: 'Food delivered',
  },
  received: {
    label: 'Received',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-100',
    iconA11y: 'Food received by organization',
  },
  verified: {
    label: 'Verified',
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    dot: 'bg-emerald-600',
    ring: 'ring-emerald-100',
    iconA11y: 'Handoff verified',
  },
  expired: {
    label: 'Expired',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    ring: 'ring-rose-100',
    iconA11y: 'Rescue window expired',
  },
  cancelled: {
    label: 'Cancelled',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
    dot: 'bg-rose-500',
    ring: 'ring-rose-100',
    iconA11y: 'Donation cancelled',
  },
  reassignment_required: {
    label: 'Reassignment Required',
    badge: 'bg-orange-50 text-orange-800 border-orange-200',
    dot: 'bg-orange-500',
    ring: 'ring-orange-100',
    iconA11y: 'Operational exception — needs reassignment',
  },
  review_required: {
    label: 'Review Required',
    badge: 'bg-fuchsia-50 text-fuchsia-800 border-fuchsia-200',
    dot: 'bg-fuchsia-500',
    ring: 'ring-fuchsia-100',
    iconA11y: 'Integrity review needed',
  },
  under_review: {
    label: 'Under Review',
    badge: 'bg-fuchsia-50 text-fuchsia-800 border-fuchsia-200',
    dot: 'bg-fuchsia-500',
    ring: 'ring-fuchsia-100',
    iconA11y: 'Verification under review',
  },
  pending: {
    label: 'Pending',
    badge: 'bg-stone-100 text-stone-700 border-stone-200',
    dot: 'bg-stone-400',
    ring: 'ring-stone-100',
    iconA11y: 'Pending',
  },
  neutral: {
    label: '—',
    badge: 'bg-stone-100 text-stone-600 border-stone-200',
    dot: 'bg-stone-400',
    ring: 'ring-stone-100',
    iconA11y: 'No status',
  },
}

export function resolveStatusToken(raw: string): RescueStatusToken {
  const s = String(raw || '').trim().toLowerCase().replace(/[\s_-]+/g, '_')
  if (!s) return 'neutral'
  if (s in STATUS_TOKENS) return s as RescueStatusToken
  if (s.includes('transit') || s.includes('route')) return 'in_transit'
  if (s.includes('progress')) return 'in_progress'
  if (s.includes('deliver') || s.includes('complete') || s.includes('finish')) return 'completed'
  if (s.includes('receive')) return 'received'
  if (s.includes('verify')) return 'verified'
  if (s.includes('match') || s.includes('allocat')) return 'matched'
  if (s.includes('assign') || s.includes('driver')) return 'assigned'
  if (s.includes('pickup') || s.includes('pick_up')) return 'pickup'
  if (s.includes('arriv')) return 'arriving'
  if (s.includes('cancel') || s.includes('expire')) return 'expired'
  if (s.includes('reassign') || s.includes('exception')) return 'reassignment_required'
  if (s.includes('review')) return 'review_required'
  if (s.includes('post') || s.includes('open') || s.includes('avail')) return 'posted'
  if (s.includes('pend')) return 'pending'
  return 'neutral'
}

export interface RescueStatusProps {
  status: string
  token?: RescueStatusToken
  className?: string
  showDot?: boolean
}

export function RescueStatus({
  status,
  token,
  className = '',
  showDot = true,
}: RescueStatusProps) {
  const t = token ?? resolveStatusToken(status)
  const style = STATUS_TOKENS[t]
  const label = status || style.label

  return (
    <span
      role="status"
      aria-label={`${style.iconA11y}: ${label}`}
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${style.badge} ${className}`}
    >
      {showDot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${style.dot} opacity-90`}
          aria-hidden
        />
      )}
      {label}
    </span>
  )
}
