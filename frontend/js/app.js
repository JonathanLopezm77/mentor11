/**
 * Mentor 11 — Login
 * Conecta con POST /api/v1/auth/login del backend FastAPI.
 */

const API_BASE = 'http://localhost:8000/api/v1';

// ── Elementos del DOM ────────────────────────────────────────
const form         = document.getElementById('loginForm');
const identifierEl = document.getElementById('identifier');
const passwordEl   = document.getElementById('password');
const toggleBtn    = document.getElementById('togglePassword');
const eyeIcon      = document.getElementById('eyeIcon');
const submitBtn    = document.getElementById('submitBtn');
const btnText      = submitBtn.querySelector('.btn__text');
const btnSpinner   = submitBtn.querySelector('.btn__spinner');
const loginAlert   = document.getElementById('loginAlert');
const loginAlertMsg = document.getElementById('loginAlertMsg');

// ── Mostrar / ocultar contraseña ─────────────────────────────
toggleBtn.addEventListener('click', () => {
  const isPassword = passwordEl.type === 'password';
  passwordEl.type = isPassword ? 'text' : 'password';

  // Cambiar ícono ojo abierto / tachado
  eyeIcon.innerHTML = isPassword
    ? /* ojo tachado */
      `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
       <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
       <line x1="1" y1="1" x2="23" y2="23"/>`
    : /* ojo normal */
      `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
       <circle cx="12" cy="12" r="3"/>`;
});

// ── Validación en tiempo real ────────────────────────────────
identifierEl.addEventListener('input', () => clearFieldError('identifier'));
passwordEl.addEventListener('input',   () => clearFieldError('password'));

function clearFieldError(fieldId) {
  const el = document.getElementById(fieldId);
  const err = document.getElementById(fieldId + 'Error');
  el.classList.remove('is-invalid');
  if (err) err.textContent = '';
}

function showFieldError(fieldId, msg) {
  const el  = document.getElementById(fieldId);
  const err = document.getElementById(fieldId + 'Error');
  el.classList.add('is-invalid');
  if (err) err.textContent = msg;
  el.focus();
}

// ── Validación local antes de enviar ────────────────────────
function validate() {
  let ok = true;

  if (!identifierEl.value.trim()) {
    showFieldError('identifier', 'Ingresa tu usuario o correo.');
    ok = false;
  }

  if (!passwordEl.value) {
    showFieldError('password', 'Ingresa tu contraseña.');
    ok = false;
  } else if (passwordEl.value.length < 8) {
    showFieldError('password', 'La contraseña debe tener al menos 8 caracteres.');
    ok = false;
  }

  return ok;
}

// ── Estado del botón ─────────────────────────────────────────
function setLoading(loading) {
  submitBtn.disabled = loading;
  btnText.hidden     = loading;
  btnSpinner.hidden  = !loading;
}

function showAlert(msg) {
  loginAlertMsg.textContent = msg;
  loginAlert.hidden = false;
}

function hideAlert() {
  loginAlert.hidden = true;
  loginAlertMsg.textContent = '';
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast toast--success';
  toast.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
    <span>${msg}</span>
  `;
  document.body.appendChild(toast);
  // Forzar reflow para que la animación arranque
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => toast.remove(), 2200);
}

// ── Envío del formulario ─────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();

  if (!validate()) return;

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        identifier: identifierEl.value.trim(),
        password: passwordEl.value,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      // El backend devuelve { detail: "mensaje" }
      const msg = data.detail ?? 'Ocurrió un error al iniciar sesión.';
      showAlert(msg);
      return;
    }

    // Guardar tokens en localStorage
    localStorage.setItem('access_token',  data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('usuario',       JSON.stringify(data.usuario));

    // Mostrar notificación de éxito y redirigir según rol
    showToast(`¡Bienvenido, ${data.usuario.username}!`);
    const destinos = {
      estudiante:      'dashboard_estudiante.html',
      profesor:        'dashboard_profesor.html',
      admin_contenido: 'dashboard_admin.html',
      admin_tech:      'dashboard_admin.html',
    };
    const destino = destinos[data.usuario.rol] ?? 'dashboard_estudiante.html';
    setTimeout(() => { window.location.href = destino; }, 1800);

  } catch (err) {
    // Error de red / backend caído
    showAlert('No se pudo conectar al servidor. Verifica que el backend esté activo.');
    console.error('[Login]', err);
  } finally {
    setLoading(false);
  }
});
