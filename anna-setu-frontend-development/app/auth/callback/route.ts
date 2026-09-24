import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next')

  if (code) {
    try {
      const supabase = await createClient()
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)

      if (!error && data?.user) {
        // If an explicit next redirect was requested (e.g. /auth/reset-password)
        if (next) {
          return NextResponse.redirect(`${origin}${next}`)
        }

        // Fetch user profile to route directly to their authoritative role dashboard
        const { data: profile } = await supabase
          .from('profiles')
          .select('role')
          .eq('id', data.user.id)
          .single()

        const role = (profile?.role || '').toLowerCase()
        if (role === 'donor') return NextResponse.redirect(`${origin}/donor/dashboard`)
        if (role === 'receiver') return NextResponse.redirect(`${origin}/receiver/dashboard`)
        if (role === 'driver') return NextResponse.redirect(`${origin}/driver/dashboard`)
        if (role === 'admin') return NextResponse.redirect(`${origin}/admin/dashboard`)

        return NextResponse.redirect(`${origin}/`)
      }
    } catch (err) {
      console.error('Error exchanging auth code for session:', err)
    }
  }

  // Return user to auth with an error message if code exchange failed
  return NextResponse.redirect(`${origin}/auth?error=confirmation_failed`)
}
