// ✅ Login: obtiene tokens y los guarda en cookies httpOnly
export async function loginUsuario(username, password) {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include',  // 👈 IMPORTANTE: Envía y recibe cookies
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Usuario o contraseña incorrectos");
  }

  const data = await response.json();

  // Guardar solo username en localStorage (no es sensible)
  if (data.username) {
    localStorage.setItem("username", data.username);
  } else {
    localStorage.setItem("username", username);
  }

  return data;
}

// ✅ Refresh: renueva el access token (automático vía cookies)
export async function refreshToken() {
  const response = await fetch("/api/auth/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: 'include'  // 👈 Envía refresh_token cookie
  });

  if (!response.ok) {
    throw new Error("No se pudo refrescar el token");
  }

  // Las cookies se actualizan automáticamente
  return true;
}

// ✅ Verificar si el usuario está autenticado
export async function estaAutenticado() {
  // Intentar hacer un request simple para verificar autenticación
  try {
    const response = await fetch('/api/configuracion-usuario/', {
      credentials: 'include'
    });
    // Si es 200, está autenticado. Si es 401, no está autenticado.
    // Ambos casos son normales, no son errores.
    return response.ok;
  } catch {
    // Error de red u otro problema
    return false;
  }
}

// ✅ Logout: limpia cookies y localStorage
export async function logoutUsuario() {
  try {
    await fetch('/api/auth/logout/', {
      method: 'POST',
      credentials: 'include'
    });
  } catch (error) {
    console.warn('Error en logout:', error);
  } finally {
    // Limpiar localStorage
    localStorage.removeItem("username");

    // Redirigir a login
    window.location.href = "/";
  }
}

// ✅ Fetch con autenticación automática y refresh
export async function fetchProtegido(url, options = {}) {
  let response = await fetch(url, {
    ...options,
    credentials: 'include',  // 👈 Envía cookies automáticamente
    headers: {
      ...options.headers,
    }
  });

  // Si recibimos 401, intentar refresh
  if (response.status === 401) {
    try {
      await refreshToken();

      // Reintentar request original
      response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
          ...options.headers,
        }
      });
    } catch (error) {
      // Si refresh falla, solo redirigir si NO estamos en páginas públicas
      const publicPages = ['/', '/login/', '/register/', '/privacy/', '/terms/'];
      const currentPath = window.location.pathname;

      if (!publicPages.includes(currentPath)) {
        console.error('Sesión expirada');
        window.location.href = '/';
      }
      // En páginas públicas, simplemente devolver el response 401 original
      return response;
    }
  }

  return response;
}

// ⚠️ DEPRECATED - Mantener por compatibilidad temporal
export async function obtenerTokenValido() {
  console.warn('obtenerTokenValido() está deprecated - usar fetchProtegido()');
  return null;
}
