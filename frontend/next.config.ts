import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Habilitar certificados del sistema para TLS
  env: {
    NEXT_TURBOPACK_EXPERIMENTAL_USE_SYSTEM_TLS_CERTS: '1'
  },
};

export default nextConfig;
