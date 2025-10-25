import { fetchProtegido } from "./auth.js";
import { mostrarToast } from "./api.js";
let planta = null;

function renderizarDetalle(planta) {
  document.getElementById("nombre").textContent = planta.nombre_personalizado;
  document.getElementById("tipo").textContent = planta.tipo_planta;
  document.getElementById("tamano").textContent = planta.tamano_planta;
  document.getElementById("maceta").textContent = `${planta.tamano_maceta_litros} `;
  document.getElementById("ultimoRiego").textContent = planta.fecha_ultimo_riego;
  document.getElementById("enFloracion").textContent = planta.en_floracion ? "Si" : "No";
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

configurarBotonVolver("btn-volver", "/dashboard/");

function habilitarEdicion(campo, boton) {
  document.getElementById("guardarCambios").classList.remove("d-none");

  const litros = document.getElementById("unidad-maceta");
  if (campo === "maceta" && litros) {
    litros.classList.add("d-none");
  }

  const span = document.getElementById(campo);
  const input = document.getElementById(`input-${campo}`);

  if (!span || !input || !boton) {
    console.warn(`Elemento no encontrado para campo: ${campo}`);
    return;
  }

  input.value = span.textContent.trim();
  span.classList.add("d-none");
  input.classList.remove("d-none");
  boton.classList.add("d-none");

  if (campo === "maceta" && litros) {
    litros.classList.remove("d-none");
  }
}

function obtenerIdDesdeURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

document.getElementById('guardarCambios').addEventListener('click', async () => {
  const idPlanta = obtenerIdDesdeURL();

  const camposMap = {
    nombre: "nombre_personalizado",
    tipo: "tipo_planta",
    tamano: "tamano_planta",
    maceta: "tamano_maceta_litros",
    ultimoRiego: "fecha_ultimo_riego",
    enFloracion: "en_floracion",
    estadoRiego: "estado_texto",
    sugerencia: "sugerencia_suplementos"
  };

  const payload = { ...planta }; // ✅ mantiene todos los campos obligatorios

  Object.entries(camposMap).forEach(([campoFrontend, campoBackend]) => {
    const input = document.getElementById(`input-${campoFrontend}`);
    if (input && !input.classList.contains('d-none')) {
      payload[campoBackend] = campoFrontend === "enFloracion"
        ? input.value.trim().toLowerCase() === "si"
        : input.value.trim();
    }
  });

      const camposObligatorios = [
      "nombre_personalizado",
      "tipo_planta",
      "tamano_planta",
      "tamano_maceta_litros",
      "fecha_ultimo_riego"
    ];

    const camposInvalidos = camposObligatorios.filter(campo => {
      const valor = payload[campo];
      return typeof valor !== "boolean" && (valor === undefined || valor === null || valor.toString().trim() === "");
    });

    if (camposInvalidos.length > 0) {
      console.warn("❌ Campos inválidos:", camposInvalidos);
      mostrarToast(`⚠️ Faltan datos obligatorios: ${camposInvalidos.join(", ")}`);
      return;
    }


  try {
    guardarCambios.disabled = true;
    guardarCambios.textContent = 'Guardando...';

    console.log("Payload enviado:", JSON.stringify(payload));

    const resPut = await fetchProtegido(`/api/plantas/${idPlanta}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!resPut || !resPut.ok) {
      const error = await resPut.json();
      console.error("❌ Backend dice:", error);
      mostrarToast('⚠️ Error al actualizar');
      throw new Error("Error en PUT");
    }

    mostrarToast('✅ Planta actualizada con éxito');

    const resGet = await fetchProtegido(`/api/plantas/${idPlanta}/`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!resGet || !resGet.ok) {
      mostrarToast('⚠️ Error al refrescar datos');
      throw new Error("Error en GET");
    }

    const plantaActualizada = await resGet.json();
    planta = plantaActualizada;

    renderizarDetalle(plantaActualizada);

    Object.keys(camposMap).forEach(campo => {
      const span = document.getElementById(campo);
      const input = document.getElementById(`input-${campo}`);
      const btnEditar = document.getElementById(`editar-${campo}`);
      if (span && input) {
        span.classList.remove('d-none');
        input.classList.add('d-none');
        if (btnEditar) btnEditar.classList.remove('d-none');
      }
    });

    document.getElementById("guardarCambios").classList.add("d-none");
    guardarCambios.disabled = false;
    guardarCambios.textContent = 'Guardar cambios';

  } catch (err) {
    console.error("❌ Error en actualización:", err);
    mostrarToast('❌ Fallo de conexión');
    guardarCambios.disabled = false;
    guardarCambios.textContent = 'Guardar cambios';
  }
});

// --- NUEVAS FUNCIONES PARA ESTADÍSTICAS E HISTORIAL ---

function renderizarEstadisticas(stats) {
  const container = document.getElementById("stats-cards-container");
  container.innerHTML = ""; // Limpiamos por si acaso

  if (!stats) return;

  const cards = [
    { icon: "bi-calendar-range", title: "Frecuencia Promedio", value: `${(stats.frecuencia_promedio_dias || 0).toFixed(1)} días` },
    { icon: "bi-droplet-fill", title: "Riegos Totales", value: `${stats.total_riegos || 0} riegos` },
    { icon: "bi-water", title: "Agua Promedio", value: `${Math.round(stats.promedio_agua_ml || 0)} ml` },
    { icon: "bi-clock-history", title: "Último Riego", value: stats.fecha_ultimo_riego ? new Date(stats.fecha_ultimo_riego).toLocaleDateString() : 'N/A' },
  ];

  cards.forEach(card => {
    const col = document.createElement("div");
    col.className = "col-md-3 col-6";
    col.innerHTML = `
      <div class="card card-stat h-100">
        <div class="card-body text-center">
          <i class="${card.icon} display-6 text-violeta"></i>
          <h6 class="card-subtitle mt-2 mb-1 text-white-50">${card.title}</h6>
          <p class="card-text fs-5 fw-bold">${card.value}</p>
        </div>
      </div>
    `;
    container.appendChild(col);
  });
}

function renderizarGrafico(historial) {
  const ctx = document.getElementById("riegoChart").getContext("2d");

  // Preparamos los datos para el gráfico (lo invertimos para que vaya de más antiguo a más nuevo)
  const labels = historial.map(riego => new Date(riego.fecha).toLocaleDateString()).reverse();
  const data = historial.map(riego => riego.cantidad_agua_ml).reverse();

  // Destruir gráfico anterior si existe para evitar solapamiento
  if (window.myRiegoChart) {
    window.myRiegoChart.destroy();
  }

  window.myRiegoChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Cantidad de Agua (ml)",
        data: data,
        borderColor: "#9ACD32", // Verde lima
        backgroundColor: "rgba(154, 205, 50, 0.2)",
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, ticks: { color: '#f8f9fa' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
        x: { ticks: { color: '#f8f9fa' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
      },
      plugins: { legend: { labels: { color: '#f8f9fa' } } }
    },
  });
}

function renderizarTablaHistorial(historial) {
  const tbody = document.getElementById("history-table-body");
  tbody.innerHTML = ""; // Limpiamos la tabla

  if (historial.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="text-center text-white-50">No hay riegos registrados.</td></tr>`;
    return;
  }

  historial.forEach(riego => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${new Date(riego.fecha).toLocaleDateString()}</td>
      <td>${riego.cantidad_agua_ml} ml</td>
      <td>${riego.comentarios || '<span class="text-white-50">Sin comentarios</span>'}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function cargarDatosPagina(plantId) {
  const historyLoading = document.getElementById("history-loading");
  historyLoading.classList.remove("d-none");

  try {
    // Hacemos las dos llamadas a la API en paralelo para más eficiencia
    const [plantaRes, historialRes] = await Promise.all([
      fetchProtegido(`/api/plantas/${plantId}/`),
      fetchProtegido(`/api/plantas/${plantId}/historial/`),
    ]);

    if (!plantaRes.ok || !historialRes.ok) {
      throw new Error("No se pudieron cargar los datos de la planta.");
    }

    const plantaData = await plantaRes.json();
    planta = plantaData; // Guardamos en la variable global para la edición
    const historialData = await historialRes.json();

    // Renderizamos todos los componentes con los datos recibidos
    renderizarDetalle(plantaData);
    renderizarEstadisticas(historialData.estadisticas);
    renderizarGrafico(historialData.historial_riegos);
    renderizarTablaHistorial(historialData.historial_riegos);

  } catch (error) {
    console.error("Error al cargar datos:", error);
    mostrarToast("No se pudieron cargar los detalles y el historial.", "danger");
  } finally {
    historyLoading.classList.add("d-none");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const plantId = obtenerIdDesdeURL();
  if (!plantId) {
    mostrarToast("No se especificó una planta.", "danger");
    setTimeout(() => (window.location.href = "/dashboard/"), 2000);
    return;
  }

  cargarDatosPagina(plantId);

  ["nombre", "tamano", "maceta", "ultimoRiego", "enFloracion"].forEach(campo => {
    const btn = document.getElementById(`editar-${campo}`);
    if (btn) btn.addEventListener("click", () => habilitarEdicion(campo, btn));
  });
});
