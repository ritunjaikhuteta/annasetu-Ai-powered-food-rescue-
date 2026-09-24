'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { User } from '@supabase/supabase-js'
import { createClient, isSupabaseConfigured } from '@/lib/supabase/client'
import { authService, getDemoSession } from '@/lib/services/auth'
import type { UserProfile, VerificationStatus } from '@/lib/types/core'

interface AuthContextType {
  user: User | null
  profile: UserProfile | null
  verificationStatus: VerificationStatus
  isLoading: boolean
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  verificationStatus: 'PENDING',
  isLoading: true,
  signOut: async () => {},
  refreshProfile: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUserProfile = useCallback(async (activeUser: User | null) => {
    if (!activeUser) {
      setProfile(null)
      setIsLoading(false)
      return
    }

    try {
      const userProfile = await authService.getCurrentProfile()
      setProfile(userProfile)
    } catch (err) {
      console.error('Failed to load profile in AuthProvider:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    let mounted = true

    if (!isSupabaseConfigured()) {
      const demoSession = getDemoSession()
      setUser(null)
      setProfile(demoSession)
      setIsLoading(false)
      return
    }

    try {
      const supabase = createClient()

      // Initial check
      supabase.auth.getUser().then(({ data: { user: currentUser } }) => {
        if (!mounted) return
        setUser(currentUser)
        loadUserProfile(currentUser)
      }).catch(() => {
        if (!mounted) return
        setIsLoading(false)
      })

      // Subscribe to auth state updates (sign in, sign out, token refresh)
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange(async (_event, session) => {
        if (!mounted) return
        const currentUser = session?.user ?? null
        setUser(currentUser)
        await loadUserProfile(currentUser)
      })

      return () => {
        mounted = false
        subscription.unsubscribe()
      }
    } catch (err) {
      console.warn('Supabase client init skipped in AuthProvider (check env):', err)
      setIsLoading(false)
    }
  }, [loadUserProfile])

  const refreshProfile = async () => {
    setIsLoading(true)
    await loadUserProfile(user)
  }

  const handleSignOut = async () => {
    await authService.signOut()
    setUser(null)
    setProfile(null)
  }

  const verificationStatus: VerificationStatus =
    profile?.verification_status || 'PENDING'

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        verificationStatus,
        isLoading,
        signOut: handleSignOut,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
