const API_BASE = "http://localhost:8000/api"; // Ajustá si usás otro puerto

async function getPlantas(token) {
  const res = await fetch(`${API_BASE}/plantas/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error("Error al obtener plantas");
  return await res.json();
}

async function crearPlanta(data, token) {
  const res = await fetch(`${API_BASE}/plantas/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Error al crear planta");
  return await res.json();
}

async function loginUsuario(username, password) {
  const res = await fetch("http://localhost:8000/api/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Credenciales inválidas");
  return await res.json(); // devuelve access y refresh
}

async function getPlantaById(id, token) {
  const res = await fetch(`${API_BASE}/plantas/${id}/`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error("Error al obtener detalle");
  return await res.json();
}

const TOKEN_KEY = "token";
const REFRESH_KEY = "refresh";

// Guarda tokens en localStorage
function guardarTokens(access, refresh) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

// Obtiene el token actual
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// Refresca el token usando el refresh
async function refrescarToken() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) throw new Error("No hay token de refresco");

  const res = await fetch("http://localhost:8000/api/auth/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) throw new Error("Token expirado o inválido");
  const data = await res.json();
  guardarTokens(data.access, refresh);
  return data.access;
}

// Valida el token actual, lo refresca si falla
async function obtenerTokenValido() {
  try {
    // Intentamos una llamada de prueba
    const res = await fetch(`${API_BASE}/plantas/`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });

    if (res.status === 401) {
      // Token expirado, intentamos refrescar
      const nuevoToken = await refrescarToken();
      return nuevoToken;
    }

    return getToken();
  } catch (err) {
    alert("Sesión expirada. Por favor, iniciá sesión nuevamente.");
    window.location.href = "/home/"; // Redirige al login
  }
}