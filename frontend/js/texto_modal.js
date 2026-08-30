/**
 * texto_modal.js — Modal para ver el texto de contexto de una pregunta.
 * Incluir en todas las páginas de preguntas antes del script principal.
 */
(function () {
  function init() {
    const overlay = document.getElementById('textoModalOverlay');
    const cerrar  = document.getElementById('textoModalCerrar');
    const btn     = document.getElementById('verTextoBtn');
    if (!overlay || !btn) return;

    btn.addEventListener('click', () => { overlay.hidden = false; });
    cerrar.addEventListener('click', () => { overlay.hidden = true; });
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.hidden = true; });
  }

  window.formatearEnunciado = function (texto) {
    if (!texto) return '';
    const seguro = texto
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    return seguro.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  };

  window.actualizarTextoModal = function (titulo, contenido) {
    const btn = document.getElementById('verTextoBtn');
    if (!btn) return;
    // Un texto vacío o de solo espacios no debe mostrar el botón — si no,
    // se abre un modal en blanco (ver captura: preguntas sin texto real
    // asociado, como las de gráficas, quedaban con el botón visible).
    const hayContenido = contenido && contenido.trim().length > 0;
    if (hayContenido) {
      btn.hidden = false;
      document.getElementById('textoModalTitulo').textContent  = titulo || 'Texto de referencia';
      document.getElementById('textoModalContenido').textContent = contenido;
    } else {
      btn.hidden = true;
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
