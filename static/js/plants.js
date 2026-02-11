import { fetchProtegido } from "./auth.js";
import { checkGoogleCalendarStatus, iniciarVinculacionGoogle, mostrarToast } from './api.js';

let plantaAEliminar = null;

async function regarPlanta(id, cantidadAgua) {
  try {
    const payload = {
      cantidad_agua_ml: cantidadAgua,
    };
    console.log("Enviando payload de riego:", JSON.stringify(payload, null, 2)); // Log para depuración
    const res = await fetchProtegido(`/api/plantas/${id}/regar/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json();
      const errorMessage = errorData.error || errorData.detail || "Error en la respuesta del servidor al regar la planta";
      mostrarToast(`❌ Error: ${errorMessage}`);
      return false;
    }
    return true; // Devolvemos true si el riego fue exitoso.
  } catch (error) {
    console.error("❌ Error al regar planta:", error);
    mostrarToast("No se pudo regar la planta.");
    return false;
  }
}

function crearTarjetaAgregarPlanta() {
  const container = document.getElementById("plant-list");
  if (!container) return;

  const cardWrapper = document.createElement("div");
  cardWrapper.className = "col-md-4 mb-3 d-flex align-items-center justify-content-center";
  cardWrapper.id = "tarjeta-agregar-planta"; // Le damos un ID para poder observarla después
  cardWrapper.innerHTML = `
    <a href="/add/" class="card card-add-plant shadow-sm text-decoration-none d-flex align-items-center justify-content-center">
      <div class="card-body text-center d-flex flex-column align-items-center justify-content-center gap-3">
        <div class="add-plant-icon">
          <i class="bi bi-plus-lg"></i>
        </div>
        <h5 class="card-title text-violeta-bold mb-0">Agregar Nueva Planta</h5>
      </div>
    </a>`;
  container.appendChild(cardWrapper);
}

async function eliminarPlanta(id, cardElement) {
  try {
    const res = await fetchProtegido(`/api/plantas/${id}/`, {
      method: "DELETE"
    });

    if (res.status === 204) {
      // ✅ Animación de desvanecimiento
      cardElement.classList.add("desvanecer");
      setTimeout(() => {
        cardElement.remove();
        // Después de eliminar, verificamos si el dashboard quedó vacío.
        const container = document.getElementById("plant-list");
        if (container && container.querySelectorAll('.card').length === 1) { // Si solo queda la tarjeta de agregar
          // Ya no es necesario hacer nada, la tarjeta de agregar siempre está
        }
      }, 600);

      mostrarToast("✅ Planta eliminada con éxito");
    } else {
      const error = await res.json();
      mostrarToast("❌ Error: " + (error.error || "No se pudo eliminar la planta"));
    }
  } catch (err) {
    console.error("Error al eliminar planta:", err);
    mostrarToast("❌ Fallo de conexión");
  }
}

// ✅ Confirmación desde el modal
// ✅ Confirmación desde el modal
document.getElementById("btnConfirmarEliminar").addEventListener("click", async () => {
  const btnConfirmar = document.getElementById("btnConfirmarEliminar");

  if (plantaAEliminar) {
    // 1. Mostrar spinner
    btnConfirmar.disabled = true;
    const textoOriginal = btnConfirmar.innerHTML;
    btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Eliminando...';

    try {
      await eliminarPlanta(plantaAEliminar.id, plantaAEliminar.card);
    } finally {
      // 2. Restaurar botón y limpiar referencia
      btnConfirmar.disabled = false;
      btnConfirmar.innerHTML = textoOriginal;
      plantaAEliminar = null;

      // 3. Cerrar modal (incluso si hubo error, o podríamos dejarlo abierto si falla... 
      // por ahora mantenemos el comportamiento de cerrar siempre para limpiar UI)
      const modal = bootstrap.Modal.getInstance(document.getElementById("modalConfirmar"));
      if (modal) modal.hide();
    }
  }
});

async function obtenerPlanta(id) {
  try {
    const response = await fetchProtegido(`/api/plantas/${id}/`, {
      method: "GET"
    });

    if (!response.ok) throw new Error("Error al obtener la planta");

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
    mostrarToast("❌ No se pudo actualizar la tarjeta");
    return null;
  }
}


document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetchProtegido("/api/plantas/", {
      headers: { "Content-Type": "application/json" }
    });
    if (!res) return;

    const plantas = await res.json();
    const container = document.getElementById("plant-list");

    crearTarjetaAgregarPlanta(); // Siempre creamos la tarjeta de "Agregar" primero

    plantas.forEach((planta, index) => {
      const card = document.createElement("div");
      card.className = "col-md-4 mb-3";

      let claseEstado = '';
      switch (planta.estado_riego) {
        case 'no_necesita':
          claseEstado = 'estado-verde';
          break;
        case 'pronto':
          claseEstado = 'estado-amarillo';
          break;
        case 'hoy':
          claseEstado = 'estado-naranja';
          break;
        case 'urgente':
          claseEstado = 'estado-urgente';
          break;
      }

      const tarjeta = document.createElement("div");
      tarjeta.className = `card h-100 shadow-sm position-relative animar-entrada ${claseEstado}`;
      tarjeta.style.animationDelay = `${index * 100}ms`;

      // Badge de tipo de cultivo (fallback a 'indoor' para plantas existentes)
      const tipoCultivo = planta.tipo_cultivo || 'indoor';
      const badgeCultivo = tipoCultivo === 'outdoor'
        ? '<span class="badge bg-primary me-2" title="Riego automático según clima" style="font-size: 0.75rem;">🌤️ Outdoor</span>'
        : '<span class="badge bg-secondary me-2" title="Ambiente controlado" style="font-size: 0.75rem;">🏠 Indoor</span>';

      // Badge de categoría botánica
      const categoriaBotanica = planta.categoria_botanica || 'Cannabis';
      const badgeCategoria = categoriaBotanica === 'Cannabis'
        ? '<span class="badge bg-success" title="Cannabis" style="font-size: 0.75rem;">🌿 Cannabis</span>'
        : '<span class="badge bg-info text-dark" title="Otras" style="font-size: 0.75rem;">🌵 Otras</span>';

      tarjeta.innerHTML = `
      <!-- Badges en esquina superior izquierda -->
      <div class="position-absolute" style="top: 14px; left: 16px; z-index: 10;">
        ${badgeCultivo}${badgeCategoria}
      </div>
      
      <div class="card-body text-center flex-grow-1 d-flex flex-column align-items-center justify-content-center">
      <h5 class="card-title mb-3">${planta.nombre_personalizado}</h5>
      <p class="card-text">🌱 <strong>${planta.estado_texto}</strong></p>

      <div class="animacion-local oculto mt-3">
        <lottie-player
          src="/static/assets/animaciones/water.json"
          background="transparent"
          speed="1"
          style="width: 220px; height: 220px;"
          autoplay>
        </lottie-player>
      </div>
    </div>

    <div class="card-footer bg-transparent border-0 mt-auto text-center">
      <div class="d-flex justify-content-center gap-2 mb-2">
        <button class="btn btn-violeta-outline btn-ver-detalle me-2" data-id="${planta.id}" title="Ver detalles">
          <i class="bi bi-text-indent-left"></i> Detalle
        </button>
        <button class="btn btn-celeste-outline btn-regar" data-id="${planta.id}" title="Regar planta">
          <i class="bi bi-droplet me-1"></i>Regar
        </button>
      </div>
      <button class="btn btn-eliminar btn-sm" data-id="${planta.id}" title="Eliminar planta">
        <i class="bi bi-trash"></i>
      </button>
    </div>
`;
      const btnRegar = tarjeta.querySelector(".btn-regar");
      btnRegar.addEventListener("click", async () => {
        // 1. Deshabilitamos el botón y mostramos el spinner
        btnRegar.disabled = true;
        btnRegar.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`;

        try {
          const animacionLocal = tarjeta.querySelector(".animacion-local");
          const player = animacionLocal.querySelector("lottie-player");

          animacionLocal.classList.remove("oculto");
          player.stop();
          player.play();

          setTimeout(() => {
            animacionLocal.classList.add("oculto");
          }, 2000);

          const riegoExitoso = await regarPlanta(planta.id, planta.recommended_water_ml);
          if (!riegoExitoso) return; // Si el riego falló, no continuamos.

          const data = await obtenerPlanta(planta.id);
          if (!data) return;

          const textoRiego = tarjeta.querySelector(".card-text");
          textoRiego.innerHTML = `🌱 <strong>${data.estado_texto}</strong>`;

          tarjeta.classList.remove("estado-verde", "estado-amarillo", "estado-naranja", "estado-urgente");

          switch (data.estado_riego) {
            case 'no_necesita':
              tarjeta.classList.add("estado-verde");
              break;
            case 'pronto':
              tarjeta.classList.add("estado-amarillo");
              break;
            case 'hoy':
              tarjeta.classList.add("estado-naranja");
              break;
            case 'urgente':
              tarjeta.classList.add("estado-urgente");
              break;
          }

          mostrarToast("🌿 ¡Planta regada con éxito!");
        } catch (error) {
          console.error("Error en el proceso de riego desde el dashboard:", error);
          // El toast de error ya se muestra dentro de regarPlanta
        } finally {
          // 3. Siempre, al final, restauramos el botón
          btnRegar.disabled = false;
          btnRegar.innerHTML = `<i class="bi bi-droplet me-1"></i>Regar`;
        }
      });

      const btnVerDetalle = tarjeta.querySelector(".btn-ver-detalle");
      btnVerDetalle.addEventListener("click", () => {
        const id = btnVerDetalle.dataset.id;
        window.location.href = `/detail?id=${id}`;
      });

      const btnEliminar = tarjeta.querySelector(".btn-eliminar");
      btnEliminar.addEventListener("click", () => {
        plantaAEliminar = {
          id: planta.id,
          card: card
        };
        const modal = new bootstrap.Modal(document.getElementById("modalConfirmar"));
        modal.show();
      });


      card.appendChild(tarjeta);
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error al cargar plantas:", err);
    alert("No se pudieron cargar las plantas. Verificá tu conexión o el token.");
  }

  const btnGoogleCalendar = document.getElementById("btnGoogleCalendar");
  if (btnGoogleCalendar) {
    btnGoogleCalendar.addEventListener("click", (e) => {
      e.preventDefault();
      iniciarVinculacionGoogle();
    });
  }

  // --- Lógica para el botón flotante/navbar ---
  const tarjetaAgregar = document.getElementById('tarjeta-agregar-planta');
  const btnAgregarNavbar = document.getElementById('btnAgregarPlantaNavbar');
  const btnAgregarNavbarMobile = document.getElementById('btnAgregarPlantaNavbarMobile');

  if (tarjetaAgregar && btnAgregarNavbar && btnAgregarNavbarMobile) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        // Si la tarjeta de "Agregar" NO está visible en la pantalla...
        if (!entry.isIntersecting) {
          // ...mostramos el botón del navbar.
          btnAgregarNavbar.classList.remove('d-none');
          btnAgregarNavbarMobile.classList.remove('d-none');
        } else {
          // ...y si SÍ está visible, lo ocultamos.
          btnAgregarNavbar.classList.add('d-none');
          btnAgregarNavbarMobile.classList.add('d-none');
        }
      });
    }, { threshold: 0.1 }); // Se activa cuando el 10% de la tarjeta es visible

    observer.observe(tarjetaAgregar);
  }

  checkGoogleCalendarStatus();
});


const params = new URLSearchParams(window.location.search);
const plantId = params.get("id");

// ==================== CONFIGURACIÓN INDOOR ====================

/**
 * Cargar configuración indoor del perfil del usuario
 */
async function cargarConfigIndoor() {
  try {
    const res = await fetchProtegido('/api/configuracion-usuario/', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (res.ok) {
      const data = await res.json();
      const inputTemp = document.getElementById('inputTemperatura');
      const inputHum = document.getElementById('inputHumedad');

      if (data.temperatura_promedio !== null) {
        inputTemp.value = data.temperatura_promedio;
      }
      if (data.humedad_relativa !== null) {
        inputHum.value = data.humedad_relativa;
      }

      // Mostrar badge en el navbar (desktop y mobile) si hay configuración activa
      const badge = document.getElementById('indoorConfigBadge');
      const badgeText = document.getElementById('indoorConfigText');

      if (data.temperatura_promedio !== null || data.humedad_relativa !== null) {
        let texto = '';
        if (data.temperatura_promedio !== null) {
          texto += `${data.temperatura_promedio}°C`;
        }
        if (data.humedad_relativa !== null) {
          if (texto) texto += ' | ';
          texto += `${data.humedad_relativa}%`;
        }

        // Desktop badge
        if (badge && badgeText) {
          badgeText.textContent = texto;
          badge.classList.remove('d-none');
          badge.classList.add('d-flex');
        }


      } else {
        // Ocultar ambos si no hay config
        if (badge) {
          badge.classList.add('d-none');
          badge.classList.remove('d-flex');
        }

      }
    }
  } catch (error) {
    console.error("Error al cargar configuración indoor:", error);
  }
}

/**
 * Guardar configuración indoor
 */
async function guardarConfigIndoor() {
  const inputTemp = document.getElementById('inputTemperatura');
  const inputHum = document.getElementById('inputHumedad');
  const btnGuardar = document.getElementById('btnGuardarIndoor');

  const temperatura = inputTemp.value !== '' ? parseFloat(inputTemp.value) : null;
  const humedad = inputHum.value !== '' ? parseFloat(inputHum.value) : null;

  // Validaciones
  if (temperatura !== null && (temperatura < -10 || temperatura > 50)) {
    mostrarToast('❌ La temperatura debe estar entre -10°C y 50°C');
    return;
  }

  if (humedad !== null && (humedad < 0 || humedad > 100)) {
    mostrarToast('❌ La humedad debe estar entre 0% y 100%');
    return;
  }

  // Deshabilitar botón mientras guardamos
  btnGuardar.disabled = true;
  btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';

  try {
    const payload = {
      temperatura_promedio: temperatura,
      humedad_relativa: humedad
    };

    const res = await fetchProtegido('/api/configuracion-usuario/', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      mostrarToast('✅ Configuración indoor guardada con éxito');

      // Recargar plantas para aplicar la nueva configuración
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } else {
      const errorData = await res.json();
      const errorMsg = errorData.temperatura_promedio || errorData.humedad_relativa || 'Error al guardar configuración';
      mostrarToast(`❌ ${errorMsg}`);
    }
  } catch (error) {
    console.error("Error al guardar configuración indoor:", error);
    mostrarToast('❌ Error de conexión al guardar configuración');
  } finally {
    btnGuardar.disabled = false;
    btnGuardar.innerHTML = 'Guardar Configuración';
  }
}

// Inicializar cuando cargue la página
document.addEventListener('DOMContentLoaded', () => {
  // Cargar configuración indoor guardada
  cargarConfigIndoor();

  // Botón para guardar configuración indoor
  const btnGuardarIndoor = document.getElementById('btnGuardarIndoor');
  if (btnGuardarIndoor) {
    btnGuardarIndoor.addEventListener('click', guardarConfigIndoor);
  }

  // ==================== CONFIGURACIÓN CALENDARIO ====================
  // Estado local para saber si está vinculado (cargado al abrir el acordeón o inicializar)
  let isCalendarLinked = false;

  async function cargarConfigCalendario() {
    try {
      const res = await fetchProtegido('/api/configuracion-calendario/', {
        method: 'GET'
      });
      if (res.ok) {
        const data = await res.json();
        const inputHora = document.getElementById('inputHoraCalendario');

        if (inputHora && data.google_calendar_event_time) {
          // El formato viene HH:MM:SS, el input time espera HH:MM
          // Cortamos los segundos si vienen
          inputHora.value = data.google_calendar_event_time.substring(0, 5);
        }
        isCalendarLinked = data.is_linked;
      }
    } catch (error) {
      console.error("Error al cargar config calendario:", error);
    }
  }

  async function guardarConfigCalendario() {
    // 1. Validar vinculación
    if (!isCalendarLinked) {
      const modal = new bootstrap.Modal(document.getElementById('modalVincularPrimero'));
      modal.show();
      return;
    }

    const inputHora = document.getElementById('inputHoraCalendario');
    const btnGuardar = document.getElementById('btnGuardarHoraCalendario');
    const hora = inputHora.value;

    if (!hora) {
      mostrarToast("⚠️ Por favor, seleccioná una hora.", "warning");
      return;
    }

    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...';

    try {
      const res = await fetchProtegido('/api/configuracion-calendario/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time: hora })
      });

      if (res.ok) {
        const data = await res.json();
        mostrarToast(`✅ ${data.message}`, "success");
      } else {
        const error = await res.json();
        mostrarToast(`❌ ${error.error || "Error al guardar"}`, "danger");
      }
    } catch (error) {
      console.error(error);
      mostrarToast("❌ Error de conexión", "danger");
    } finally {
      btnGuardar.disabled = false;
      btnGuardar.innerHTML = 'Guardar Preferencia';
    }
  }

  // Cargar configuración al iniciar
  cargarConfigCalendario();

  const btnGuardarCal = document.getElementById('btnGuardarHoraCalendario');
  if (btnGuardarCal) {
    btnGuardarCal.addEventListener('click', guardarConfigCalendario);
  }


});
