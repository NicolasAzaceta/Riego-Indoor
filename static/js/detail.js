import { fetchProtegido } from "./auth.js";
import { mostrarToast, logoutUsuario } from "./api.js";

let currentPlantData = null; // Para almacenar los datos de la planta y revertir cambios
let isEditMode = false; // Estado del modo de edición

function getPlantIdFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

function getEstadoBadgeClass(estado) {
  switch (estado) {
    case 'no_necesita': return 'bg-success';
    case 'pronto': return 'bg-warning text-dark';
    case 'hoy': return 'bg-danger';
    default: return 'bg-secondary';
  }
}

function renderizarDetalle(planta) {
  currentPlantData = planta; // Guardamos los datos originales

  // --- Ficha de la Planta ---
  document.getElementById('plant-title').textContent = planta.nombre_personalizado;
  document.getElementById('nombre').textContent = planta.nombre_personalizado;
  document.getElementById('tipo').textContent = planta.tipo_planta;
  document.getElementById('tamano').textContent = planta.tamano_planta;
  document.getElementById('maceta').textContent = `${planta.tamano_maceta_litros} litros`;
  document.getElementById('ultimoRiego').textContent = planta.fecha_ultimo_riego ? new Date(planta.fecha_ultimo_riego).toLocaleDateString('es-AR', { timeZone: 'UTC' }) : 'N/A';
  document.getElementById('enFloracion').textContent = planta.en_floracion ? 'Sí' : 'No';

  // Rellenamos los inputs solo una vez para la edición, no en cada renderizado.
  document.getElementById('input-nombre').value = planta.nombre_personalizado;
  document.getElementById('input-tamano').value = planta.tamano_planta;
  document.getElementById('input-maceta').value = planta.tamano_maceta_litros;
  document.getElementById('input-ultimoRiego').value = planta.fecha_ultimo_riego;
  document.getElementById('input-enFloracion').value = planta.en_floracion ? 'Si' : 'No';

  // --- Estado del Riego ---
  const estadoRiegoSpan = document.getElementById('estadoRiego');
  estadoRiegoSpan.textContent = planta.estado_texto;
  estadoRiegoSpan.className = `badge ${getEstadoBadgeClass(planta.estado_riego)}`;
  const diasRestantesSpan = document.getElementById('diasRestantes');
  diasRestantesSpan.className = `badge ${getEstadoBadgeClass(planta.estado_riego)}`; // Reutilizamos la misma clase de color

  document.getElementById('proximoRiego').textContent = planta.next_watering_date ? new Date(planta.next_watering_date).toLocaleDateString('es-AR', { timeZone: 'UTC' }) : 'N/A';
  document.getElementById('diasRestantes').textContent = planta.days_left !== null ? `${planta.days_left} días` : 'N/A';
  document.getElementById('recomendado').textContent = `${planta.recommended_water_ml} ml`;
  document.getElementById('frecuencia').textContent = `Cada ${planta.frequency_days} días`;

  // --- Suplementos Sugeridos ---
  document.getElementById('sugerencia').textContent = planta.sugerencia_suplementos || 'No hay sugerencias.';

  // --- Galería de Fotos ---
  const carouselInner = document.querySelector('#plant-carousel .carousel-inner');
  carouselInner.innerHTML = ''; // Limpiamos el carrusel
  if (planta.imagenes && planta.imagenes.length > 0) {
    planta.imagenes.forEach((imgUrl, index) => {
      const item = document.createElement('div');
      item.className = `carousel-item ${index === 0 ? 'active' : ''}`;
      item.innerHTML = `<img src="${imgUrl}" class="d-block w-100" alt="Imagen de la planta ${index + 1}">`;
      carouselInner.appendChild(item);
    });
  } else {
    carouselInner.innerHTML = `
      <div class="carousel-item active">
        <div class="d-flex align-items-center justify-content-center" style="height: 250px; background-color: #f8f9fa;">
          <p class="text-muted">Aún no hay fotos de esta planta</p>
        </div>
      </div>
    `;
  }
}

function toggleEditMode(enable) {
  isEditMode = enable;
  const fields = [
    { id: 'nombre', input: 'input-nombre' },
    { id: 'tamano', input: 'input-tamano' },
    { id: 'maceta', input: 'input-maceta', inputGroup: 'input-group-maceta' },
    { id: 'ultimoRiego', input: 'input-ultimoRiego' },
    { id: 'enFloracion', input: 'input-enFloracion' },
  ];

  fields.forEach(field => {
    const span = document.getElementById(field.id);
    const input = document.getElementById(field.input);
    const inputGroup = field.inputGroup ? document.getElementById(field.inputGroup) : null;

    if (span && input) {
      if (enable) {
        span.classList.add('d-none');
        if (inputGroup) inputGroup.classList.remove('d-none'); else input.classList.remove('d-none');
      } else {
        span.classList.remove('d-none');
        if (inputGroup) inputGroup.classList.add('d-none'); else input.classList.add('d-none');
      }
    }
  });

  document.getElementById('btn-editar-ficha').classList.toggle('d-none', enable);
  document.getElementById('btn-guardar-ficha').classList.toggle('d-none', !enable);
  document.getElementById('btn-cancelar-ficha').classList.toggle('d-none', !enable);
}

async function guardarFicha() {
  const plantId = getPlantIdFromURL();
  const btnGuardar = document.getElementById('btn-guardar-ficha');

  // 1. Deshabilitamos el botón y mostramos el spinner
  btnGuardar.disabled = true;
  btnGuardar.innerHTML = `
    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
    <span class="d-none d-md-inline"> Guardando...</span>
  `;
  // 1. Tomamos como base la data actual de la planta para asegurar que todos los campos estén.
  // 2. Sobrescribimos con los nuevos valores de los inputs.
  const payload = {
    ...currentPlantData, // Base con todos los campos (incluyendo tipo_planta)
    nombre_personalizado: document.getElementById('input-nombre').value,
    tamano_planta: document.getElementById('input-tamano').value,
    tamano_maceta_litros: parseFloat(document.getElementById('input-maceta').value),
    fecha_ultimo_riego: document.getElementById('input-ultimoRiego').value,
    en_floracion: document.getElementById('input-enFloracion').value === 'Si',
  };

  try {
    const putResponse = await fetchProtegido(`/api/plantas/${plantId}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!putResponse.ok) {
      const errorData = await putResponse.json();
      throw new Error(errorData.detail || 'Error al guardar cambios.');
    }

    // ¡LA CLAVE ESTÁ AQUÍ! Leemos el JSON de la respuesta del PUT.
    const plantaActualizada = await putResponse.json();

    mostrarToast('Ficha de planta actualizada con éxito.', 'success');

    renderizarDetalle(plantaActualizada); // Renderizamos con los datos que ya tenemos.
    toggleEditMode(false);
  } catch (error) {
    console.error('Error al guardar cambios:', error);
    mostrarToast(`Error: ${error.message}`, 'danger');
  } finally {
    // 3. Siempre, al final, restauramos el botón a su estado original
    btnGuardar.disabled = false;
    btnGuardar.innerHTML = `
      <i class="bi bi-save"></i> <span class="d-none d-md-inline">Guardar</span>
    `;
  }
}

function cancelarEdicion() {
  if (currentPlantData) {
    document.getElementById('input-nombre').value = currentPlantData.nombre_personalizado;
    document.getElementById('input-tamano').value = currentPlantData.tamano_planta;
    document.getElementById('input-maceta').value = currentPlantData.tamano_maceta_litros;
    document.getElementById('input-ultimoRiego').value = currentPlantData.fecha_ultimo_riego;
    document.getElementById('input-enFloracion').value = currentPlantData.en_floracion ? 'Si' : 'No';
  }
  toggleEditMode(false);
}

async function regarPlantaDetail() {
  const plantId = getPlantIdFromURL();
  if (!currentPlantData) return;

  const btnRegar = document.getElementById('btn-regar-detail');
  btnRegar.disabled = true;
  btnRegar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Regando...';

  try {
    const payload = { cantidad_agua_ml: currentPlantData.recommended_water_ml };
    const res = await fetchProtegido(`/api/plantas/${plantId}/regar/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error("Error en la respuesta del servidor al regar.");

    mostrarToast("🌿 ¡Planta regada con éxito!", "success");

    await cargarDatosPagina(plantId); // Llamamos a la función principal de carga.
  } catch (error) {
    console.error("❌ Error al regar planta:", error);
    mostrarToast(`No se pudo regar la planta: ${error.message}`, "danger");
  } finally {
    btnRegar.disabled = false;
    btnRegar.innerHTML = '<i class="bi bi-droplet me-2"></i>Regar Ahora';
  }
}

// --- NUEVAS FUNCIONES PARA ESTADÍSTICAS E HISTORIAL ---

function renderizarEstadisticas(stats) {
  const container = document.getElementById("stats-cards-container");
  container.innerHTML = "";

  if (!stats) return;

  const formatTotalWater = (ml) => {
    if (ml >= 1000) {
      return `${(ml / 1000).toFixed(2)} L`;
    }
    return `${ml} ml`;
  };

  const cards = [
    { icon: "bi-calendar-range", title: "Frecuencia Promedio", value: `${(stats.frecuencia_promedio_dias || 0).toFixed(1)} días` },
    { icon: "bi-droplet-fill", title: "Riegos Totales", value: `${stats.total_riegos || 0} riegos` },
    { icon: "bi-water", title: "Agua Promedio", value: stats.promedio_agua_ml > 0 ? `${Math.round(stats.promedio_agua_ml)} ml` : 'N/A' },
    { icon: "bi-bucket-fill", title: "Agua Total", value: stats.total_agua_ml > 0 ? formatTotalWater(stats.total_agua_ml) : 'N/A' },
    { icon: "bi-clock-history", title: "Último Riego", value: stats.ultimo_riego_fecha ? new Date(stats.ultimo_riego_fecha).toLocaleDateString() : 'N/A' },
  ];

  cards.forEach(card => {
    const col = document.createElement("div");
    // Usamos una clase que se adapte a 5 elementos. 'col' permite que Bootstrap los distribuya.
    col.className = "col-lg col-md-4 col-6";
    col.innerHTML = `
      <div class="card card-stat h-100">
        <div class="card-body text-center">
          <i class="${card.icon} display-6 text-violeta"></i>
          <h6 class="card-subtitle mt-2 mb-1 text-muted">${card.title}</h6>
          <p class="card-text fs-5 fw-bold text-dark">${card.value}</p>
        </div>
      </div>
    `;
    container.appendChild(col);
  });
}

function renderizarGrafico(historial) {
  let riegoChartInstance = window.myRiegoChart;
  const ctx = document.getElementById("riegoChart").getContext("2d");

  const labels = historial.map(riego => {
    return new Date(riego.fecha).toLocaleDateString('es-AR', { timeZone: 'UTC' });
  }).reverse();
  const data = historial.map(riego => riego.cantidad_agua_ml).reverse();

  if (riegoChartInstance) {
    riegoChartInstance.destroy();
  }

  window.myRiegoChart = new Chart(ctx, { // Guardamos la instancia en window para poder destruirla
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
  tbody.innerHTML = "";

  if (historial.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="text-center text-white-50">No hay riegos registrados.</td></tr>`;
    return;
  }

  historial.forEach(riego => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${new Date(riego.fecha).toLocaleDateString('es-AR', { timeZone: 'UTC' })}</td>
      <td>${riego.cantidad_agua_ml} ml</td>
      <td>${riego.comentarios || '<span class="text-white-50">Sin comentarios</span>'}</td>
    `;
    tbody.appendChild(tr);
  });
}

// LÓGICA DE CARGA PRINCIPAL (MANTENEMOS LA ORIGINAL)
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

// --- Lógica de Carga de Imágenes (Frontend UI) ---
function setupImageUpload() {
  const uploadArea = document.getElementById('upload-area');
  const fileInput = document.getElementById('file-input');
  const progressBar = document.querySelector('#upload-progress .progress-bar');
  const uploadProgressContainer = document.getElementById('upload-progress');

  if (!uploadArea || !fileInput) return;

  const preventDefaults = e => { e.preventDefault(); e.stopPropagation(); };
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  const highlight = () => uploadArea.classList.add('highlight');
  const unhighlight = () => uploadArea.classList.remove('highlight');
  ['dragenter', 'dragover'].forEach(eventName => uploadArea.addEventListener(eventName, highlight, false));
  ['dragleave', 'drop'].forEach(eventName => uploadArea.addEventListener(eventName, unhighlight, false));

  uploadArea.addEventListener('drop', e => handleFiles(e.dataTransfer.files), false);
  fileInput.addEventListener('change', e => handleFiles(e.target.files));

  function handleFiles(files) {
    if (files.length === 0) return;

    uploadProgressContainer.classList.remove('d-none');
    progressBar.style.width = '0%';
    progressBar.setAttribute('aria-valuenow', 0);
    progressBar.textContent = '0%';

    // Lógica de subida real a GCS (simulada por ahora)
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      if (progress > 100) progress = 100;
      progressBar.style.width = `${progress}%`;
      progressBar.setAttribute('aria-valuenow', progress);
      progressBar.textContent = `${progress}%`;

      if (progress === 100) {
        clearInterval(interval);
        mostrarToast(`✅ ${files.length} imagen(es) subida(s) (simulado).`, 'success');
        setTimeout(() => {
          uploadProgressContainer.classList.add('d-none');
          cargarDatosPagina(getPlantIdFromURL()); // Recargamos los datos para ver la nueva foto
        }, 1000);
      }
    }, 100);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const plantId = getPlantIdFromURL();
  if (!plantId) {
    mostrarToast("No se especificó una planta.", "danger");
    setTimeout(() => (window.location.href = "/dashboard/"), 2000);
    return;
  }

  // Llamada inicial para cargar todo
  cargarDatosPagina(plantId);

  // Listeners para los botones
  document.getElementById('btn-volver').addEventListener('click', () => {
    window.location.href = '/dashboard/'; // Navegamos al dashboard para forzar la recarga
  });
  document.getElementById('btn-editar-ficha').addEventListener('click', () => toggleEditMode(true));
  document.getElementById('btn-guardar-ficha').addEventListener('click', guardarFicha);
  document.getElementById('btn-cancelar-ficha').addEventListener('click', cancelarEdicion);
  document.getElementById('btn-regar-detail').addEventListener('click', regarPlantaDetail);

  setupImageUpload();
});
