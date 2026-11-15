'use strict';

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { createACaptcha } = require('./lib/acaptcha');

const PUBLIC_DIR = path.join(__dirname, 'public');
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
};

const captcha = createACaptcha({
  secret: process.env.ACAPTCHA_SECRET || undefined,
});

// Per-IP cap on new challenges, so the photo pipeline can't be used to burn CPU.
const RATE_LIMIT = 30;
const RATE_WINDOW_MS = 60 * 1000;
const hits = new Map();
setInterval(() => {
  const t = Date.now();
  for (const [ip, h] of hits) if (h.reset < t) hits.delete(ip);
}, RATE_WINDOW_MS).unref();

function rateLimited(ip) {
  const t = Date.now();
  const h = hits.get(ip);
  if (!h || h.reset < t) {
    hits.set(ip, { count: 1, reset: t + RATE_WINDOW_MS });
    return false;
  }
  return ++h.count > RATE_LIMIT;
}

function json(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > 128 * 1024) {
        reject(new Error('too large'));
        req.destroy();
      } else chunks.push(c);
    });
    req.on('end', () => {
      try {
        resolve(chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function serveStatic(req, res, pathname) {
  const rel = pathname === '/' ? 'index.html' : decodeURIComponent(pathname).replace(/^\/+/, '');
  const file = path.join(PUBLIC_DIR, rel);
  if (!file.startsWith(PUBLIC_DIR + path.sep)) return json(res, 403, { error: 'forbidden' });
  fs.readFile(file, (err, data) => {
    if (err) return json(res, 404, { error: 'not found' });
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const { pathname } = new URL(req.url, 'http://localhost');
  try {
    if (req.method === 'POST' && pathname === '/api/acaptcha/challenge') {
      if (rateLimited(req.socket.remoteAddress)) return json(res, 429, { error: 'rate_limited' });
      return json(res, 200, await captcha.issue());
    }
    if (req.method === 'POST' && pathname === '/api/acaptcha/solve') {
      return json(res, 200, captcha.solve(await readJson(req)));
    }
    // Demo of the protected action: your backend calls captcha.verify(token)
    // before doing the real work.
    if (req.method === 'POST' && pathname === '/api/demo/submit') {
      const body = await readJson(req);
      return json(res, 200, { success: captcha.verify(body.token) });
    }
    if (req.method === 'GET') return serveStatic(req, res, pathname);
    json(res, 405, { error: 'method not allowed' });
  } catch (e) {
    json(res, 400, { error: 'bad request' });
  }
});

if (require.main === module) {
  const port = Number(process.env.PORT) || 3000;
  server.listen(port, () => console.log(`ACaptcha demo: http://localhost:${port}`));
}

module.exports = { server, captcha };
