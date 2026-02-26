"use client"

import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Mail, Moon, Sun, Wallet, LogOut } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/components/theme-provider'
import { authApi } from '@/lib/api'

export function Sidebar() {
  const router = useRouter()
  const [isExpanded, setIsExpanded] = useState(false)
  const { theme, toggleTheme } = useTheme()

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } finally {
      router.replace('/login')
    }
  }

  return (
    <aside 
      className={cn(
        "fixed lg:static inset-y-0 left-0 z-50 bg-[#714B67] dark:bg-[#1a1a24] dark:border-r dark:border-slate-800 text-white transition-all duration-300 ease-in-out flex flex-col shadow-2xl overflow-hidden group",
        isExpanded ? "w-64" : "w-20"
      )}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      <div className="p-6 mb-8 flex items-center gap-4">
        <div className="min-w-[32px] h-8 bg-white rounded-lg flex items-center justify-center overflow-hidden p-1">
          <Image
            src="/docs/assets/logo-agrovet.png"
            alt="Agrovet Market"
            width={28}
            height={28}
            className="h-7 w-7 object-contain"
            priority
          />
        </div>
        <div className={cn("transition-opacity duration-300 whitespace-nowrap", isExpanded ? "opacity-100" : "opacity-0")}>
          <h1 className="text-xl font-bold text-white leading-tight">Finanzas AGV</h1>
          <p className="text-purple-200 dark:text-purple-400 text-[10px] uppercase tracking-tighter">Gestión Inteligente</p>
        </div>
      </div>
      
      <nav className="flex-1 px-4 space-y-2">
        <SidebarLink
          href="/collections"
          icon={<Wallet size={22} />}
          label="Cobranzas"
          isExpanded={isExpanded}
        />
        <SidebarLink 
          href="/letters" 
          icon={<Mail size={22} />} 
          label="Letras" 
          isExpanded={isExpanded} 
        />
      </nav>
      
      <div className="p-4 space-y-2 border-t border-purple-400/30 dark:border-slate-700">
        <button
          onClick={handleLogout}
          className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/10 dark:hover:bg-slate-800 transition-all duration-200 w-full group/logout relative"
        >
          <div className="min-w-[24px] flex justify-center text-purple-200 dark:text-purple-400">
            <LogOut size={20} />
          </div>
          <span className={cn(
            "transition-all duration-300 whitespace-nowrap font-medium text-sm",
            isExpanded ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4 pointer-events-none"
          )}>
            Cerrar sesión
          </span>
          {!isExpanded && (
            <div className="absolute left-full ml-6 px-3 py-2 bg-slate-800 dark:bg-slate-700 text-white text-xs rounded-md opacity-0 group-hover/logout:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-[60] shadow-xl">
              Cerrar sesión
            </div>
          )}
        </button>
        <button 
          onClick={toggleTheme}
          className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/10 dark:hover:bg-slate-800 transition-all duration-200 w-full group/theme relative"
        >
          <div className="min-w-[24px] flex justify-center text-purple-200 dark:text-purple-400">
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </div>
          <span className={cn(
            "transition-all duration-300 whitespace-nowrap font-medium text-sm",
            isExpanded ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4 pointer-events-none"
          )}>
            {theme === 'light' ? 'Modo Oscuro' : 'Modo Claro'}
          </span>
          {!isExpanded && (
            <div className="absolute left-full ml-6 px-3 py-2 bg-slate-800 dark:bg-slate-700 text-white text-xs rounded-md opacity-0 group-hover/theme:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-[60] shadow-xl">
              {theme === 'light' ? 'Cambiar a Oscuro' : 'Cambiar a Claro'}
            </div>
          )}
        </button>

        <div className={cn("px-2 transition-opacity duration-300 flex flex-col", isExpanded ? "opacity-100" : "opacity-0")}>
          <p className="text-purple-300 dark:text-purple-400 text-[9px] uppercase tracking-widest font-black">Versión 2.1.0</p>
          <p className="text-white/30 dark:text-slate-500 text-[9px]">Optimizado para Odoo v17</p>
        </div>
      </div>
    </aside>
  )
}

function SidebarLink({ href, icon, label, isExpanded }: { href: string, icon: React.ReactNode, label: string, isExpanded: boolean }) {
  return (
    <Link 
      href={href} 
      className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/10 dark:hover:bg-slate-800 transition-all duration-200 group/link relative"
    >
      <div className="min-w-[24px] flex justify-center">
        {icon}
      </div>
      <span className={cn(
        "transition-all duration-300 whitespace-nowrap font-medium",
        isExpanded ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4 pointer-events-none"
      )}>
        {label}
      </span>
      
      {!isExpanded && (
        <div className="absolute left-full ml-6 px-3 py-2 bg-slate-800 dark:bg-slate-700 text-white text-xs rounded-md opacity-0 group-hover/link:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-[60] shadow-xl">
          {label}
        </div>
      )}
    </Link>
  )
}
