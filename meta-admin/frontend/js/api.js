/**
 * api.js — Cliente HTTP para el meta-admin.
 * Gestiona el token JWT en sessionStorage y redirige a /login.html
 * automáticamente si la respuesta es 401.
 */

const BASE = '/api/v1';

// ── Token helpers ─────────────────────────────────────────────
function getToken()    { return sessionStorage.getItem('meta_token'); }
function setToken(t)   { sessionStorage.setItem('meta_token', t); }
function clearToken()  { sessionStorage.removeItem('meta_token'); }

// ── Fetch autenticado ────────────────────────────────────────
async function metaFetch(path, opts = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(BASE + path, { ...opts, headers });

  if (res.status === 401) {
    clearToken();
    location.href = '/login.html';
    return null;
  }
  return res;
}

// ── API pública ──────────────────────────────────────────────
const api = {

  /** Autenticación */
  async login(username, password) {
    return fetch(BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
  },

  /** Tenants */
  async getTenants()         { return metaFetch('/tenants'); },
  async getTenant(slug)      { return metaFetch(`/tenants/${slug}`); },
  async createTenant(data)   {
    return metaFetch('/tenants', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  async startTenant(slug)    { return metaFetch(`/tenants/${slug}/start`,  { method: 'POST' }); },
  async stopTenant(slug)     { return metaFetch(`/tenants/${slug}/stop`,   { method: 'POST' }); },
  async deleteTenant(slug)   { return metaFetch(`/tenants/${slug}`,        { method: 'DELETE' }); },

  /** Estadísticas */
  async getStats(slug)       { return metaFetch(`/tenants/${slug}/stats`); },
};
