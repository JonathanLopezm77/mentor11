/**
 * Mentor 11 -- Minijuego de secuencia (pausa cada 5 preguntas en Arcade)
 * Dura 15s: cada secuencia acertada suma puntos y lanza una nueva ronda,
 * un poco mas larga, hasta que se acaba el tiempo.
 */

const MJ_DURACION_MS = 15000;

function esperar(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function iniciarMinijuegoSecuencia(onFinish, onPunto) {
  let ronda = 0;
  let terminado = false;

  const overlay = document.createElement('div');
  overlay.className = 'mj-overlay';
  overlay.innerHTML =
    '<div class="mj-panel">' +
    '<div class="mj-header">' +
    '<div class="mj-top">' +
    '<p class="mj-ronda" id="mjRonda">Ronda 1</p>' +
    '<p class="mj-timer" id="mjTimer">15s</p>' +
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

  const inicio = Date.now();
  timerFill.style.transition = `width ${MJ_DURACION_MS}ms linear`;
  requestAnimationFrame(() => { timerFill.style.width = '0%'; });
  const intervalId = setInterval(() => {
    const restante = Math.max(0, MJ_DURACION_MS - (Date.now() - inicio));
    timerLabel.textContent = Math.ceil(restante / 1000) + 's';
  }, 200);
  const finTimeoutId = setTimeout(terminar, MJ_DURACION_MS);

  function terminar() {
    if (terminado) return;
    terminado = true;
    clearInterval(intervalId);
    clearTimeout(finTimeoutId);
    overlay.classList.add('mj-overlay--saliendo');
    setTimeout(() => {
      overlay.remove();
      if (typeof onFinish === 'function') onFinish();
    }, 300);
  }

  function esperarEntrada(secuencia) {
    return new Promise((resolve) => {
      const entrada = [];
      function onClick(e) {
        if (terminado) { cleanup(); resolve('agotado'); return; }
        const idx = Number(e.currentTarget.dataset.idx);
        flash(idx, 'mj-tile--activa', 220);
        entrada.push(idx);
        const pos = entrada.length - 1;
        if (entrada[pos] !== secuencia[pos]) { cleanup(); resolve('incorrecta'); return; }
        if (entrada.length === secuencia.length) { cleanup(); resolve('correcta'); }
      }
      function cleanup() { tiles.forEach((t) => t.removeEventListener('click', onClick)); }
      tiles.forEach((t) => t.addEventListener('click', onClick));
    });
  }

  async function jugarRonda() {
    if (terminado) return;
    ronda++;
    rondaLabel.textContent = 'Ronda ' + ronda;
    const largo = ronda + 2;
    const secuencia = [];
    for (let i = 0; i < largo; i++) secuencia.push(Math.floor(Math.random() * 9));

    hint.textContent = 'Memoriza la secuencia...';
    await esperar(500);
    for (const idx of secuencia) {
      if (terminado) return;
      await flash(idx, 'mj-tile--lit', 420);
      await esperar(160);
    }
    if (terminado) return;
    hint.textContent = 'Tu turno: repite la secuencia';

    const resultado = await esperarEntrada(secuencia);
    if (terminado) return;

    if (resultado === 'correcta') {
      if (typeof onPunto === 'function') onPunto();
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
