/**
 * Mentor 11 — Dashboard Estudiante
 */

const usuario = JSON.parse(localStorage.getItem('usuario') ?? 'null');
const token = localStorage.getItem('access_token');

// Si no hay sesión, redirigir al login
if (!usuario || !token) {
  window.location.href = '/';
}


// ── Avatar Creator (canvas) ───────────────────────────────

const AVATARES_LIST = [
  { key: 'buho', label: 'Búho', src: '/static/img/avatares/buho_n.png' },
  { key: 'tiburon', label: 'Tiburón', src: '/static/img/avatares/tiburon_n.png' },
  { key: 'gato', label: 'Gato', src: '/static/img/avatares/gato_n.png' },
  { key: 'mono', label: 'Mono', src: '/static/img/avatares/mono_n.png' },
  { key: 'perro', label: 'Perro', src: '/static/img/avatares/perro_n.png' },
  { key: 'tigre', label: 'Tigre', src: '/static/img/avatares/tigre_n.png' },
  { key: 'ardilla', label: 'Ardilla', src: '/static/img/avatares/ardilla_n.png' },
  { key: 'conejo', label: 'Conejo', src: '/static/img/avatares/conejo_n.png' },
  { key: 'lobo', label: 'Lobo', src: '/static/img/avatares/lobo_n.png' },
  { key: 'pinguino', label: 'Pingüino', src: '/static/img/avatares/pinguino_n.png' },
];

const SOMBREROS_LIST = [
  { key: null, label: 'Sin sombrero', src: null },
  { key: 'ac_sombruj', label: 'Bruja', src: '/static/img/sombreros/ac_sombruj.png' },
  { key: 'ac_somvaq', label: 'Vaquero', src: '/static/img/sombreros/ac_somvaq.png' },
  { key: 'ac_somfiesta', label: 'Fiesta', src: '/static/img/sombreros/ac_somfiesta.png' },
  { key: 'ac_sommagofan', label: 'Mago', src: '/static/img/sombreros/ac_sommagofan.png' },
  { key: 'ac_sompirata', label: 'Pirata', src: '/static/img/sombreros/ac_sompirata.png' },
  { key: 'ac_somchino', label: 'Chino', src: '/static/img/sombreros/ac_somchino.png' },
  { key: 'ac_sommexi', label: 'Mexicano', src: '/static/img/sombreros/ac_sommexi.png' },
  { key: 'ac_somele', label: 'Elefante', src: '/static/img/sombreros/ac_somele.png' },
  { key: 'ac_somcoro', label: 'Corona', src: '/static/img/sombreros/ac_somcoro.png' },
  { key: 'ac_somdrag', label: 'Dragón', src: '/static/img/sombreros/ac_somdrag.png' },
  { key: 'ac_somnavi', label: 'Navidad', src: '/static/img/sombreros/ac_somnavi.png' },
];

const GAFAS_LIST = [
  { key: null, label: 'Sin gafas', src: null },
  { key: 'ac_gafasfiesta', label: 'Fiesta', src: '/static/img/gafas/ac_gafasfiesta.png' },
  { key: 'ac_gafassol', label: 'Sol', src: '/static/img/gafas/ac_gafassol.png' },
  { key: 'ac_gafasarc', label: 'Arcoíris', src: '/static/img/gafas/ac_gafasarc.png' },
  { key: 'ac_gafasantifiesta', label: 'Anti-fiesta', src: '/static/img/gafas/ac_gafasantifiesta.png' },
  { key: 'ac_gafascine', label: 'Cine', src: '/static/img/gafas/ac_gafascine.png' },
  { key: 'ac_gafascora', label: 'Corazón', src: '/static/img/gafas/ac_gafascora.png' },
  { key: 'ac_gafasvisor', label: 'Visor', src: '/static/img/gafas/ac_gafasvisor.png' },
  { key: 'ac_gafaspixeleadas', label: 'Pixeladas', src: '/static/img/gafas/ac_gafaspixeleadas.png' },
  { key: 'ac_gafaspixel', label: 'Pixel', src: '/static/img/gafas/ac_gafaspixel.png' },
  { key: 'ac_gafasojogran', label: 'Ojo Grande', src: '/static/img/gafas/ac_gafasojogran.png' },
  { key: 'ac_gafasdorada', label: 'Doradas', src: '/static/img/gafas/ac_gafasdorada.png' },
];

const AJUSTES_AVATAR = {
  '/static/img/avatares/buho_n.png': { sombrero: { x: 100, y: -20, w: 300, h: 280 }, gafas: { escala: 0.6, offsetX: 15, y: 92 } },
  '/static/img/avatares/tiburon_n.png': { sombrero: { x: 100, y: -45, w: 300, h: 280 }, gafas: { escala: 0.6, offsetX: 3, y: 55 }, gafasOverrides: { '/static/img/gafas/ac_gafasantifiesta.png': { escalaX: 0.69, escalaY: 0.6, offsetX: 3, y: 55 } } },
  '/static/img/avatares/gato_n.png': { sombrero: { x: 100, y: -20, w: 300, h: 280 }, gafas: { escala: 0.6, offsetX: 15, y: 92 } },
  '/static/img/avatares/mono_n.png': { sombrero: { x: 100, y: -35, w: 300, h: 280 }, sombreroOverrides: { '/static/img/sombreros/ac_sommagofan.png': { x: 100, y: -45, w: 300, h: 280 } }, gafas: { escala: 0.6, offsetX: 15, y: 92 } },
  '/static/img/avatares/perro_n.png': { sombrero: { x: 100, y: -25, w: 300, h: 280 }, gafas: { escala: 0.6, offsetX: 2, y: 92 }, gafasOverrides: { '/static/img/gafas/ac_gafasantifiesta.png': { escala: 0.6, offsetX: 2, y: 77 } } },
  '/static/img/avatares/tigre_n.png': { sombrero: { x: 100, y: -25, w: 300, h: 280 }, gafas: { escala: 0.6, offsetX: 15, y: 92 } },
  '/static/img/avatares/ardilla_n.png': { sombrero: { x: 100, y: -25, w: 300, h: 280 }, gafas: { escala: 0.7, offsetX: 2, y: 62 } },
  '/static/img/avatares/conejo_n.png': { sombrero: { x: 100, y: -25, w: 300, h: 280 }, gafas: { escala: 0.7, offsetX: 2, y: 62 } },
  '/static/img/avatares/lobo_n.png': { sombrero: { x: 100, y: -20, w: 300, h: 280 }, gafas: { escala: 0.6, offsetX: 15, y: 92 } },
  '/static/img/avatares/pinguino_n.png': { sombrero: { x: 100, y: -25, w: 300, h: 280 }, gafas: { escala: 0.7, offsetX: 2, y: 62 } },
};

let iAvatar = 0;
let iSombrero = 0;
let iGafas = 0;

// ── Cargar avatar guardado desde el servidor ──────────────────
async function cargarAvatar() {
  try {
    const res = await fetch('/api/v1/perfil/avatar', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) return;
    const data = await res.json();

    // Restaurar índices para el editor
    if (data.animal_base) {
      const idx = AVATARES_LIST.findIndex(a => a.key === data.animal_base);
      if (idx >= 0) iAvatar = idx;
    }
    if (data.accesorio_sombrero) {
      const idx = SOMBREROS_LIST.findIndex(s => s.key === data.accesorio_sombrero);
      if (idx >= 0) iSombrero = idx;
    }
    if (data.accesorio_gafas) {
      const idx = GAFAS_LIST.findIndex(g => g.key === data.accesorio_gafas);
      if (idx >= 0) iGafas = idx;
    }

    // Mostrar imagen compuesta guardada en el header
    if (data.imagen_src) {
      document.querySelector('.dash-avatar img').src = data.imagen_src;
      const perfilImg = document.getElementById('perfilAvatarImg');
      if (perfilImg) perfilImg.src = data.imagen_src;
    }
  } catch (_) { }
}


// Rango según puntos
function calcularRango(puntos) {
  if (puntos < 500) return 'Novato';
  if (puntos < 1500) return 'Aprendiz';
  if (puntos < 3000) return 'Explorador';
  if (puntos < 6000) return 'Avanzado';
  if (puntos < 10000) return 'Experto';
  return 'Maestro';
}

// Llenar datos del usuario
document.getElementById('rankLabel').textContent = calcularRango(usuario.puntos_totales ?? 0);
document.getElementById('streakCount').textContent = usuario.racha_actual ?? 0;


// ── Sonido cambav.mp3 para pestañas del modal ────────────
const cambavSound = new Audio('/static/cambav.mp3');
cambavSound.volume = 0.5;

function playCambav() {
  const s = cambavSound.cloneNode();
  s.volume = 0.5;
  s.play().catch(() => { });
}

// ── Sonido cam_ava.mp3 para cambiar avatar ────────────────
const camAvaSound = new Audio('/static/cam_ava.mp3');
camAvaSound.volume = 0.5;

function playCamAva() {
  const s = camAvaSound.cloneNode();
  s.volume = 0.5;
  s.play().catch(() => { });
}

// ── Sonido bop.mp3 para click en badge ───────────────────
const bopSound = new Audio('/static/bop.mp3');
bopSound.volume = 0.5;

// ── Sonido back.mp3 para cerrar modal ────────────────────
const backSound = new Audio('/static/back.mp3');
backSound.volume = 0.5;

function playBack() {
  const s = backSound.cloneNode();
  s.volume = 0.5;
  s.play().catch(() => { });
}

function playBop() {
  const s = bopSound.cloneNode();
  s.volume = 0.5;
  s.play().catch(() => { });
}

// ── Canvas render ─────────────────────────────────────────
const avatarCanvas = document.getElementById('avatarCanvas');
const avatarCtx = avatarCanvas.getContext('2d');
const CANVAS_S = 1.0; // canvas 500px = resolución nativa de los ajustes

function cargarImgCanvas(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`No se pudo cargar: ${src}`));
    img.src = src;
  });
}

async function renderAvatarCanvas() {
  const W = avatarCanvas.width;
  avatarCtx.clearRect(0, 0, W, W);
  const avatarSrc = AVATARES_LIST[iAvatar].src;
  const cfg = AJUSTES_AVATAR[avatarSrc];

  try {
    const img = await cargarImgCanvas(avatarSrc);
    avatarCtx.drawImage(img, 0, 0, W, W);
  } catch (e) { }

  if (cfg) {
    const gafasItem = GAFAS_LIST[iGafas];
    if (gafasItem.src) {
      try {
        const imgG = await cargarImgCanvas(gafasItem.src);
        const g = (cfg.gafasOverrides && cfg.gafasOverrides[gafasItem.src]) || cfg.gafas;
        const gw = imgG.naturalWidth * (g.escalaX || g.escala) * CANVAS_S;
        const gh = imgG.naturalHeight * (g.escalaY || g.escala) * CANVAS_S;
        const gx = (W - gw) / 2 + g.offsetX * CANVAS_S;
        avatarCtx.drawImage(imgG, gx, g.y * CANVAS_S, gw, gh);
      } catch (e) { }
    }

    const sombreroItem = SOMBREROS_LIST[iSombrero];
    if (sombreroItem.src) {
      try {
        const imgS = await cargarImgCanvas(sombreroItem.src);
        const s = (cfg.sombreroOverrides && cfg.sombreroOverrides[sombreroItem.src]) || cfg.sombrero;
        avatarCtx.drawImage(imgS, s.x * CANVAS_S, s.y * CANVAS_S, s.w * CANVAS_S, s.h * CANVAS_S);
      } catch (e) { }
    }
  }
}

// ── Modal de avatar ───────────────────────────────────────
const avatarOverlay = document.getElementById('avatarOverlay');
const avatarClose = document.getElementById('avatarClose');
const userBadge = document.querySelector('.dash-user-badge');

function actualizarSlotsBloqueo() {
  const puntos = JSON.parse(localStorage.getItem('usuario') ?? '{}')?.puntos_totales ?? 0;
  const UMBRALES = {
    buho: 0, gato: 500, conejo: 1500, ardilla: 3000, perro: 6000,
    mono: 10000, lobo: 15000, tiburon: 22000, tigre: 30000, pinguino: 50000,
  };
  document.querySelectorAll('#gridAvatar .avatar-slot[data-animal]').forEach(slot => {
    const umbral = UMBRALES[slot.dataset.animal] ?? 0;
    const bloqueado = puntos < umbral;
    slot.classList.toggle('avatar-slot--locked', bloqueado);
    // Añadir/quitar candado visual
    let lock = slot.querySelector('.avatar-lock-icon');
    if (bloqueado && !lock) {
      lock = document.createElement('div');
      lock.className = 'avatar-lock-icon';
      lock.innerHTML = '🔒';
      slot.appendChild(lock);
    } else if (!bloqueado && lock) {
      lock.remove();
    }
  });
}

function actualizarSlotsSeleccionados() {
  document.querySelectorAll('#gridAvatar .avatar-slot').forEach(s => {
    s.classList.toggle('avatar-slot--selected', s.dataset.animal === AVATARES_LIST[iAvatar].key);
  });
  const somKey = SOMBREROS_LIST[iSombrero].key ?? 'none';
  document.querySelectorAll('#gridSombrero .avatar-slot').forEach(s => {
    const k = s.dataset.sombrero === 'none' ? 'none' : s.dataset.sombrero;
    s.classList.toggle('avatar-slot--selected', k === somKey);
  });
  const gafKey = GAFAS_LIST[iGafas].key ?? 'none';
  document.querySelectorAll('#gridGafas .avatar-slot').forEach(s => {
    const k = s.dataset.gafas === 'none' ? 'none' : s.dataset.gafas;
    s.classList.toggle('avatar-slot--selected', k === gafKey);
  });
}

userBadge.addEventListener('mouseenter', playBip);
userBadge.addEventListener('click', () => {
  playBop();
  avatarOverlay.classList.add('open');
  actualizarSlotsSeleccionados();
  actualizarSlotsBloqueo();
  renderAvatarCanvas();
});

avatarClose.addEventListener('click', () => {
  playBack();
  avatarOverlay.classList.remove('open');
});

avatarOverlay.addEventListener('click', (e) => {
  if (e.target === avatarOverlay) avatarOverlay.classList.remove('open');
});

// Tabs
const tabGridMap = { avatar: 'gridAvatar', sombrero: 'gridSombrero', gafas: 'gridGafas' };

document.querySelectorAll('.avatar-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    playCambav();
    document.querySelectorAll('.avatar-tab').forEach(t => t.classList.remove('avatar-tab--active'));
    tab.classList.add('avatar-tab--active');
    Object.values(tabGridMap).forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
    const grid = document.getElementById(tabGridMap[tab.dataset.tab]);
    if (grid) grid.style.display = 'grid';
  });
});

// Selección de slots
document.getElementById('avatarOverlay').addEventListener('click', (e) => {
  const slot = e.target.closest('.avatar-slot--filled');
  if (!slot) return;
  if (slot.classList.contains('avatar-slot--locked')) return;

  if ('animal' in slot.dataset) {
    const idx = AVATARES_LIST.findIndex(a => a.key === slot.dataset.animal);
    if (idx >= 0) { iAvatar = idx; playCamAva(); }
  } else if ('sombrero' in slot.dataset) {
    const key = slot.dataset.sombrero === 'none' ? null : slot.dataset.sombrero;
    const idx = SOMBREROS_LIST.findIndex(s => s.key === key);
    if (idx >= 0) { iSombrero = idx; playCambav(); }
  } else if ('gafas' in slot.dataset) {
    const key = slot.dataset.gafas === 'none' ? null : slot.dataset.gafas;
    const idx = GAFAS_LIST.findIndex(g => g.key === key);
    if (idx >= 0) { iGafas = idx; playCambav(); }
  } else {
    return;
  }

  actualizarSlotsSeleccionados();
  renderAvatarCanvas();
});

// Hover sonido
document.getElementById('avatarOverlay').addEventListener('mouseover', (e) => {
  if (e.target.closest('.avatar-slot')) playAvatarHover();
});

// Guardar
document.getElementById('avatarSaveBtn').addEventListener('click', async () => {
  playBop();
  const btn = document.getElementById('avatarSaveBtn');
  const msg = document.getElementById('avatarSaveMsg');
  btn.disabled = true;
  btn.textContent = 'Guardando...';
  msg.style.display = 'none';

  try {
    const animal = AVATARES_LIST[iAvatar];
    const sombrero = SOMBREROS_LIST[iSombrero];
    const gafas = GAFAS_LIST[iGafas];

    await renderAvatarCanvas();
    const imagenSrc = avatarCanvas.toDataURL('image/png');

    document.querySelector('.dash-avatar img').src = imagenSrc;
    const perfilImg = document.getElementById('perfilAvatarImg');
    if (perfilImg) perfilImg.src = imagenSrc;

    const res = await fetch('/api/v1/perfil/avatar', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        imagen_src: imagenSrc,
        animal_base: animal.key,
        accesorio_sombrero: sombrero.key ?? null,
        accesorio_gafas: gafas.key ?? null,
      }),
    });

    if (res.ok) {
      avatarOverlay.classList.remove('open');
    } else {
      const err = await res.json().catch(() => ({}));
      msg.textContent = `Error ${res.status}: ${err.detail || 'No se pudo guardar el avatar'}`;
      msg.style.cssText = 'display:block;text-align:center;margin-top:8px;font-size:0.85rem;color:#e74c3c;';
      console.error('[Avatar] Error al guardar:', res.status, err);
    }
  } catch (e) {
    msg.textContent = 'Error de conexión. ¿Está el servidor encendido?';
    msg.style.cssText = 'display:block;text-align:center;margin-top:8px;font-size:0.85rem;color:#e74c3c;';
    console.error('[Avatar] Error de red:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Guardar avatar';
  }
});

// ── Sonido bip.mp3 para tarjetas de modos ────────────────
const bipSound = new Audio('/static/bip.mp3');
bipSound.volume = 0.5;

function playBip() {
  const s = bipSound.cloneNode();
  s.volume = 0.5;
  s.play().catch(() => { });
}

document.querySelectorAll('.dash-mode-card').forEach(card => {
  card.addEventListener('mouseenter', playBip);
});

// ── Sonido generado para botones del nav inferior ────────
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playNavSound() {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.type = 'sine';
  osc.frequency.setValueAtTime(520, audioCtx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(640, audioCtx.currentTime + 0.08);
  gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);
  osc.start(audioCtx.currentTime);
  osc.stop(audioCtx.currentTime + 0.12);
}

const menuBipSfx = new Audio('/static/menu_bip.mp3');
menuBipSfx.volume = 0.6;

document.querySelectorAll('.dash-nav__btn').forEach(btn => {
  btn.addEventListener('mouseenter', playNavSound);
  btn.addEventListener('click', () => {
    const sfx = menuBipSfx.cloneNode();
    sfx.volume = 0.6;
    sfx.play().catch(() => { });
  });
});

// ── Sonido hover para slots de avatar en el modal ─────────
function playAvatarHover() {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.type = 'sine';
  osc.frequency.setValueAtTime(880, audioCtx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(1100, audioCtx.currentTime + 0.06);
  gain.gain.setValueAtTime(0.02, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.1);
  osc.start(audioCtx.currentTime);
  osc.stop(audioCtx.currentTime + 0.1);
}


// Cargar avatar al entrar al dashboard
cargarAvatar();

// ── Modal de estadísticas ─────────────────────────────────────
const statsOverlay = document.getElementById('statsOverlay');
const statsBtn = document.getElementById('statsBtn');

let datosStats = [];
let vistaStats = 'bars';

const ABREV_MATERIA = {
  'Lectura Crítica': 'LC',
  'Matemáticas': 'Mat',
  'Ciencias Naturales': 'CN',
  'Sociales y Ciudadanas': 'Soc',
  'Inglés': 'Ing',
};

function abrevMateria(nombre) {
  for (const [key, val] of Object.entries(ABREV_MATERIA)) {
    if (nombre.toLowerCase().includes(key.toLowerCase()) ||
      key.toLowerCase().includes(nombre.toLowerCase())) return val;
  }
  return nombre.slice(0, 3);
}

function ocultarAvatarFlotante() {
  document.getElementById('statsRadarFloat').classList.remove('visible');
}

function renderBars(datos) {
  ocultarAvatarFlotante();
  const card = document.getElementById('statsBars');
  card.innerHTML = datos.map(d => `
    <div class="stats-subject-row">
      <div class="stats-subject-info">
        <span class="stats-subject-icon">${getIconoMateria(d.materia)}</span>
        <span class="stats-subject-name">${d.materia}</span>
        <span class="stats-subject-pct" data-pct="${d.porcentaje}">0 %</span>
      </div>
      <div class="stats-bar-track">
        <div class="stats-bar-fill" data-width="${d.porcentaje}" style="background:${colorMateria(d.materia)}"></div>
      </div>
    </div>
  `).join('');
  requestAnimationFrame(() => {
    card.querySelectorAll('.stats-bar-fill').forEach(b => { b.style.width = b.dataset.width + '%'; });
    card.querySelectorAll('.stats-subject-pct').forEach(el => {
      animarContador(el, parseInt(el.dataset.pct), 900);
    });
  });
}

function renderColumns(datos) {
  ocultarAvatarFlotante();
  const card = document.getElementById('statsBars');
  card.innerHTML = `<div class="stats-cols-view">
    ${datos.map(d => `
      <div class="stats-col-item">
        <span class="stats-col-pct" data-pct="${d.porcentaje}">0 %</span>
        <div class="stats-col-bar-wrap">
          <div class="stats-col-bar" data-h="${d.porcentaje}" style="height:0;background:${colorMateria(d.materia)}"></div>
        </div>
        <span class="stats-col-label">${abrevMateria(d.materia)}</span>
      </div>
    `).join('')}
  </div>`;
  requestAnimationFrame(() => {
    card.querySelectorAll('.stats-col-bar').forEach(b => { b.style.height = b.dataset.h + '%'; });
    card.querySelectorAll('.stats-col-pct').forEach(el => {
      animarContador(el, parseInt(el.dataset.pct), 900);
    });
  });
}

const COLORES_MATERIA = {
  'Lectura Crítica': '#6366F1',
  'Matemáticas': '#F59E0B',
  'Ciencias Naturales': '#10B981',
  'Sociales y Ciudadanas': '#EC4899',
  'Inglés': '#3B82F6',
};
const COLORES_FALLBACK = ['#F97316', '#3B82F6', '#22C55E', '#A855F7', '#EF4444'];

function colorMateria(nombre) {
  for (const [key, val] of Object.entries(COLORES_MATERIA)) {
    if (nombre.toLowerCase().includes(key.toLowerCase()) ||
      key.toLowerCase().includes(nombre.toLowerCase())) return val;
  }
  return COLORES_FALLBACK[Math.abs(nombre.charCodeAt(0)) % COLORES_FALLBACK.length];
}

function renderPie(datos) {
  ocultarAvatarFlotante();
  const R = 27, C = +(2 * Math.PI * R).toFixed(2);
  const card = document.getElementById('statsBars');
  card.innerHTML = `<div class="stats-radial-view">
    ${datos.map(d => {
    const offset = +(C * (1 - d.porcentaje / 100)).toFixed(2);
    const color = colorMateria(d.materia);
    return `
        <div class="stats-radial-item">
          <svg class="stats-radial-svg" viewBox="0 0 64 64">
            <circle class="stats-radial-track" cx="32" cy="32" r="${R}"/>
            <circle class="stats-radial-fill" cx="32" cy="32" r="${R}"
              stroke="${color}" stroke-dasharray="${C}" stroke-dashoffset="${C}" data-offset="${offset}"/>
          </svg>
          <span class="stats-radial-pct" data-pct="${d.porcentaje}">0 %</span>
          <span class="stats-radial-label">${abrevMateria(d.materia)}</span>
        </div>`;
  }).join('')}
  </div>`;
  requestAnimationFrame(() => {
    card.querySelectorAll('.stats-radial-fill').forEach(c => { c.style.strokeDashoffset = c.dataset.offset; });
    card.querySelectorAll('.stats-radial-pct').forEach(el => {
      animarContador(el, parseInt(el.dataset.pct), 900);
    });
  });
}

function renderRadar(datos) {
  const card = document.getElementById('statsBars');

  // 5 materias + promedio general → 6 puntos = hexágono (igual que DBX)
  const promedio = Math.round(datos.reduce((s, d) => s + d.porcentaje, 0) / datos.length);
  const all = [...datos, { materia: 'General', porcentaje: promedio }];

  const N = all.length;
  const cx = 110, cy = 110, maxR = 78;
  const step = (2 * Math.PI) / N;

  function polyPts(scale) {
    return all.map((d, i) => {
      const a = -Math.PI / 2 + i * step;
      const r = maxR * (d.porcentaje / 100) * scale;
      return `${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`;
    }).join(' ');
  }

  function gridPts(frac) {
    return all.map((_, i) => {
      const a = -Math.PI / 2 + i * step;
      return `${(cx + maxR * frac * Math.cos(a)).toFixed(1)},${(cy + maxR * frac * Math.sin(a)).toFixed(1)}`;
    }).join(' ');
  }

  const gridPolys = [0.33, 0.66, 1].map(f =>
    `<polygon points="${gridPts(f)}" fill="none"
      stroke="rgba(56,189,248,${f === 1 ? 0.3 : 0.1})"
      stroke-width="${f === 1 ? 1.5 : 0.8}"
      stroke-dasharray="${f < 1 ? '3 3' : ''}"/>`
  ).join('');

  const axes = all.map((_, i) => {
    const a = -Math.PI / 2 + i * step;
    return `<line x1="${cx}" y1="${cy}"
      x2="${(cx + maxR * Math.cos(a)).toFixed(1)}" y2="${(cy + maxR * Math.sin(a)).toFixed(1)}"
      stroke="rgba(56,189,248,0.12)" stroke-width="1"/>`;
  }).join('');

  const labelEls = all.map((d, i) => {
    const a = -Math.PI / 2 + i * step;
    const lx = (cx + (maxR + 24) * Math.cos(a)).toFixed(1);
    const ly = (cy + (maxR + 24) * Math.sin(a)).toFixed(1);
    const color = d.materia === 'General' ? '#fde047' : colorMateria(d.materia);
    return `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle"
      fill="${color}" font-size="9.5" font-weight="800"
      font-family="Inter,sans-serif">${abrevMateria(d.materia)}</text>`;
  }).join('');

  const dotEls = all.map((d, i) =>
    `<circle class="stats-radar-dot" cx="${cx}" cy="${cy}"
      r="${d.materia === 'General' ? 5 : 3.5}"
      fill="${d.materia === 'General' ? '#fde047' : colorMateria(d.materia)}"
      stroke="rgba(0,0,0,0.5)" stroke-width="1.5"/>`
  ).join('');

  const avatarSrc = document.querySelector('.dash-avatar img').src;
  const overlay = document.getElementById('statsOverlay');
  const scrollSnap = overlay.scrollTop;

  card.innerHTML = `
    <div class="stats-radar-arcade">
      <div class="stats-radar-avatar">
        <img src="${avatarSrc}" alt="Avatar" />
      </div>
      <svg class="stats-radar-svg" viewBox="0 0 220 220">
        <defs>
          <radialGradient id="gemGrad" cx="42%" cy="32%" r="62%">
            <stop offset="0%"   stop-color="#d4fbff"/>
            <stop offset="35%"  stop-color="#00d4ff"/>
            <stop offset="70%"  stop-color="#0077c2"/>
            <stop offset="100%" stop-color="#003870"/>
          </radialGradient>
          <filter id="radarGlow" x="-35%" y="-35%" width="170%" height="170%">
            <feGaussianBlur stdDeviation="7" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        <!-- Fondo oscuro circular -->
        <circle cx="${cx}" cy="${cy}" r="${maxR + 8}" fill="#110600"/>

        <!-- Cuadrícula -->
        ${gridPolys}
        ${axes}

        <!-- Polígono de datos — gema animada -->
        <polygon class="stats-radar-fill" points="${polyPts(0)}"
          fill="url(#gemGrad)" stroke="#00e5ff"
          stroke-width="1.5" stroke-linejoin="round"
          filter="url(#radarGlow)"/>

        <!-- Anillo metálico exterior (naranja marca) -->
        <circle cx="${cx}" cy="${cy}" r="${maxR + 7}" fill="none"
          stroke="#7c2d00" stroke-width="12"/>
        <circle cx="${cx}" cy="${cy}" r="${maxR + 7}" fill="none"
          stroke="rgba(249,115,22,0.85)" stroke-width="2"/>
        <circle cx="${cx}" cy="${cy}" r="${maxR + 1}" fill="none"
          stroke="rgba(249,115,22,0.2)" stroke-width="1.5"/>

        <!-- Etiquetas -->
        ${labelEls}
      </svg>

      <div class="stats-radar-legend-dark">
        ${all.map(d => `
          <div class="stats-radar-legend-dark-item">
            <span class="stats-radar-legend-dark-dot"
              style="background:${d.materia === 'General' ? '#fde047' : colorMateria(d.materia)}"></span>
            <span class="stats-radar-legend-dark-name">${d.materia}</span>
            <span class="stats-radar-legend-dark-pct" data-pct="${d.porcentaje}">0 %</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  overlay.scrollTop = scrollSnap;

  const polygon = card.querySelector('.stats-radar-fill');
  const t0 = performance.now();
  const FLUC = 1000;   // 1 s de fluctuación
  const EASE = 900;    // ms de ease hacia valores reales
  let countersStarted = false;

  // Puntos que fluctúan: cada vértice oscila con desfase propio
  function fluctuatePts(elapsed) {
    const phase = elapsed / FLUC;
    return all.map((_, i) => {
      const a = -Math.PI / 2 + i * step;
      const v = 0.28 + 0.22 * Math.sin(phase * Math.PI * 5 + i * 1.1);
      const r = maxR * v;
      return `${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`;
    }).join(' ');
  }

  (function animateRadar(now) {
    const elapsed = now - t0;
    if (elapsed < FLUC) {
      // Fase 1 — fluctúa durante 1 s
      if (polygon) polygon.setAttribute('points', fluctuatePts(elapsed));
      requestAnimationFrame(animateRadar);
    } else {
      // Fase 2 — ease-out hacia valores reales
      if (!countersStarted) {
        countersStarted = true;
        card.querySelectorAll('.stats-radar-legend-dark-pct').forEach(el => {
          animarContador(el, parseInt(el.dataset.pct), EASE);
        });
      }
      const t = Math.min((elapsed - FLUC) / EASE, 1);
      const e = 1 - Math.pow(1 - t, 3);
      if (polygon) polygon.setAttribute('points', polyPts(e));
      if (t < 1) requestAnimationFrame(animateRadar);
    }
  })(t0);
}

function renderVista(datos) {
  if (vistaStats === 'bars') renderBars(datos);
  else if (vistaStats === 'columns') renderColumns(datos);
  else if (vistaStats === 'radar') renderRadar(datos);
  else renderPie(datos);
}

const arcadeStatSfx = new Audio('/static/arcade_stat.mp3');
arcadeStatSfx.volume = 0.7;
const statSfx1 = new Audio('/static/stat_1.mp3');
statSfx1.volume = 0.7;
const statSfx2 = new Audio('/static/stat_2.mp3');
statSfx2.volume = 0.7;
let statSfxToggle = false;   // false → stat_1, true → stat_2

// ── Loop 8-bit ────────────────────────────────────────────
let eightBitLoop = null;

function startEightBitLoop() {
  stopEightBitLoop();
  eightBitLoop = new Audio('/static/8bit_sonido.mp3');
  eightBitLoop.loop = true;
  eightBitLoop.volume = 0.45;
  eightBitLoop.play().catch(() => { });
}

function stopEightBitLoop() {
  if (eightBitLoop) {
    eightBitLoop.pause();
    eightBitLoop.currentTime = 0;
    eightBitLoop = null;
  }
}

document.getElementById('statsViewTabs').addEventListener('click', (e) => {
  const btn = e.target.closest('.stats-pill-tab');
  if (!btn) return;
  document.querySelectorAll('.stats-pill-tab').forEach(b => {
    b.classList.remove('stats-pill-tab--active');
    b.style.animation = 'none';
  });
  btn.classList.add('stats-pill-tab--active');
  void btn.offsetWidth;
  btn.style.animation = '';
  vistaStats = btn.dataset.view;
  if (vistaStats === 'radar') {
    const sfx = arcadeStatSfx.cloneNode();
    sfx.volume = 0.7;
    sfx.play().catch(() => { });
    startEightBitLoop();
  } else {
    stopEightBitLoop();
    const src = statSfxToggle ? statSfx2 : statSfx1;
    statSfxToggle = !statSfxToggle;
    const sfx = src.cloneNode();
    sfx.volume = 0.7;
    sfx.play().catch(() => { });
  }
  if (datosStats.length) renderVista(datosStats);
});

const ICONOS_MATERIA = {
  'Lectura Crítica': `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
  </svg>`,
  'Matemáticas': `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="14" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/>
  </svg>`,
  'Ciencias Naturales': `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
  </svg>`,
  'Sociales y Ciudadanas': `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>`,
  'Inglés': `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M4 5h7M9 3v2c0 4.418-2.239 8-5 8"/>
    <path d="M5 9c-.003 2.144 2.952 3.908 6.7 4"/>
    <path d="M12 20l4-9 4 9M19.1 18h-6.2"/>
  </svg>`,
};

function getIconoMateria(materia) {
  for (const key of Object.keys(ICONOS_MATERIA)) {
    if (materia.toLowerCase().includes(key.toLowerCase()) ||
      key.toLowerCase().includes(materia.toLowerCase())) {
      return ICONOS_MATERIA[key];
    }
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>`;
}

function animarContador(el, destino, duracionMs) {
  const inicio = performance.now();
  function tick(ahora) {
    const t = Math.min((ahora - inicio) / duracionMs, 1);
    // Ease-out cúbico
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = `${Math.round(eased * destino)} %`;
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

async function abrirEstadisticas() {
  const card = document.getElementById('statsBars');
  const promedioEl = document.getElementById('promedioGeneral');
  card.innerHTML = '<p class="stats-loading-msg">Cargando...</p>';
  promedioEl.textContent = '— %';
  // Resetear vista al abrir
  vistaStats = 'bars';
  document.querySelectorAll('.stats-pill-tab').forEach(b => b.classList.remove('stats-pill-tab--active'));
  document.querySelector('.stats-pill-tab[data-view="bars"]').classList.add('stats-pill-tab--active');
  ocultarAvatarFlotante();
  statsOverlay.classList.add('open');

  try {
    const res = await fetch('/api/v1/perfil/estadisticas', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const datos = await res.json();

    if (!datos.length) {
      card.innerHTML = '<p class="stats-loading-msg">Aún no has respondido preguntas.</p>';
      promedioEl.textContent = '0 %';
      return;
    }

    datosStats = datos;
    const promedio = Math.round(datos.reduce((s, d) => s + d.porcentaje, 0) / datos.length);
    animarContador(promedioEl, promedio, 900);
    renderVista(datos);
  } catch (_) {
    card.innerHTML = '<p class="stats-loading-msg">Error al cargar estadísticas.</p>';
  }
}

statsBtn.addEventListener('click', abrirEstadisticas);
const backSfx = new Audio('/static/back.mp3');
backSfx.volume = 0.7;

document.getElementById('statsClose').addEventListener('click', () => {
  stopEightBitLoop();
  const sfx = backSfx.cloneNode();
  sfx.volume = 0.7;
  sfx.play().catch(() => { });
  statsOverlay.classList.remove('open');
});
