/**
 * Mentor 11 — Sistema de Progresión
 * Muestra barra de progreso y desbloqueo de avatares tras cada actividad.
 */

const TITULOS = [
  { nombre: 'Novato',      puntos: 0,      avatar: 'buho',     src: '/static/img/avatares/buho_n.png' },
  { nombre: 'Aprendiz',    puntos: 500,    avatar: 'gato',     src: '/static/img/avatares/gato_n.png' },
  { nombre: 'Explorador',  puntos: 1500,   avatar: 'conejo',   src: '/static/img/avatares/conejo_n.png' },
  { nombre: 'Estudioso',   puntos: 3000,   avatar: 'ardilla',  src: '/static/img/avatares/ardilla_n.png' },
  { nombre: 'Avanzado',    puntos: 6000,   avatar: 'perro',    src: '/static/img/avatares/perro_n.png' },
  { nombre: 'Experto',     puntos: 10000,  avatar: 'mono',     src: '/static/img/avatares/mono_n.png' },
  { nombre: 'Maestro',     puntos: 15000,  avatar: 'lobo',     src: '/static/img/avatares/lobo_n.png' },
  { nombre: 'Campeón',     puntos: 22000,  avatar: 'tiburon',  src: '/static/img/avatares/tiburon_n.png' },
  { nombre: 'Leyenda',     puntos: 30000,  avatar: 'tigre',    src: '/static/img/avatares/tigre_n.png' },
  { nombre: 'Élite',       puntos: 50000,  avatar: 'pinguino', src: '/static/img/avatares/pinguino_n.png' },
];

function getTituloIdx(puntos) {
  let idx = 0;
  for (let i = 0; i < TITULOS.length; i++) {
    if (puntos >= TITULOS[i].puntos) idx = i;
    else break;
  }
  return idx;
}

function getTitulo(puntos) {
  return TITULOS[getTituloIdx(puntos)];
}

// Retorna los avatares desbloqueados según puntos
function getAvatarsDesbloqueados(puntos) {
  return TITULOS.filter(t => puntos >= t.puntos).map(t => t.avatar);
}

// ── Overlay ───────────────────────────────────────────────

function crearOverlay() {
  if (document.getElementById('progresoOverlay')) return;
  const el = document.createElement('div');
  el.id = 'progresoOverlay';
  el.className = 'progreso-overlay';
  el.innerHTML = `
    <div class="progreso-card">
      <span class="progreso-ganados" id="progresoGanados">+0</span>
      <span class="progreso-ganados-label">puntos ganados</span>

      <div class="progreso-unlock" id="progresoUnlock" style="display:none">
        <span class="progreso-unlock__badge">¡Nuevo título desbloqueado!</span>
        <img class="progreso-unlock__avatar" id="progresoUnlockAvatar" src="" alt="Avatar" />
        <div class="progreso-unlock__titulo" id="progresoUnlockTitulo"></div>
        <div class="progreso-unlock__aviso">Avatar desbloqueado</div>
      </div>

      <div class="progreso-titulos-row">
        <span class="progreso-titulo-actual" id="progresoTituloActual"></span>
        <span class="progreso-titulo-sig" id="progresoTituloSig"></span>
      </div>
      <div class="progreso-bar-wrap">
        <div class="progreso-bar-track">
          <div class="progreso-bar-fill" id="progresoBarFill"></div>
        </div>
        <span class="progreso-bar-pct" id="progresoBarPct">0%</span>
      </div>
      <div class="progreso-pts-row">
        <span id="progresoPtsActual"></span>
        <span id="progresoPtsSig"></span>
      </div>

      <button class="progreso-btn" id="progresoContinuarBtn">Continuar</button>
    </div>
  `;
  document.body.appendChild(el);
}

// ── Función principal ─────────────────────────────────────

async function mostrarProgreso(puntosAntes, onContinuar, puntosGanados = null) {
  crearOverlay();

  const token = localStorage.getItem('access_token');
  let puntosNuevos = puntosAntes;

  try {
    const res = await fetch('http://localhost:8000/api/v1/perfil/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      puntosNuevos = data.puntos_totales;
      // Actualizar localStorage
      const usuario = JSON.parse(localStorage.getItem('usuario') ?? '{}');
      usuario.puntos_totales = puntosNuevos;
      localStorage.setItem('usuario', JSON.stringify(usuario));
    }
  } catch (_) {}

  // Si se pasa puntosGanados directamente (desde el backend), usarlo.
  // Calcular puntosAntes real para animar la barra correctamente.
  const ganados        = puntosGanados !== null ? puntosGanados : Math.max(0, puntosNuevos - puntosAntes);
  const puntosAntesBar = puntosGanados !== null ? Math.max(0, puntosNuevos - puntosGanados) : puntosAntes;
  const idxAntes   = getTituloIdx(puntosAntesBar);
  const idxNuevos  = getTituloIdx(puntosNuevos);
  const subio      = idxNuevos > idxAntes;
  const tActual    = TITULOS[idxNuevos];
  const tSig       = TITULOS[idxNuevos + 1] ?? null;

  // Calcular porcentaje dentro del rango del título actual
  const pBase      = tActual.puntos;
  const pSig       = tSig?.puntos ?? tActual.puntos;
  const rango      = tSig ? pSig - pBase : 1;
  const pctNuevo   = tSig ? Math.min(((puntosNuevos - pBase) / rango) * 100, 100) : 100;
  const pctAntes   = tSig ? Math.min(((Math.max(puntosAntesBar, pBase) - pBase) / rango) * 100, 100) : 100;

  // Llenar datos
  document.getElementById('progresoGanados').textContent    = `+${ganados}`;
  document.getElementById('progresoTituloActual').textContent = tActual.nombre;
  document.getElementById('progresoTituloSig').textContent  = tSig ? `→ ${tSig.nombre}` : '¡Nivel máximo!';
  document.getElementById('progresoPtsActual').textContent  = `${puntosNuevos.toLocaleString()} pts`;
  document.getElementById('progresoPtsSig').textContent     = tSig ? `Meta: ${pSig.toLocaleString()} pts` : '';

  // Desbloqueo de título
  const unlockEl = document.getElementById('progresoUnlock');
  if (subio) {
    document.getElementById('progresoUnlockAvatar').src      = tActual.src;
    document.getElementById('progresoUnlockTitulo').textContent = tActual.nombre;
    unlockEl.style.display = 'flex';
  } else {
    unlockEl.style.display = 'none';
  }

  // Mostrar overlay
  const overlay = document.getElementById('progresoOverlay');
  overlay.classList.add('visible');

  // Animar barra: parte del % anterior y avanza al nuevo
  const barFill = document.getElementById('progresoBarFill');
  const barPct  = document.getElementById('progresoBarPct');
  barFill.style.transition = 'none';
  barFill.style.width = pctAntes + '%';

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      barFill.style.transition = 'width 1.2s cubic-bezier(0.34, 1.1, 0.64, 1)';
      barFill.style.width = pctNuevo + '%';

      // Sonido de logro si subió de título (con delay para que suene después)
      if (subio) {
        setTimeout(() => {
          try {
            const sfxLogro = new Audio('/static/logro.mp3');
            sfxLogro.volume = 0.85;
            sfxLogro.play().catch(() => {});
          } catch (_) {}
        }, 800);
      }

      // Animar número del porcentaje
      const start = performance.now();
      const dur = 1200;
      const desde = pctAntes;
      const hasta = pctNuevo;
      (function tick(now) {
        const t = Math.min((now - start) / dur, 1);
        const e = 1 - Math.pow(1 - t, 3);
        barPct.textContent = Math.round(desde + (hasta - desde) * e) + '%';
        if (t < 1) requestAnimationFrame(tick);
      })(start);
    });
  });

  // Botón continuar
  document.getElementById('progresoContinuarBtn').onclick = () => {
    overlay.classList.remove('visible');
    setTimeout(() => {
      overlay.remove();
      if (typeof onContinuar === 'function') onContinuar();
    }, 350);
  };
}
