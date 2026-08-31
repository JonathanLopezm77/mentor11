/**
 * reporte_modal.js — Modal compartido para reportar preguntas.
 * Expone window.abrirReporteModal(preguntaId).
 * Debe cargarse después de auth_fetch.js.
 */
(function () {
  const HTML = `
    <div id="reporteOverlay" class="texto-modal-overlay" hidden>
      <div class="texto-modal" style="max-width:420px">
        <div class="texto-modal__header">
          <h3 class="texto-modal__titulo">Reportar pregunta</h3>
          <button class="texto-modal__cerrar" id="reporteCerrar">✕</button>
        </div>
        <div class="texto-modal__body" style="display:flex;flex-direction:column;gap:12px">
          <label style="font-size:.85rem;font-weight:600;color:#374151">Tipo de error</label>
          <select id="reporteTipo" style="padding:10px 12px;border:1.5px solid #d1d5db;border-radius:10px;font-size:.9rem;background:#fff">
            <option value="respuesta_incorrecta">Respuesta incorrecta</option>
            <option value="error_contenido">Error en el contenido</option>
            <option value="imagen_rota">Imagen rota o faltante</option>
            <option value="error_tecnico">Error técnico</option>
            <option value="otro">Otro</option>
          </select>
          <label style="font-size:.85rem;font-weight:600;color:#374151">Descripción <span style="font-weight:400;color:#6b7280">(opcional)</span></label>
          <textarea id="reporteDescripcion" rows="3"
            placeholder="Describe el problema con detalle..."
            style="padding:10px 12px;border:1.5px solid #d1d5db;border-radius:10px;font-size:.9rem;resize:vertical;font-family:inherit"></textarea>
          <button id="reporteEnviar"
            style="padding:12px;background:#ef4444;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:.95rem;cursor:pointer">
            Enviar reporte
          </button>
          <p id="reporteMensaje" style="text-align:center;font-size:.85rem;color:#059669;display:none"></p>
        </div>
      </div>
    </div>`;

  document.body.insertAdjacentHTML('beforeend', HTML);

  let _preguntaId = null;

  const overlay = document.getElementById('reporteOverlay');
  const cerrar = document.getElementById('reporteCerrar');
  const enviar = document.getElementById('reporteEnviar');
  const mensaje = document.getElementById('reporteMensaje');

  cerrar.addEventListener('click', () => { overlay.hidden = true; });
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.hidden = true; });

  enviar.addEventListener('click', async () => {
    const tipo = document.getElementById('reporteTipo').value;
    const descripcion = document.getElementById('reporteDescripcion').value.trim() || null;
    const token = localStorage.getItem('access_token');

    enviar.disabled = true;
    enviar.textContent = 'Enviando...';

    try {
      const res = await fetch('/api/v1/juego/reportar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ pregunta_id: _preguntaId, tipo, descripcion }),
      });
      const data = await res.json();
      mensaje.textContent = res.ok ? '✓ ' + data.mensaje : '✗ ' + (data.detail ?? 'Error al enviar');
      mensaje.style.color = res.ok ? '#059669' : '#dc2626';
      mensaje.style.display = 'block';
      if (res.ok) setTimeout(() => { overlay.hidden = true; }, 1800);
    } catch (_) {
      mensaje.textContent = '✗ Error de conexión';
      mensaje.style.color = '#dc2626';
      mensaje.style.display = 'block';
    } finally {
      enviar.disabled = false;
      enviar.textContent = 'Enviar reporte';
    }
  });

  window.abrirReporteModal = function (preguntaId) {
    _preguntaId = preguntaId;
    document.getElementById('reporteTipo').value = 'respuesta_incorrecta';
    document.getElementById('reporteDescripcion').value = '';
    mensaje.style.display = 'none';
    overlay.hidden = false;
  };
})();
