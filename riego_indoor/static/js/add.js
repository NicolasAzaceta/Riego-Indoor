document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#form-agregar-planta");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nombre = document.querySelector("#nombre").value.trim();
    const tipo = document.querySelector("#tipo").value.trim();
    const tamaño = document.querySelector("#tamano").value;
    const maceta = document.querySelector("#maceta").value.trim();
    //const enFloracion = document.querySelector("#en_floracion").checked;
    const ultimoRiego = document.querySelector("#ultimo_riego").value;

    // Validación básica
    if (!nombre || !tipo || !tamaño || !ultimoRiego || !maceta) {
    alert("Por favor, completá todos los campos.");
    return;
    }

    const nuevaPlanta = {
      nombre_personalizado: nombre,
      tipo_planta: tipo,
      tamano_planta: tamaño,
      tamano_maceta_litros: maceta,
      fecha_ultimo_riego: ultimoRiego,
      //en_floracion: enFloracion,
    };
    try {
      const token = await obtenerTokenValido();
      const res = await fetch("/api/plantas/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(nuevaPlanta),
      });

      if (!res.ok) throw new Error("Error al guardar la planta");

      // Feedback visual y redirección
      alert("🌱 Planta guardada con éxito");
      window.location.href = "home/dashboard/";
    } catch (err) {
      console.error(err);
      alert("Hubo un problema al agregar la planta. Revisá los datos e intentá de nuevo.");
    }
  });
});
