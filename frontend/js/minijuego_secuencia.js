/**
 * Mentor 11 -- Minijuego de secuencia (pausa cada 2 preguntas en Arcade)
 * Dura 20s: cada secuencia acertada suma puntos y lanza una nueva ronda,
 * un poco mas larga, hasta que se acaba el tiempo. El reloj corre siempre,
 * incluso mientras se muestra la secuencia.
 */

const MJ_DURACION_MS = 20000;
const MJ_MUESTRA_MS = 800;

function esperar(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function iniciarMinijuegoSecuencia(onFinish, onPunto, onMemorizarInicio, onMemorizarFin) {
  let ronda = 0;
  let terminado = false;

  const overlay = document.createElement('div');
  overlay.className = 'mj-overlay';
  overlay.innerHTML =
    '<div class="mj-panel">' +
    '<div class="mj-header">' +
    '<div class="mj-top">' +
    '<p class="mj-ronda" id="mjRonda">Ronda 1</p>' +
    '<p class="mj-timer" id="mjTimer">20s</p>' +
    '</div>' +
    '<div class="mj-timerbar"><div class="mj-timerbar__fill" id="mjTimerFill"></div></div>' +
    '</div>' +
    '<div class="mj-grid" id="mjGrid"></div>' +
    '<p class="mj-hint" id="mjHint">Memoriza la secuencia...</p>' +
    '</div>';
  document.body.appendChild(overlay);

  const grid = overlay.querySelector('#mjGrid');
  const hint = overlay.querySelector('#mjHint');
  const rondaLabel = overlay.querySelector('#mjRonda');
  const timerLabel = overlay.querySelector('#mjTimer');
  const timerFill = overlay.querySelector('#mjTimerFill');

  const tiles = [];
  for (let i = 0; i < 9; i++) {
    const t = document.createElement('button');
    t.type = 'button';
    t.className = 'mj-tile';
    t.dataset.idx = i;
    grid.appendChild(t);
    tiles.push(t);
  }

  function flash(idx, cls, dur) {
    return new Promise((resolve) => {
      tiles[idx].classList.add(cls);
      setTimeout(() => { tiles[idx].classList.remove(cls); resolve(); }, dur);
    });
  }

  function mostrarSecuenciaCompleta(secuencia) {
    secuencia.forEach((idx) => tiles[idx].classList.add('mj-tile--lit'));
  }

  function ocultarSecuenciaCompleta() {
    tiles.forEach((t) => t.classList.remove('mj-tile--lit'));
  }

  let restante = MJ_DURACION_MS;
  let ultimoTick = Date.now();
  const intervalId = setInterval(() => {
    const ahora = Date.now();
    const delta = ahora - ultimoTick;
    ultimoTick = ahora;
    restante = Math.max(0, restante - delta);
    timerLabel.textContent = Math.ceil(restante / 1000) + 's';
    timerFill.style.width = (restante / MJ_DURACION_MS * 100) + '%';
    if (restante <= 0) terminar();
  }, 100);

  function terminar() {
    if (terminado) return;
    terminado = true;
    clearInterval(intervalId);
    overlay.classList.add('mj-overlay--saliendo');
    setTimeout(() => {
      overlay.remove();
      if (typeof onFinish === 'function') onFinish();
    }, 300);
  }

  function esperarEntrada(secuencia) {
    return new Promise((resolve) => {
      const objetivo = new Set(secuencia);
      function onClick(e) {
        if (terminado) { cleanup(); resolve('agotado'); return; }
        const idx = Number(e.currentTarget.dataset.idx);
        if (!objetivo.has(idx)) { cleanup(); resolve('incorrecta'); return; }
        objetivo.delete(idx);
        flash(idx, 'mj-tile--activa', 220);
        if (objetivo.size === 0) { cleanup(); resolve('correcta'); }
      }
      function cleanup() { tiles.forEach((t) => t.removeEventListener('click', onClick)); }
      tiles.forEach((t) => t.addEventListener('click', onClick));
    });
  }

  async function jugarRonda() {
    if (terminado) return;
    ronda++;
    rondaLabel.textContent = 'Ronda ' + ronda;
    const largo = Math.min(ronda + 2, 9);
    const disponibles = [0, 1, 2, 3, 4, 5, 6, 7, 8];
    const secuencia = [];
    for (let i = 0; i < largo; i++) {
      const pick = disponibles.splice(Math.floor(Math.random() * disponibles.length), 1)[0];
      secuencia.push(pick);
    }

    hint.textContent = 'Memoriza la secuencia...';
    await esperar(400);
    if (terminado) return;
    if (typeof onMemorizarInicio === 'function') onMemorizarInicio();
    mostrarSecuenciaCompleta(secuencia);
    await esperar(MJ_MUESTRA_MS);
    ocultarSecuenciaCompleta();
    if (typeof onMemorizarFin === 'function') onMemorizarFin();
    if (terminado) return;
    hint.textContent = 'Tu turno: toca las casillas que se iluminaron';

    const resultado = await esperarEntrada(secuencia);
    if (terminado) return;

    if (resultado === 'correcta') {
      if (typeof onPunto === 'function') onPunto(ronda);
      hint.textContent = '+2 puntos. Siguiente secuencia...';
      tiles.forEach((t) => t.classList.add('mj-tile--exito'));
      await esperar(450);
    } else if (resultado === 'incorrecta') {
      hint.textContent = 'Casi... otra secuencia';
      tiles.forEach((t) => t.classList.add('mj-tile--error'));
      await esperar(450);
    }
    tiles.forEach((t) => t.classList.remove('mj-tile--exito', 'mj-tile--error'));

    if (!terminado) jugarRonda();
  }

  jugarRonda();
}
