import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
