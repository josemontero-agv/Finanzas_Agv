"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Search, X } from "lucide-react"

interface FilterBarProps {
  onFilterChange: (filters: Record<string, string>) => void
  showSupplier?: boolean
  showCustomer?: boolean
  showDateRange?: boolean
  showPaymentState?: boolean
}

export function FilterBar({
  onFilterChange,
  showSupplier = false,
  showCustomer = false,
  showDateRange = true,
  showPaymentState = false,
}: FilterBarProps) {
  const [filters, setFilters] = useState({
    date_from: "",
    date_to: "",
    supplier: "",
    customer: "",
    payment_state: "",
  })

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
  }

  const applyFilters = () => {
    const activeFilters = Object.entries(filters)
      .filter(([_, value]) => value !== "")
      .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {})
    
    onFilterChange(activeFilters)
  }

  const clearFilters = () => {
    const emptyFilters = {
      date_from: "",
      date_to: "",
      supplier: "",
      customer: "",
      payment_state: "",
    }
    setFilters(emptyFilters)
    onFilterChange({})
  }

  return (
    <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-4 transition-colors duration-300">
      <h3 className="font-semibold text-sm text-muted-foreground">Filtros</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {showDateRange && (
          <>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Fecha Desde
              </label>
              <input
                type="date"
                className="w-full mt-1 px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-md text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 transition-colors duration-300"
                value={filters.date_from}
                onChange={(e) => handleFilterChange("date_from", e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Fecha Hasta
              </label>
              <input
                type="date"
                className="w-full mt-1 px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-md text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 transition-colors duration-300"
                value={filters.date_to}
                onChange={(e) => handleFilterChange("date_to", e.target.value)}
              />
            </div>
          </>
        )}
        
        {showSupplier && (
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Proveedor
            </label>
            <input
              type="text"
              placeholder="Buscar proveedor..."
              className="w-full mt-1 px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-md text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-colors duration-300"
              value={filters.supplier}
              onChange={(e) => handleFilterChange("supplier", e.target.value)}
            />
          </div>
        )}
        
        {showCustomer && (
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Cliente
            </label>
            <input
              type="text"
              placeholder="Buscar cliente..."
              className="w-full mt-1 px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-md text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 transition-colors duration-300"
              value={filters.customer}
              onChange={(e) => handleFilterChange("customer", e.target.value)}
            />
          </div>
        )}
        
        {showPaymentState && (
          <div>
            <label className="text-xs font-medium text-muted-foreground">
              Estado de Pago
            </label>
            <select
              className="w-full mt-1 px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-md text-sm bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 transition-colors duration-300"
              value={filters.payment_state}
              onChange={(e) => handleFilterChange("payment_state", e.target.value)}
            >
              <option value="">Todos</option>
              <option value="not_paid">No Pagado</option>
              <option value="paid">Pagado</option>
              <option value="partial">Parcial</option>
              <option value="in_payment">En Proceso</option>
            </select>
          </div>
        )}
      </div>
      
      <div className="flex gap-2">
        <Button onClick={applyFilters} size="sm">
          <Search className="h-4 w-4 mr-2" />
          Aplicar Filtros
        </Button>
        <Button onClick={clearFilters} variant="outline" size="sm">
          <X className="h-4 w-4 mr-2" />
          Limpiar
        </Button>
      </div>
    </div>
  )
}
