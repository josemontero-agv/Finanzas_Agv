"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Letter } from "@/lib/api"

export const columns: ColumnDef<Letter>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <input
        type="checkbox"
        className="h-4 w-4 rounded border-slate-300 text-[#714B67] focus:ring-[#714B67]"
        checked={table.getIsAllPageRowsSelected()}
        onChange={(e) => table.toggleAllPageRowsSelected(!!e.target.checked)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <input
        type="checkbox"
        className="h-4 w-4 rounded border-slate-300 text-[#714B67] focus:ring-[#714B67]"
        checked={row.getIsSelected()}
        onChange={(e) => row.toggleSelected(!!e.target.checked)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "number",
    header: "N° Letra",
  },
  {
    accessorKey: "acceptor_id",
    header: "Cliente",
  },
  {
    accessorKey: "vat",
    header: "RUC",
  },
  {
    accessorKey: "amount",
    header: "Monto",
    cell: ({ row }) => {
      const amount = parseFloat(String(row.getValue("amount")))
      const currency = row.original.currency
      const formatted = new Intl.NumberFormat("es-PE", {
        style: "currency",
        currency: currency || "PEN",
      }).format(amount)
      return <div className="text-right font-medium">{formatted}</div>
    },
  },
  {
    accessorKey: "due_date",
    header: "Vencimiento",
    cell: ({ row }) => {
      const date = row.getValue("due_date")
      if (!date) return "-"
      return new Date(String(date)).toLocaleDateString("es-PE")
    },
  },
  {
    accessorKey: "city",
    header: "Ciudad",
  },
  {
    accessorKey: "status_calc",
    header: "Estado",
    cell: ({ row }) => {
      const status = row.getValue("status_calc") as string
      
      let variant: "default" | "destructive" | "secondary" | "outline" | "warning" = "default"
      if (status === "VENCIDO") {
        variant = "destructive"
      } else if (status === "POR VENCER") {
        variant = "warning"
      }

      return (
        <Badge variant={variant}>
          {status}
        </Badge>
      )
    },
  },
  {
    id: "actions",
    header: "Acciones",
    cell: ({ row }) => {
      return (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            console.log("Enviar email a:", row.original.customer_email)
            // TODO: Implementar lógica de envío
          }}
        >
          Enviar Email
        </Button>
      )
    },
  },
]
