import { fetchProtegido, logoutUsuario as authLogout } from './auth.js';

export function logoutUsuario() {
  // Centralizamos la lógica de logout para asegurar que siempre redirija a la página de bienvenida.
  // Ya no borramos la temperatura aquí, se asocia al usuario.
  authLogout();
  window.location.href = "/";
}

export function mostrarToast(mensaje, tipo = "success") {
  const toastBody = document.getElementById("toast-body");
  const toast = document.getElementById("toast");

  toastBody.textContent = mensaje;
  toast.classList.remove("bg-success", "bg-danger", "bg-warning", "bg-violeta");

  const claseBg = (tipo === "success" || tipo === "info") ? "bg-violeta" : `bg-${tipo}`;
  toast.classList.add(claseBg);

  // Inicializar y mostrar el toast
  const bsToast = new bootstrap.Toast(toast, { delay: 2000 });
  bsToast.show();

}

export function iniciarVinculacionGoogle() {
  // Simplemente redirigimos al usuario a la vista de inicio de autenticación del backend.
  // El backend se encargará de todo el flujo de OAuth.
  // Para que esto funcione, necesitamos una forma de pasar el token JWT en la URL.
  const token = localStorage.getItem("access");

  if (!token) {
    alert("No se encontró el token de autenticación. Por favor, inicie sesión de nuevo.");
    // Opcionalmente, podrías redirigir al login:
    // window.location.href = "/home/"; 
    return;
  }

  window.location.href = `/google-calendar/auth/?jwt=${token}`;
}

export async function checkGoogleCalendarStatus() {
  try {
    const res = await fetchProtegido('/api/google-calendar-status/');
    if (!res.ok) {
      console.error('Error al verificar el estado de Google Calendar');
      return;
    }
    const data = await res.json();
    updateGoogleCalendarButton(data.is_linked);
  } catch (error) {
    console.error('Fallo de conexión al verificar estado de Google Calendar:', error);
  }
}

function updateGoogleCalendarButton(isLinked) {
  const btnGoogleCalendar = document.getElementById("btnGoogleCalendar");
  const btnGoogleCalendarMobile = document.getElementById("google-calendar-container-mobile");
  const googleCalendarLinked = document.getElementById("googleCalendarLinked");

  if (!btnGoogleCalendar || !googleCalendarLinked || !btnGoogleCalendarMobile) return;

  if (isLinked) {
    // Ocultar el botón de "Vincular" y mostrar el menú de "Vinculado"
    btnGoogleCalendar.classList.add('d-none');
    googleCalendarLinked.classList.remove('d-none');
    // Clonamos el menú de "Vinculado" para el móvil
    // NO clonamos el dropdown anidado. Creamos un botón simple para desvincular.
    btnGoogleCalendarMobile.innerHTML = `
      <a href="#" class="btn btn-rojo-outline w-100 btn-google-disconnect">
        <i class="bi bi-calendar-x me-2"></i>Desvincular Calendario
      </a>
    `;
  } else {
    // Mostrar el botón de "Vincular" y ocultar el menú de "Vinculado"
    btnGoogleCalendar.classList.remove('d-none');
    googleCalendarLinked.classList.add('d-none');
    // Clonamos el botón de "Vincular" para el móvil
    const mobileLinkButton = btnGoogleCalendar.cloneNode(true);
    mobileLinkButton.id = 'btnGoogleCalendarMobile'; // Cambiamos el ID para evitar duplicados
    mobileLinkButton.classList.add('w-100'); // Hacemos que ocupe todo el ancho
    btnGoogleCalendarMobile.innerHTML = '';
    btnGoogleCalendarMobile.appendChild(mobileLinkButton);
  }
}

function getTemperaturaKey() {
  const username = localStorage.getItem('username');
  if (!username) return null;
  return `temperaturaManual_${username}`;
}

function getClimaKey() {
  const username = localStorage.getItem('username');
  if (!username) return null;
  return `climaGuardado_${username}`;
}

function actualizarDisplayTemperaturaExterna(data) {
  const containerDesktop = document.getElementById('temp-externa-container');
  const containerMobile = document.getElementById('temp-externa-container-mobile');

  [containerDesktop, containerMobile].forEach(container => {
    // Limpiamos el contenedor
    container.innerHTML = '';

    if (!data) {
      return;
    }

    let displayHTML = '';
    let keyToRemove = '';
    let toastMessage = '';

    if (data.type === 'manual') {
      displayHTML = `
      <button type="button" class="btn btn-violeta-solid" disabled style="opacity: 1;">
          <i class="bi bi-thermometer-half me-1"></i>
          ${data.value}°C (Manual)
      </button>
    `;
      keyToRemove = getTemperaturaKey();
      toastMessage = "Temperatura manual desactivada. Recargando...";
    } else if (data.type === 'clima') {
      displayHTML = `
      <button type="button" class="btn btn-violeta-solid" disabled style="opacity: 1;">
          <i class="bi bi-cloud-sun me-1"></i>
          ${data.value.toFixed(1)}°C (${data.location})
      </button>
    `;
      keyToRemove = getClimaKey();
      toastMessage = "Clima guardado desactivado. Recargando...";
    }

    const tempDisplay = document.createElement('div');
    tempDisplay.className = 'btn-group';
    tempDisplay.innerHTML = displayHTML + `
      <button type="button" class="btn btn-violeta-outline btn-quitar-temp" title="Dejar de usar temperatura manual">
          <i class="bi bi-x-lg"></i>
      </button>
  `;
    container.appendChild(tempDisplay);

    // Agregamos el listener a todos los botones de quitar temperatura
    container.querySelectorAll('.btn-quitar-temp').forEach(btn => btn.addEventListener('click', () => {
      if (keyToRemove) localStorage.removeItem(keyToRemove);
      actualizarDisplayTemperaturaExterna(null);
      mostrarToast(toastMessage, "info");
      setTimeout(() => window.location.reload(), 1500);
    }));
  });
}

// Cargar localidad outdoor guardada
async function cargarLocalidadOutdoor() {
  try {
    const res = await fetchProtegido("/api/localidad-outdoor/");
    if (res.ok) {
      const data = await res.json();
      const inputLocalidad = document.getElementById("inputLocalidad");
      if (inputLocalidad && data.nombre_localidad) {
        inputLocalidad.value = data.nombre_localidad;
        inputLocalidad.placeholder = `Guardado: ${data.nombre_localidad}`;
      }
    }
  } catch (error) {
    // Es normal que no haya localidad guardada
    console.log("No hay localidad outdoor configurada (es normal si no se usó antes)");
  }
}

async function recalcularTodasLasPlantas(temperatura, sufijo = '') {
  const plantCards = document.querySelectorAll('#plant-list .card');
  for (const card of plantCards) {
    const plantId = card.querySelector('[data-id]').dataset.id;
    try {
      const recalcUrl = `/api/plantas/${plantId}/recalcular/?temperatura=${temperatura}`;
      const recalcRes = await fetchProtegido(recalcUrl);
      if (!recalcRes.ok) continue;

      const nuevosDatos = await recalcRes.json();
      const textoRiego = card.querySelector('.card-text');
      if (textoRiego) {
        textoRiego.innerHTML = `🌱 <strong>${nuevosDatos.estado_texto}</strong>${sufijo}`;
      }
    } catch (error) {
      console.warn(`No se pudo recalcular la planta ${plantId}:`, error);
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.getElementById("main-content");

  // Inicializar todos los tooltips de la página.
  [...document.querySelectorAll('[data-bs-toggle="tooltip"]')].forEach(el => new bootstrap.Tooltip(el));

  if (sidebarToggle && sidebar && mainContent) {
    const toggleIcon = sidebarToggle.querySelector("i");
    const sidebarTooltip = bootstrap.Tooltip.getInstance(sidebarToggle);

    // Lógica de estado inicial del sidebar:
    // - En pantallas grandes (desktop), empieza expandido.
    // - En pantallas pequeñas (móvil), empieza colapsado.
    if (window.innerWidth < 992) {
      sidebar.classList.add("collapsed");
    } else {
      sidebar.classList.remove("collapsed");
    }

    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      mainContent.classList.toggle("expanded");

      // Cambiar ícono y tooltip
      if (sidebar.classList.contains("collapsed")) {
        toggleIcon.className = "bi bi-chevron-double-right";
        sidebarTooltip.setContent({ '.tooltip-inner': 'Expandir' });
      } else {
        toggleIcon.className = "bi bi-chevron-double-left";
        sidebarTooltip.setContent({ '.tooltip-inner': 'Contraer' });
      }

      // Ocultamos el tooltip inmediatamente después del clic para que no se quede "pegado".
      sidebarTooltip.hide();
    });
  }


  const btnLogout = document.getElementById("btnLogout");
  const btnLogoutMobile = document.getElementById("btnLogoutMobile");

  const handleLogout = (e) => {
    e.preventDefault();
    mostrarToast("👋 ¡Sesión cerrada! ¡Hasta luego!", "info");
    setTimeout(() => logoutUsuario(), 1500);
  };

  if (btnLogout) {
    btnLogout.addEventListener("click", handleLogout);
  }
  if (btnLogoutMobile) {
    btnLogoutMobile.addEventListener("click", handleLogout);
  }

  // Re-asignar listeners a los elementos clonados
  document.body.addEventListener('click', function (e) {
    if (e.target && (e.target.id === 'btnGoogleCalendarMobile' || e.target.closest('#btnGoogleCalendarMobile'))) {
      e.preventDefault();
      iniciarVinculacionGoogle();
    }
    // Usamos delegación de eventos con una clase para que funcione en desktop y móvil
    if (e.target.classList.contains('btn-google-disconnect') || e.target.closest('.btn-google-disconnect')) {
      e.preventDefault();
      const modal = new bootstrap.Modal(document.getElementById("modalConfirmarDesvincular"));
      modal.show();
    }
  });

  const btnGoogleCalendar = document.getElementById("btnGoogleCalendar");
  if (btnGoogleCalendar) {
    btnGoogleCalendar.addEventListener("click", (e) => {
      e.preventDefault();
      iniciarVinculacionGoogle();
    });
  }

  async function desvincularGoogleCalendar(btn, modal) {
    // 1. Deshabilitar botón y mostrar estado de carga
    btn.disabled = true;
    btn.innerHTML = `
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      Desvinculando...
    `;

    try {
      const res = await fetchProtegido('/api/google-calendar-disconnect/', { method: 'POST' });
      if (!res.ok) throw new Error('Error en el servidor');
      const data = await res.json();
      mostrarToast(`✅ ${data.message}`, "success");
      setTimeout(() => window.location.reload(), 1500); // Recargamos para refrescar el estado
    } catch (error) {
      mostrarToast("❌ No se pudo desvincular el calendario.", "danger");
    } finally {
      // 2. Ocultar el modal
      modal.hide();
      // 3. Restaurar el botón a su estado original (incluso si hay un error)
      setTimeout(() => { // Damos un pequeño delay para que el modal se cierre suavemente
        btn.disabled = false;
        btn.innerHTML = 'Desvincular';
      }, 500);
    }
  }

  const btnConfirmar = document.getElementById("btnConfirmarDesvincular");
  if (btnConfirmar) {
    btnConfirmar.addEventListener("click", (e) => {
      const modalInstance = bootstrap.Modal.getInstance(document.getElementById("modalConfirmarDesvincular"));
      desvincularGoogleCalendar(btnConfirmar, modalInstance);
    });
  }

  // Al cargar la página, revisamos si hay una temperatura (manual o de clima) guardada
  const tempKey = getTemperaturaKey();
  const temperaturaGuardada = tempKey ? localStorage.getItem(tempKey) : null;
  const climaKey = getClimaKey();
  const climaGuardado = climaKey ? localStorage.getItem(climaKey) : null;

  if (temperaturaGuardada) {
    actualizarDisplayTemperaturaExterna({ type: 'manual', value: temperaturaGuardada });
  } else if (climaGuardado) {
    actualizarDisplayTemperaturaExterna(JSON.parse(climaGuardado));
  }

  // Verificamos el estado de la vinculación al cargar la página.
  checkGoogleCalendarStatus();

  const btnRecalcularTemp = document.getElementById("btnRecalcularTemp");
  if (btnRecalcularTemp) {
    btnRecalcularTemp.addEventListener("click", async () => {
      const inputTemperatura = document.getElementById("inputTemperatura");
      const temperatura = inputTemperatura.value.trim();

      if (!temperatura) {
        mostrarToast("Por favor, ingresá una temperatura.", "warning");
        return;
      }

      // Guardamos en localStorage, limpiamos el otro valor y actualizamos el display
      const tempKey = getTemperaturaKey();
      const climaKey = getClimaKey();

      if (tempKey) localStorage.setItem(tempKey, temperatura);
      if (climaKey) localStorage.removeItem(climaKey);

      actualizarDisplayTemperaturaExterna({ type: 'manual', value: temperatura });
      mostrarToast(`Usando ${temperatura}°C para recalcular riegos...`, "info");
      recalcularTodasLasPlantas(temperatura);
    });
  }

  // ========== OUTDOOR: Guardar localidad y recalcular con clima real ==========
  const btnRecalcularClima = document.getElementById("btnRecalcularClima");
  const inputLocalidad = document.getElementById("inputLocalidad");

  if (btnRecalcularClima && inputLocalidad) {
    // Cargar localidad guardada al iniciar
    cargarLocalidadOutdoor();

    btnRecalcularClima.addEventListener("click", async () => {
      const localidad = inputLocalidad.value.trim();
      if (!localidad) {
        mostrarToast("❌ Por favor, ingresá una localidad", "error");
        return;
      }

      btnRecalcularClima.disabled = true;
      btnRecalcularClima.textContent = "Recalculando...";

      try {
        // 1. Guardar localidad usando Google Places Geocoding
        const geocodeRes = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(localidad)}&key=${window.GOOGLE_MAPS_API_KEY}`);
        const geocode = await geocodeRes.json();

        if (!geocode.results || geocode.results.length === 0) {
          mostrarToast("❌ No se encontró la localidad", "error");
          return;
        }

        const location = geocode.results[0].geometry.location;
        const nombreCompleto = geocode.results[0].formatted_address;

        // 2. Guardar localidad en backend
        const saveRes = await fetchProtegido("/api/localidad-outdoor/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nombre_localidad: nombreCompleto,
            latitud: location.lat,
            longitud: location.lng,
            activo: true
          })
        });

        if (!saveRes.ok) {
          throw new Error("No se pudo guardar la localidad");
        }

        // 3. Trigger recálculo con clima actual
        const recalcRes = await fetchProtegido("/api/recalcular-outdoor/", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });

        if (!recalcRes.ok) {
          const error = await recalcRes.json();
          throw new Error(error.error || "Error al recalcular");
        }

        const resultado = await recalcRes.json();

        // 4. Mostrar resultado
        mostrarToast(`✅ ${resultado.mensaje}
🌤️ Temp: ${resultado.clima.temperatura_max.toFixed(1)}°C
💧 Precipitación: ${resultado.clima.precipitacion.toFixed(1)}mm`, "success");

        // 5. Refrescar lista de plantas
        setTimeout(() => {
          window.location.reload();
        }, 2000);

      } catch (error) {
        console.error("Error en recálculo outdoor:", error);
        mostrarToast(`❌ ${error.message}`, "error");
      } finally {
        btnRecalcularClima.disabled = false;
        btnRecalcularClima.textContent = "Usar Clima Actual";
      }
    });
  }
  // --- Lógica para el botón de instalación de la PWA ---
  let deferredPrompt; // Variable para guardar el evento de instalación
  const btnInstalar = document.getElementById('btnInstalarPWA');
  const btnInstalarMobile = document.getElementById('btnInstalarPWAMobile');

  window.addEventListener('beforeinstallprompt', (e) => {
    // Previene que Chrome 67 y anteriores muestren el prompt automáticamente
    e.preventDefault();
    // Guarda el evento para que pueda ser disparado más tarde.
    deferredPrompt = e;
    // Muestra nuestro botón de instalación personalizado
    if (btnInstalar) btnInstalar.classList.remove('d-none');
    if (btnInstalarMobile) btnInstalarMobile.classList.remove('d-none');
  });

  const handleInstallClick = (e) => {
    e.preventDefault();
    // Oculta nuestro botón, ya que solo se puede usar una vez.
    if (btnInstalar) btnInstalar.classList.add('d-none');
    if (btnInstalarMobile) btnInstalarMobile.classList.add('d-none');

    // Muestra el prompt de instalación
    deferredPrompt.prompt();
    // Espera a que el usuario responda al prompt
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('El usuario aceptó instalar la PWA');
      } else {
        console.log('El usuario rechazó instalar la PWA');
      }
      deferredPrompt = null;
    });
  };

  if (btnInstalar) btnInstalar.addEventListener('click', handleInstallClick);
  if (btnInstalarMobile) btnInstalarMobile.addEventListener('click', handleInstallClick);
});
