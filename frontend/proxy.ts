import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const ALLOWED_PATH_PREFIXES = [
  "/letters",
  "/collections",
  "/treasury",
  "/dashboard",
  "/diagnostics",
  "/login",
]

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Dejar pasar archivos estáticos de /public y recursos internos.
  if (pathname.includes(".") || pathname.startsWith("/_next/")) {
    return NextResponse.next()
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
