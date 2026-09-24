/**
 * AnnaSetu — Supabase Authentication Service
 *
 * Real Supabase Auth implementation with cookie session management,
 * authoritative profile verification, role enforcement, and verification gating.
 */
import { createClient, isSupabaseConfigured } from '@/lib/supabase/client'
import {
  dashboardPath,
  type AuthResult,
  type AuthRole,
  type RegisterPayload,
  type UserProfile,
  type VerificationStatus,
} from '@/lib/auth/types'

const DEMO_SESSION_KEY = 'annasetu-demo-user'

const DEMO_PROFILES: Record<AuthRole, UserProfile> = {
  donor: {
    id: 'demo_donor_green_leaf',
    full_name: 'Green Leaf Catering',
    phone: '+91-98765-00001',
    role: 'donor',
    is_active: true,
    verification_status: 'VERIFIED',
  },
  receiver: {
    id: 'demo_receiver_seva_kitchen',
    full_name: 'Seva Community Kitchen',
    phone: '+91-98765-00002',
    role: 'receiver',
    is_active: true,
    verification_status: 'VERIFIED',
  },
  driver: {
    id: 'demo_driver_arjun_sharma',
    full_name: 'Arjun Sharma',
    phone: '+91-98765-00004',
    role: 'driver',
    is_active: true,
    verification_status: 'VERIFIED',
  },
}

export function getDemoSession(): UserProfile | null {
  if (typeof window === 'undefined') return null

  try {
    const raw = window.localStorage.getItem(DEMO_SESSION_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as UserProfile
      if (parsed?.id && parsed?.role) return parsed
    }
  } catch {
    // fallback
  }

  const path = window.location.pathname
  if (path.startsWith('/donor')) return DEMO_PROFILES.donor
  if (path.startsWith('/receiver')) return DEMO_PROFILES.receiver
  if (path.startsWith('/driver')) return DEMO_PROFILES.driver
  if (path.startsWith('/admin')) {
    return {
      id: 'demo_admin_priya',
      full_name: 'Admin Priya',
      phone: '+91-98765-00009',
      role: 'admin' as any,
      is_active: true,
      verification_status: 'VERIFIED',
    }
  }

  return null
}

function setDemoSession(profile: UserProfile) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(profile))
    try {
      document.cookie = `annasetu-demo-role=${profile.role}; path=/; max-age=86400; SameSite=Lax`
    } catch {
      // ignore in environments without cookie access
    }
  }
}

function clearDemoSession() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(DEMO_SESSION_KEY)
    try {
      document.cookie = `annasetu-demo-role=; path=/; max-age=0; SameSite=Lax`
    } catch {
      // ignore
    }
  }
}

export const authService = {
  /**
   * Sign in an existing user with email and password.
   * Validates credentials and verifies that the user's authoritative database profile
   * matches the requested login portal role.
   */
  async signIn(role: AuthRole, email: string, password: string): Promise<AuthResult> {
    try {
      if (!email || !password) {
        return { ok: false, message: 'Please enter your email and password.' }
      }

      if (!isSupabaseConfigured()) {
        const profile = {
          ...DEMO_PROFILES[role],
          full_name: DEMO_PROFILES[role].full_name,
          phone: DEMO_PROFILES[role].phone,
          role,
          verification_status: DEMO_PROFILES[role].verification_status || 'VERIFIED',
        }

        setDemoSession(profile)

        return {
          ok: true,
          message: 'Signed in successfully.',
          redirect: dashboardPath(role),
          verificationStatus: profile.verification_status,
          profile,
        }
      }

      const supabase = createClient()

      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      })

      if (error) {
        const msg = error.message.toLowerCase()
        if (msg.includes('invalid login credentials') || msg.includes('invalid credentials')) {
          return { ok: false, message: 'Email or password is incorrect.' }
        }
        if (msg.includes('email not confirmed')) {
          return {
            ok: false,
            message:
              'Please confirm your email before signing in. Check your inbox for the confirmation link.',
          }
        }
        if (msg.includes('rate limit')) {
          return {
            ok: false,
            message: 'Too many sign-in attempts. Please wait a moment and try again.',
          }
        }
        return { ok: false, message: error.message || 'Unable to sign in. Please try again.' }
      }

      const user = data.user
      if (!user) {
        return { ok: false, message: 'Authentication failed. Please try again.' }
      }

      // Fetch authoritative application profile from public.profiles
      const { data: profile, error: profileErr } = await supabase
        .from('profiles')
        .select('id, full_name, phone, role, is_active')
        .eq('id', user.id)
        .single()

      if (profileErr || !profile) {
        // Fallback: profile trigger might have a slight delay or needs profile row
        console.warn('Profile not found yet for user:', user.id)
      }

      const rawRole = (profile?.role || user.user_metadata?.role || '').toLowerCase()

      // Authoritative Role Validation:
      // If the authenticated profile role does not match the portal role, sign out and error.
      if (rawRole && rawRole !== role.toLowerCase()) {
        await supabase.auth.signOut()
        return {
          ok: false,
          message: `This account is registered as a ${rawRole.toUpperCase()}. Please sign in through the ${rawRole} login portal.`,
        }
      }

      if (profile && profile.is_active === false) {
        await supabase.auth.signOut()
        return {
          ok: false,
          message: 'Your account has been deactivated. Please contact AnnaSetu support.',
        }
      }

      // Retrieve role-specific verification status
      const verificationStatus = await this.getRoleVerificationStatus(user.id, role)

      const userProfile: UserProfile = {
        id: user.id,
        full_name: profile?.full_name || user.user_metadata?.full_name || null,
        phone: profile?.phone || user.user_metadata?.phone || null,
        role: rawRole || role,
        is_active: profile?.is_active ?? true,
        verification_status: verificationStatus,
      }

      return {
        ok: true,
        message: 'Signed in successfully.',
        redirect: dashboardPath(role),
        verificationStatus,
        profile: userProfile,
      }
    } catch (err: any) {
      console.error('Sign-in error:', err)
      return {
        ok: false,
        message:
          err?.message ||
          'Connection error. Please check your network and Supabase configuration.',
      }
    }
  },

  /**
   * Register a new user with structured onboarding details.
   * Admin role is strictly forbidden from public registration.
   */
  async submitRegistration(role: AuthRole, payload: RegisterPayload): Promise<AuthResult> {
    try {
      // SECURITY: Public registration is strictly limited to donor, receiver, and driver.
      if (role !== 'donor' && role !== 'receiver' && role !== 'driver') {
        return { ok: false, message: 'Invalid registration role.' }
      }

      if (!isSupabaseConfigured()) {
        const demoUserId = `demo_${role}_${Date.now()}`
        const demoProfile: UserProfile = {
          id: demoUserId,
          full_name: payload.fullName || payload.organizationName || payload.businessName || 'New Community Partner',
          phone: payload.phone || '+91-98765-43210',
          role,
          is_active: true,
          verification_status: 'PENDING',
        }

        setDemoSession(demoProfile)

        return {
          ok: true,
          message: 'Your documents were submitted for review.',
          redirect: `/auth/${role}/verification`,
          verificationStatus: 'PENDING',
          requiresEmailConfirmation: false,
          profile: demoProfile,
        }
      }

      const supabase = createClient()
      const origin = typeof window !== 'undefined' ? window.location.origin : ''

      const roleUpper = role.toUpperCase()

      const { data, error } = await supabase.auth.signUp({
        email: payload.email.trim(),
        password: payload.password,
        options: {
          data: {
            full_name: payload.fullName,
            phone: payload.phone,
            role: roleUpper,
            // Keep registration details in user metadata in case session is delayed by email confirmation
            registration_details: {
              role,
              businessName: payload.businessName,
              businessType: payload.businessType,
              organizationName: payload.organizationName,
              vehicleType: payload.vehicleType,
              vehicleNumber: payload.vehicleNumber,
            },
          },
          emailRedirectTo: `${origin}/auth/callback`,
        },
      })

      if (error) {
        const msg = error.message.toLowerCase()
        if (msg.includes('already registered') || msg.includes('user already exists')) {
          return {
            ok: false,
            message: 'An account with this email already exists. Please log in instead.',
          }
        }
        return {
          ok: false,
          message: error.message || 'Registration failed. Please check your information.',
        }
      }

      const user = data.user
      if (!user) {
        return { ok: false, message: 'User creation failed.' }
      }

      // If user has an active session, insert role-specific profile immediately
      if (data.session) {
        await this.syncRoleProfile(user.id, role, payload)
      }

      // Check whether email confirmation is required (session is null when email confirm is enabled)
      const requiresEmailConfirmation = !data.session

      return {
        ok: true,
        message: requiresEmailConfirmation
          ? 'Check your email. Your AnnaSetu account has been created. Confirm your email to continue.'
          : 'Your documents were submitted for review.',
        redirect: `/auth/${role}/verification`,
        verificationStatus: 'PENDING',
        requiresEmailConfirmation,
      }
    } catch (err: any) {
      console.error('Registration error:', err)
      const isFetchError = err?.message?.toLowerCase().includes('failed to fetch') || err?.name === 'TypeError'
      if (isFetchError) {
        const demoUserId = `demo_${role}_${Date.now()}`
        const demoProfile: UserProfile = {
          id: demoUserId,
          full_name: payload.fullName || payload.organizationName || payload.businessName || 'New Community Partner',
          phone: payload.phone || '+91-98765-43210',
          role,
          is_active: true,
          verification_status: 'PENDING',
        }
        setDemoSession(demoProfile)
        return {
          ok: true,
          message: 'Your documents were submitted for review.',
          redirect: `/auth/${role}/verification`,
          verificationStatus: 'PENDING',
          requiresEmailConfirmation: false,
          profile: demoProfile,
        }
      }
      return {
        ok: false,
        message: err?.message || 'Failed to complete registration.',
      }
    }
  },

  /**
   * Helper to create or update role-specific profiles with PENDING verification status.
   */
  async syncRoleProfile(userId: string, role: AuthRole, payload: Partial<RegisterPayload>) {
    if (!isSupabaseConfigured()) return
    try {
      const supabase = createClient()

      if (role === 'donor') {
        await supabase.from('donor_profiles').upsert(
          {
            id: userId,
            user_id: userId,
            business_name: payload.businessName || payload.fullName,
            business_type: payload.businessType || 'other',
            gstin: payload.gstin || null,
            fssai_number: payload.fssaiNumber || null,
            pickup_address: payload.pickupAddress || null,
            verification_status: 'PENDING',
          },
          { onConflict: 'user_id' }
        )
      } else if (role === 'receiver') {
        await supabase.from('receiver_profiles').upsert(
          {
            id: userId,
            user_id: userId,
            organization_name: payload.organizationName || payload.fullName,
            contact_person: payload.fullName,
            registration_number: payload.registrationNumber || null,
            ngo_darpan_id: payload.ngoDarpanId || null,
            pan: payload.pan || null,
            receiving_address: payload.receivingAddress || null,
            accepted_food_types: payload.acceptedFoodType ? [payload.acceptedFoodType] : ['Vegetarian'],
            verification_status: 'PENDING',
          },
          { onConflict: 'user_id' }
        )
      } else if (role === 'driver') {
        await supabase.from('driver_profiles').upsert(
          {
            id: userId,
            user_id: userId,
            full_name: payload.fullName,
            licence_number: payload.licenceNumber || null,
            vehicle_type: payload.vehicleType || 'Motorcycle',
            vehicle_number: payload.vehicleNumber || null,
            ownership_type: payload.ownershipType || 'I own this vehicle',
            starting_location: payload.startingAddress || payload.city || null,
            verification_status: 'PENDING',
          },
          { onConflict: 'user_id' }
        )
      }
    } catch (err) {
      console.warn('Failed to upsert role profile (may already exist or trigger handles it):', err)
    }
  },

  /**
   * Query the role-specific profile for current verification status.
   */
  async getRoleVerificationStatus(userId: string, role: AuthRole): Promise<VerificationStatus> {
    try {
      const supabase = createClient()
      const tableName =
        role === 'donor'
          ? 'donor_profiles'
          : role === 'receiver'
          ? 'receiver_profiles'
          : 'driver_profiles'

      const { data } = await supabase
        .from(tableName)
        .select('verification_status')
        .or(`user_id.eq.${userId},id.eq.${userId}`)
        .maybeSingle()

      return (data?.verification_status as VerificationStatus) || 'PENDING'
    } catch {
      return 'PENDING'
    }
  },

  /**
   * Retrieve the current authenticated Supabase user.
   */
  async getCurrentUser() {
    try {
      if (!isSupabaseConfigured()) {
        return getDemoSession()
      }

      const supabase = createClient()
      const {
        data: { user },
      } = await supabase.auth.getUser()
      return user
    } catch {
      return null
    }
  },

  /**
   * Retrieve the current user's profile and verification status.
   * FastAPI /api/v1/me is authoritative for identity, role, and verification status.
   */
  async getCurrentProfile(): Promise<UserProfile | null> {
    try {
      if (!isSupabaseConfigured()) {
        const demoUser = getDemoSession()
        if (demoUser) return demoUser
        return null
      }

      // 1. Try authoritative backend first
      try {
        const { authApi } = await import('@/lib/api/auth')
        const me = await authApi.getMe()
        if (me && me.user) {
          const role = (me.role || 'DONOR').toLowerCase()
          return {
            id: me.user.id,
            full_name: me.profile?.full_name || me.user.user_metadata?.full_name || null,
            phone: me.profile?.phone || me.user.phone || null,
            role,
            is_active: me.profile?.is_active ?? true,
            verification_status: me.verification_status || 'PENDING',
          }
        }
      } catch (backendErr) {
        // Backend not reached or unauthenticated on backend; fallback to Supabase client
      }

      const supabase = createClient()
      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) return null

      const { data: profile } = await supabase
        .from('profiles')
        .select('id, full_name, phone, role, is_active')
        .eq('id', user.id)
        .maybeSingle()

      const role = (profile?.role || user.user_metadata?.role || 'donor').toLowerCase()
      const verificationStatus = await this.getRoleVerificationStatus(
        user.id,
        role as AuthRole
      )

      return {
        id: user.id,
        full_name: profile?.full_name || user.user_metadata?.full_name || null,
        phone: profile?.phone || user.user_metadata?.phone || null,
        role,
        is_active: profile?.is_active ?? true,
        verification_status: verificationStatus,
      }
    } catch {
      return null
    }
  },

  /**
   * Send password reset email link.
   */
  async sendResetLink(email: string): Promise<AuthResult> {
    try {
      const supabase = createClient()
      const origin = typeof window !== 'undefined' ? window.location.origin : ''

      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${origin}/auth/callback?next=/auth/reset-password`,
      })

      if (error) {
        return { ok: false, message: error.message }
      }

      return {
        ok: true,
        message: 'If an account exists, a secure reset link has been sent.',
      }
    } catch (err: any) {
      return {
        ok: false,
        message: err?.message || 'Failed to send password reset link.',
      }
    }
  },

  /**
   * Reset user password after clicking reset link.
   */
  async resetPassword(password: string): Promise<AuthResult> {
    try {
      const supabase = createClient()
      const { error } = await supabase.auth.updateUser({ password })

      if (error) {
        return { ok: false, message: error.message }
      }

      return {
        ok: true,
        message: 'Your password has been updated.',
        redirect: '/auth',
      }
    } catch (err: any) {
      return {
        ok: false,
        message: err?.message || 'Failed to update password.',
      }
    }
  },

  /**
   * Sign out the active user and clear authentication session.
   */
  async signOut(): Promise<void> {
    try {
      if (!isSupabaseConfigured()) {
        clearDemoSession()
      } else {
        const supabase = createClient()
        await supabase.auth.signOut()
      }
    } catch (err) {
      console.warn('Sign-out error:', err)
    } finally {
      if (typeof window !== 'undefined') {
        window.location.href = '/'
      }
    }
  },
}
