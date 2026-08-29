/**
 * Mentor 11 — Pantalla de pregunta (Modo Libre)
 */

const SFX_P = {};
[
  ['/static/correcta.mp3', 0.8],
  ['/static/error.mp3', 0.8],
  ['/static/sig_pregun.mp3', 0.7],
  ['/static/back.mp3', 0.7],
].forEach(([src, vol]) => {
  const a = new Audio(src);
  a.preload = 'auto';
  a.volume = vol;
  SFX_P[src] = a;
});

const playSfxP = (src) => {
  const a = SFX_P[src];
  if (!a) return;
  a.currentTime = 0;
  a.play().catch(() => { });
};

const API_BASE = '/api/v1';
const token = localStorage.getItem('access_token');
const sesionId = sessionStorage.getItem('sesion_id');
const materiaIds = sessionStorage.getItem('materia_ids');
const totalPreguntas = new URLSearchParams(window.location.search).get('cantidad') ?? 10;

if (!token || !sesionId) location.href = '/';

let preguntas = [];
let actual = 0;
let correctas = 0;
let incorrectas = 0;

async function init() {
  try {
    const res = await fetch(
      `${API_BASE}/juego/preguntas?materia_ids=${materiaIds}&cantidad=${totalPreguntas}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Error al cargar preguntas: ${err.detail ?? `HTTP ${res.status}`}`);
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

function mostrarPregunta() {
  if (actual >= preguntas.length) {
    finalizarSesion();
    return;
  }

  const p = preguntas[actual];

  document.getElementById('contador').textContent = `${actual + 1} / ${preguntas.length}`;
  document.getElementById('progresoBarra').style.width = `${(actual / preguntas.length) * 100}%`;
  document.getElementById('enunciado').textContent = p.enunciado;

  // Imagen de la pregunta
  const imgPregunta = document.getElementById('preguntaImagen');
  if (imgPregunta) {
    if (p.imagen_url) {
      imgPregunta.src = p.imagen_url;
      imgPregunta.style.display = 'block';
    } else {
      imgPregunta.src = '';
      imgPregunta.style.display = 'none';
    }
  }

  // Opciones
  const grid = document.getElementById('opcionesGrid');
  grid.innerHTML = '';

  p.opciones.forEach(op => {
    const btn = document.createElement('button');
    btn.className = 'opcion-btn';
    btn.dataset.id = op.id;

    if (op.imagen_url) {
      // Opción con imagen: la imagen va en un div que NO tiene overflow:hidden
      // El color de fondo se aplica al botón directamente (sin ::before)
      // así la imagen nunca queda tapada
      btn.dataset.tieneImagen = '1';
      btn.innerHTML = `
        <span class="opcion-letra">${op.letra}</span>
        <img src="${op.imagen_url}" alt="Opción ${op.letra}"
          style="max-width:100%;max-height:120px;object-fit:contain;border-radius:8px;margin-top:6px;position:relative;z-index:2;" />
      `;
    } else {
      btn.innerHTML = `
        <span class="opcion-letra">${op.letra}</span>
        <span class="opcion-texto">${op.texto}</span>
      `;
    }

    btn.addEventListener('click', () => responder(op.id, p.id));
    grid.appendChild(btn);
  });

  document.getElementById('siguienteBtn').hidden = true;
  document.getElementById('explicacion').hidden = true;
  document.getElementById('explicacion').textContent = '';
}

async function responder(opcionId, preguntaId) {
  document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = true));

  try {
    const res = await fetch(`${API_BASE}/juego/sesiones/${sesionId}/responder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ pregunta_id: preguntaId, opcion_id: opcionId, checkpoint: actual }),
    });

    const data = await res.json();

    document.querySelectorAll('.opcion-btn').forEach(btn => {
      const id = Number(btn.dataset.id);
      const tieneImagen = btn.dataset.tieneImagen === '1';

      if (id === data.opcion_correcta_id) {
        if (tieneImagen) {
          // Con imagen: aplicar color de fondo directo sin animación ::before
          btn.style.background = '#D1FAE5';
          btn.style.borderColor = '#059669';
          btn.style.transition = 'background 0.45s ease, border-color 0.45s ease';
          const letra = btn.querySelector('.opcion-letra');
          if (letra) { letra.style.background = '#059669'; letra.style.color = '#fff'; }
        } else {
          btn.classList.add('opcion-btn--correcta');
        }
      } else if (id === opcionId && !data.es_correcta) {
        if (tieneImagen) {
          btn.style.background = '#FEE2E2';
          btn.style.borderColor = '#DC2626';
          btn.style.transition = 'background 0.45s ease, border-color 0.45s ease';
          const letra = btn.querySelector('.opcion-letra');
          if (letra) { letra.style.background = '#DC2626'; letra.style.color = '#fff'; }
        } else {
          btn.classList.add('opcion-btn--incorrecta');
        }
      }
    });

    if (data.es_correcta) correctas++; else incorrectas++;
    playSfxP(data.es_correcta ? '/static/correcta.mp3' : '/static/error.mp3');

    if (data.explicacion) {
      const exp = document.getElementById('explicacion');
      exp.textContent = `💡 ${data.explicacion}`;
      exp.hidden = false;
    }

    const sigBtn = document.getElementById('siguienteBtn');
    sigBtn.textContent = actual + 1 < preguntas.length ? 'Siguiente →' : 'Ver resultado';
    sigBtn.hidden = false;

  } catch (err) {
    console.error('[Pregunta] Error al responder:', err);
    document.querySelectorAll('.opcion-btn').forEach(b => (b.disabled = false));
  }
}

async function finalizarSesion() {
  const puntosGanados = correctas * 10;

  try {
    await fetch(`${API_BASE}/juego/sesiones/${sesionId}/finalizar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch (_) { }

  sessionStorage.setItem('resultado_libre', JSON.stringify({
    total: correctas + incorrectas, correctas, incorrectas, puntosGanados,
  }));
  sessionStorage.removeItem('sesion_id');
  sessionStorage.removeItem('materia_ids');

  const sfx = new Audio('/static/arcade_stat.mp3');
  sfx.volume = 0.6;
  sfx.play().catch(() => { });
  setTimeout(() => location.href = 'resultado_libre.html', 400);
}

document.getElementById('siguienteBtn').addEventListener('click', () => {
  playSfxP('/static/sig_pregun.mp3');
  actual++;
  mostrarPregunta();
});

init();