import React from 'react'

export interface FoodTypeBadgeProps {
  type: string
  category?: string
  className?: string
}

export function FoodTypeBadge({ type, category, className = '' }: FoodTypeBadgeProps) {
  const isVeg = type.toLowerCase().includes('veg') && !type.toLowerCase().includes('non')
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isVeg
          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
          : 'bg-amber-50 text-amber-800 border border-amber-200'
      } ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${isVeg ? 'bg-emerald-500' : 'bg-amber-500'}`} />
      {type}
      {category && <span className="opacity-75">· {category}</span>}
    </span>
  )
}
