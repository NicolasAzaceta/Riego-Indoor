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
document.getElementById("btnConfirmarEliminar").addEventListener("click", async () => {
  if (plantaAEliminar) {
    await eliminarPlanta(plantaAEliminar.id, plantaAEliminar.card);
    plantaAEliminar = null;
  }
    const modal = bootstrap.Modal.getInstance(document.getElementById("modalConfirmar"));
    if (modal) modal.hide();
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
      }

      const tarjeta = document.createElement("div");
      tarjeta.className = `card h-100 shadow-sm position-relative animar-entrada ${claseEstado}`;
      tarjeta.style.animationDelay = `${index * 100}ms`;

      tarjeta.innerHTML = `
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

          tarjeta.classList.remove("estado-verde", "estado-amarillo", "estado-naranja");

          switch (data.estado_riego) {
            case 'no_necesita':
              tarjeta.classList.add("estado-verde");
              break;
            case 'pronto':
              tarjeta.classList.add("estado-amarillo");
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
