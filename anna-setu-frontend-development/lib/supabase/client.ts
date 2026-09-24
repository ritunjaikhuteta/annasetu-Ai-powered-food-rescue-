import { createBrowserClient } from '@supabase/ssr'

export function isSupabaseConfigured() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    ''

  const hasRealValues = Boolean(url && key && !url.includes('demo.supabase.co') && !key.includes('demo-'))
  return hasRealValues
}

/**
 * Creates a Supabase client for use in browser / client components.
 * Reads NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.
 */
export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://demo.supabase.co'
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    'demo-anon-key'

  if (!isSupabaseConfigured()) {
    console.warn('Supabase auth is disabled in local demo mode; using safe fallback state.')
  }

  return createBrowserClient(url, key)
}
