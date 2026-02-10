document.addEventListener('DOMContentLoaded', function() {
    const navContainer = document.getElementById('toc');
    if (!navContainer) return;

    // Determinar la ruta base relativa al archivo actual
    const pathDepth = window.location.pathname.split('/').filter(p => p !== '').length;
    // Esto es un poco frágil si no conocemos la estructura exacta de carpetas en el servidor.
    // Una mejor forma es contar cuántas carpetas hay después de "docs"
    
    const href = window.location.href;
    let prefix = '';
    if (href.includes('/adrs/') || href.includes('/arquitectura/') || href.includes('/runbooks/')) {
        prefix = '../';
    }

    const currentFile = window.location.pathname.split('/').pop() || 'index.html';

    const navHTML = `
        <div class="nav-logo">
            <img src="${prefix}assets/logo-agrovet.png" alt="Agrovet Market Logo">
        </div>
        <h2><i class="bi bi-folder2-open"></i> Documentación</h2>
        <ul>
            <li><a href="${prefix}index.html" class="${currentFile === 'index.html' && prefix === '' ? 'active' : ''}"><i class="bi bi-house"></i> Inicio</a></li>
            <li><a href="${prefix}manual_usuario.html" class="${currentFile === 'manual_usuario.html' ? 'active' : ''}"><i class="bi bi-person-workspace"></i> Manual Usuario</a></li>
            <li><a href="${prefix}manual_desarrollador.html" class="${currentFile === 'manual_desarrollador.html' ? 'active' : ''}"><i class="bi bi-code-slash"></i> Manual Dev</a></li>
            <li class="nav-submenu">
                <a href="${prefix}arquitectura.html" class="${currentFile === 'arquitectura.html' ? 'active' : ''}"><i class="bi bi-diagram-3"></i> Arquitectura</a>
                <ul>
                    <li><a href="${prefix}arquitectura/c4model.html" class="${currentFile === 'c4model.html' ? 'active' : ''}">Vista C4</a></li>
                    <li><a href="${prefix}arquitectura/analisis_arquitectonico.html" class="${currentFile === 'analisis_arquitectonico.html' ? 'active' : ''}">Análisis Stack</a></li>
                </ul>
            </li>
            <li><a href="${prefix}adrs/index.html" class="${currentFile === 'index.html' && prefix.includes('adrs') ? 'active' : ''}"><i class="bi bi-diagram-2"></i> Decisiones (ADRs)</a></li>
            <li><a href="${prefix}runbooks/index.html" class="${currentFile === 'index.html' && prefix.includes('runbooks') ? 'active' : ''}"><i class="bi bi-tools"></i> Runbooks</a></li>
            <li><a href="${prefix}guia_diseno.html" class="${currentFile === 'guia_diseno.html' ? 'active' : ''}"><i class="bi bi-palette"></i> Guía de Diseño</a></li>
            <li><a href="${prefix}bitacora.html" class="${currentFile === 'bitacora.html' ? 'active' : ''}"><i class="bi bi-journal-text"></i> Bitácora</a></li>
            <li><a href="${prefix}guia_git_main.html" class="${currentFile === 'guia_git_main.html' ? 'active' : ''}"><i class="bi bi-git"></i> Guía Git</a></li>
        </ul>
    `;

    navContainer.innerHTML = navHTML;

    // Asegurar que los submenús funcionen o se resalten correctamente
    if (href.includes('/arquitectura/')) {
        const arqLink = navContainer.querySelector('a[href*="arquitectura.html"]');
        if (arqLink) arqLink.classList.add('active');
    }
});
