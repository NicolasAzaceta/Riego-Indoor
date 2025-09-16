import { fetchProtegido } from "./auth.js";

let plantaAEliminar = null;

function mostrarToast(mensaje, tipo = "success") {
  const toastBody = document.getElementById("toast-body");
  const toast = document.getElementById("toast");

  toastBody.textContent = mensaje;
  toast.classList.remove("bg-success", "bg-danger", "bg-warning");
  toast.classList.add(`bg-${tipo}`);

  // Inicializar y mostrar el toast
  const bsToast = new bootstrap.Toast(toast, { delay: 2000 });
  bsToast.show();

}

async function eliminarPlanta(id, cardElement) {
  try {
    const res = await fetchProtegido(`/api/plantas/${id}/`, {
      method: "DELETE"
    });

    if (res.status === 204) {
      // ✅ Animación de desvanecimiento
      cardElement.classList.add("desvanecer");
      setTimeout(() => cardElement.remove(), 600);

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
// export async function eliminarPlanta(id, cardElement) {
//   try {
//     const res = await fetchProtegido(`/api/plantas/${id}/`, {
//       method: "DELETE"
//     });

//     if (res.status === 204) {
//       alert("✅ Planta eliminada");
//       cardElement.remove(); // Elimina la tarjeta del DOM
//     } else {
//       const error = await res.json();
//       alert("❌ Error: " + (error.error || "No se pudo eliminar la planta"));
//     }
//   } catch (err) {
//     console.error("Error al eliminar planta:", err);
//     alert("No se pudo eliminar la planta. Verificá tu conexión.");
//   }
// }




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



// function mostrarToast(mensaje) {
//   const toast = document.createElement("div");
//   toast.textContent = mensaje;
//   toast.className = "toast-mensaje"; // Asegurate de tener estilos CSS para esto
//   document.body.appendChild(toast);

//   setTimeout(() => {
//     toast.remove();
//   }, 3000);
// }



// document.addEventListener("DOMContentLoaded", async () => {
//   try {
//     const res = await fetchProtegido("/api/plantas/", {
//       headers: { "Content-Type": "application/json" }
//     });
//     if (!res) return;

//     const plantas = await res.json();
//     const container = document.getElementById("plant-list");

//     if (!plantas.length) {
//       container.innerHTML = "<p>No hay plantas registradas.</p>";
//       return;
//     }

//     plantas.forEach((planta, index) => {
//       const card = document.createElement("div");
//       card.className = "col-md-4 mb-3";

//       const tarjeta = document.createElement("div");
//       tarjeta.className = "card h-100 shadow-sm position-relative animar-entrada";
//       tarjeta.style.animationDelay = `${index * 100}ms`;

//       tarjeta.innerHTML = `
//         <div class="card-body">
//           <h5 class="card-title">${planta.nombre_personalizado}</h5>
//           <p class="card-text">🌱 Riego en <strong>${planta.estado_riego}</strong> días</p> 
//           <button class="btn btn-outline-success btn-ver-detalle" data-id="${planta.id}" title="Ver detalles">
//             <i class="bi bi-eye"></i> Ver detalles
//           </button>

//           <button class="btn btn-outline-primary btn-regar" data-id="${planta.id}" title="Regar planta">
//             <i class="bi bi-droplet"></i> Regar planta
//           </button>

//           <button class="btn btn-outline-danger btn-eliminar" data-id="${planta.id}" title="Eliminar planta">
//             <i class="bi bi-trash"></i>
//           </button>

//           <div class="animacion-local oculto">
//             <lottie-player
//             src="/static/assets/animaciones/water.json"
//             background="transparent"
//             speed="1"
//             style="width: 220px; height: 220px;"
//             autoplay>
//             </lottie-player>
//           </div>

//         </div>
//       `;

//   // ✅ Evento para botón Regar
//   const btnRegar = tarjeta.querySelector(".btn-regar");
//   btnRegar.addEventListener("click", async () => {
//     const animacionLocal = tarjeta.querySelector(".animacion-local");
//     const player = animacionLocal.querySelector("lottie-player");

//     animacionLocal.classList.remove("oculto");
//     player.stop();
//     player.play();

//     setTimeout(() => {
//     animacionLocal.classList.add("oculto");
//     }, 2000);

//      await regarPlanta(planta.id, token); // solo ejecuta el POST

//      const data = await obtenerPlanta(planta.id, token); // ahora sí obtenés el estado actualizado
//      if (!data) return;

//      const textoRiego = tarjeta.querySelector(".card-text");
//      textoRiego.innerHTML = `🌱 Riego en <strong>${data.estado_riego}</strong> días`;

//     // mostrarAnimacionRiego();
//      mostrarToast("🌿 ¡Planta regada con éxito!");
//      });


//   // ✅ Evento para botón Ver Detalle
//   const btnVerDetalle = tarjeta.querySelector(".btn-ver-detalle");
//   btnVerDetalle.addEventListener("click", () => {
//   const id = btnVerDetalle.dataset.id;
//   window.location.href = `/home/detail/?id=${id}`;
//   });

//   // ✅ Evento para botón Eliminar
//   const btnEliminar = tarjeta.querySelector(".btn-eliminar");
//   btnEliminar.addEventListener("click", () => {
//     const confirmar = confirm("¿Seguro que querés eliminar esta planta?");
//     if (!confirmar) return;
//     eliminarPlanta(planta.id, token, card);
//     });

//     card.appendChild(tarjeta);
//     container.appendChild(card);
//     });

//   } catch (err) {
//     console.error("Error al cargar plantas:", err);
//     alert("No se pudieron cargar las plantas. Verificá tu conexión o el token.");
//   }
// });
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetchProtegido("/api/plantas/", {
      headers: { "Content-Type": "application/json" }
    });
    if (!res) return;

    const plantas = await res.json();
    const container = document.getElementById("plant-list");

    if (!plantas.length) {
      container.innerHTML = "<p>No hay plantas registradas.</p>";
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
        <button class="btn btn-outline-primary btn-ver-detalle me-2" data-id="${planta.id}" title="Ver detalles">
          <i class="bi bi-text-indent-left"></i> Ver detalles
        </button>
        <button class="btn btn-primary btn-regar" data-id="${planta.id}" title="Regar planta">
          <i class="bi bi-droplet me-1"></i>Regar planta
        </button>
      </div>
      <button class="btn btn-outline-danger btn-eliminar btn-sm" data-id="${planta.id}" title="Eliminar planta">
        <i class="bi bi-trash"></i>
      </button>
    </div>
`;

//       tarjeta.innerHTML = `
//       <div class="card-body text-center d-flex flex-column align-items-center">
//         <h5 class="card-title">${planta.nombre_personalizado}</h5>
//         <p class="card-text">🌱 <strong>${planta.estado_texto}</strong></p>
        
//         <div class="d-flex gap-2 mt-2">
//           <button class="btn btn-outline-primary btn-ver-detalle btn-sm me-2" data-id="${planta.id}" title="Ver detalles">
//             <i class="bi bi-text-indent-left"></i>Detalles
//           </button>

//           <button class="btn btn-primary btn-regar btn-sm" data-id="${planta.id}" title="Regar planta">
//             <i class="bi bi-droplet me-1"></i>Regar
//           </button>
//         </div>

//         <button class="btn btn-outline-danger btn-eliminar mt-2" data-id="${planta.id}" title="Eliminar planta">
//           <i class="bi bi-trash"></i>
//         </button>

//         <div class="animacion-local oculto">
//           <lottie-player
//           src="/static/assets/animaciones/water.json"
//           background="transparent"
//           speed="1"
//           style="width: 220px; height: 220px;"
//           autoplay>
//           </lottie-player>
//         </div>
//       </div>
// `;


      // tarjeta.innerHTML = `
      //   <div class="card-body text-center d-flex flex-column align-items-center">
      //     <h5 class="card-title">${planta.nombre_personalizado}</h5>
      //     <p class="card-text">🌱 <strong>${planta.estado_texto}</strong></p> 
      //     <button class="btn btn-outline-primary btn-ver-detalle" data-id="${planta.id}" title="Ver detalles">
      //       <i class="bi bi-text-indent-left" style="font-size: 1.1rem;"></i> Ver detalles
      //     </button>

      //     <button class="btn btn-outline-primary btn-regar" data-id="${planta.id}" title="Regar planta">
      //       <i class="bi bi-droplet"></i> Regar planta
      //     </button>

      //     <button class="btn btn-outline-danger btn-eliminar" data-id="${planta.id}" title="Eliminar planta">
      //       <i class="bi bi-trash"></i>
      //     </button>

      //     <div class="animacion-local oculto">
      //       <lottie-player
      //         src="/static/assets/animaciones/water.json"
      //         background="transparent"
      //         speed="1"
      //         style="width: 220px; height: 220px;"
      //         autoplay>
      //       </lottie-player>
      //     </div>
      //   </div>
      // `;

      const btnRegar = tarjeta.querySelector(".btn-regar");
      btnRegar.addEventListener("click", async () => {
        const animacionLocal = tarjeta.querySelector(".animacion-local");
        const player = animacionLocal.querySelector("lottie-player");

        animacionLocal.classList.remove("oculto");
        player.stop();
        player.play();

        setTimeout(() => {
          animacionLocal.classList.add("oculto");
        }, 2000);

        await regarPlanta(planta.id);
        const data = await obtenerPlanta(planta.id);
        if (!data) return;

        const textoRiego = tarjeta.querySelector(".card-text");
        textoRiego.innerHTML = `🌱 <strong>${data.estado_texto}</strong>`;

        tarjeta.classList.remove("estado-amarillo", "estado-naranja");
        switch (data.estado_riego) {
          case 'no_necesita':
            tarjeta.classList.add("estado-verde");
            break;
          }

        mostrarToast("🌿 ¡Planta regada con éxito!");
      });

      const btnVerDetalle = tarjeta.querySelector(".btn-ver-detalle");
      btnVerDetalle.addEventListener("click", () => {
        const id = btnVerDetalle.dataset.id;
        window.location.href = `/home/detail/?id=${id}`;
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
});


const params = new URLSearchParams(window.location.search);
const plantId = params.get("id");

// async function regarPlanta(id, token) {
//   try {
//     const response = await fetch(`/api/plantas/${id}/regar/`, {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//         "Authorization": `Bearer ${token}`
//       }
//     });

//     if (!response.ok) throw new Error("Error al regar la planta");

//     const data = await response.json();
//     console.log("Planta regada:", data);
//     mostrarAnimacionRiego(); // feedback visual
//     mostrarToast("🌿 ¡Planta regada con éxito!");
//   } catch (error) {
//     console.error(error);
//     mostrarToast("❌ No se pudo regar la planta");
//   }
// }

async function regarPlanta(id) {
  try {
    const res = await fetchProtegido(`/api/plantas/${id}/regar/`, {
      method: "POST"
    });

    if (!res.ok) throw new Error("Error al regar la planta");
  } catch (error) {
    console.error("❌ Error al regar planta:", error);
    mostrarToast("No se pudo regar la planta.");
  }
};


