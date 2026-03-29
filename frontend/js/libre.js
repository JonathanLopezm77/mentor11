/**
 * Mentor 11 — Modo Libre
 * Compartido por libre_intro.html y libre_temas.html
 */

const API_BASE = 'http://localhost:8000/api/v1';

const usuario = JSON.parse(localStorage.getItem('usuario') ?? 'null');
if (!usuario) window.location.href = '/';

const getToken = () => localStorage.getItem('access_token');

// ── Iconos SVG por código ICFES ───────────────────────────
const ICONOS = {
  LC: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
  </svg>`,
  MAT: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="2" width="16" height="20" rx="2"/>
    <line x1="8" y1="6" x2="16" y2="6"/>
    <line x1="8" y1="10" x2="16" y2="10"/>
    <line x1="8" y1="14" x2="16" y2="14"/>
    <line x1="8" y1="18" x2="16" y2="18"/>
  </svg>`,
  CN: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="1"/>
    <path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5z"/>
    <path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5z"/>
  </svg>`,
  SOC: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>`,
  ING: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="2" y1="12" x2="22" y2="12"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>`,
};

// ── Sonidos precargados ───────────────────────────────────
const SFX = {};
[
  ['/static/materias_en.mp3',  0.5],
  ['/static/clic_materia.mp3', 0.7],
  ['/static/bip.mp3',          0.4],
  ['/static/lib_audio.mp3',    0.8],
  ['/static/back.mp3',         0.7],
].forEach(([src, vol]) => {
  const a = new Audio(src);
  a.preload = 'auto';
  a.volume  = vol;
  SFX[src]  = a;
});

const playSfx = (src) => {
  const a = SFX[src];
  if (!a) return;
  a.currentTime = 0;
  a.play().catch(() => {});
};

// ── Botón volver — todas las pantallas libre ──────────────
const backBtn = document.querySelector('.libre-back');
if (backBtn) {
  backBtn.addEventListener('click', () => {
    const sfx = SFX['/static/back.mp3'];
    sfx.currentTime = 0;
    sfx.onended = () => history.back();
    sfx.play().catch(() => history.back());
    setTimeout(() => history.back(), 1200);
  });
}

// ── libre_temas.html ──────────────────────────────────────
const materiasList = document.getElementById('materiasList');
const comenzarBtn  = document.getElementById('comenzarBtn');

// Input de cantidad (default 10, máx 20)
const cantidadInput = document.getElementById('cantidadInput');
if (cantidadInput) {
  cantidadInput.addEventListener('change', () => {
    let v = parseInt(cantidadInput.value, 10);
    if (isNaN(v) || v < 1) v = 1;
    if (v > 20) v = 20;
    cantidadInput.value = v;
  });
}

const getCantidad = () => {
  const v = parseInt(cantidadInput?.value ?? '10', 10);
  return isNaN(v) ? 10 : Math.min(20, Math.max(1, v));
};

if (materiasList) {
  cargarMaterias();
}

async function cargarMaterias() {
  try {
    const res = await fetch(`${API_BASE}/juego/materias`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });

    if (!res.ok) {
      materiasList.innerHTML = '<li class="prof-preview__empty">No se pudieron cargar las materias</li>';
      return;
    }

    const materias = await res.json();
    materiasList.innerHTML = '';

    materias.forEach(m => {
      const li = document.createElement('li');
      li.className = 'materia-item';
      li.dataset.id = m.id;
      li.innerHTML = `
        <span class="materia-item__icon">${ICONOS[m.codigo_icfes] ?? ''}</span>
        <span class="materia-item__name">${m.nombre}</span>
      `;
      li.addEventListener('mouseenter', () => {
        playSfx('/static/materias_en.mp3');
      });

      li.addEventListener('click', () => {
        playSfx('/static/clic_materia.mp3');
        li.classList.toggle('selected');
        const hay = document.querySelectorAll('.materia-item.selected').length > 0;
        if (comenzarBtn) comenzarBtn.disabled = !hay;
      });
      materiasList.appendChild(li);
    });

  } catch (err) {
    console.error('[Libre] Error cargando materias:', err);
    materiasList.innerHTML = '<li class="prof-preview__empty">Error de conexión con el servidor</li>';
  }
}

// Resetea el botón si el usuario vuelve con el botón atrás
window.addEventListener('pageshow', () => {
  if (comenzarBtn) {
    comenzarBtn.textContent = 'Comenzar';
    const hay = document.querySelectorAll('.materia-item.selected').length > 0;
    comenzarBtn.disabled = !hay;
  }
});

if (comenzarBtn) {
  comenzarBtn.addEventListener('mouseenter', () => {
    playSfx('/static/bip.mp3');
  });

  comenzarBtn.addEventListener('click', async () => {
    // Esperar que termine el audio (máx 1.2s) antes de continuar
    const sfx = SFX['/static/lib_audio.mp3'];
    sfx.currentTime = 0;
    await new Promise(resolve => {
      sfx.onended = resolve;
      sfx.play().catch(resolve);
      setTimeout(resolve, 1200);
    });

    const ids     = [...document.querySelectorAll('.materia-item.selected')]
      .map(el => Number(el.dataset.id));
    const cantidad = getCantidad();   // se lee UNA sola vez aquí

    comenzarBtn.disabled = true;
    comenzarBtn.textContent = 'Cargando...';

    try {
      const res = await fetch(`${API_BASE}/juego/sesiones`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          modo_juego: 'libre',
          materia_ids: ids,
          total_preguntas: cantidad,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        alert(err.detail ?? 'Error al iniciar la sesión');
        comenzarBtn.disabled = false;
        comenzarBtn.textContent = 'Comenzar';
        return;
      }

      const data = await res.json();
      sessionStorage.setItem('sesion_id', data.sesion_id);
      sessionStorage.setItem('materia_ids', ids.join(','));
      location.href = `pregunta_libre.html?cantidad=${cantidad}`;

    } catch (err) {
      console.error('[Libre] Error creando sesión:', err);
      alert('No se pudo conectar al servidor');
      comenzarBtn.disabled = false;
      comenzarBtn.textContent = 'Comenzar';
    }
  });
}
