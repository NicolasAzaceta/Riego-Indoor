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

    // Aseguramos que el sidebar siempre inicie desplegado.
    sidebar.classList.remove("collapsed");
    mainContent.classList.remove("expanded");

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
  document.body.addEventListener('click', function(e) {
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

  const btnRecalcularClima = document.getElementById("btnRecalcularClima");
  if (btnRecalcularClima) {
    btnRecalcularClima.addEventListener("click", async () => {
      const inputLocalidad = document.getElementById("inputLocalidad");
      const localidad = inputLocalidad.value.trim();

      if (!localidad) {
        mostrarToast("Por favor, ingresá una localidad.", "warning");
        return;
      }

      mostrarToast("Buscando datos del clima...", "info");

      try {
        // Ahora usamos GET y pasamos la localidad como un query parameter
        const url = `/api/weather/?location=${encodeURIComponent(localidad)}`;
        const res = await fetchProtegido(url);

        const data = await res.json();

        // Verificamos si la respuesta es un error o si tiene la estructura esperada
        if (!res.ok || !data.temperature?.degrees) {
          throw new Error(data.error || 'Respuesta inesperada del servidor.');
        }

        const temp = data.temperature.degrees;
        const climaData = {
          type: 'clima',
          value: temp,
          location: localidad.split(',')[0] // Guardamos solo el nombre de la ciudad
        };

        // Guardamos en localStorage, limpiamos el otro valor y actualizamos el display
        const climaKey = getClimaKey();
        const tempKey = getTemperaturaKey();
        if (climaKey) localStorage.setItem(climaKey, JSON.stringify(climaData));
        if (tempKey) localStorage.removeItem(tempKey);

        actualizarDisplayTemperaturaExterna(climaData);
        mostrarToast(`Clima en ${localidad}: ${temp.toFixed(1)}°C. Recalculando riegos...`, "info");

        recalcularTodasLasPlantas(temp, ' (con clima)');
      } catch (error) {
        mostrarToast(`❌ Error al buscar el clima: ${error.message}`, "danger");
      }
    });
  }
});
