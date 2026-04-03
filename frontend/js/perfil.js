/**
 * Mentor 11 — Perfil overlay
 * Agregar al final de dashboard_estudiante.js o en un <script> separado
 */

const API_BASE = '/api/v1';
const perfilOverlay = document.getElementById('perfilOverlay');
const perfilClose = document.getElementById('perfilClose');

// ── Sonidos (reutiliza los del dashboard) ─────────────────
function playPerfilSfx(src, vol = 0.6) {
    const a = new Audio(src);
    a.volume = vol;
    a.play().catch(() => { });
}

// ── Abrir / cerrar ────────────────────────────────────────
document.getElementById('profileBtn').addEventListener('click', () => {
    playPerfilSfx('/static/bop.mp3', 0.5);
    abrirPerfil();
});

perfilClose.addEventListener('click', () => {
    playPerfilSfx('/static/back.mp3', 0.5);
    perfilOverlay.classList.remove('open');
});

perfilOverlay.addEventListener('click', (e) => {
    if (e.target === perfilOverlay) perfilOverlay.classList.remove('open');
});

// ── Cerrar sesión ─────────────────────────────────────────
document.getElementById('perfilLogoutBtn').addEventListener('click', () => {
    playPerfilSfx('/static/back.mp3', 0.6);
    setTimeout(() => {
        localStorage.clear();
        window.location.href = '/';
    }, 350);
});

// ── Helpers ───────────────────────────────────────────────
function calcRango(puntos) {
    if (puntos < 500) return 'Novato';
    if (puntos < 1500) return 'Aprendiz';
    if (puntos < 3000) return 'Explorador';
    if (puntos < 6000) return 'Avanzado';
    if (puntos < 10000) return 'Experto';
    return 'Maestro';
}

function mostrarMsg(el, texto, tipo) {
    el.textContent = texto;
    el.className = `perfil-msg perfil-msg--${tipo}`;
    el.hidden = false;
    setTimeout(() => { el.hidden = true; }, 4000);
}

function animarNum(el, destino, ms = 700) {
    const t0 = performance.now();
    (function tick(now) {
        const t = Math.min((now - t0) / ms, 1);
        const e = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(e * destino);
        if (t < 1) requestAnimationFrame(tick);
    })(t0);
}

// ── Cargar datos del perfil ───────────────────────────────
async function abrirPerfil() {
    perfilOverlay.classList.add('open');

    try {
        const res = await fetch(`${API_BASE_PERFIL}/perfil/me`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();

        // Avatar
        const avatarSrc = data.avatar?.imagen_src || '/static/img/avatares/buho_n.png';
        document.getElementById('perfilAvatarImg').src = avatarSrc;

        // Nombre y rango
        document.getElementById('perfilUsername').textContent = data.username;
        document.getElementById('perfilRango').textContent = calcRango(data.puntos_totales);

        // Stats con animación
        animarNum(document.getElementById('perfilRachaActual'), data.racha_actual);
        animarNum(document.getElementById('perfilRachaMax'), data.racha_maxima);
        animarNum(document.getElementById('perfilPuntos'), data.puntos_totales);

        // Campos de edición
        document.getElementById('perfilInputUsername').value = data.username;
        document.getElementById('perfilInputEmail').value = data.email;
        if (data.fecha_nacimiento) {
            const fecha = new Date(data.fecha_nacimiento);
            document.getElementById('perfilInputFecha').value =
                fecha.toISOString().split('T')[0];
        }

    } catch (err) {
        console.error('[Perfil] Error al cargar:', err);
    }
}

// ── Guardar perfil ────────────────────────────────────────
document.getElementById('perfilSaveBtn').addEventListener('click', async () => {
    const btn = document.getElementById('perfilSaveBtn');
    const btnText = document.getElementById('perfilSaveBtnText');
    const msg = document.getElementById('perfilMsg');

    const username = document.getElementById('perfilInputUsername').value.trim();
    const email = document.getElementById('perfilInputEmail').value.trim();
    const fecha = document.getElementById('perfilInputFecha').value;

    if (!username || !email) {
        mostrarMsg(msg, 'El usuario y el correo no pueden estar vacíos.', 'error');
        return;
    }

    btn.disabled = true;
    btnText.textContent = 'Guardando...';

    try {
        const body = { username, email };
        if (fecha) body.fecha_nacimiento = new Date(fecha).toISOString();

        const res = await fetch(`${API_BASE_PERFIL}/perfil/me`, {
            method: 'PUT',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        const data = await res.json();

        if (!res.ok) {
            mostrarMsg(msg, data.detail || 'Error al guardar.', 'error');
            return;
        }

        // Actualizar datos en localStorage y en la UI
        const usuarioLocal = JSON.parse(localStorage.getItem('usuario') ?? '{}');
        usuarioLocal.username = data.username;
        usuarioLocal.email = data.email;
        localStorage.setItem('usuario', JSON.stringify(usuarioLocal));

        document.getElementById('perfilUsername').textContent = data.username;
        playPerfilSfx('/static/bop.mp3', 0.5);
        mostrarMsg(msg, '✓ Cambios guardados correctamente.', 'ok');

    } catch (_) {
        mostrarMsg(msg, 'Error de conexión.', 'error');
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Guardar cambios';
    }
});

// ── Cambiar contraseña ────────────────────────────────────
document.getElementById('perfilPassBtn').addEventListener('click', async () => {
    const btn = document.getElementById('perfilPassBtn');
    const btnText = document.getElementById('perfilPassBtnText');
    const msg = document.getElementById('perfilPassMsg');

    const actual = document.getElementById('perfilPassActual').value;
    const nueva = document.getElementById('perfilPassNueva').value;
    const confirma = document.getElementById('perfilPassConfirm').value;

    if (!actual || !nueva || !confirma) {
        mostrarMsg(msg, 'Completa todos los campos.', 'error');
        return;
    }

    if (nueva !== confirma) {
        mostrarMsg(msg, 'Las contraseñas nuevas no coinciden.', 'error');
        return;
    }

    if (nueva.length < 8) {
        mostrarMsg(msg, 'La contraseña debe tener al menos 8 caracteres.', 'error');
        return;
    }

    btn.disabled = true;
    btnText.textContent = 'Cambiando...';

    try {
        const res = await fetch(`${API_BASE_PERFIL}/perfil/me/password`, {
            method: 'PUT',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                password_actual: actual,
                password_nuevo: nueva,
                password_nuevo_confirmar: confirma,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            mostrarMsg(msg, data.detail || 'Error al cambiar contraseña.', 'error');
            return;
        }

        // Limpiar campos
        document.getElementById('perfilPassActual').value = '';
        document.getElementById('perfilPassNueva').value = '';
        document.getElementById('perfilPassConfirm').value = '';

        playPerfilSfx('/static/bop.mp3', 0.5);
        mostrarMsg(msg, '✓ Contraseña actualizada correctamente.', 'ok');

    } catch (_) {
        mostrarMsg(msg, 'Error de conexión.', 'error');
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Cambiar contraseña';
    }
});