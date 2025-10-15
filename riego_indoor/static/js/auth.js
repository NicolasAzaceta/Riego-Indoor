// ✅ Login: obtiene access y refresh
export async function loginUsuario(username, password) {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) throw new Error("Usuario o contraseña incorrectos");

  const data = await response.json();
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  return data;
}

// ✅ Refresh: renueva el access token
export async function refreshToken() {
  const refresh = localStorage.getItem("refresh");

  const response = await fetch("/api/auth/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh })
  });

  if (!response.ok) throw new Error("No se pudo refrescar el token");

  const data = await response.json();
  localStorage.setItem("access", data.access);
  return data.access;
}



// ✅ Devuelve un access token válido
export async function obtenerTokenValido() {
  const access = localStorage.getItem("access");
  const refresh = localStorage.getItem("refresh");

  if (!access || !refresh) {
    console.warn("No hay tokens disponibles");
    window.location.href = "/login/";
    return null;
  }

  return access; // devolvemos el access sin verificar
}

// ✅ Logout: limpia tokens y redirige
export function logoutUsuario() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  window.location.href = "/login/";
}

// ✅ Fetch con token: realiza peticiones autenticadas
export async function fetchProtegido(url, options = {}) {
  let token = localStorage.getItem("access");
  const refresh = localStorage.getItem("refresh");

  // Si no hay tokens, no tiene sentido continuar. Redirigir al login.
  if (!token || !refresh) {
    logoutUsuario();
    return new Response(null, { status: 401, statusText: "No hay tokens, cerrando sesión." });
  }

  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    token = await refreshToken();
    response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`
      }
    });
  }

  return response;
}
