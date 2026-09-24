import React from 'react'
import { Sparkles } from 'lucide-react'

export interface AIInsightProps {
  title?: string
  text: string
  metric?: string
  className?: string
}

export function AIInsight({
  title = 'AI Matching Intelligence',
  text,
  metric,
  className = '',
}: AIInsightProps) {
  return (
    <div className={`p-3.5 rounded-xl bg-gradient-to-r from-emerald-50/80 via-teal-50/50 to-stone-50 border border-emerald-100/80 flex items-start gap-3 ${className}`}>
      <div className="w-7 h-7 rounded-lg bg-emerald-600/10 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
        <Sparkles size={16} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="text-xs font-semibold text-emerald-950 uppercase tracking-wider">{title}</span>
          {metric && (
            <span className="text-xs font-bold text-emerald-700 bg-emerald-100/60 px-2 py-0.5 rounded-full">
              {metric}
            </span>
          )}
        </div>
        <p className="text-xs text-stone-600 leading-relaxed">{text}</p>
      </div>
    </div>
  )
}
