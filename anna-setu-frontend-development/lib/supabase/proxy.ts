import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

/**
 * Updates the user session and handles cookie synchronization.
 * Also performs server-side route protection and role verification.
 */
export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  const isConfigured = Boolean(
    url &&
    key &&
    !url.includes('demo.supabase.co') &&
    !key.includes('demo-')
  )

  // If Supabase environment variables are missing or use demo placeholders, allow request to proceed
  // to avoid blocking static rendering, demo mode walkthroughs, or local setup without live Supabase.
  if (!url || !key || !isConfigured) {
    return supabaseResponse
  }

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll() {
        return request.cookies.getAll()
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) =>
          request.cookies.set(name, value)
        )
        supabaseResponse = NextResponse.next({
          request,
        })
        cookiesToSet.forEach(({ name, value, options }) =>
          supabaseResponse.cookies.set(name, value, options)
        )
      },
    },
  })

  // IMPORTANT: Do NOT use auth.getSession() in server-side middleware or route guards.
  // getUser() validates the JWT with Supabase Auth server.
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const pathname = request.nextUrl.pathname

  // Protected route checking
  const isDonorRoute = pathname.startsWith('/donor')
  const isReceiverRoute = pathname.startsWith('/receiver')
  const isDriverRoute = pathname.startsWith('/driver')
  const isAdminRoute = pathname.startsWith('/admin')

  const isProtectedRoute = isDonorRoute || isReceiverRoute || isDriverRoute || isAdminRoute

  if (isProtectedRoute) {
    // 1. Unauthenticated check
    if (!user) {
      let loginRedirect = '/auth'
      if (isDonorRoute) loginRedirect = '/auth/donor/login'
      else if (isReceiverRoute) loginRedirect = '/auth/receiver/login'
      else if (isDriverRoute) loginRedirect = '/auth/driver/login'
      else if (isAdminRoute) loginRedirect = '/auth'

      const redirectUrl = request.nextUrl.clone()
      redirectUrl.pathname = loginRedirect
      redirectUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(redirectUrl)
    }

    // 2. Fetch authoritative profile from public.profiles
    const { data: profile } = await supabase
      .from('profiles')
      .select('id, role, is_active')
      .eq('id', user.id)
      .single()

    const rawRole = (profile?.role || '').toLowerCase()

    // 3. Role-based routing validation
    if (isDonorRoute && rawRole !== 'donor') {
      const redirectUrl = request.nextUrl.clone()
      redirectUrl.pathname = rawRole ? `/${rawRole}/dashboard` : '/auth'
      redirectUrl.searchParams.set('error', 'unauthorized_role')
      return NextResponse.redirect(redirectUrl)
    }

    if (isReceiverRoute && rawRole !== 'receiver') {
      const redirectUrl = request.nextUrl.clone()
      redirectUrl.pathname = rawRole ? `/${rawRole}/dashboard` : '/auth'
      redirectUrl.searchParams.set('error', 'unauthorized_role')
      return NextResponse.redirect(redirectUrl)
    }

    if (isDriverRoute && rawRole !== 'driver') {
      const redirectUrl = request.nextUrl.clone()
      redirectUrl.pathname = rawRole ? `/${rawRole}/dashboard` : '/auth'
      redirectUrl.searchParams.set('error', 'unauthorized_role')
      return NextResponse.redirect(redirectUrl)
    }

    if (isAdminRoute && rawRole !== 'admin') {
      const redirectUrl = request.nextUrl.clone()
      redirectUrl.pathname = rawRole ? `/${rawRole}/dashboard` : '/auth'
      redirectUrl.searchParams.set('error', 'admin_access_required')
      return NextResponse.redirect(redirectUrl)
    }
  }

  return supabaseResponse
}
