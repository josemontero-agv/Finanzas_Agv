"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { TreasuryLine } from "@/lib/api"
import { ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"

export const columns: ColumnDef<TreasuryLine>[] = [
  {
    accessorKey: "invoice_date",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Fecha Factura
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const date = row.getValue("invoice_date")
      if (!date) return "-"
      return new Date(String(date)).toLocaleDateString("es-PE")
    },
  },
  {
    accessorKey: "move_name",
    header: "N° Documento",
  },
  {
    accessorKey: "ref",
    header: "Referencia",
    cell: ({ row }) => {
      const ref = row.getValue("ref")
      return ref || "-"
    },
  },
  {
    accessorKey: "supplier_name",
    header: "Proveedor",
    cell: ({ row }) => {
      return (
        <div className="max-w-[200px] truncate">
          {row.getValue("supplier_name")}
        </div>
      )
    },
  },
  {
    accessorKey: "supplier_vat",
    header: "RUC",
  },
  {
    accessorKey: "currency_id",
    header: "Moneda",
    cell: ({ row }) => {
      const currency = row.getValue("currency_id") as string
      return <span className="font-mono text-xs">{currency || "PEN"}</span>
    },
  },
  {
    accessorKey: "amount_total",
    header: "Monto Total",
    cell: ({ row }) => {
      const amount = parseFloat(String(row.getValue("amount_total") || 0))
      const formatted = new Intl.NumberFormat("es-PE", {
        style: "currency",
        currency: "PEN",
      }).format(amount)
      return <div className="text-right font-medium">{formatted}</div>
    },
  },
  {
    accessorKey: "amount_residual",
    header: "Saldo",
    cell: ({ row }) => {
      const amount = parseFloat(String(row.getValue("amount_residual") || 0))
      const formatted = new Intl.NumberFormat("es-PE", {
        style: "currency",
        currency: "PEN",
      }).format(amount)
      return <div className="text-right font-medium text-red-600">{formatted}</div>
    },
  },
  {
    accessorKey: "invoice_date_due",
    header: "Vencimiento",
    cell: ({ row }) => {
      const date = row.getValue("invoice_date_due")
      if (!date) return "-"
      return new Date(String(date)).toLocaleDateString("es-PE")
    },
  },
  {
    accessorKey: "dias_vencido",
    header: "Días Vencido",
    cell: ({ row }) => {
      const dias = row.getValue("dias_vencido") as number
      return (
        <div
          className={`text-center font-bold ${
            dias > 0 ? "text-red-600" : "text-green-600"
          }`}
        >
          {dias}
        </div>
      )
    },
  },
  {
    accessorKey: "estado_deuda",
    header: "Estado",
    cell: ({ row }) => {
      const estado = row.getValue("estado_deuda") as string
      return (
        <Badge variant={estado === "VIGENTE" ? "default" : "destructive"}>
          {estado}
        </Badge>
      )
    },
  },
  {
    accessorKey: "antiguedad",
    header: "Antigüedad",
    cell: ({ row }) => {
      const antiguedad = row.getValue("antiguedad") as string
      let variant: "default" | "secondary" | "destructive" = "default"
      
      if (antiguedad.includes("Judicial") || antiguedad.includes("Prolongado")) {
        variant = "destructive"
      } else if (antiguedad.includes("Medio")) {
        variant = "secondary"
      }
      
      return <Badge variant={variant}>{antiguedad}</Badge>
    },
  },
  {
    accessorKey: "payment_state",
    header: "Estado Pago",
    cell: ({ row }) => {
      const state = row.getValue("payment_state") as string
      const stateMap: Record<string, string> = {
        not_paid: "No Pagado",
        paid: "Pagado",
        partial: "Parcial",
        in_payment: "En Proceso",
      }
      return <span className="text-xs">{stateMap[state] || state}</span>
    },
  },
]
