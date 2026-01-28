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

    // Allow onboarding routes to proceed without auth check
    // These routes handle their own authentication
    if (pathname === '/app/create' || pathname === '/app/select') {
      return NextResponse.next()
    }

    // Create Supabase client for auth check
    // In production Edge runtime, auth checks may fail - make them completely optional
    let user: any = null
    let authCheckSucceeded = false

    try {
      const supabase = createMiddlewareClient(request)

      // Check authentication - use getUser() to validate token
      // In production, if this fails, we'll allow the request to proceed
      const authResult = await supabase.auth.getUser()
      authCheckSucceeded = true

      if (authResult.error) {
        // Auth error - user is not authenticated (check succeeded, user is not logged in)
        user = null
      } else if (authResult.data?.user) {
        // User is authenticated
        user = authResult.data.user
      } else {
        // No user found
        user = null
      }
    } catch (error) {
      // Any error in auth check (client creation, network, Edge runtime issues)
      // In production Edge runtime, allow request to proceed
      // App layer will handle authentication
      authCheckSucceeded = false
      user = null
    }

    // Only redirect to login if auth check succeeded AND user is not authenticated
    // If auth check failed (caught error), allow request to proceed to avoid breaking the app
    if (authCheckSucceeded && !user) {
      // User is not authenticated - redirect to login
      try {
        const origin = request.nextUrl.origin
        const redirectUrl = createAppUrl('/login', origin)
        redirectUrl.searchParams.set('redirect', pathname)
        return NextResponse.redirect(redirectUrl)
      } catch {
        // If URL creation fails, just allow request
        return NextResponse.next()
      }
    }

    // If auth check failed or user is authenticated, continue with app ID handling

    // Get app ID from cookie or header (no database query in middleware)
    // Database queries are unreliable in Edge runtime - let app layer handle it
    const cookieAppId = request.cookies.get('app_id')?.value
    const headerAppId = request.headers.get('x-app-id')
    const appId = headerAppId || cookieAppId || null

    // Set app_id in headers and cookies for downstream use (if we have one)
    const response = NextResponse.next()
    if (appId) {
      response.headers.set('x-app-id', appId)
      response.cookies.set('app_id', appId, {
        path: '/',
        maxAge: 365 * 24 * 60 * 60, // 1 year
      })
    }

    return response
  } catch (error) {
    // Catch any unexpected errors and allow request to proceed
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
