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

const api = {
  // Usuarios
  getUsuarios: () => apiFetch("/usuarios"),
  getUsuarioPorQR: (codigo_qr) => apiFetch(`/usuarios/qr/${encodeURIComponent(codigo_qr)}`),
  createUsuario: (data) => apiFetch("/usuarios", { method: "POST", body: JSON.stringify(data) }),
  updateUsuario: (id, data) => apiFetch(`/usuarios/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteUsuario: (id) => apiFetch(`/usuarios/${id}`, { method: "DELETE" }),
  getQRImagenUsuario: (id) => `${BASE}/usuarios/${id}/qr/imagen`,
  getPDFCarnets: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return `${BASE}/usuarios/pdf-carnets` + (qs ? "?" + qs : "");
  },

  // Categorías
  getCategorias: () => apiFetch("/categorias"),
  createCategoria: (data) => apiFetch("/categorias", { method: "POST", body: JSON.stringify(data) }),
  deleteCategoria: (id) => apiFetch(`/categorias/${id}`, { method: "DELETE" }),

  // Material
  getMaterial: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch("/material" + (qs ? "?" + qs : ""));
  },
  getMaterialPorQR: (codigo_qr) => apiFetch(`/material/qr/${encodeURIComponent(codigo_qr)}`),
  createMaterial: (data) => apiFetch("/material", { method: "POST", body: JSON.stringify(data) }),
  updateMaterial: (id, data) => apiFetch(`/material/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteMaterial: (id) => apiFetch(`/material/${id}`, { method: "DELETE" }),
  getQRImage: (id) => `${BASE}/material/${id}/qr/imagen`,
  getPDFEtiquetas: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return `${BASE}/material/pdf-etiquetas` + (qs ? "?" + qs : "");
  },

  // Movimientos
  salida: (data) => apiFetch("/movimientos/salida", { method: "POST", body: JSON.stringify(data) }),
  entrada: (data) => apiFetch("/movimientos/entrada", { method: "POST", body: JSON.stringify(data) }),
  getActivos: () => apiFetch("/movimientos/activos"),
  getMovimientos: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch("/movimientos" + (qs ? "?" + qs : ""));
  },
};
