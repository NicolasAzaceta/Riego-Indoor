document.addEventListener("DOMContentLoaded", () => {
  // Simulación inicial, luego podemos conectar con API o sensores
  const location = "Córdoba, Argentina";
  const temperature = "72°F"; // Podés usar una API como OpenWeather si querés hacerlo dinámico

  document.getElementById("location").textContent = location;
  document.getElementById("temperature").textContent = temperature;

  document.getElementById("edit-settings").addEventListener("click", () => {
    alert("Funcionalidad de edición en desarrollo 🚧");
    // Acá podrías abrir un modal o redirigir a una pantalla de edición
  });
});