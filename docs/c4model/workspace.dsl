workspace "Finanzas AGV" "Sistema de gestión financiera y cobranzas." {

    model {
        user = person "Usuario Financiero" "Personal de finanzas, cobranzas y tesorería."
        admin = person "Administrador" "Administrador del sistema y TI."

        enterprise "Agrovet Market" {
            financeSystem = softwareSystem "Sistema Finanzas AGV" "Permite la gestión de cobranzas, tesorería, detracciones y reportes." {
                description "Sistema central de finanzas que integra datos de ERP y facilita la toma de decisiones."

                container webUi "UI Finanzas AGV" "Flask + Jinja" "Dashboards (cobranzas, letras, reportes)."
                container lettersApi "API Letras" "Flask Blueprint /api/v1/letters" "Endpoints JSON para Letras (to-accept, to-recover, in-bank, envío de correos)."
                container emailEngine "Motor de Correos" "Flask + SMTP" "Plantillas HTML y envío de recordatorios."
                container investigationScripts "Scripts Investigación" "Python CLI (XML-RPC)" "investigate_letters_model, trace_document_flow, etc."

                container lettersApi {
                    component lettersRoutes "letters.routes" "Flask Blueprint" "Rutas: /to-accept, /send-acceptance, /to-recover, /in-bank, /summary."
                    component lettersService "LettersService" "Python Service" "Consulta account.move (state=to_accept, l10n_latam_boe_number, bill_form_id) y arma dataset de letras."
                    component odooRepo "OdooRepository" "Python XML-RPC wrapper" "Abstrae execute_kw/search_read/read contra Odoo."
                    component emailService "EmailService" "Python Service" "Envía plantillas letters_bank, letters_recover y recordatorios."
                }
            }

            erp = softwareSystem "ERP Odoo" "Sistema ERP central de la empresa." "External System"
            emailSystem = softwareSystem "Servidor de Correo" "Envía notificaciones y estados de cuenta." "External System"
            sunat = softwareSystem "SUNAT / OSE" "Plataforma de facturación electrónica y validación." "External System"
        }

        # Relaciones (nivel contenedor/componente)
        user -> webUi "Usa dashboards y gestión de letras"
        admin -> webUi "Administra usuarios/parámetros"

        webUi -> lettersApi "HTTP JSON /api/v1/letters"
        lettersRoutes -> lettersService "Orquesta casos de uso"
        lettersService -> odooRepo "search_read/read account.move, account.bill.form"
        odooRepo -> erp "XML-RPC"
        lettersService -> emailService "Prepara destinatarios y payload"
        emailService -> emailSystem "SMTP"

        investigationScripts -> erp "XML-RPC directo (auditoría)"

        financeSystem -> erp "Extrae facturas, pagos y clientes" "API/DB"
        financeSystem -> emailSystem "Envía correos a clientes" "SMTP"
        financeSystem -> sunat "Consulta validez de comprobantes" "API"
    }

    views {
        systemContext financeSystem "Contexto" {
            include *
            autoLayout
            description "Diagrama de Contexto del Sistema Finanzas AGV mostrando sus interacciones con usuarios y sistemas externos."
        }

        container financeSystem "Letras - Contenedores" {
            include webUi
            include lettersApi
            include emailEngine
            include investigationScripts
            include erp
            include emailSystem
            autoLayout lr
            description "Vista C2 enfocada en el módulo de Letras."
        }

        component lettersApi "Letras - Componentes API" {
            include lettersRoutes
            include lettersService
            include odooRepo
            include emailService
            autoLayout lr
            description "Vista C3 de los componentes clave para letras."
        }

        dynamic "FlujoLetrasToAccept" {
            title "Flujo: Letras por Aceptar y Envío de Correos"
            description "Secuencia UI -> API -> Odoo -> Correo (estado to_accept)."
            autoLayout lr
            user -> webUi "Abre Gestión de Letras"
            webUi -> lettersRoutes "GET /api/v1/letters/to-accept"
            lettersRoutes -> lettersService "get_letters_to_accept()"
            lettersService -> odooRepo "search_read(account.move, state=to_accept, l10n_latam_boe_number)"
            odooRepo -> erp "XML-RPC"
            lettersService -> emailService "Agrupa y dispara recordatorios"
            emailService -> emailSystem "SMTP / Plantillas HTML"
            lettersRoutes -> webUi "JSON con letras (status_calc, bill_form_id, etc.)"
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "External System" {
                background #999999
                color #ffffff
            }
            element "Container" {
                background #714B67
                color #ffffff
            }
            element "Component" {
                background #b08497
                color #ffffff
            }
            relationship {
                color #444444
            }
        }
    }
}

