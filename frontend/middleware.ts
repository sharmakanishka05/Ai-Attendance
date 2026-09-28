import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const authToken = request.cookies.get('auth_token')?.value;

  const isAuthRoute = pathname.startsWith('/login');
  const isApiRoute = pathname.startsWith('/api');
  const isStaticFile = pathname.startsWith('/_next') || pathname.startsWith('/favicon.ico') || pathname.includes('.');

  // Skip static assets and internal next requests
  if (isStaticFile || isApiRoute) {
    return NextResponse.next();
  }

  // 1. If user is authenticated and tries to access /login, redirect to dashboard /
  if (isAuthRoute && authToken) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  // 2. If user is unauthenticated and tries to access protected routes, redirect to /login
  if (!isAuthRoute && !authToken) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/',
    '/login',
    '/attendance/:path*',
    '/students/:path*',
    '/classes/:path*',
    '/reports/:path*',
    '/sessions/:path*',
    '/settings/:path*',
  ],
};
