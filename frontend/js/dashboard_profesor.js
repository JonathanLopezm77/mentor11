/**
 * Mentor 11 — Dashboard Profesor
 */

const API_BASE = '/api/v1';

const usuario = JSON.parse(localStorage.getItem('usuario') ?? 'null');

// Si no hay sesión, redirigir al login
if (!usuario) {
  window.location.href = '/';
}

// ── Perfil → logout ───────────────────────────────────────
document.getElementById('profileBtn').addEventListener('click', () => {
  localStorage.clear();
  window.location.href = '/';
});

// ── Cargar estadísticas del profesor ─────────────────────
async function cargarStats() {
  const token = localStorage.getItem('access_token');
  if (!token) return;

  try {
    const res = await fetch(`${API_BASE}/profesor/stats`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (res.ok) {
      const data = await res.json();
      document.getElementById('statAulas').textContent = data.aulas ?? 0;
      document.getElementById('statEstudiantes').textContent = data.estudiantes ?? 0;
      document.getElementById('statRetos').textContent = data.retos ?? 0;
      renderEstudiantes(data.estudiantes_lista ?? []);
    }
  } catch (err) {
    console.warn('[Dashboard Profesor] No se pudo cargar stats:', err);
  }
}

// ── Renderizar grid de estudiantes ────────────────────────
function renderEstudiantes(lista) {
  const grid = document.getElementById('estudiantesGrid');
  if (!lista.length) return;

  grid.innerHTML = '';
  lista.forEach(est => {
    const div = document.createElement('div');
    div.className = 'prof-student-avatar';
    div.innerHTML = `
      <div class="prof-student-avatar__img">
        <img src="${est.avatar ?? '/static/img/tigre.png'}" alt="${est.username}" />
      </div>
      <span class="prof-student-avatar__name">${est.username}</span>
    `;
    grid.appendChild(div);
  });
}

// Inicializar
cargarStats();
