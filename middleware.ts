/**
 * Next.js Middleware
 *
 * Handles multi-tenant routing and app ID detection.
 */

// Note: validateAppId is not used in middleware as it requires server-only features
// App ID validation happens in the app layer instead
import { createMiddlewareClient } from '@/lib/auth/server'
import { createAppUrl } from '@/lib/utils/url'
import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

/**
 * Public routes that don't require authentication
 */
const publicRoutes = [
  '/',
  '/login',
  '/signup',
  '/features',
  '/pricing',
  '/privacy',
  '/terms',
  '/auth/callback',
]

/**
 * Check if route is public
 */
function isPublicRoute(pathname: string): boolean {
  return publicRoutes.some((route) => pathname === route || pathname.startsWith('/api/auth'))
}

export async function middleware(request: NextRequest) {
  try {
    const { pathname } = request.nextUrl

    // Skip middleware for public routes
    if (isPublicRoute(pathname)) {
      return NextResponse.next()
    }

    // Skip middleware for API routes (they handle auth separately)
    if (pathname.startsWith('/api/')) {
      return NextResponse.next()
    }

    // Skip middleware for static files
    if (
      pathname.startsWith('/_next/') ||
      pathname.startsWith('/favicon.ico') ||
      pathname.startsWith('/public/')
    ) {
      return NextResponse.next()
    }

    let supabase
    try {
      supabase = createMiddlewareClient(request)
    } catch (error) {
      // If Supabase client creation fails (e.g., missing env vars), allow request
      // This prevents middleware from breaking the entire app
      console.error('[Middleware] Failed to create Supabase client:', error)
      return NextResponse.next()
    }

    // Check authentication - use getUser() to validate token with Supabase Auth server
    // Add timeout protection for Edge runtime
    let user, userError
    try {
      const getUserPromise = supabase.auth.getUser()
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Auth timeout')), 10000)
      )
      const result = (await Promise.race([getUserPromise, timeoutPromise])) as any
      user = result.data?.user
      userError = result.error
    } catch (error) {
      // On timeout or error, redirect to login
      console.error('[Middleware] Auth check failed:', error)
      const redirectUrl = createAppUrl('/login')
      redirectUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(redirectUrl)
    }

    // If not authenticated, redirect to login
    if (userError || !user) {
      const redirectUrl = createAppUrl('/login')
      redirectUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(redirectUrl)
    }

    // Get session after validating user
    // Add timeout protection for Edge runtime
    let session
    try {
      const getSessionPromise = supabase.auth.getSession()
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Session timeout')), 5000)
      )
      const result = (await Promise.race([getSessionPromise, timeoutPromise])) as any
      session = result.data?.session
    } catch (error) {
      // On timeout or error, redirect to login
      console.error('[Middleware] Session check failed:', error)
      const redirectUrl = createAppUrl('/login')
      redirectUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(redirectUrl)
    }

    if (!session) {
      const redirectUrl = createAppUrl('/login')
      redirectUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(redirectUrl)
    }

    // Get app ID from cookie or header
    const cookieAppId = request.cookies.get('app_id')?.value
    const headerAppId = request.headers.get('x-app-id')

    let appId: string | null = null

    // Priority: header > cookie > user membership
    // Note: validateAppId uses createServerSupabaseClient which may not work in middleware
    // For now, we'll trust the appId from header/cookie and validate later if needed
    if (headerAppId) {
      appId = headerAppId
    } else if (cookieAppId) {
      appId = cookieAppId
    }

    // If no app ID, check user's app memberships
    // Note: In production Edge runtime, database queries may timeout or fail
    // We'll make this optional and fail gracefully
    if (!appId && user) {
      // Allow onboarding routes to proceed without redirect loop
      if (pathname === '/app/create' || pathname === '/app/select') {
        return NextResponse.next()
      }

      try {
        // Add timeout for database query (Edge runtime has strict limits)
        const queryPromise = (async () => {
          const supabaseForQuery = createMiddlewareClient(request)
          return await supabaseForQuery
            .from('app_members')
            .select('app_id')
            .eq('user_id', user.id as any)
        })()

        // Race against timeout (5 seconds max for Edge runtime)
        const timeoutPromise = new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Query timeout')), 5000)
        )

        const { data: memberships, error: membershipsError } = (await Promise.race([
          queryPromise,
          timeoutPromise,
        ])) as any

        if (membershipsError) {
          // On error, allow request to proceed - app layer will handle app selection
          return NextResponse.next()
        }

        const userAppIds = (memberships as any)?.map((m: any) => m.app_id) || []

        if (userAppIds.length === 0) {
          // No apps - redirect to app creation
          return NextResponse.redirect(createAppUrl('/app/create'))
        } else if (userAppIds.length === 1) {
          // Single app - set app_id cookie and header
          const response = NextResponse.next()
          response.cookies.set('app_id', userAppIds[0], {
            path: '/',
            maxAge: 365 * 24 * 60 * 60, // 1 year
          })
          response.headers.set('x-app-id', userAppIds[0])
          return response
        } else {
          // Multiple apps - redirect to app selection
          return NextResponse.redirect(createAppUrl('/app/select'))
        }
      } catch (error) {
        // On timeout or error, allow request to proceed
        // The app layer will handle app selection if needed
        // This prevents middleware from blocking all requests
        return NextResponse.next()
      }
    }

    // Set app_id in headers and cookies for downstream use (if we have one)
    // Note: We skip validation here as validateAppId uses server-only features
    // Validation will happen in the app layer if needed
    if (appId) {
      const response = NextResponse.next()
      response.headers.set('x-app-id', appId)
      response.cookies.set('app_id', appId, {
        path: '/',
        maxAge: 365 * 24 * 60 * 60, // 1 year
      })
      return response
    }

    // No app ID but user is authenticated - allow request to proceed
    // The app will handle app selection if needed
    return NextResponse.next()
  } catch (error) {
    // Catch any unexpected errors and log them
    console.error('[Middleware] Unexpected error:', error)
    // Fail open - allow request to proceed rather than blocking
    // This prevents middleware from breaking the entire app
    return NextResponse.next()
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
