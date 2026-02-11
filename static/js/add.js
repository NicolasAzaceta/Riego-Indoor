import { fetchProtegido } from "./auth.js";
import { mostrarToast } from "./api.js";

function configurarBotonVolver(idBoton, destino) {
  const boton = document.getElementById(idBoton);
  if (boton) {
    boton.addEventListener("click", () => window.location.href = destino);
  }
}

/**
 * Muestra/oculta campos según la categoría botánica seleccionada.
 * Cannabis: muestra tipo_planta, oculta campos manuales
 * Otras: oculta tipo_planta, muestra campos manuales
 */
function toggleCamposPorCategoria() {
  const categoria = document.getElementById("categoria_botanica").value;
  const containerTipo = document.getElementById("container-tipo-planta");
  const containerManuales = document.getElementById("container-campos-manuales");
  const selectTipo = document.getElementById("tipo");
  const inputFrecuencia = document.getElementById("frecuencia_riego_manual");
  const inputCantidad = document.getElementById("cantidad_agua_manual");

  if (categoria === "Cannabis") {
    containerTipo.style.display = "";
    containerManuales.style.display = "none";
    selectTipo.required = true;
    inputFrecuencia.required = false;
    inputCantidad.required = false;
    // Limpiar campos manuales
    inputFrecuencia.value = "";
    inputCantidad.value = "";
  } else {
    // Otras
    containerTipo.style.display = "none";
    containerManuales.style.display = "";
    selectTipo.required = false;
    selectTipo.value = ""; // Limpiar selección
    inputFrecuencia.required = true;
    inputCantidad.required = true;
  }
}


document.addEventListener("DOMContentLoaded", () => {

  configurarBotonVolver("btn-volver", "/dashboard/");

  // Escuchar cambios en categoría botánica
  const selectCategoria = document.getElementById("categoria_botanica");
  if (selectCategoria) {
    selectCategoria.addEventListener("change", toggleCamposPorCategoria);
    // Ejecutar una vez al cargar por si el valor ya está seteado
    toggleCamposPorCategoria();
  }

  console.log("✅ add.js cargado");
  const form = document.getElementById("form-agregar-planta");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("✅ Listener activo, preventDefault ejecutado");

    const nombre = document.querySelector("#nombre").value.trim();
    const categoriaBotanica = document.querySelector("#categoria_botanica").value;
    const tipo = document.querySelector("#tipo").value.trim();
    const tamaño = document.querySelector("#tamano").value;
    const tipoCultivo = document.querySelector("#tipo_cultivo").value;
    const maceta = document.querySelector("#maceta").value.trim();
    const enFloracion = document.querySelector("#enFloracion").checked;
    const ultimoRiego = document.querySelector("#ultimo_riego").value;
    const frecuenciaManual = document.querySelector("#frecuencia_riego_manual").value;
    const cantidadManual = document.querySelector("#cantidad_agua_manual").value;

    // Validación básica común
    if (!nombre || !tamaño || !tipoCultivo || !ultimoRiego || !maceta) {
      mostrarToast("⚠️ Por favor, completá todos los campos obligatorios.", "warning");
      return;
    }

    // Validación condicional
    if (categoriaBotanica === "Cannabis" && !tipo) {
      mostrarToast("⚠️ Seleccioná el tipo de planta (Autofloreciente o Fotoperiódica).", "warning");
      return;
    }
    if (categoriaBotanica === "Otras" && (!frecuenciaManual || !cantidadManual)) {
      mostrarToast("⚠️ Completá la frecuencia de riego y la cantidad de agua.", "warning");
      return;
    }

    const nuevaPlanta = {
      nombre_personalizado: nombre,
      categoria_botanica: categoriaBotanica,
      tipo_planta: categoriaBotanica === "Cannabis" ? tipo : null,
      tamano_planta: tamaño,
      tipo_cultivo: tipoCultivo,
      tamano_maceta_litros: maceta,
      fecha_ultimo_riego: ultimoRiego,
      en_floracion: enFloracion,
      frecuencia_riego_manual: categoriaBotanica === "Otras" ? parseInt(frecuenciaManual) : null,
      cantidad_agua_manual_ml: categoriaBotanica === "Otras" ? parseInt(cantidadManual) : null,
    };

    const btnSubmit = form.querySelector('button[type="submit"]');
    const originalBtnText = btnSubmit.innerHTML;

    // Deshabilitar botón y mostrar spinner
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Guardando...`;

    try {
      const res = await fetchProtegido("/api/plantas/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(nuevaPlanta)
      });
      if (!res.ok) throw new Error("Error al guardar la planta");

      // Feedback visual y redirección 
      mostrarToast("🌱 Planta guardada con éxito");
      setTimeout(() => {
        window.location.href = "/add/";
      }, 2500);


    } catch (err) {
      console.error(err);
      mostrarToast("❌ Hubo un problema al agregar la planta. Revisá los datos.", "danger");
    } finally {
      // Restaurar botón (si no redirige inmediatamente o si hubo error)
      if (btnSubmit.disabled) { // Pequeño check por si acaso
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = originalBtnText;
      }
    }
  });
});
