import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    turbo: {
      resolveAlias: {
        // Evitar problemas con fuentes de Google en entornos corporativos
      }
    }
  },
  // Habilitar certificados del sistema para TLS
  env: {
    NEXT_TURBOPACK_EXPERIMENTAL_USE_SYSTEM_TLS_CERTS: '1'
  },
  async rewrites() {
    return [
      {
        source: "/docs/assets/logo-agrovet.png",
        destination: "/img/agrovet-market.png",
      },
    ]
  },
};

export default nextConfig;
