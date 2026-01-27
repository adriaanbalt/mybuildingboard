/**
 * Server-Side Permission and Redirect Resolution
 *
 * Handles redirect logic after authentication, checking app membership
 * and determining the appropriate destination for users.
 */

import { getSupabaseAdmin } from '@/lib/database/client'
import { logger } from '@/lib/errors/logger'

/**
 * Check if a pathname is an app route (requires app membership)
 */
function isAppRoutePath(pathname: string): boolean {
  // App routes that require membership
  const appRoutes = [
    '/dashboard',
    '/documents',
    '/query',
    '/history',
    '/settings',
    '/app/',
  ]

  return appRoutes.some((route) => pathname.startsWith(route))
}

/**
 * Server-side function to resolve the redirect destination after authentication
 * This is used in API routes where we need to determine where to redirect the user
 * @param userId - The authenticated user's ID
 * @param pathname - The intended destination pathname
 * @returns The redirect path (or null if no redirect needed)
 */
export async function resolveAccessRedirectServer(
  userId: string,
  pathname: string
): Promise<string | null> {
  try {
    // Don't redirect if already on app creation/selection routes
    const isAppCreationRoute =
      pathname.startsWith('/app/create') || pathname.startsWith('/app/select')

    if (isAppCreationRoute) {
      logger.debug('Already on app creation/selection route, skipping redirect', {
        pathname,
      })
      return null
    }

    // Use admin client to bypass RLS and check user membership
    const supabase = getSupabaseAdmin()

    // Check if user exists in app_members table (indicates they've completed onboarding)
    // For MyBuildingBoard, we check if user is a member of any app
    logger.debug('Checking app membership for user', { userId, pathname })
    const { data: memberCheckData, error: memberCheckError } = await supabase
      .from('app_members')
      .select('id, app_id, role')
      .eq('user_id', userId)
      .limit(1)

    logger.debug('App membership check result', {
      userId,
      hasError: !!memberCheckError,
      errorCode: memberCheckError?.code,
      errorMessage: memberCheckError?.message,
      hasData: !!memberCheckData,
      dataLength: memberCheckData?.length || 0,
      membership: memberCheckData?.[0] || null,
    })

    // Handle PostgREST schema cache errors (PGRST205) - table not found in schema cache
    // This can happen in development when schema changes
    if (memberCheckError) {
      if (memberCheckError.code === 'PGRST205') {
        logger.warn(
          'PostgREST schema cache error - table not found in schema cache',
          {
            error: memberCheckError.message,
            suggestion:
              'This may resolve after a moment. If it persists, restart Supabase.',
          }
        )
        // On schema cache error, allow access (fail open)
        // The middleware will handle app selection if needed
        return null
      }

      // For other errors, log and allow access (fail open)
      logger.error('Error checking app membership', {
        error: memberCheckError,
        userId,
      })
      return null
    }

    const hasMembership =
      !memberCheckError && memberCheckData && memberCheckData.length > 0

    logger.debug('Membership check final result', {
      userId,
      hasMembership,
      pathname,
      errorCode: memberCheckError?.code,
    })

    // If user is not a member of any app (new user), redirect to app creation if on app route
    if (!hasMembership) {
      const isAppRoute = isAppRoutePath(pathname)
      if (isAppRoute) {
        logger.info('User not a member of any app, redirecting to app creation', {
          userId,
          pathname,
          hasError: !!memberCheckError,
        })
        return '/app/create'
      }
      return null // Allow access to non-app routes
    }

    // User is a member of an app, allow access to intended destination
    logger.debug('User is a member of an app, allowing access', {
      pathname,
      userId,
    })

    return null // No redirect needed
  } catch (error) {
    logger.error('Error in resolveAccessRedirectServer', { error })
    // On error, allow access (fail open) - let client-side handle it
    return null
  }
}
