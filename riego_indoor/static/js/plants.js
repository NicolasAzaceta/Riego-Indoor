document.addEventListener("DOMContentLoaded", async () => {
  const token = await obtenerTokenValido();
  const plantas = await getPlantas(token);
  // ... renderizado visual como antes
});
document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token"); // asumimos que ya hiciste login
  try {
    const plantas = await getPlantas(token);
    const container = document.getElementById("plant-list");

    plantas.forEach((planta) => {
      const card = document.createElement("div");
      card.className = "col-md-4";

      card.innerHTML = `
        <div class="card h-100">
          <div class="card-body">
            <h5 class="card-title">${planta.nombre}</h5>
            <p class="card-text">Riego en ${planta.dias_para_riego} días</p>
            <a href="detail.html?id=${planta.id}" class="btn btn-outline-dark">Ver detalle</a>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    alert("No se pudieron cargar las plantas");
    console.error(err);
  }
});