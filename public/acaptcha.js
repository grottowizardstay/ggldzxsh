/* ACaptcha widget. Usage:
 *   ACaptcha.mount(element, { endpoint, lang, onSuccess(token), onReset() })
 * or declaratively: <div data-acaptcha></div> inside a <form> — the token is
 * written to a hidden "acaptcha-token" input.
 */
(function (global) {
  'use strict';

  const I18N = {
    ru: {
      prompt: 'Наведите прицел на метку:',
      reload: 'Другое фото',
      slider: 'Положение прицела',
      loading: 'Загрузка',
      ready: 'Ожидание',
      checking: 'Проверка',
      success: 'Пройдено',
      fail: 'Мимо',
      suspicious: 'Повторите',
      error: 'Ошибка',
      attempt: 'Попытка',
      time: 'Время',
      offset: 'Смещение',
      sec: 'с',
      retry: 'Нет связи с сервером',
      limited: 'Слишком много попыток',
    },
    en: {
      prompt: 'Lock the scope onto the mark:',
      reload: 'Another photo',
      slider: 'Scope position',
      loading: 'Loading',
      ready: 'Waiting',
      checking: 'Checking',
      success: 'Passed',
      fail: 'Missed',
      suspicious: 'Try again',
      error: 'Error',
      attempt: 'Attempt',
      time: 'Time',
      offset: 'Offset',
      sec: 's',
      retry: 'Server unreachable',
      limited: 'Too many attempts',
    },
  };

  const LOGO =
    '<svg class="acap__logo" viewBox="0 0 32 32" aria-hidden="true">' +
    '<circle cx="16" cy="16" r="10" fill="none" stroke="#fff" stroke-width="3.2"/>' +
    '<path d="M6 16A10 10 0 0 1 16 6" fill="none" stroke="#ff2d46" stroke-width="3.2"/>' +
    '<path d="M16 1v8M16 23v8M1 16h8M23 16h8" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/>' +
    '<circle cx="16" cy="16" r="2.6" fill="#ff2d46"/></svg>';
  const RELOAD =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M20 11a8 8 0 1 0-2.3 6.3"/><path d="M20 4v7h-7"/></svg>';

  function mount(root, options) {
    const opts = Object.assign({}, options);
    const endpoint = opts.endpoint || '/api/acaptcha';
    // Explicit option, then the page language, then the browser's.
    const hint = (opts.lang || document.documentElement.lang || navigator.language || '').toLowerCase().slice(0, 2);
    const lang = I18N[hint] ? hint : 'en';
    const t = I18N[lang];

    root.classList.add('acap');
    root.innerHTML =
      '<div class="acap__head">' + LOGO +
      '<span class="acap__name"><b>A</b>Captcha</span>' +
      '<button type="button" class="acap__reload" title="' + t.reload + '" aria-label="' + t.reload + '">' + RELOAD + '</button></div>' +
      '<div class="acap__prompt">' + t.prompt + '</div>' +
      '<div class="acap__stage"><img class="acap__bg" alt="" draggable="false"><img class="acap__piece" alt="" draggable="false"></div>' +
      '<div class="acap__slider" role="slider" tabindex="0" aria-label="' + t.slider + '" aria-valuemin="0" aria-valuenow="0">' +
      '<div class="acap__track"></div><div class="acap__fill"></div><div class="acap__thumb"></div></div>' +
      '<div class="acap__foot"><span class="acap__status" role="status"></span><span class="acap__meta"></span></div>';

    const $ = (s) => root.querySelector(s);
    const bg = $('.acap__bg');
    const piece = $('.acap__piece');
    const slider = $('.acap__slider');
    const fill = $('.acap__fill');
    const thumb = $('.acap__thumb');
    const status = $('.acap__status');
    const meta = $('.acap__meta');

    let challenge = null;
    let state = 'loading';
    let x = 0;
    let max = 1;
    let trail = [];
    let startedAt = 0;
    let dragging = false;
    let attempt = 0;
    let expiry = 0;
    let retryTimer = 0;

    function setState(next, label) {
      state = next;
      root.dataset.state = next;
      status.textContent = label || t[next] || '';
      slider.setAttribute('aria-disabled', String(next !== 'ready'));
    }

    function render() {
      const ratio = x / max;
      fill.style.width = ratio * 100 + '%';
      thumb.style.left = ratio * 100 + '%';
      slider.setAttribute('aria-valuenow', String(Math.round(x)));
      if (challenge) piece.style.left = (x / challenge.width) * 100 + '%';
    }

    function showMeta(extra) {
      meta.textContent = t.attempt + ': ' + attempt + (extra ? '  |  ' + extra : '');
    }

    async function post(path, body) {
      const res = await fetch(endpoint + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {}),
      });
      if (res.status === 429) throw new Error('limited');
      if (!res.ok) throw new Error('retry');
      return res.json();
    }

    async function load() {
      clearTimeout(expiry);
      clearTimeout(retryTimer);
      if (state === 'success' && opts.onReset) opts.onReset();
      challenge = null;
      x = 0;
      trail = [];
      setState('loading');
      render();
      try {
        const c = await post('/challenge');
        await Promise.all([c.background, c.pieceImage].map((src, i) => {
          const img = i ? piece : bg;
          img.src = src;
          return img.decode ? img.decode().catch(() => {}) : null;
        }));
        challenge = c;
        max = c.width - c.piece;
        slider.setAttribute('aria-valuemax', String(max));
        piece.style.width = (c.piece / c.width) * 100 + '%';
        piece.style.top = (c.y / c.height) * 100 + '%';
        attempt += 1;
        render();
        showMeta();
        setState('ready');
        expiry = setTimeout(load, Math.max(5000, c.expiresIn - 2000));
      } catch (e) {
        setState('error');
        meta.textContent = t[e.message] || t.retry;
      }
    }

    function record(e) {
      if (!startedAt) startedAt = performance.now();
      trail.push([Math.round(performance.now() - startedAt), Math.round(x * 10) / 10, e && e.clientY ? Math.round(e.clientY) : 0]);
    }

    function moveTo(next, e) {
      x = Math.min(max, Math.max(0, next));
      record(e);
      render();
      showMeta(t.offset + ': ' + Math.round(x) + ' px');
    }

    async function submit() {
      if (state !== 'ready' || !challenge || x === 0) return;
      const seconds = ((performance.now() - startedAt) / 1000).toFixed(1);
      setState('checking');
      try {
        const result = await post('/solve', { id: challenge.id, x: x, trail: trail });
        startedAt = 0;
        if (result.ok) {
          clearTimeout(expiry);
          setState('success');
          showMeta(t.time + ': ' + seconds + ' ' + t.sec);
          // The token expires server-side; ask again once it has.
          expiry = setTimeout(load, result.expiresIn);
          if (opts.onSuccess) opts.onSuccess(result.token);
        } else {
          setState('fail', result.reason === 'suspicious' ? t.suspicious : t.fail);
          retryTimer = setTimeout(load, 900);
        }
      } catch (e) {
        setState('error');
        meta.textContent = t[e.message] || t.retry;
      }
    }

    slider.addEventListener('pointerdown', (e) => {
      if (state !== 'ready' || (e.pointerType === 'mouse' && e.button !== 0)) return;
      dragging = true;
      slider.setPointerCapture(e.pointerId);
      // Grabbing must not jump the scope: the drag is relative to where it began.
      const rect = slider.getBoundingClientRect();
      const grabX = e.clientX;
      const startX = x;
      const onMove = (ev) => moveTo(startX + ((ev.clientX - grabX) / rect.width) * max, ev);
      const onUp = () => {
        dragging = false;
        slider.removeEventListener('pointermove', onMove);
        slider.removeEventListener('pointerup', onUp);
        slider.removeEventListener('pointercancel', onUp);
        submit();
      };
      slider.addEventListener('pointermove', onMove);
      slider.addEventListener('pointerup', onUp);
      slider.addEventListener('pointercancel', onUp);
      record(e);
    });

    slider.addEventListener('keydown', (e) => {
      if (state !== 'ready' || dragging) return;
      const step = e.shiftKey ? 10 : 2;
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp') moveTo(x + step);
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') moveTo(x - step);
      else if (e.key === 'Enter' || e.key === ' ') submit();
      else return;
      e.preventDefault();
    });

    $('.acap__reload').addEventListener('click', () => {
      if (state !== 'loading' && state !== 'checking') load();
    });

    load();
    return { reset: load, getState: () => state };
  }

  function autoMount() {
    document.querySelectorAll('[data-acaptcha]:not(.acap)').forEach((el) => {
      const form = el.closest('form');
      let input = null;
      if (form) {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'acaptcha-token';
        form.appendChild(input);
      }
      mount(el, {
        lang: el.dataset.lang,
        endpoint: el.dataset.endpoint || undefined,
        onSuccess: (token) => {
          if (input) input.value = token;
          el.dispatchEvent(new CustomEvent('acaptcha:success', { bubbles: true, detail: { token: token } }));
        },
        onReset: () => {
          if (input) input.value = '';
          el.dispatchEvent(new CustomEvent('acaptcha:reset', { bubbles: true }));
        },
      });
    });
  }

  global.ACaptcha = { mount: mount, autoMount: autoMount };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoMount);
  else autoMount();
})(window);
