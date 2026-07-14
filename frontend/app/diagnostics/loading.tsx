export default function Loading() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-gray-100 mx-auto"></div>
        <p className="mt-4 text-sm text-muted-foreground">Ejecutando diagnóstico...</p>
      </div>
    </div>
  )
}
