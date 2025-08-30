document.getElementById("plant-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const token = localStorage.getItem("token");

  const data = {
    nombre: document.getElementById("nombre").value,
    tipo: document.getElementById("tipo").value,
    tamano: document.getElementById("tamano").value,
    ultimo_riego: document.getElementById("ultimo_riego").value,
  };

  try {
    await crearPlanta(data, token);
    alert("Planta creada con éxito");
    window.location.href = "index.html";
  } catch (err) {
    alert("Error al guardar la planta");
    console.error(err);
  }
});