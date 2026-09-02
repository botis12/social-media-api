'use strict';

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const { openDb } = require('./db');
const api = require('./api');

const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const MAX_BODY_BYTES = 64 * 1024;

const CONTENT_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
    'cache-control': 'no-store',
  });
  res.end(body);
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new api.ApiError(413, 'Το αίτημα είναι πολύ μεγάλο.'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8').trim();
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch {
        reject(new api.ApiError(400, 'Μη έγκυρο JSON.'));
      }
    });
    req.on('error', reject);
  });
}

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const relative = urlPath === '/' ? 'index.html' : urlPath.replace(/^\/+/, '');
  let filePath = path.join(PUBLIC_DIR, relative);

  // Άγνωστες διαδρομές (π.χ. /ABC123) σερβίρουν τη μία σελίδα της εφαρμογής.
  if (
    !filePath.startsWith(PUBLIC_DIR) ||
    !fs.existsSync(filePath) ||
    fs.statSync(filePath).isDirectory()
  ) {
    filePath = path.join(PUBLIC_DIR, 'index.html');
  }

  const body = fs.readFileSync(filePath);
  res.writeHead(200, {
    'content-type': CONTENT_TYPES[path.extname(filePath)] || 'application/octet-stream',
    'content-length': body.length,
    'cache-control': 'no-cache',
  });
  res.end(body);
}

function route(method, pathname, store) {
  const parts = pathname.split('/').filter(Boolean); // ['api', 'boards', code, ...]
  if (parts[0] !== 'api') return null;

  if (method === 'GET' && parts.length === 2 && parts[1] === 'health') return () => ({ ok: true });
  if (method === 'POST' && parts.length === 2 && parts[1] === 'boards') {
    return (body) => api.createBoard(store, body);
  }
  if (parts[1] !== 'boards' || parts.length < 3) return null;

  const code = parts[2];
  const section = parts[3];

  if (method === 'GET' && parts.length === 3) return () => api.getBoard(store, code);
  if (method === 'POST' && parts.length === 4) {
    if (section === 'people') return (body) => api.addPerson(store, code, body);
    if (section === 'tasks') return (body) => api.addTask(store, code, body);
    if (section === 'prefs') return (body) => api.setPref(store, code, body);
    if (section === 'rounds') return (body) => api.createRound(store, code, body);
  }
  if (method === 'DELETE' && parts.length === 5) {
    if (section === 'people') return () => api.removePerson(store, code, parts[4]);
    if (section === 'tasks') return () => api.removeTask(store, code, parts[4]);
    if (section === 'rounds') return () => api.deleteRound(store, code, parts[4]);
  }
  return null;
}

function createServer(store) {
  return http.createServer(async (req, res) => {
    const { pathname } = new URL(req.url, 'http://localhost');

    if (!pathname.startsWith('/api/')) {
      if (req.method !== 'GET' && req.method !== 'HEAD') {
        return sendJson(res, 405, { error: 'Method Not Allowed' });
      }
      try {
        return serveStatic(req, res);
      } catch {
        return sendJson(res, 500, { error: 'Σφάλμα διακομιστή.' });
      }
    }

    const handler = route(req.method, pathname, store);
    if (!handler) return sendJson(res, 404, { error: 'Άγνωστο endpoint.' });

    try {
      const body = req.method === 'POST' ? await readJsonBody(req) : {};
      return sendJson(res, 200, handler(body));
    } catch (err) {
      if (err instanceof api.ApiError) return sendJson(res, err.status, { error: err.message });
      console.error('[seira]', err);
      return sendJson(res, 500, { error: 'Κάτι πήγε στραβά. Δοκίμασε ξανά.' });
    }
  });
}

function start() {
  const port = Number(process.env.PORT) || 3000;
  const dbFile = process.env.DB_FILE || path.join(__dirname, '..', 'data', 'seira.db');
  const store = openDb(dbFile);
  const server = createServer(store);

  server.listen(port, () => {
    console.log(`Σειρά → http://localhost:${port}  (db: ${dbFile})`);
  });

  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.on(signal, () => {
      server.close(() => {
        store.close();
        process.exit(0);
      });
    });
  }

  return server;
}

if (require.main === module) start();

module.exports = { createServer, start };
