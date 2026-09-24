/**
 * AnnaSetu — Frontend API Client Layer (FastAPI Backend)
 */

import { createClient, isSupabaseConfigured } from '@/lib/supabase/client'

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000'

export interface ApiErrorResponse {
  success: false
  error: {
    code: string
    message: string
    details?: any
  }
}

export class ApiError extends Error {
  code: string
  status: number
  details?: any

  constructor(message: string, code: string, status: number, details?: any) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`

  const headers = new Headers(options.headers || {})
  headers.set('Content-Type', 'application/json')

  // Automatically attach Supabase session JWT if available in browser
  if (!headers.has('Authorization') && typeof window !== 'undefined' && isSupabaseConfigured()) {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) {
        headers.set('Authorization', `Bearer ${session.access_token}`)
      }
    } catch {
      // Ignored for unauthenticated calls
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorData: ApiErrorResponse | null = null
    try {
      errorData = await response.json()
    } catch {
      // Non-JSON response
    }

    const message = errorData?.error?.message || `API request failed with status ${response.status}`
    const code = errorData?.error?.code || 'API_ERROR'
    const details = errorData?.error?.details

    throw new ApiError(message, code, response.status, details)
  }

  return response.json() as Promise<T>
}
