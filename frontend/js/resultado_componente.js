/**
 * Mentor 11 -- Componente reutilizable para pantallas de resultado
 * (Arcade y Online): avatar con carga segura + fila de jugador
 * (avatar, nombre, correctas, puntos). Usado por resultado_arcade.html
 * y por los overlays de fin de partida en pregunta_online.html.
 */

const RC = (() => {
  // Igual al patrón ya usado en online_intro.html/pregunta_online.html:
  // precarga la imagen y solo la muestra si carga bien, para no romper
  // el layout si el avatar (base64) llega corrupto o incompleto.
  function crearAvatar(src, inicial, tamano) {
    const cont = document.createElement('div');
    cont.className = 'rc-avatar' + (tamano ? ' rc-avatar--' + tamano : '');
    const ini = document.createElement('span');
    ini.className = 'rc-avatar__ini';
    ini.textContent = (inicial || '?').charAt(0).toUpperCase();
    cont.appendChild(ini);

    if (src && src.startsWith('data:image')) {
      const img = new Image();
      img.alt = 'Avatar';
      img.onload = () => { cont.insertBefore(img, ini); ini.hidden = true; };
      img.onerror = () => { }; // se queda con la inicial que ya estaba
      img.src = src;
    }
    return cont;
  }

  function truncarNombre(nombre, maxLen) {
    if (!nombre) return '';
    return nombre.length > maxLen ? nombre.slice(0, maxLen - 1) + '…' : nombre;
  }

  function crearPlayerRow({ avatarSrc, nombre, correctas, puntos, esGanador, nota }) {
    const row = document.createElement('div');
    row.className = 'rc-player-row' + (esGanador ? ' rc-player-row--winner' : '');

    row.appendChild(crearAvatar(avatarSrc, nombre, 'sm'));

    const info = document.createElement('div');
    info.className = 'rc-player-row__info';

    const nameEl = document.createElement('p');
    nameEl.className = 'rc-player-row__name';
    nameEl.textContent = truncarNombre(nombre || '—', 18);
    if (nombre) nameEl.title = nombre;
    info.appendChild(nameEl);

    const sub = document.createElement('p');
    sub.className = 'rc-player-row__sub';
    sub.textContent = nota || (correctas != null ? `${correctas} correctas` : '');
    info.appendChild(sub);

    row.appendChild(info);

    const puntosEl = document.createElement('span');
    puntosEl.className = 'rc-player-row__puntos';
    puntosEl.textContent = (puntos ?? 0) + ' pts';
    row.appendChild(puntosEl);

    if (esGanador) {
      const badge = document.createElement('span');
      badge.className = 'rc-player-row__crown';
      badge.textContent = '👑';
      row.appendChild(badge);
    }

    return row;
  }

  return { crearAvatar, crearPlayerRow, truncarNombre };
})();
