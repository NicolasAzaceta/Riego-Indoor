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

function mostrarTarjetaBienvenida() {
  const container = document.getElementById("plant-list");
  if (!container) return;
  container.innerHTML = `
    <div class="col-12 d-flex justify-content-center">
      <div class="card card-bienvenida text-center" style="max-width: 500px;">
        <div class="card-body">
          <h5 class="card-title mb-3">¡Bienvenido a Riegum!</h5>
          <p class="card-text">
            Aquí se mostrarán tus plantas una vez que las agregues.
          </p>
        </div>
      </div>
    </div>`;
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
        if (container && container.children.length === 0) {
          mostrarTarjetaBienvenida();
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

    if (!plantas.length) {
      mostrarTarjetaBienvenida();
      return;
    }

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
      <div class="card-body text-center flex-grow-1 d-flex flex-column align-items-center justify-content-start">
      <h5 class="card-title">${planta.nombre_personalizado}</h5>
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
      const btnRegar = tarjeta.querySelector(".btn-regar");      btnRegar.addEventListener("click", async () => {
        const animacionLocal = tarjeta.querySelector(".animacion-local");
        const player = animacionLocal.querySelector("lottie-player");

        animacionLocal.classList.remove("oculto");
        player.stop();
        player.play();

        setTimeout(() => {
          animacionLocal.classList.add("oculto");
        }, 2000);

        // Corregimos: regarPlanta ahora devuelve el estado actualizado.
        const riegoExitoso = await regarPlanta(planta.id, planta.recommended_water_ml);
        if (!riegoExitoso) return; // Si el riego falló, no continuamos.

        const data = await obtenerPlanta(planta.id); // Obtenemos los datos completos y recalculados de la planta.
        if (!data) return;

        const textoRiego = tarjeta.querySelector(".card-text");
        textoRiego.innerHTML = `🌱 <strong>${data.estado_texto}</strong>`;

        // Limpiamos todas las clases de estado antes de aplicar la nueva
        tarjeta.classList.remove("estado-verde", "estado-amarillo", "estado-naranja");

        // Aplicamos la clase correcta según el nuevo estado
        switch (data.estado_riego) {
          case 'no_necesita':
            tarjeta.classList.add("estado-verde");
            break;
          case 'pronto':
            tarjeta.classList.add("estado-amarillo");
            break;
          // No hay caso para 'hoy' porque después de regar, nunca será 'hoy'.
        }

        mostrarToast("🌿 ¡Planta regada con éxito!");
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

  checkGoogleCalendarStatus();
});


const params = new URLSearchParams(window.location.search);
const plantId = params.get("id");


document.getElementById("btnAgregarPlanta").addEventListener("click", () => {
  window.location.href = "/add/";
});
