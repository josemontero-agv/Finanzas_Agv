import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const LETTERS_ENABLED =
  process.env.NEXT_PUBLIC_ENABLE_LETTERS?.trim().toLowerCase() === "true"

const ALLOWED_PATH_PREFIXES = [
  ...(LETTERS_ENABLED ? ["/letters"] : []),
  "/collections",
  "/treasury",
  "/dashboard",
  "/diagnostics",
  "/observability",
  "/apps",
  "/login",
]

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.includes(".") || pathname.startsWith("/_next/")) {
    return NextResponse.next()
  }

  // Bloqueo en el borde: sin renderizar la página ni disparar peticiones al backend.
  if (
    !LETTERS_ENABLED &&
    (pathname === "/letters" || pathname.startsWith("/letters/"))
  ) {
    const redirectUrl = request.nextUrl.clone()
    redirectUrl.pathname = "/collections"
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
