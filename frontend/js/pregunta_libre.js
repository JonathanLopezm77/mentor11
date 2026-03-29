/**
 * Mentor 11 — Pantalla de pregunta (Modo Libre)
 */

// ── Sonidos precargados ───────────────────────────────────
const SFX_P = {};
[
  ['/static/correcta.mp3',   0.8],
  ['/static/error.mp3',      0.8],
  ['/static/sig_pregun.mp3', 0.7],
  ['/static/back.mp3',       0.7],
].forEach(([src, vol]) => {
  const a = new Audio(src);
  a.preload = 'auto';
  a.volume  = vol;
  SFX_P[src] = a;
});

const playSfxP = (src) => {
  const a = SFX_P[src];
  if (!a) return;
  a.currentTime = 0;
  a.play().catch(() => {});
};

const API_BASE   = 'http://localhost:8000/api/v1';
const token      = localStorage.getItem('access_token');
const sesionId       = sessionStorage.getItem('sesion_id');
const materiaIds     = sessionStorage.getItem('materia_ids');
const totalPreguntas = new URLSearchParams(window.location.search).get('cantidad') ?? 10;

// Redirigir si no hay sesión activa
if (!token || !sesionId) {
  location.href = '/';
}

let preguntas  = [];
let actual     = 0;
let correctas  = 0;
let incorrectas = 0;

// ── Inicializar: cargar todas las preguntas ───────────────
async function init() {
  try {
    const res = await fetch(
      `${API_BASE}/juego/preguntas?materia_ids=${materiaIds}&cantidad=${totalPreguntas}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detalle = err.detail ?? `HTTP ${res.status}`;
      alert(`Error al cargar preguntas: ${detalle}`);
      location.href = 'libre_intro.html';
      return;
    }

    preguntas = await res.json();

    if (!preguntas.length) {
      alert('No hay preguntas disponibles para las materias seleccionadas.');
      location.href = 'libre_temas.html';
      return;
    }

    mostrarPregunta();
  } catch (err) {
    console.error('[Pregunta] Error cargando preguntas:', err);
    alert('Error de conexión con el servidor.');
  }
}

// ── Mostrar la pregunta actual ────────────────────────────
function mostrarPregunta() {
  if (actual >= preguntas.length) {
    finalizarSesion();
    return;
  }

  const p = preguntas[actual];

  // Contador y barra de progreso
  document.getElementById('contador').textContent = `${actual + 1} / ${preguntas.length}`;
  document.getElementById('progresoBarra').style.width =
    `${(actual / preguntas.length) * 100}%`;

  // Enunciado
  document.getElementById('enunciado').textContent = p.enunciado;

  // Opciones
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

  // Ocultar elementos post-respuesta
  document.getElementById('siguienteBtn').hidden = true;
  document.getElementById('explicacion').hidden  = true;
  document.getElementById('explicacion').textContent = '';
}

// ── Enviar respuesta al backend ───────────────────────────
async function responder(opcionId, preguntaId) {
  // Deshabilitar todos los botones mientras espera
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

    // Colorear botones: verde = correcto, rojo = elegida incorrecta
    document.querySelectorAll('.opcion-btn').forEach(btn => {
      const id = Number(btn.dataset.id);
      if (id === data.opcion_correcta_id) {
        btn.classList.add('opcion-btn--correcta');
      } else if (id === opcionId && !data.es_correcta) {
        btn.classList.add('opcion-btn--incorrecta');
      }
    });

    // Contadores
    if (data.es_correcta) correctas++; else incorrectas++;

    // Sonido según resultado
    playSfxP(data.es_correcta ? '/static/correcta.mp3' : '/static/error.mp3');

    // Mostrar explicación si existe
    if (data.explicacion) {
      const exp = document.getElementById('explicacion');
      exp.textContent = `💡 ${data.explicacion}`;
      exp.hidden = false;
    }

    // Botón siguiente
    const sigBtn = document.getElementById('siguienteBtn');
    sigBtn.textContent = actual + 1 < preguntas.length ? 'Siguiente →' : 'Ver resultado';
    sigBtn.hidden = false;

  } catch (err) {
    console.error('[Pregunta] Error al responder:', err);
    document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = false));
  }
}

// ── Finalizar sesión e ir a pantalla de resultados ───────
async function finalizarSesion() {
  // Calcular puntos ganados antes de finalizar (misma fórmula que el backend)
  const puntosGanados = correctas * 10;

  try {
    await fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (_) {}

  sessionStorage.setItem('resultado_libre', JSON.stringify({
    total:       correctas + incorrectas,
    correctas,
    incorrectas,
    puntosGanados,
  }));
  sessionStorage.removeItem('sesion_id');
  sessionStorage.removeItem('materia_ids');

  const sfx = new Audio('/static/arcade_stat.mp3');
  sfx.volume = 0.6;
  sfx.play().catch(() => {});
  setTimeout(() => location.href = 'resultado_libre.html', 400);
}

// ── Botón "Siguiente" ─────────────────────────────────────
document.getElementById('siguienteBtn').addEventListener('click', () => {
  playSfxP('/static/sig_pregun.mp3');
  actual++;
  mostrarPregunta();
});

init();
