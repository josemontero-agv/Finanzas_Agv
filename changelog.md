# Changelog - Finanzas AGV

Todas las modificaciones notables a este proyecto serán documentadas en este archivo.

## [Unreleased] - 2026-06-25

### Herramientas / DevOps
- **Script `sync-wiki.ps1`**: Nuevo script PowerShell para sincronizar documentación del repositorio principal hacia la GitHub Wiki (`Finanzas_Agv.wiki`). Detecta archivos con fecha dinámica (wildcards), verifica cambios antes de commitear, incluye modo `-DryRun`, `-NoPush`, y actualiza automáticamente `Home.md` con la fecha del último sync. Los documentos de auditoría quedan mapeados como páginas numeradas 20-25 en la wiki.

## [Unreleased] - 2026-06-22

### Rendimiento
- **Migración XML-RPC → JSON-RPC (`app/core/odoo.py`)**: Se reemplazó `xmlrpc.client` por `requests.Session` con JSON-RPC. Las sesiones HTTP/TLS se reutilizan (caché por credenciales), reduciendo la latencia por llamada en ~15-25%.
- **Paralelismo en consultas a Odoo (`call_parallel`)**: Nuevo método que ejecuta múltiples llamadas independientes a la vez usando `ThreadPoolExecutor`. Permite que los reportes de cobranzas (que realizan 12-18 llamadas secuenciales a modelos distintos) puedan aprovechar concurrencia real, con una ganancia estimada de 50-70% en tiempo total de respuesta.
- **Soporte nativo para API Keys de Odoo**: La autenticación JSON-RPC (`/web/session/authenticate`) es compatible con API Keys, lo que permite operar con usuarios que tienen 2FA/Google Authenticator habilitado. Simplemente reemplazar `ODOO_PASSWORD` en `.env` con la API Key generada desde el perfil en Odoo.

## [Unreleased] - 2026-06-08

### Agregado
- **Filtro de Corte Histórico sin Límites**: Se eliminó la restricción hardcodeada de fecha origen del 1 de enero de 2026. Ahora el corte histórico puede consultar retroactivamente deudas originadas en el **2025 y años anteriores**, ofreciendo total flexibilidad según los rangos de fecha ingresados.
- **Exclusión de la Cuenta 1239001**: Omitida permanentemente del universo de cobranza activa al representar únicamente saldos iniciales contables.
- **Buscador Multicampo**: Nueva barra de búsqueda inteligente en tiempo real que permite filtrar simultáneamente por **Número de Factura**, **Número de Pedido** y **Número de Letra (BOE)**.

### Mejorado
- **Lógica de Agrupación y Colapso Contable**:
  - **Cuenta 1212* (Facturas/Boletas)**: Ahora las cuotas parciales y vencimientos divididos se consolidan en una sola línea unificada por factura (haciendo sumatoria de Debe, Haber, Saldo y recalculando fechas de vencimiento efectivas y días vencidos), evitando filas duplicadas por cada cuota.
  - **Cuenta 123* (Letras)**: Se mantiene el desglose individual e independiente por letra/título de forma nativa para respetar el control de cobranza de letras.
### Revertido
- **Exclusión Inteligente de Pagos y Excepción de Anticipos (Cuenta 122*)**: Se revirtió por completo la lógica de exclusión de asientos de pago (prefijos `PAPANT`, `BCP`, `IBK`, `PTRP`, `SCTK`, `PSCT`, `BBVA`, `DAP`) y la excepción de la cuenta `122*` a petición del usuario, permitiendo nuevamente que estos registros fluyan sin transformaciones para un análisis más exhaustivo.
- **Sincronización Exacta de KPIs (Débito, Haber, Saldo)**: Se solucionó el desfase donde las tarjetas de KPI calculaban totales basándose únicamente en los 500 registros del preview en pantalla, mientras el card de registros mostraba el total de base de datos. Ahora los KPIs se calculan sobre el **100% de la data filtrada real** antes del truncamiento de vista de la tabla.

## [Unreleased] - 2026-02-03

### Corregido
- **Backend (Letters)**: Se corrigió un error 404 al enviar correos causado por un mismatch de tipos (Int vs Str) al filtrar IDs de letras.
- **Rendimiento**: Optimización del servicio de letras para filtrar por IDs directamente en la consulta a Odoo, evitando la carga innecesaria de cientos de registros.
- **Estabilidad**: Se incrementó el timeout de Axios en el frontend a 120s para soportar procesos largos de envío masivo sin desconexiones de red.

### Mejorado
- **Backend (Letras)**: Se añadió normalización de estado en el servicio para que cualquier valor legacy `POR RECUPERAR` se transforme a `VENCIDO` antes de responder a la API.
- **Estados (Normalización)**: Se retiró `POR RECUPERAR` de la interfaz de filtros y visualización; ahora se normaliza y muestra como `VENCIDO` en toda la pantalla de letras.
- **Estados (Letras)**: Se aplicó semaforización visual general de estados en `LettersPage`: `POR VENCER` ahora usa color amarillo y `VENCIDO` usa rojo de alerta (incluye tabla principal y previsualización).
- **Filtros**: Se amplió el filtro rápido por estado para incluir `POR VENCER` y `VENCIDO`, además de los estados ya existentes.
- **Diseño de Correos**: Migración del formato de lista simple a un template HTML profesional (`letters_acceptance.html`) con logo corporativo y estilos modernos.
- **Visualización**: Se aumentó el ancho máximo de la previsualización del correo y de la plantilla real para evitar cortes en la información financiera.
- **Extracción de Datos**: Mejora en la obtención del número de factura, navegando desde la letra hasta la factura original a través de la planilla de letras (`bill_form_id`).
- **Mensajería**: Actualización de los textos en el cuerpo del correo y la firma para un lenguaje más directo y corporativo ("Adjunto el detalle...", "Confirmar fecha de recojo").
- **Filtros**: Implementación de un filtro rápido por estado (VIGENTE / POR RECUPERAR) en la tabla principal de letras.
- **UX (Interfaz de Usuario)**: 
  - Reemplazo completo de las alertas y confirmaciones nativas del navegador (`alert`, `confirm`) por modales personalizados.
  - **Minimalismo**: Rediseño de modales para ocupar menos espacio en pantalla, con layouts compactos, tipografía refinada y micro-interacciones suaves.
  - **Modal de Confirmación**: Diseño con resumen de letras a enviar y advertencia de modo desarrollo.
  - **Modal de Éxito**: Iconos discretos, contadores precisos y cierre rápido.
  - **Modal de Error**: Interfaz compacta para reportar problemas de forma clara sin saturar la pantalla.
- **Estandarización**: Cambio de símbolo de moneda de `PEN` a `S/.` y adición de fecha dinámica en el asunto de los correos.

### Activos
- **Logo**: Se integró el logo de Agrovet Market en los correos mediante adjuntos CID (inline) para mayor compatibilidad.

### Configuración
- **Pruebas**: Se actualizó la dirección de correo de destino para el modo desarrollo a `josemontero2415@gmail.com`.
- **Pruebas**: Se actualizó nuevamente el destinatario de correos en modo desarrollo a `creditosycobranzas@agrovetmarket.com` (UI y fallbacks backend).

### Prevención de Errores
- **Detección de Duplicados**: Se implementó una lógica de historial de sesión que marca las letras ya enviadas con un badge verde y muestra una alerta roja si se intenta re-enviar una letra en la misma sesión, evitando envíos duplicados por error de filtrado.

### Mejorado (2026-02-20)
- **Exportación Excel (Cobranzas)**: Las columnas de fecha ahora se exportan como tipo fecha real de Excel (no texto), con formato `DD/MM/YYYY`, permitiendo ordenar y filtrar cronológicamente de forma correcta.
- **Web Cobranzas (Fechas)**: Se robusteció el formateo en frontend para soportar `YYYY-MM-DD`, `YYYY-MM-DD HH:mm:ss` y `YYYY-MM-DDTHH:mm:ss`.
- **Fecha de Corte (Mini feature)**: Se reforzó el cálculo histórico para que mora/antigüedad se evalúen contra la fecha de corte y el saldo al corte use la lógica `saldo_actual + pagos_despues_del_corte`, mejorando casos de pagos en meses posteriores.
- **Conciliados al Corte**: Se ajustó el filtro para excluir conciliados usando saldo histórico al corte (`<= 0`) cuando `include_reconciled` está desactivado, evitando exclusiones incorrectas por fecha máxima de conciliación.
- **Cuentas Contables (Cobranzas)**: Se reemplazó el dominio rígido por un filtro dinámico por prefijos de cuenta (`account_id.code`) en base al campo `account_codes`, eliminando exclusiones hardcodeadas que quitaban cuentas válidas (como `123`).
- **Corte Histórico (Dominio Base)**: En consultas con fecha de corte se dejó de filtrar por `amount_residual != 0` para no perder documentos ya cancelados hoy pero pendientes al corte.
- **UX Filtros Web**: El campo `Códigos de Cuenta` ahora inicia vacío y muestra el placeholder `Ingresa su cuenta contable`.

### Seguridad (2026-02-26)
- **Cobranzas protegido por sesión**: Todos los endpoints de Collections y la exportación Excel de cobranzas ahora exigen `@require_login`; sin sesión se devuelve 401.
- **Frontend Cobranzas**: La página `/collections` valida sesión al cargar (getUserInfo) y redirige a `/login` si no hay sesión; ya no es posible ver datos entrando por URL directa sin autenticación.
- **Cerrar sesión en toda la app**: El botón "Cerrar sesión" se movió al Sidebar (compartido por Letras y Cobranzas), de modo que está disponible en todos los módulos.
- **Checklist de seguridad**: Se añadió `docs/CHECKLIST_SEGURIDAD.md` como estándar de revisión (autenticación, URLs, sesión, secretos, API) para despliegue y auditorías.

### Pendiente (2026-02-20)
- **Cuadre de Data Cobranzas**: Aún falta cuadrar al 100% la data contra ERP; al consultar cuenta 12 se están incluyendo letras y el resultado no coincide totalmente con el esperado operativo.
- **Paginación Cobranzas**: Se requiere optimizar/mejorar la paginación del módulo para evitar sobrecarga de registros y facilitar validaciones de cuadre por bloques.