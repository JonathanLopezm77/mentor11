/**
 * Mentor 11 — Modo Contrarreloj
 * 3 minutos, +10s por acierto, -15s por fallo.
 * Game over cuando el tiempo llega a 0.
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
  ['/static/game_over.mp3', 1.0],
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

// ── Constantes del temporizador ───────────────────────────
const TOTAL_TIME = 180;  // segundos
const BONUS_OK = 10;   // segundos al acertar
const PENALTY_FAIL = 15;   // segundos al fallar
const CIRCUNF = 2 * Math.PI * 20; // ≈ 125.66 (radio=20)

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
let juegoTerminado = false;

let timeLeft = TOTAL_TIME;
let timerInterval = null;

// ── Temporizador circular ─────────────────────────────────
const timerRing = document.getElementById('timerRing');
const timerText = document.getElementById('timerText');

timerRing.style.strokeDasharray = CIRCUNF;
timerRing.style.strokeDashoffset = 0;

function formatTime(s) {
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
}

function actualizarTimer() {
  timerText.textContent = formatTime(timeLeft);

  const pct = Math.max(timeLeft / TOTAL_TIME, 0);
  const offset = CIRCUNF * (1 - pct);
  timerRing.style.strokeDashoffset = offset;

  // Color según tiempo restante
  timerRing.classList.remove('ctr-timer-ring--warning', 'ctr-timer-ring--danger');
  timerText.classList.remove('ctr-timer-text--warning', 'ctr-timer-text--danger');
  if (timeLeft <= 30) {
    timerRing.classList.add('ctr-timer-ring--danger');
    timerText.classList.add('ctr-timer-text--danger');
  } else if (timeLeft <= 60) {
    timerRing.classList.add('ctr-timer-ring--warning');
    timerText.classList.add('ctr-timer-text--warning');
  }
}

function iniciarTimer() {
  timerInterval = setInterval(() => {
    if (juegoTerminado) return;
    timeLeft--;
    actualizarTimer();
    if (timeLeft <= 0) {
      timeLeft = 0;
      clearInterval(timerInterval);
      juegoTerminado = true;
      document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = true));
      setTimeout(mostrarGameOver, 600);
    }
  }, 1000);
}

function ajustarTiempo(delta) {
  timeLeft = Math.max(0, Math.min(TOTAL_TIME + 60, timeLeft + delta));
  actualizarTimer();

  // Flash visual en el ring
  timerRing.classList.add(delta > 0 ? 'ctr-timer-ring--flash-ok' : 'ctr-timer-ring--flash-fail');
  setTimeout(() => {
    timerRing.classList.remove('ctr-timer-ring--flash-ok', 'ctr-timer-ring--flash-fail');
  }, 400);
}

// ── Marcador ──────────────────────────────────────────────
function actualizarScore() {
  document.getElementById('scoreOk').textContent = `✓ ${correctas}`;
  document.getElementById('scoreFail').textContent = `✗ ${incorrectas}`;
  const total = correctas + incorrectas;
  document.getElementById('progresoBarra').style.width =
    total > 0 ? `${(correctas / total) * 100}%` : '0%';
}

// ── Init ──────────────────────────────────────────────────
async function init() {
  try {
    const matRes = await fetch(`${API_BASE}/juego/materias`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!matRes.ok) throw new Error('No se pudieron cargar las materias');
    const materias = await matRes.json();
    materiaIds = materias.map(m => m.id);

    const sesRes = await fetch(`${API_BASE}/juego/sesiones`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        modo_juego: 'contrareloj',
        materia_ids: materiaIds,
        total_preguntas: 999,
      }),
    });
    if (!sesRes.ok) throw new Error('No se pudo crear la sesión');
    const sesData = await sesRes.json();
    sesionId = sesData.sesion_id;

    await cargarMasPreguntas();
    actualizarTimer();
    iniciarTimer();
    mostrarPregunta();
  } catch (err) {
    console.error('[Contrarreloj] Error init:', err);
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

    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
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

// ── Mostrar pregunta ──────────────────────────────────────
function mostrarPregunta() {
  if (juegoTerminado) return;
  respondida = false;

  if (preguntas.length - actual <= 4) cargarMasPreguntas();

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
  if (respondida || juegoTerminado) return;
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

    document.querySelectorAll('.opcion-btn').forEach(btn => {
      const id = Number(btn.dataset.id);
      if (id === data.opcion_correcta_id) btn.classList.add('opcion-btn--correcta');
      else if (id === opcionId && !data.es_correcta) btn.classList.add('opcion-btn--incorrecta');
    });

    if (data.es_correcta) {
      correctas++;
      playSfx('/static/correcta.mp3');
      ajustarTiempo(+BONUS_OK);
      actualizarScore();
      setTimeout(() => { actual++; mostrarPregunta(); }, 900);
    } else {
      incorrectas++;
      playSfx('/static/error.mp3');
      ajustarTiempo(-PENALTY_FAIL);
      actualizarScore();
      if (data.explicacion) {
        const exp = document.getElementById('explicacion');
        exp.textContent = `💡 ${data.explicacion}`;
        exp.hidden = false;
      }
      if (!juegoTerminado) {
        document.getElementById('siguienteBtn').hidden = false;
      }
    }

  } catch (err) {
    console.error('[Contrarreloj] Error al responder:', err);
    document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = false));
    respondida = false;
  }
}

// ── Game Over ─────────────────────────────────────────────
async function mostrarGameOver() {
  clearInterval(timerInterval);
  playSfx('/static/game_over.mp3');

  const puntosAntes = JSON.parse(localStorage.getItem('usuario') ?? '{}')?.puntos_totales ?? 0;

  try {
    await fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (_) { }

  const total = correctas + incorrectas;
  sessionStorage.setItem('resultado_contrareloj', JSON.stringify({
    correctas, incorrectas, total, puntosAntes,
  }));
  location.href = 'resultado_contrareloj.html';
}

// ── Botón Siguiente ───────────────────────────────────────
document.getElementById('siguienteBtn').addEventListener('click', () => {
  if (juegoTerminado) return;
  playSfx('/static/sig_pregun.mp3');
  actual++;
  mostrarPregunta();
});

// ── Botón Volver (header) ─────────────────────────────────
document.getElementById('ctrBackBtn').addEventListener('click', () => {
  clearInterval(timerInterval);
  playSfx('/static/back.mp3');
  const pa = JSON.parse(localStorage.getItem('usuario') ?? '{}')?.puntos_totales ?? 0;
  if (sesionId) {
    fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => { });
  }
  setTimeout(() => location.href = 'dashboard_estudiante.html', 350);
});

// ── Botones Game Over ─────────────────────────────────────
document.getElementById('reiniciarBtn').addEventListener('click', () => {
  playSfx('/static/bop.mp3');
  setTimeout(() => location.reload(), 400);
});

document.getElementById('volverBtn').addEventListener('click', () => {
  playSfx('/static/bloop.mp3');
  setTimeout(() => location.href = 'dashboard_estudiante.html', 400);
});

init();
