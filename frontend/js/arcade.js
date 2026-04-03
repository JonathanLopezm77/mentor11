/**
 * Mentor 11 — Modo Arcade
 * Preguntas infinitas de todas las materias, 3 vidas.
 * Game over al perder la 3ra vida.
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
  ['/static/game_over.mp3', 1.0],
  ['/static/bloop.mp3', 0.7],
  ['/static/arcade_reintentar.mp3', 0.8],
  ['/static/back_menu.mp3', 0.8],
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

// ── Música de fondo (muy baja) ────────────────────────────
const bgMusic = new Audio('/static/arcade_musica.mp3');
bgMusic.loop = true;
bgMusic.volume = 0.015;
bgMusic.muted = sessionStorage.getItem('arcade_muted') === '1';
bgMusic.play().catch(() => {
  document.addEventListener('pointerdown', () => bgMusic.play().catch(() => { }), { once: true });
});

// ── Estado ────────────────────────────────────────────────
let sesionId = null;
let materiaIds = [];
let preguntas = [];
let actual = 0;
let vidas = 3;
let puntaje = 0;
let correctas = 0;
let vistasIds = new Set();
let cargandoMas = false;
let juegoTerminado = false;

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

    // 2. Crear sesión arcade
    const sesRes = await fetch(`${API_BASE}/juego/sesiones`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        modo_juego: 'arcade',
        materia_ids: materiaIds,
        total_preguntas: 999,
      }),
    });
    if (!sesRes.ok) throw new Error('No se pudo crear la sesión');
    const sesData = await sesRes.json();
    sesionId = sesData.sesion_id;

    // 3. Cargar avatar del usuario
    cargarAvatarBar();

    // 4. Cargar primer lote
    await cargarMasPreguntas();
    mostrarPregunta();
  } catch (err) {
    console.error('[Arcade] Error init:', err);
    document.getElementById('enunciado').textContent = 'Error de conexión. Recarga la página.';
  }
}

// ── Cargar avatar en la barra ─────────────────────────────
async function cargarAvatarBar() {
  try {
    const res = await fetch(`${API_BASE}/perfil/avatar`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.imagen_src) {
      document.getElementById('arcadeAvatarImg').src = data.imagen_src;
    }
  } catch (_) { }
}

// ── Cargar más preguntas (excluye ya vistas) ──────────────
async function cargarMasPreguntas() {
  if (cargandoMas) return;
  cargandoMas = true;
  try {
    const excluir = [...vistasIds].slice(-60).join(',');
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

// ── Mostrar pregunta ──────────────────────────────────────
function mostrarPregunta() {
  if (juegoTerminado) return;

  // Prefetch cuando quedan pocas
  if (preguntas.length - actual <= 4) {
    cargarMasPreguntas();
  }

  // Aún no llegó el lote, reintentar
  if (actual >= preguntas.length) {
    document.getElementById('enunciado').textContent = 'Cargando siguiente pregunta...';
    setTimeout(mostrarPregunta, 500);
    return;
  }

  const p = preguntas[actual];

  // Barra de progreso infinita: cicla entre 0 y 100 por racha de 10
  document.getElementById('progresoBarra').style.width =
    `${((correctas % 10) / 10) * 100}%`;

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
      puntaje += 10;
      correctas++;
      document.getElementById('arcadeScore').textContent = puntaje;
      playSfx('/static/correcta.mp3');
      // Correcto → avanza solo después de 900ms
      setTimeout(() => { actual++; mostrarPregunta(); }, 900);
    } else {
      playSfx('/static/error.mp3');
      perderVida();
      // Incorrecto → mostrar explicación y botón Siguiente
      if (data.explicacion) {
        const exp = document.getElementById('explicacion');
        exp.textContent = `💡 ${data.explicacion}`;
        exp.hidden = false;
      }
      if (vidas > 0) {
        document.getElementById('siguienteBtn').hidden = false;
      }
    }

  } catch (err) {
    console.error('[Arcade] Error al responder:', err);
    document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = false));
  }
}

// ── Perder una vida ───────────────────────────────────────
function perderVida() {
  vidas--;
  const hearts = document.querySelectorAll('.arcade-heart');
  const idx = 2 - vidas;

  if (hearts[idx]) {
    const rect = hearts[idx].getBoundingClientRect();
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;

    // Clonar el corazón en posición fija
    const fly = document.createElement('span');
    fly.textContent = '❤️';
    fly.style.cssText = [
      `position:fixed`,
      `left:${rect.left + rect.width / 2}px`,
      `top:${rect.top + rect.height / 2}px`,
      `transform:translate(-50%,-50%) scale(1)`,
      `font-size:2rem`,
      `z-index:9999`,
      `pointer-events:none`,
      `transition:none`,
    ].join(';');
    document.body.appendChild(fly);

    // Fase 1: volar al centro
    fly.getBoundingClientRect(); // force reflow
    fly.style.transition = 'left .35s cubic-bezier(.34,1.56,.64,1), top .35s cubic-bezier(.34,1.56,.64,1), font-size .35s';
    fly.style.left = `${cx}px`;
    fly.style.top = `${cy}px`;
    fly.style.fontSize = '3.5rem';

    // Fase 2: partir el corazón en el centro
    setTimeout(() => {
      // Pequeño shake antes de romperse
      fly.style.transition = 'transform .08s';
      fly.style.transform = 'translate(-50%,-50%) scale(1.25) rotate(-10deg)';
      setTimeout(() => {
        fly.style.transform = 'translate(-50%,-50%) scale(1.25) rotate(10deg)';
        setTimeout(() => {
          fly.remove();

          // Crear dos mitades con clip-path
          const makeShard = (side) => {
            const el = document.createElement('span');
            el.textContent = '❤️';
            el.style.cssText = [
              'position:fixed',
              `left:${cx}px`,
              `top:${cy}px`,
              'font-size:3.5rem',
              'transform:translate(-50%,-50%)',
              'z-index:9999',
              'pointer-events:none',
              `clip-path:${side === 'L' ? 'inset(0 50% 0 0)' : 'inset(0 0 0 50%)'}`,
              'transition:none',
            ].join(';');
            document.body.appendChild(el);
            return el;
          };

          const sL = makeShard('L');
          const sR = makeShard('R');
          sL.getBoundingClientRect(); // force reflow

          sL.style.transition = 'left .6s ease-out, top .65s ease-in, opacity .55s, transform .65s';
          sL.style.left = `${cx - 90}px`;
          sL.style.top = `${cy + 210}px`;
          sL.style.opacity = '0';
          sL.style.transform = 'translate(-50%,-50%) rotate(-40deg) scale(0.7)';

          sR.style.transition = 'left .6s ease-out, top .65s ease-in, opacity .55s, transform .65s';
          sR.style.left = `${cx + 90}px`;
          sR.style.top = `${cy + 210}px`;
          sR.style.opacity = '0';
          sR.style.transform = 'translate(-50%,-50%) rotate(40deg) scale(0.7)';

          setTimeout(() => { sL.remove(); sR.remove(); }, 700);
        }, 80);
      }, 80);
    }, 370);

    // Marcar el corazón original como perdido
    setTimeout(() => {
      hearts[idx].classList.add('arcade-heart--lost');
    }, 370);
  }

  if (vidas === 0) {
    juegoTerminado = true;
    setTimeout(mostrarGameOver, 950);
  }
}

// ── Game Over ─────────────────────────────────────────────
async function mostrarGameOver() {
  bgMusic.pause();
  playSfx('/static/game_over.mp3');

  const puntosAntes = JSON.parse(localStorage.getItem('usuario') ?? '{}')?.puntos_totales ?? 0;

  try {
    await fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (_) { }

  sessionStorage.setItem('resultado_arcade', JSON.stringify({
    puntaje, correctas, puntosAntes,
  }));
  location.href = 'resultado_arcade.html';
}

// ── Botón Siguiente ───────────────────────────────────────
document.getElementById('siguienteBtn').addEventListener('click', () => {
  playSfx('/static/bop.mp3');
  actual++;
  mostrarPregunta();
});

// ── Botón Volver ──────────────────────────────────────────
document.getElementById('arcadeBackBtn').addEventListener('click', () => {
  playSfx('/static/back.mp3');
  const pa = JSON.parse(localStorage.getItem('usuario') ?? '{}')?.puntos_totales ?? 0;
  const finalize = sesionId
    ? fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => { })
    : Promise.resolve();

  finalize.finally(() => {
    setTimeout(() => (location.href = 'dashboard_estudiante.html'), 350);
  });
});

// ── Botones Game Over ─────────────────────────────────────
const reiniciarBtn = document.getElementById('reiniciarBtn');
reiniciarBtn.addEventListener('mouseenter', () => playSfx('/static/bloop.mp3'));
reiniciarBtn.addEventListener('click', () => {
  playSfx('/static/arcade_reintentar.mp3');
  setTimeout(() => location.reload(), 400);
});

document.getElementById('volverBtn').addEventListener('click', () => {
  playSfx('/static/back_menu.mp3');
  setTimeout(() => { location.href = 'dashboard_estudiante.html'; }, 400);
});

init();
