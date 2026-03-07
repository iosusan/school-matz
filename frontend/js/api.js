const BASE = "/api/v1";

async function apiFetch(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Error desconocido");
  }
  if (res.status === 204) return null;
  return res.json();
}

// Fetch that includes the admin Bearer token. On 401, clears the token
// and calls window._onAuthExpired() if defined (set by admin.html).
async function adminFetch(path, options = {}) {
  const token = sessionStorage.getItem("admin_token");
  const res = await fetch(BASE + path, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (res.status === 401) {
    sessionStorage.removeItem("admin_token");
    if (typeof window._onAuthExpired === "function") window._onAuthExpired();
    throw new Error("Sesión expirada. Por favor, vuelve a iniciar sesión.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Error desconocido");
  }
  if (res.status === 204) return null;
  return res.json();
}

const api = {
  // ── Auth ─────────────────────────────────────────────────────────────────
  login: (username, password) =>
    apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  me: () => adminFetch("/auth/me"),

  // ── Usuarios ─────────────────────────────────────────────────────────────
  getUsuarios: () => apiFetch("/usuarios"),
  getUsuarioPorQR: (codigo_qr) => apiFetch(`/usuarios/qr/${encodeURIComponent(codigo_qr)}`),
  createUsuario: (data) => adminFetch("/usuarios", { method: "POST", body: JSON.stringify(data) }),
  updateUsuario: (id, data) => adminFetch(`/usuarios/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteUsuario: (id) => adminFetch(`/usuarios/${id}`, { method: "DELETE" }),
  getQRImagenUsuario: (id) => `${BASE}/usuarios/${id}/qr/imagen`,
  getPDFCarnets: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return `${BASE}/usuarios/pdf-carnets` + (qs ? "?" + qs : "");
  },

  // ── Categorías ───────────────────────────────────────────────────────────
  getCategorias: () => apiFetch("/categorias"),
  createCategoria: (data) => adminFetch("/categorias", { method: "POST", body: JSON.stringify(data) }),
  deleteCategoria: (id) => adminFetch(`/categorias/${id}`, { method: "DELETE" }),

  // ── Material ─────────────────────────────────────────────────────────────
  getMaterial: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch("/material" + (qs ? "?" + qs : ""));
  },
  getMaterialPorQR: (codigo_qr) => apiFetch(`/material/qr/${encodeURIComponent(codigo_qr)}`),
  createMaterial: (data) => adminFetch("/material", { method: "POST", body: JSON.stringify(data) }),
  updateMaterial: (id, data) => adminFetch(`/material/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteMaterial: (id) => adminFetch(`/material/${id}`, { method: "DELETE" }),
  getQRImage: (id) => `${BASE}/material/${id}/qr/imagen`,
  getPDFEtiquetas: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return `${BASE}/material/pdf-etiquetas` + (qs ? "?" + qs : "");
  },

  // ── Movimientos ──────────────────────────────────────────────────────────
  salida: (data) => apiFetch("/movimientos/salida", { method: "POST", body: JSON.stringify(data) }),
  entrada: (data) => apiFetch("/movimientos/entrada", { method: "POST", body: JSON.stringify(data) }),
  getActivos: () => apiFetch("/movimientos/activos"),
  getMovimientos: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch("/movimientos" + (qs ? "?" + qs : ""));
  },
};
