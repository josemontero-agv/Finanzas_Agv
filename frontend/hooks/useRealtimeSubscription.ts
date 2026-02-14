import { useEffect } from "react"
import { useQueryClient, QueryKey } from "@tanstack/react-query"
import { supabase } from "@/lib/supabase"

export function useRealtimeSubscription(table: string, queryKey: QueryKey) {
  const queryClient = useQueryClient()

  useEffect(() => {
    const channel = supabase
      .channel(`${table}_changes`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table },
        (payload) => {
          console.log("Cambio detectado en", table, ":", payload)
          // Invalidar query para refetch automático
          queryClient.invalidateQueries({ queryKey })
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [table, queryKey, queryClient])
}
