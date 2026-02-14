import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const ALLOWED_PATH_PREFIXES = ["/letters", "/login"]
const SESSION_COOKIE_NAME = "session"

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const hasSession = Boolean(request.cookies.get(SESSION_COOKIE_NAME)?.value)

  // Dejar pasar archivos estáticos de /public y recursos internos.
  if (pathname.includes(".") || pathname.startsWith("/_next/")) {
    return NextResponse.next()
  }

  const isLettersRoute = pathname === "/letters" || pathname.startsWith("/letters/")
  const isLoginRoute = pathname === "/login" || pathname.startsWith("/login/")

  // Protección temprana: evita renderizar /letters sin sesión.
  if (isLettersRoute && !hasSession) {
    const redirectUrl = request.nextUrl.clone()
    redirectUrl.pathname = "/login"
    redirectUrl.search = ""
    return NextResponse.redirect(redirectUrl)
  }

  // Si ya hay sesión, evita volver a login.
  if (isLoginRoute && hasSession) {
    const redirectUrl = request.nextUrl.clone()
    redirectUrl.pathname = "/letters"
    redirectUrl.search = ""
    return NextResponse.redirect(redirectUrl)
  }

  const isAllowedPath =
    pathname === "/" ||
    ALLOWED_PATH_PREFIXES.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
    )

  if (isAllowedPath) {
    return NextResponse.next()
  }

  const redirectUrl = request.nextUrl.clone()
  redirectUrl.pathname = "/login"
  redirectUrl.search = ""
  return NextResponse.redirect(redirectUrl)
}

export const config = {
  matcher: ["/((?!api).*)"],
}
