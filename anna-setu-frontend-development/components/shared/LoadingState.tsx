import React from 'react'

export interface LoadingStateProps {
  message?: string
  className?: string
}

export function LoadingState({ message = 'Loading…', className = '' }: LoadingStateProps) {
  return (
    <div className={`p-12 flex flex-col items-center justify-center text-center ${className}`}>
      <div className="w-8 h-8 rounded-full border-2 border-stone-200 border-t-emerald-600 animate-spin mb-3" />
      <p className="text-sm font-medium text-stone-600">{message}</p>
    </div>
  )
}
