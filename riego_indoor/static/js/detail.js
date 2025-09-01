const params = new URLSearchParams(window.location.search);
const plantId = params.get("id");

function renderizarDetalle(planta) {
  document.getElementById("nombre").textContent = planta.nombre_personalizado;
  document.getElementById("tipo").textContent = planta.tipo_planta;
  document.getElementById("tamano").textContent = planta.tamano_planta;
  document.getElementById("maceta").textContent = `${planta.tamano_maceta_litros} L`;
  document.getElementById("ultimoRiego").textContent = planta.fecha_ultimo_riego;
  document.getElementById("enFloracion").textContent = planta.en_floracion ? "Sí" : "No";
  document.getElementById("estadoRiego").textContent = planta.estado_texto;
  document.getElementById("sugerencia").textContent = planta.sugerencia_suplementos;
  document.getElementById("recomendado").textContent = `${planta.recommended_water_ml} ml`;
  document.getElementById("frecuencia").textContent = `${planta.frequency_days} días`;
  document.getElementById("proximoRiego").textContent = planta.next_watering_date;
  document.getElementById("diasRestantes").textContent = planta.days_left;
}


function configurarBotonVolver(idBoton, destino) {
  const boton = document.getElementById(idBoton);
  if (boton) {
    boton.addEventListener("click", () => window.location.href = destino);
  }
}

configurarBotonVolver("Volver", "/home/dashboard/");

document.addEventListener("DOMContentLoaded", async () => {
  const id = params.get("id");
  if (!id) {
    alert("No se proporcionó un ID de planta. Redirigiendo al dashboard...");
    window.location.href = "/home/dashboard/";
    return;
  }


  const plantaId = id; // función que extrae el ID de la URL
  const token = await obtenerTokenValido();

  try {
    const res = await fetch(`/api/plantas/${plantaId}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Error al obtener los datos de la planta");

    const planta = await res.json();
    console.log("🌱 Detalle de planta:", planta);

    renderizarDetalle(planta); // función que actualiza el DOM con los datos
  } catch (err) {
    console.error("❌ Error en el fetch:", err);
    alert("No se pudo cargar el detalle de la planta. Intentá de nuevo.");
  }
});


// fetch(`/api/plants/${plantId}`, {
//   headers: {
//     Authorization: `Bearer ${localStorage.getItem("token")}`
//   }
// })
//   .then(res => res.json())
//   .then(data => {
//     document.getElementById("plant-title").textContent = data.name;
//     document.getElementById("plant-details").innerHTML = `
//       <li class="list-group-item">Tipo: ${data.type}</li>
//       <li class="list-group-item">Último riego: ${data.last_watered}</li>
//     `;
//   })
//   .catch(err => {
//     console.error("Error al cargar la planta:", err);
//     document.getElementById("plant-title").textContent = "Error al cargar la planta";
//   });

// document.addEventListener("DOMContentLoaded", async () => {
//   const token = localStorage.getItem("token");
//   const params = new URLSearchParams(window.location.search);
//   const id = params.get("id");

//   try {
//     const planta = await getPlantaById(id, token);
//     document.getElementById("plant-title").textContent = planta.nombre;

//     const detalles = [
//       { label: "Tipo", value: planta.tipo },
//       { label: "Tamaño", value: planta.tamano },
//       { label: "Último riego", value: planta.ultimo_riego },
//       { label: "Riego en", value: `${planta.dias_para_riego} días` },
//     ];

//     const list = document.getElementById("plant-details");
//     detalles.forEach((item) => {
//       const li = document.createElement("li");
//       li.className = "list-group-item";
//       li.textContent = `${item.label}: ${item.value}`;
//       list.appendChild(li);
//     });
//   } catch (err) {
//     alert("No se pudo cargar el detalle");
//     console.error(err);
//   }
// });