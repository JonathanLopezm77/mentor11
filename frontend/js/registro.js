/**
 * Mentor 11 — Registro
 * Conecta con POST /api/v1/auth/registro del backend FastAPI.
 */

const API_BASE = 'http://localhost:8000/api/v1';

// ── Elementos del DOM ────────────────────────────────────────
const form         = document.getElementById('registroForm');
const usernameEl   = document.getElementById('username');
const emailEl      = document.getElementById('email');
const passwordEl   = document.getElementById('password');
const fechaEl      = document.getElementById('fecha_nacimiento');
const toggleBtn    = document.getElementById('togglePassword');
const eyeIcon      = document.getElementById('eyeIcon');
const submitBtn    = document.getElementById('submitBtn');
const btnText      = submitBtn.querySelector('.btn__text');
const btnSpinner   = submitBtn.querySelector('.btn__spinner');
const registroAlert    = document.getElementById('registroAlert');
const registroAlertMsg = document.getElementById('registroAlertMsg');

// ── Mostrar / ocultar contraseña ─────────────────────────────
toggleBtn.addEventListener('click', () => {
  const isPassword = passwordEl.type === 'password';
  passwordEl.type = isPassword ? 'text' : 'password';
  eyeIcon.innerHTML = isPassword
    ? `<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
       <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
       <line x1="1" y1="1" x2="23" y2="23"/>`
    : `<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
       <circle cx="12" cy="12" r="3"/>`;
});

// ── Validación en tiempo real ────────────────────────────────
usernameEl.addEventListener('input', () => clearFieldError('username'));
emailEl.addEventListener('input',    () => clearFieldError('email'));
passwordEl.addEventListener('input', () => clearFieldError('password'));

function clearFieldError(fieldId) {
  const el  = document.getElementById(fieldId);
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

// ── Validación local ─────────────────────────────────────────
function validate() {
  let ok = true;

  const username = usernameEl.value.trim();
  if (!username) {
    showFieldError('username', 'El nombre de usuario es obligatorio.');
    ok = false;
  } else if (username.length < 3) {
    showFieldError('username', 'Mínimo 3 caracteres.');
    ok = false;
  } else if (!/^[a-zA-Z0-9_.]+$/.test(username)) {
    showFieldError('username', 'Solo letras, números, puntos y guiones bajos.');
    ok = false;
  }

  const email = emailEl.value.trim();
  if (!email) {
    showFieldError('email', 'El correo es obligatorio.');
    ok = false;
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showFieldError('email', 'Ingresa un correo válido.');
    ok = false;
  }

  if (!passwordEl.value) {
    showFieldError('password', 'La contraseña es obligatoria.');
    ok = false;
  } else if (passwordEl.value.length < 8) {
    showFieldError('password', 'Mínimo 8 caracteres.');
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
  registroAlertMsg.textContent = msg;
  registroAlert.hidden = false;
}

function hideAlert() {
  registroAlert.hidden = true;
  registroAlertMsg.textContent = '';
}

function showTigerAnimation() {
  const el = document.createElement('div');
  el.className = 'tiger-popup';
  el.innerHTML = `
    <div class="tiger-popup__bubble">
      <span class="tiger-popup__text">¡Nueva cuenta creada!</span>
    </div>
    <div class="tiger-popup__avatar">
      <img class="tiger-popup__img" src="/static/img/tigre.png" alt="Tigre" />
      <div class="tiger-popup__mouth"></div>
    </div>
  `;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add('tiger-popup--visible'));
  setTimeout(() => {
    el.classList.remove('tiger-popup--visible');
    setTimeout(() => el.remove(), 500);
  }, 2800);
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
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => toast.remove(), 2200);
}

// ── Envío del formulario ─────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hideAlert();

  if (!validate()) return;

  setLoading(true);

  // Construir payload
  const rol = document.querySelector('input[name="rol"]:checked').value;
  const payload = {
    username:         usernameEl.value.trim(),
    email:            emailEl.value.trim(),
    password:         passwordEl.value,
    rol,
    fecha_nacimiento: fechaEl.value ? `${fechaEl.value}T00:00:00` : null,
  };

  try {
    const response = await fetch(`${API_BASE}/auth/registro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      const msg = data.detail ?? 'No se pudo crear la cuenta.';
      showAlert(msg);
      return;
    }

    // Guardar tokens igual que en login
    localStorage.setItem('access_token',  data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('usuario',       JSON.stringify(data.usuario));

    showTigerAnimation();
    const destinos = {
      estudiante:      'dashboard_estudiante.html',
      profesor:        'dashboard_profesor.html',
      admin_contenido: 'dashboard_admin.html',
      admin_tech:      'dashboard_admin.html',
    };
    const destino = destinos[data.usuario.rol] ?? 'dashboard_estudiante.html';
    setTimeout(() => { window.location.href = destino; }, 3200);

  } catch (err) {
    showAlert('No se pudo conectar al servidor. Verifica que el backend esté activo.');
    console.error('[Registro]', err);
  } finally {
    setLoading(false);
  }
});
