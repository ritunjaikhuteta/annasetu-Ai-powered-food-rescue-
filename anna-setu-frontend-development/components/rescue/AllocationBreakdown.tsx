import React from 'react'
import { Building2 } from 'lucide-react'

export interface AllocationItem {
  name: string
  quantity: number
  address?: string
}

export interface AllocationBreakdownProps {
  totalQuantity: number
  unit?: string
  receivers: AllocationItem[]
  className?: string
}

export function AllocationBreakdown({
  totalQuantity,
  unit = 'kg',
  receivers,
  className = '',
}: AllocationBreakdownProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between text-xs text-stone-500 font-medium">
        <span>Allocation Split ({receivers.length} verified receivers)</span>
        <span>{totalQuantity} {unit} total</span>
      </div>

      <div className="w-full h-2 rounded-full overflow-hidden bg-stone-100 flex gap-0.5">
        {receivers.map((r, i) => {
          const pct = Math.max(5, (r.quantity / totalQuantity) * 100)
          const colors = ['bg-emerald-500', 'bg-blue-500', 'bg-amber-500', 'bg-purple-500']
          return (
            <div
              key={r.name + i}
              style={{ width: `${pct}%` }}
              className={`h-full ${colors[i % colors.length]}`}
              title={`${r.name}: ${r.quantity} ${unit}`}
            />
          )
        })}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {receivers.map((r, i) => {
          const dots = ['text-emerald-500', 'text-blue-500', 'text-amber-500', 'text-purple-500']
          return (
            <div
              key={r.name + i}
              className="p-2.5 rounded-lg border border-stone-100 bg-stone-50/50 flex flex-col justify-between"
            >
              <div className="flex items-center gap-1.5 text-xs font-semibold text-stone-800">
                <span className={`w-2 h-2 rounded-full bg-current ${dots[i % dots.length]}`} />
                <span className="truncate">{r.name}</span>
              </div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="text-base font-bold text-stone-900">{r.quantity} <span className="text-xs font-normal text-stone-500">{unit}</span></span>
                {r.address && <span className="text-[11px] text-stone-400 truncate max-w-[100px]">{r.address.split(',')[0]}</span>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
