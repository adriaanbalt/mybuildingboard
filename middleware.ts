/**
 * Next.js Middleware
 *
 * Handles multi-tenant routing and app ID detection.
 */

import { validateAppId } from '@/lib/app/detection'
import { createMiddlewareClient } from '@/lib/auth/server'
import { createAppUrl } from '@/lib/utils/url'
import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

/**
 * Public routes that don't require authentication
 */
const publicRoutes = ['/', '/login', '/signup', '/features', '/pricing', '/privacy', '/terms', '/auth/callback']

/**
 * Check if route is public
 */
function isPublicRoute(pathname: string): boolean {
  return publicRoutes.some((route) => pathname === route || pathname.startsWith('/api/auth'))
}

export async function middleware(request: NextRequest) {
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

  const supabase = createMiddlewareClient(request)

  // Check authentication - use getUser() to validate token with Supabase Auth server
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser()

  // If not authenticated, redirect to login
  if (userError || !user) {
    const redirectUrl = createAppUrl('/login')
    redirectUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // Get session after validating user
  const {
    data: { session },
  } = await supabase.auth.getSession()

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
  if (headerAppId && (await validateAppId(headerAppId))) {
    appId = headerAppId
  } else if (cookieAppId && (await validateAppId(cookieAppId))) {
    appId = cookieAppId
  }

  // If no app ID, check user's app memberships
  if (!appId && user) {
    // Allow onboarding routes to proceed without redirect loop
    if (pathname === '/app/create' || pathname === '/app/select') {
      return NextResponse.next()
    }

    const supabaseForQuery = createMiddlewareClient(request)
    const { data: memberships } = await supabaseForQuery
      .from('app_members')
      .select('app_id')
      .eq('user_id', user.id)

    const userAppIds = memberships?.map((m) => m.app_id) || []

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
  }

  // Validate app ID exists
  const isValid = await validateAppId(appId)
  if (!isValid) {
    // Invalid app ID - clear cookie and redirect to app selection
    // But allow /app/select to proceed if already there to prevent redirect loop
    if (pathname === '/app/select') {
      const response = NextResponse.next()
      response.cookies.delete('app_id')
      return response
    }
    const response = NextResponse.redirect(createAppUrl('/app/select'))
    response.cookies.delete('app_id')
    return response
  }

  // Set app_id in headers and cookies for downstream use
  const response = NextResponse.next()
  response.headers.set('x-app-id', appId)
  response.cookies.set('app_id', appId, {
    path: '/',
    maxAge: 365 * 24 * 60 * 60, // 1 year
  })

  return response
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
