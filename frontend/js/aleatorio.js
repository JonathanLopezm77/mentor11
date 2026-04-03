/**
 * Mentor 11 — Modo Aleatorio
 * Preguntas infinitas de todas las materias, sin vidas.
 * El usuario termina cuando quiera.
 */

const API_BASE = '/api/v1';
const token = localStorage.getItem('access_token');

if (!token) location.href = '/';

// ── Sonidos ───────────────────────────────────────────────
const SFX = {};
[
  ['/static/correcta.mp3', 0.8],
  ['/static/error.mp3', 0.8],
  ['/static/back.mp3', 0.7],
  ['/static/bop.mp3', 0.8],
  ['/static/bloop.mp3', 0.7],
  ['/static/sig_pregun.mp3', 0.7],
  ['/static/arcade_stat.mp3', 0.6],
].forEach(([src, vol]) => {
  const a = new Audio(src);
  a.preload = 'auto';
  a.volume = vol;
  SFX[src] = a;
});

const playSfx = (src) => {
  const a = SFX[src]?.cloneNode();
  if (!a) return;
  a.volume = SFX[src].volume;
  a.play().catch(() => { });
};

// ── Estado ────────────────────────────────────────────────
let sesionId = null;
let materiaIds = [];
let preguntas = [];
let actual = 0;
let correctas = 0;
let incorrectas = 0;
let vistasIds = new Set();
let cargandoMas = false;
let respondida = false;

// ── Init ──────────────────────────────────────────────────
async function init() {
  try {
    // 1. Obtener todas las materias
    const matRes = await fetch(`${API_BASE}/juego/materias`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!matRes.ok) throw new Error('No se pudieron cargar las materias');
    const materias = await matRes.json();
    materiaIds = materias.map(m => m.id);

    // 2. Crear sesión
    const sesRes = await fetch(`${API_BASE}/juego/sesiones`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        modo_juego: 'aleatorio',
        materia_ids: materiaIds,
        total_preguntas: 999,
      }),
    });
    if (!sesRes.ok) throw new Error('No se pudo crear la sesión');
    const sesData = await sesRes.json();
    sesionId = sesData.sesion_id;

    // 3. Cargar primer lote y arrancar
    await cargarMasPreguntas();
    mostrarPregunta();
  } catch (err) {
    console.error('[Aleatorio] Error init:', err);
    document.getElementById('enunciado').textContent =
      'Error de conexión. Recarga la página.';
  }
}

// ── Cargar más preguntas (sin repetir) ────────────────────
async function cargarMasPreguntas() {
  if (cargandoMas) return;
  cargandoMas = true;
  try {
    const excluir = [...vistasIds].slice(-80).join(',');
    const url = `${API_BASE}/juego/preguntas`
      + `?materia_ids=${materiaIds.join(',')}&cantidad=15`
      + (excluir ? `&excluir_ids=${excluir}` : '');

    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) { cargandoMas = false; return; }

    const nuevas = await res.json();
    for (const p of nuevas) {
      if (!vistasIds.has(p.id)) {
        preguntas.push(p);
        vistasIds.add(p.id);
      }
    }
  } catch (_) { }
  cargandoMas = false;
}

// ── Actualizar marcador en header ─────────────────────────
function actualizarScore() {
  document.getElementById('scoreOk').textContent = `✓ ${correctas}`;
  document.getElementById('scoreFail').textContent = `✗ ${incorrectas}`;
  const total = correctas + incorrectas;
  document.getElementById('progresoBarra').style.width =
    total > 0 ? `${(correctas / total) * 100}%` : '0%';
}

// ── Mostrar pregunta ──────────────────────────────────────
function mostrarPregunta() {
  respondida = false;

  // Prefetch cuando quedan pocas
  if (preguntas.length - actual <= 4) cargarMasPreguntas();

  // Esperar si aún no llegó el lote
  if (actual >= preguntas.length) {
    document.getElementById('enunciado').textContent = 'Cargando siguiente pregunta...';
    setTimeout(mostrarPregunta, 500);
    return;
  }

  const p = preguntas[actual];
  document.getElementById('enunciado').textContent = p.enunciado;

  const grid = document.getElementById('opcionesGrid');
  grid.innerHTML = '';
  p.opciones.forEach(op => {
    const btn = document.createElement('button');
    btn.className = 'opcion-btn';
    btn.dataset.id = op.id;
    btn.innerHTML = `
      <span class="opcion-letra">${op.letra}</span>
      <span class="opcion-texto">${op.texto}</span>
    `;
    btn.addEventListener('click', () => responder(op.id, p.id));
    grid.appendChild(btn);
  });

  document.getElementById('siguienteBtn').hidden = true;
  document.getElementById('explicacion').hidden = true;
  document.getElementById('explicacion').textContent = '';
}

// ── Enviar respuesta ──────────────────────────────────────
async function responder(opcionId, preguntaId) {
  if (respondida) return;
  respondida = true;
  document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = true));

  try {
    const res = await fetch(`${API_BASE}/juego/sesiones/${sesionId}/responder`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ pregunta_id: preguntaId, opcion_id: opcionId }),
    });

    const data = await res.json();

    // Colorear botones
    document.querySelectorAll('.opcion-btn').forEach(btn => {
      const id = Number(btn.dataset.id);
      if (id === data.opcion_correcta_id) btn.classList.add('opcion-btn--correcta');
      else if (id === opcionId && !data.es_correcta) btn.classList.add('opcion-btn--incorrecta');
    });

    if (data.es_correcta) {
      correctas++;
      playSfx('/static/correcta.mp3');
      actualizarScore();
      // Avanza solo después de 900ms
      setTimeout(() => { actual++; mostrarPregunta(); }, 900);
    } else {
      incorrectas++;
      playSfx('/static/error.mp3');
      actualizarScore();
      if (data.explicacion) {
        const exp = document.getElementById('explicacion');
        exp.textContent = `💡 ${data.explicacion}`;
        exp.hidden = false;
      }
      document.getElementById('siguienteBtn').hidden = false;
    }

  } catch (err) {
    console.error('[Aleatorio] Error al responder:', err);
    document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = false));
    respondida = false;
  }
}

// ── Finalizar sesión y navegar a resultados ───────────────
async function finalizarSesion() {
  // Deshabilitar botones para evitar doble clic
  document.getElementById('terminarBtn').disabled = true;
  document.getElementById('siguienteBtn').disabled = true;

  try {
    await fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (_) { }

  const puntosAntes = JSON.parse(localStorage.getItem('usuario') ?? '{}')?.puntos_totales ?? 0;

  sessionStorage.setItem('resultado_aleatorio', JSON.stringify({
    total: correctas + incorrectas,
    correctas,
    incorrectas,
    puntosAntes,
  }));

  playSfx('/static/arcade_stat.mp3');
  setTimeout(() => location.href = 'resultado_aleatorio.html', 400);
}

// ── Botón Siguiente ───────────────────────────────────────
document.getElementById('siguienteBtn').addEventListener('click', () => {
  playSfx('/static/sig_pregun.mp3');
  actual++;
  mostrarPregunta();
});

// ── Botón Terminar (footer) ───────────────────────────────
document.getElementById('terminarBtn').addEventListener('click', () => {
  playSfx('/static/bop.mp3');
  finalizarSesion();
});

// ── Botón Volver (header) — también termina ───────────────
document.getElementById('aleatBackBtn').addEventListener('click', () => {
  playSfx('/static/back.mp3');
  finalizarSesion();
});

init();
