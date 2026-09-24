import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import type { UserProfile, UserRole } from '@/lib/types/core'

/**
 * Server-side helper to retrieve the authenticated Supabase user.
 * Validates the session with the Supabase Auth server.
 */
export async function getCurrentUser() {
  try {
    const supabase = await createClient()
    const {
      data: { user },
    } = await supabase.auth.getUser()
    return user
  } catch {
    return null
  }
}

/**
 * Server-side helper to retrieve the authoritative user profile from public.profiles.
 */
export async function getCurrentProfile(): Promise<UserProfile | null> {
  try {
    const supabase = await createClient()
    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (!user) return null

    const { data: profile } = await supabase
      .from('profiles')
      .select('id, full_name, phone, role, is_active')
      .eq('id', user.id)
      .maybeSingle()

    if (!profile) return null

    return {
      id: profile.id,
      full_name: profile.full_name,
      phone: profile.phone,
      role: (profile.role || '').toLowerCase(),
      is_active: profile.is_active,
    }
  } catch {
    return null
  }
}

/**
 * Server-side guard requiring an authenticated user.
 * Redirects to the specified login path if unauthenticated.
 */
export async function requireUser(redirectPath = '/auth') {
  const user = await getCurrentUser()
  if (!user) {
    redirect(redirectPath)
  }
  return user
}

/**
 * Server-side guard requiring a specific authoritative role.
 * Redirects if unauthenticated or if profile role does not match.
 */
export async function requireRole(expectedRole: UserRole) {
  const user = await requireUser(`/auth/${expectedRole}/login`)
  const profile = await getCurrentProfile()

  if (!profile || profile.role.toLowerCase() !== expectedRole.toLowerCase()) {
    redirect(profile?.role ? `/${profile.role}/dashboard?error=unauthorized` : '/auth')
  }

  return { user, profile }
}
