'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

// Logical (CSS px) geometry shared with the widget; images are rendered at 2x.
const W = 320;
const H = 180;
const PIECE = 56;
const SCALE = 2;

const rand = (min, max) => min + crypto.randomInt(max - min + 1);

function scopeSvg(d) {
  const c = d / 2;
  const r = c - 3;
  const tick = 14;
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${d}" height="${d}">
      <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="rgba(10,11,15,.55)" stroke-width="6"/>
      <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#fff" stroke-width="3.5"/>
      <g stroke="#fff" stroke-width="3.5" stroke-linecap="round">
        <path d="M${c} 3v${tick}M${c} ${d - 3}v-${tick}M3 ${c}h${tick}M${d - 3} ${c}h-${tick}"/>
      </g>
      <circle cx="${c}" cy="${c}" r="4.5" fill="#ff2d46"/>
    </svg>`
  );
}

function holeSvg(d) {
  const c = d / 2;
  const r = c - 3;
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${d}" height="${d}">
      <circle cx="${c}" cy="${c}" r="${r}" fill="rgba(9,10,14,.74)" stroke="rgba(255,255,255,.8)" stroke-width="3" stroke-dasharray="9 7"/>
      <circle cx="${c}" cy="${c}" r="4.5" fill="#ff2d46"/>
    </svg>`
  );
}

function maskSvg(d) {
  const c = d / 2;
  return Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${d}" height="${d}"><circle cx="${c}" cy="${c}" r="${c - 3}" fill="#fff"/></svg>`
  );
}

/**
 * Creates an ACaptcha instance. State lives in memory, so run one instance
 * per process (or put a shared store behind the same interface).
 */
function createACaptcha(options = {}) {
  const {
    photosDir = path.join(__dirname, '..', 'photos'),
    secret = crypto.randomBytes(32),
    tolerance = 5,
    challengeTtlMs = 2 * 60 * 1000,
    tokenTtlMs = 5 * 60 * 1000,
    minSolveMs = 350,
    now = Date.now,
  } = options;

  const photos = fs
    .readdirSync(photosDir)
    .filter((f) => /\.(jpe?g|png|webp)$/i.test(f))
    .map((f) => path.join(photosDir, f));
  if (!photos.length) throw new Error(`ACaptcha: no photos found in ${photosDir}`);

  const challenges = new Map();
  const usedTokens = new Map();

  const sweep = setInterval(() => {
    const t = now();
    for (const [id, c] of challenges) if (c.expires < t) challenges.delete(id);
    for (const [id, exp] of usedTokens) if (exp < t) usedTokens.delete(id);
  }, 30 * 1000);
  sweep.unref();

  const sign = (payload) => crypto.createHmac('sha256', secret).update(payload).digest('base64url');

  async function issue() {
    const file = photos[rand(0, photos.length - 1)];
    const meta = await sharp(file).metadata();

    // Random crop and colour jitter, so a challenge can't be solved by
    // diffing it against the known source photo.
    const ratio = W / H;
    const maxW = Math.min(meta.width, Math.floor(meta.height * ratio));
    const cropW = rand(Math.floor(maxW * 0.72), maxW);
    const cropH = Math.floor(cropW / ratio);
    const { data, info } = await sharp(file)
      .extract({
        left: rand(0, meta.width - cropW),
        top: rand(0, meta.height - cropH),
        width: cropW,
        height: cropH,
      })
      .resize(W * SCALE, H * SCALE)
      .modulate({ brightness: rand(92, 108) / 100, saturation: rand(90, 115) / 100, hue: rand(-10, 10) })
      .removeAlpha()
      .raw()
      .toBuffer({ resolveWithObject: true });
    const raw = { raw: { width: info.width, height: info.height, channels: info.channels } };

    const d = PIECE * SCALE;
    const x = rand(PIECE + 36, W - PIECE - 6);
    const y = rand(8, H - PIECE - 8);

    const [bg, piece] = await Promise.all([
      sharp(data, raw)
        .composite([{ input: holeSvg(d), left: x * SCALE, top: y * SCALE }])
        .webp({ quality: 80 })
        .toBuffer(),
      sharp(data, raw)
        .extract({ left: x * SCALE, top: y * SCALE, width: d, height: d })
        .ensureAlpha()
        .composite([{ input: maskSvg(d), blend: 'dest-in' }, { input: scopeSvg(d) }])
        .png()
        .toBuffer(),
    ]);

    const id = crypto.randomBytes(18).toString('base64url');
    const issued = now();
    challenges.set(id, { x, issued, expires: issued + challengeTtlMs });

    return {
      id,
      width: W,
      height: H,
      piece: PIECE,
      y,
      expiresIn: challengeTtlMs,
      background: `data:image/webp;base64,${bg.toString('base64')}`,
      pieceImage: `data:image/png;base64,${piece.toString('base64')}`,
    };
  }

  function looksAutomated(trail) {
    if (!Array.isArray(trail) || trail.length < 6 || trail.length > 2000) return true;
    let prevT = -1;
    for (const p of trail) {
      if (!Array.isArray(p) || p.length < 2 || !Number.isFinite(p[0]) || !Number.isFinite(p[1])) return true;
      if (p[0] < prevT) return true;
      prevT = p[0];
    }
    if (trail[trail.length - 1][0] - trail[0][0] < 200) return true;

    // A scripted drag typically moves at a perfectly constant speed.
    const speeds = [];
    for (let i = 1; i < trail.length; i++) {
      const dt = trail[i][0] - trail[i - 1][0];
      if (dt > 0) speeds.push((trail[i][1] - trail[i - 1][1]) / dt);
    }
    if (speeds.length < 4) return true;
    const mean = speeds.reduce((a, b) => a + b, 0) / speeds.length;
    const variance = speeds.reduce((a, b) => a + (b - mean) ** 2, 0) / speeds.length;
    return variance < 1e-6;
  }

  /** Checks an answer. Every challenge is single-use, pass or fail. */
  function solve({ id, x, trail } = {}) {
    const challenge = typeof id === 'string' ? challenges.get(id) : undefined;
    if (!challenge) return { ok: false, reason: 'expired' };
    challenges.delete(id);

    const t = now();
    if (challenge.expires < t) return { ok: false, reason: 'expired' };
    if (!Number.isFinite(x) || Math.abs(x - challenge.x) > tolerance) return { ok: false, reason: 'miss' };
    if (t - challenge.issued < minSolveMs || looksAutomated(trail)) return { ok: false, reason: 'suspicious' };

    const payload = `${crypto.randomBytes(12).toString('base64url')}.${t + tokenTtlMs}`;
    return { ok: true, token: `${payload}.${sign(payload)}`, expiresIn: tokenTtlMs };
  }

  /** Server-side check of a token from the widget. A token is valid once. */
  function verify(token) {
    if (typeof token !== 'string') return false;
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    const [nonce, exp, sig] = parts;
    const expected = Buffer.from(sign(`${nonce}.${exp}`));
    const given = Buffer.from(sig);
    if (given.length !== expected.length || !crypto.timingSafeEqual(given, expected)) return false;
    const expires = Number(exp);
    if (!Number.isFinite(expires) || expires < now() || usedTokens.has(nonce)) return false;
    usedTokens.set(nonce, expires);
    return true;
  }

  return { issue, solve, verify, _challenges: challenges };
}

module.exports = { createACaptcha, WIDTH: W, HEIGHT: H, PIECE };
