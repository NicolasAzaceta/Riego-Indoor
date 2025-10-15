import { fetchProtegido } from "./auth.js";
import { mostrarToast } from "./api.js";

function configurarBotonVolver(idBoton, destino) {
  const boton = document.getElementById(idBoton);
  if (boton) {
    boton.addEventListener("click", () => window.location.href = destino);
  }
}


document.addEventListener("DOMContentLoaded", () => {

  configurarBotonVolver("btn-volver", "/dashboard/");

  console.log("✅ add.js cargado");
  const form = document.getElementById("form-agregar-planta");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    console.log("✅ Listener activo, preventDefault ejecutado");
    // Aquí va tu lógica de envío por fetch

    const nombre = document.querySelector("#nombre").value.trim();
    const tipo = document.querySelector("#tipo").value.trim();
    const tamaño = document.querySelector("#tamano").value;
    const maceta = document.querySelector("#maceta").value.trim();
    const enFloracion = document.querySelector("#enFloracion").checked;
    const ultimoRiego = document.querySelector("#ultimo_riego").value;

    // Validación básica
    if (!nombre || !tipo || !tamaño || !ultimoRiego || !maceta) {
    mostrarToast("⚠️ Por favor, completá todos los campos.", "warning");
    return;
    }

    const nuevaPlanta = {
      nombre_personalizado: nombre,
      tipo_planta: tipo,
      tamano_planta: tamaño,
      tamano_maceta_litros: maceta,
      fecha_ultimo_riego: ultimoRiego,
      en_floracion: enFloracion,
    };
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
      alert("Hubo un problema al agregar la planta. Revisá los datos e intentá de nuevo.");
    }
  });
});
