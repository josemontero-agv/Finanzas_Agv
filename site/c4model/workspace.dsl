workspace "Finanzas AGV" "Sistema de gestión financiera y cobranzas." {

    model {
        user = person "Usuario Financiero" "Personal de finanzas, cobranzas y tesorería."
        admin = person "Administrador" "Administrador del sistema y TI."

        enterprise "Agrovet Market" {
            financeSystem = softwareSystem "Sistema Finanzas AGV" "Permite la gestión de cobranzas, tesorería, detracciones y reportes." {
                description "Sistema central de finanzas que integra datos de ERP y facilita la toma de decisiones."
            }

            erp = softwareSystem "ERP Odoo" "Sistema ERP central de la empresa." "External System"
            emailSystem = softwareSystem "Servidor de Correo" "Envía notificaciones y estados de cuenta." "External System"
            sunat = softwareSystem "SUNAT / OSE" "Plataforma de facturación electrónica y validación." "External System"
        }

        # Relaciones
        user -> financeSystem "Visualiza reportes, gestiona cobranzas y tesorería"
        admin -> financeSystem "Configura usuarios y parámetros"
        
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
        }
    }
}

