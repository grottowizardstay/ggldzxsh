'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createACaptcha, WIDTH, PIECE } = require('../lib/acaptcha');

// A drag with uneven speed, ending on `x`.
function humanTrail(x) {
  const trail = [];
  for (let i = 0; i <= 20; i++) {
    const p = i / 20;
    trail.push([i * 30 + (i % 3) * 4, Math.round(x * (1 - (1 - p) ** 2) * 10) / 10, 300]);
  }
  return trail;
}

function setup() {
  let clock = 1_000_000;
  const captcha = createACaptcha({ now: () => clock });
  return { captcha, advance: (ms) => (clock += ms) };
}

test('issues a photo challenge without leaking the answer', async () => {
  const { captcha } = setup();
  const c = await captcha.issue();
  assert.match(c.background, /^data:image\/webp;base64,/);
  assert.match(c.pieceImage, /^data:image\/png;base64,/);
  assert.equal(c.width, WIDTH);
  assert.equal(c.piece, PIECE);
  assert.equal('x' in c, false);
});

test('accepts a correct answer and issues a single-use token', async () => {
  const { captcha, advance } = setup();
  const c = await captcha.issue();
  const { x } = captcha._challenges.get(c.id);
  advance(1500);
  const res = captcha.solve({ id: c.id, x: x + 3, trail: humanTrail(x + 3) });
  assert.equal(res.ok, true);
  assert.equal(captcha.verify(res.token), true);
  assert.equal(captcha.verify(res.token), false);
});

test('rejects a miss and burns the challenge', async () => {
  const { captcha, advance } = setup();
  const c = await captcha.issue();
  const { x } = captcha._challenges.get(c.id);
  advance(1500);
  assert.deepEqual(captcha.solve({ id: c.id, x: x - 20, trail: humanTrail(x - 20) }), { ok: false, reason: 'miss' });
  assert.deepEqual(captcha.solve({ id: c.id, x, trail: humanTrail(x) }), { ok: false, reason: 'expired' });
});

test('rejects instant and constant-speed answers', async () => {
  const { captcha, advance } = setup();
  let c = await captcha.issue();
  let { x } = captcha._challenges.get(c.id);
  assert.equal(captcha.solve({ id: c.id, x, trail: humanTrail(x) }).reason, 'suspicious');

  c = await captcha.issue();
  ({ x } = captcha._challenges.get(c.id));
  advance(1500);
  const linear = Array.from({ length: 21 }, (_, i) => [i * 30, (x * i) / 20, 300]);
  assert.equal(captcha.solve({ id: c.id, x, trail: linear }).reason, 'suspicious');
});

test('rejects expired challenges and forged or expired tokens', async () => {
  const { captcha, advance } = setup();
  let c = await captcha.issue();
  let { x } = captcha._challenges.get(c.id);
  advance(3 * 60 * 1000);
  assert.equal(captcha.solve({ id: c.id, x, trail: humanTrail(x) }).reason, 'expired');

  c = await captcha.issue();
  ({ x } = captcha._challenges.get(c.id));
  advance(1500);
  const { token } = captcha.solve({ id: c.id, x, trail: humanTrail(x) });
  assert.equal(captcha.verify(token.slice(0, -2) + 'xx'), false);
  assert.equal(captcha.verify('a.b.c'), false);
  advance(6 * 60 * 1000);
  assert.equal(captcha.verify(token), false);
});
