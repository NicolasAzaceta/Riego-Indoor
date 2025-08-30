const params = new URLSearchParams(window.location.search);
const plantId = params.get("id");

fetch(`http://localhost:8000/api/plants/${plantId}`, {
  headers: {
    Authorization: `Bearer ${localStorage.getItem("token")}`
  }
})
  .then(res => res.json())
  .then(data => {
    document.getElementById("plant-title").textContent = data.name;
    document.getElementById("plant-details").innerHTML = `
      <li class="list-group-item">Tipo: ${data.type}</li>
      <li class="list-group-item">Último riego: ${data.last_watered}</li>
    `;
  })
  .catch(err => {
    console.error("Error al cargar la planta:", err);
    document.getElementById("plant-title").textContent = "Error al cargar la planta";
  });

document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");

  try {
    const planta = await getPlantaById(id, token);
    document.getElementById("plant-title").textContent = planta.nombre;

    const detalles = [
      { label: "Tipo", value: planta.tipo },
      { label: "Tamaño", value: planta.tamano },
      { label: "Último riego", value: planta.ultimo_riego },
      { label: "Riego en", value: `${planta.dias_para_riego} días` },
    ];

    const list = document.getElementById("plant-details");
    detalles.forEach((item) => {
      const li = document.createElement("li");
      li.className = "list-group-item";
      li.textContent = `${item.label}: ${item.value}`;
      list.appendChild(li);
    });
  } catch (err) {
    alert("No se pudo cargar el detalle");
    console.error(err);
  }
});