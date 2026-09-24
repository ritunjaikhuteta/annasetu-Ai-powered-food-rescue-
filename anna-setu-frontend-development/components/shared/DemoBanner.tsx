'use client'

import { AlertTriangle, FlaskConical } from 'lucide-react'
import { isDemoMode } from '@/lib/utils'

export function DemoBanner() {
  if (!isDemoMode()) return null

  return (
    <div
      role="region"
      aria-label="Demo environment notice"
      className="w-full bg-gradient-to-r from-amber-50 via-yellow-50 to-amber-50 border-b border-amber-200/60 text-amber-900 px-4 py-2 text-[11px] font-medium flex items-center justify-center gap-2 tracking-wide"
    >
      <FlaskConical size={13} className="text-amber-700" aria-hidden />
      <span className="font-semibold uppercase tracking-wider">Demo Environment</span>
      <span className="text-amber-700/80 hidden sm:inline">
        · Data shown uses a seeded scenario and is reset between sessions.
      </span>
      <AlertTriangle size={12} className="text-amber-600 ml-1 hidden md:inline" aria-hidden />
    </div>
  )
}
