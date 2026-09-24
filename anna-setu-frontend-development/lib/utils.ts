import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const APP_CONFIG = {
  DEMO_MODE: process.env.NEXT_PUBLIC_DEMO_MODE === 'true',
  APP_ENV: process.env.NEXT_PUBLIC_APP_ENV || 'development',
} as const

export function isDemoMode(): boolean {
  return APP_CONFIG.DEMO_MODE
}

export function formatKg(kg: number): string {
  return `${kg.toLocaleString('en-IN')} kg`
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}
