/**
 * Mentor 11 -- Refresco automático de sesión (REL-01)
 *
 * El access_token dura 60 minutos y hasta ahora nunca se refrescaba: pasado
 * ese tiempo, cada fetch() empezaba a fallar con 401 y cada pantalla lo
 * mostraba como un "error de conexión" genérico, sin dar forma de arreglarlo
 * (crítico en el Simulacro, que dura 3 horas por bloque).
 *
 * Este script intercepta window.fetch una sola vez: si una llamada a la API
 * responde 401, intenta renovar el access_token con el refresh_token ya
 * guardado (dura 30 días) y reintenta esa misma petición una vez. Si el
 * refresh también falla, limpia la sesión y manda a iniciar sesión de nuevo.
 *
 * Debe cargarse ANTES que cualquier otro script de la página que use fetch().
 */
(function () {
  const _fetchOriginal = window.fetch.bind(window);
  let _refrescando = null; // promesa compartida: evita refrescar en paralelo

  async function _refrescarToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return null;
    try {
      const res = await _fetchOriginal('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        try {
          const datos = await res.clone().json();
          if (datos && typeof datos.detail === 'string' && datos.detail.includes('otro dispositivo')) {
            localStorage.clear();
            alert('Tu sesión fue cerrada porque iniciaste sesión en otro dispositivo.');
            location.href = '/index.html';
          }
        } catch (_) {}
        return null;
      }
      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return data.access_token;
    } catch (_) {
      return null;
    }
  }

  function _esLlamadaApiAutenticada(input) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    return url.includes('/api/v1/') && !url.includes('/api/v1/auth/');
  }

  function _irALogin() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    const yaEnLogin = location.pathname === '/' || location.pathname.endsWith('index.html');
    if (!yaEnLogin) location.href = '/index.html';
  }

  window.fetch = async function (input, init) {
    const res = await _fetchOriginal(input, init);

    if (res.status !== 401 || !_esLlamadaApiAutenticada(input)) return res;

    // Detectar sesión desplazada por otro dispositivo — no intentar refresh
    const resClonado = res.clone();
    try {
      const datos = await resClonado.json();
      if (datos && typeof datos.detail === 'string' && datos.detail.includes('otro dispositivo')) {
        localStorage.clear();
        alert('Tu sesión fue cerrada porque iniciaste sesión en otro dispositivo.');
        location.href = '/index.html';
        return res;
      }
    } catch (_) { /* la respuesta no era JSON, continuar con el flujo normal */ }

    if (!_refrescando) {
      _refrescando = _refrescarToken().finally(() => { _refrescando = null; });
    }
    const nuevoToken = await _refrescando;

    if (!nuevoToken) {
      _irALogin();
      return res;
    }

    // Reintenta la misma petición una sola vez con el token nuevo
    const initNuevo = Object.assign({}, init || {});
    if (initNuevo.headers) {
      const headers = new Headers(initNuevo.headers);
      if (headers.has('Authorization')) headers.set('Authorization', `Bearer ${nuevoToken}`);
      initNuevo.headers = headers;
    }
    return _fetchOriginal(input, initNuevo);
  };
})();
