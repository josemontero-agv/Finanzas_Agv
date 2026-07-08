// Feature flags controlados por variables de entorno NEXT_PUBLIC_*.
// Permiten ocultar módulos en producción sin eliminar su código.
// Por defecto deshabilitado (defensa en profundidad / ISO 27001 A.8.9).

export function isLettersModuleEnabled(): boolean {
  return process.env.NEXT_PUBLIC_ENABLE_LETTERS?.trim().toLowerCase() === "true"
}

/** Lanza si el módulo está apagado; evita llamadas accidentales al backend. */
export function assertLettersModuleEnabled(): void {
  if (!isLettersModuleEnabled()) {
    throw new Error("El módulo de Letras no está habilitado")
  }
}
