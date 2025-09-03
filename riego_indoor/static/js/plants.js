async function eliminarPlanta(id, token, cardElement) {
  try {
    const res = await fetch(`/api/plantas/${id}/`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (res.status === 204) {
      alert("✅ Planta eliminada");
      cardElement.remove(); // Elimina la tarjeta del DOM
    } else {
      const error = await res.json();
      alert("❌ Error: " + error.error);
    }
  } catch (err) {
    console.error("Error al eliminar planta:", err);
    alert("No se pudo eliminar la planta. Verificá tu conexión.");
  }
}


document.addEventListener("DOMContentLoaded", async () => {
  const token = await obtenerTokenValido(); // o localStorage.getItem("token") si ya lo tenés
  if (!token) {
    alert("No hay token disponible. Redirigiendo al login...");
    window.location.href = "home/"; // Redirigir al login
    return;
  }
  try {
    const res = await fetch("/api/plantas/", {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    if (!res.ok) throw new Error("Error al traer plantas");

    const plantas = await res.json();
    const container = document.getElementById("plant-list");

    if (!plantas.length) {
      container.innerHTML = "<p>No hay plantas registradas.</p>";
      return;
    }

    plantas.forEach((planta) => {
      const card = document.createElement("div");
      card.className = "col-md-4 mb-3";

            card.innerHTML = `
            <div class="card h-100 shadow-sm">
              <div class="card-body">
              <h5 class="card-title">${planta.nombre_personalizado}</h5>
              <p class="card-text">🌱 Riego en <strong>${planta.estado_riego}</strong> días</p> 
              <a href="/home/detail/?id=${planta.id}" class="btn btn-outline-success">Ver detalle</a>
              <button class="btn btn-outline-danger btn-eliminar" data-id="${planta.id}">Eliminar</button>
              </div>
            </div>
            `;
            const btnEliminar = card.querySelector(".btn-eliminar");
            btnEliminar.addEventListener("click", () => {
              const confirmar = confirm("¿Seguro que querés eliminar esta planta?");
              if (!confirmar) return;
              eliminarPlanta(planta.id, token, card);
            });

            container.appendChild(card);
            });
  } catch (err) {
    console.error("Error al cargar plantas:", err);
    alert("No se pudieron cargar las plantas. Verificá tu conexión o el token.");
  }
});
