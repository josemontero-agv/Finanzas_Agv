import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "Finanzas AGV - Sistema de Gestión Financiera",
  description: "Sistema de gestión de cobranzas, tesorería y letras de cambio",
  icons: {
    icon: "/docs/assets/logo-agrovet.png",
    shortcut: "/docs/assets/logo-agrovet.png",
    apple: "/docs/assets/logo-agrovet.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/docs/assets/logo-agrovet.png" type="image/png" />
        <link rel="apple-touch-icon" href="/docs/assets/logo-agrovet.png" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  if (theme === 'dark') {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="font-sans antialiased bg-background text-foreground transition-colors duration-300">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
