import { logoutUsuario } from './auth.js';
import { fetchProtegido } from './auth.js';

export function mostrarToast(mensaje, tipo = "success") {
  const toastBody = document.getElementById("toast-body");
  const toast = document.getElementById("toast");

  toastBody.textContent = mensaje;
  toast.classList.remove("bg-success", "bg-danger", "bg-warning", "bg-violeta");

  const claseBg = tipo === "success" ? "bg-violeta" : `bg-${tipo}`;
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
  const btnGoogleDisconnect = document.getElementById("btnGoogleDisconnect");
  const googleDivider = document.getElementById("google-divider");

  if (!btnGoogleCalendar || !btnGoogleDisconnect || !googleDivider) return;

  if (isLinked) {
    // Botón principal: Mostrar como vinculado y deshabilitar
    btnGoogleCalendar.classList.remove('btn-violeta-outline');
    btnGoogleCalendar.classList.add('btn-violeta-solid'); // Cambia a violeta sólido
    btnGoogleCalendar.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Vinculado';
    btnGoogleCalendar.style.pointerEvents = 'none';
    btnGoogleCalendar.setAttribute('disabled', 'disabled');

    // Menú desplegable: Mostrar opción para desvincular
    btnGoogleDisconnect.classList.remove('d-none');
    googleDivider.classList.remove('d-none');
  } else {
    // Estado por defecto si no está vinculado
    btnGoogleCalendar.classList.add('btn-violeta-outline');
    btnGoogleCalendar.classList.remove('btn-violeta-solid');
    btnGoogleCalendar.innerHTML = '<i class="bi bi-calendar-plus me-1"></i> Vincular Calendario';
    btnGoogleCalendar.style.pointerEvents = 'auto';
    btnGoogleCalendar.removeAttribute('disabled');

    // Ocultar opción de desvincular
    btnGoogleDisconnect.classList.add('d-none');
    googleDivider.classList.add('d-none');
  }
}

// Hacemos la función de inicialización global para que el script de Google Maps la encuentre.
function initializeAutocomplete() { // Renombrada para mayor claridad
  const inputLocalidad = document.getElementById("inputLocalidad");
  console.log("✅ initializeAutocomplete called.");
  console.log("inputLocalidad found:", !!inputLocalidad);

  // Verificamos si el objeto 'google' y sus componentes están disponibles
  if (typeof google === 'undefined' || typeof google.maps === 'undefined' || typeof google.maps.places === 'undefined') {
    console.error("❌ Google Maps API o la librería Places no se cargaron correctamente.");
    console.error("Asegurate de que la API Key sea válida, la facturación esté habilitada y la 'Places API' esté activada en Google Cloud Console.");
    return; // Salimos si la API no está lista
  }

  if (inputLocalidad) {
    console.log("✅ Inicializando autocompletado de Google Places...");
    const autocomplete = new google.maps.places.Autocomplete(inputLocalidad, {
      types: ['(cities)'], // Limita la búsqueda a ciudades
      fields: ['formatted_address'] // Pedimos la dirección formateada para más precisión
    });

    // Listener para cuando el usuario selecciona un lugar del autocompletado
    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();
      if (place.formatted_address) {
        inputLocalidad.value = place.formatted_address; // Rellenamos el input con la dirección formateada
        console.log("Localidad seleccionada por autocompletado:", place.formatted_address);
      } else {
        console.warn("No se encontraron detalles para la localidad seleccionada.");
      }
    });
  }
}

window.initAutocomplete = initializeAutocomplete;

document.addEventListener("DOMContentLoaded", () => {
  const btnLogout = document.getElementById("btnLogout");
  if (btnLogout) {
    btnLogout.addEventListener("click", (e) => {
      e.preventDefault(); // evita navegación por el href
      mostrarToast("👋 ¡Sesión cerrada! ¡Hasta luego!");
      setTimeout(() => logoutUsuario(), 2000);
    });
  }

  const btnGoogleCalendar = document.getElementById("btnGoogleCalendar");
  if (btnGoogleCalendar) {
    btnGoogleCalendar.addEventListener("click", (e) => {
      e.preventDefault();
      iniciarVinculacionGoogle();
    });
  }

  const btnGoogleDisconnect = document.getElementById("btnGoogleDisconnect");
  if (btnGoogleDisconnect) {
    btnGoogleDisconnect.addEventListener("click", async (e) => {
      e.preventDefault();
      if (!confirm("¿Estás seguro de que querés desvincular tu calendario? Los eventos ya creados no se eliminarán.")) {
        return;
      }
      try {
        const res = await fetchProtegido('/api/google-calendar-disconnect/', { method: 'POST' });
        if (!res.ok) throw new Error('Error en el servidor');
        mostrarToast("✅ Calendario desvinculado con éxito.", "success");
        setTimeout(() => window.location.reload(), 1500); // Recargamos para refrescar el estado
      } catch (error) {
        mostrarToast("❌ No se pudo desvincular el calendario.", "danger");
      }
    });
  }

  // Verificamos el estado de la vinculación al cargar la página
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

      mostrarToast(`Usando ${temperatura}°C para recalcular riegos...`, "info");

      // Recalculamos el riego para cada planta visible
      const plantCards = document.querySelectorAll('#plant-list .card');
      plantCards.forEach(async (card) => {
        const plantId = card.querySelector('[data-id]').dataset.id;
        try {
          const recalcUrl = `/api/plantas/${plantId}/recalcular/?temperatura=${temperatura}`;
          const recalcRes = await fetchProtegido(recalcUrl);
          if (!recalcRes.ok) return;

          const nuevosDatos = await recalcRes.json();
          
          // Actualizamos el texto de la tarjeta
          const textoRiego = card.querySelector('.card-text');
          if (textoRiego) {
            textoRiego.innerHTML = `🌱 <strong>${nuevosDatos.estado_texto}</strong> (con T° manual)`;
          }
        } catch (error) {
          console.warn(`No se pudo recalcular la planta ${plantId}:`, error);
        }
      });
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
        mostrarToast(`Clima en ${localidad}: ${temp.toFixed(1)}°C. Recalculando riegos...`, "info");

        // Ahora, recalculamos el riego para cada planta visible
        const plantCards = document.querySelectorAll('#plant-list .card');
        plantCards.forEach(async (card) => {
          const plantId = card.querySelector('[data-id]').dataset.id;
          try {
            const recalcUrl = `/api/plantas/${plantId}/recalcular/?temperatura=${temp}`;
            const recalcRes = await fetchProtegido(recalcUrl);
            if (!recalcRes.ok) return;

            const nuevosDatos = await recalcRes.json();
            
            // Actualizamos el texto de la tarjeta
            const textoRiego = card.querySelector('.card-text');
            if (textoRiego) {
              textoRiego.innerHTML = `🌱 <strong>${nuevosDatos.estado_texto}</strong> (con clima)`;
            }

          } catch (error) {
            console.warn(`No se pudo recalcular la planta ${plantId}:`, error);
          }
        });
      } catch (error) {
        mostrarToast(`❌ Error al buscar el clima: ${error.message}`, "danger");
      }
    });
  }
});
