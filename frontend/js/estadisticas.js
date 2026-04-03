/**
 * Mentor 11 — Estadísticas
 */

const token = localStorage.getItem('access_token');

if (!token) {
  window.location.href = '/';
}

// ── Icono SVG por materia ─────────────────────────────────
const ICONOS = {
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

function getIcono(materia) {
  for (const key of Object.keys(ICONOS)) {
    if (materia.toLowerCase().includes(key.toLowerCase()) ||
        key.toLowerCase().includes(materia.toLowerCase())) {
      return ICONOS[key];
    }
  }
  // Fallback: bookmark icon
  return `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>`;
}

// ── Cargar y renderizar estadísticas ─────────────────────────
async function cargarEstadisticas() {
  const card = document.getElementById('subjectsCard');
  const promedioEl = document.getElementById('promedioGeneral');

  try {
    const res = await fetch('/api/v1/perfil/estadisticas', {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const datos = await res.json();

    if (!datos.length) {
      card.innerHTML = '<p class="stats-loading">Aún no has respondido preguntas.</p>';
      promedioEl.textContent = '0 %';
      return;
    }

    // Calcular promedio general
    const promedio = Math.round(datos.reduce((s, d) => s + d.porcentaje, 0) / datos.length);
    promedioEl.textContent = `${promedio} %`;

    // Renderizar filas de materias
    card.innerHTML = datos.map(d => `
      <div class="stats-subject-row">
        <div class="stats-subject-info">
          <span class="stats-subject-icon">${getIcono(d.materia)}</span>
          <span class="stats-subject-name">${d.materia}</span>
          <span class="stats-subject-pct">${d.porcentaje}%</span>
        </div>
        <div class="stats-bar-track">
          <div class="stats-bar-fill" data-width="${d.porcentaje}"></div>
        </div>
      </div>
    `).join('');

    // Animar barras tras render
    requestAnimationFrame(() => {
      document.querySelectorAll('.stats-bar-fill').forEach(bar => {
        bar.style.width = bar.dataset.width + '%';
      });
    });

  } catch (_) {
    card.innerHTML = '<p class="stats-loading">Error al cargar estadísticas.</p>';
  }
}

// ── Navegación ────────────────────────────────────────────────
document.getElementById('backBtn').addEventListener('click', () => {
  history.back();
});

document.getElementById('navHome').addEventListener('click', () => {
  window.location.href = '/dashboard_estudiante.html';
});

cargarEstadisticas();
