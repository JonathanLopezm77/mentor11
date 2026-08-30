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

  window.actualizarTextoModal = function (titulo, contenido) {
    const btn = document.getElementById('verTextoBtn');
    if (!btn) return;
    if (contenido) {
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
