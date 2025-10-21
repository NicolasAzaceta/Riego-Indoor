// Función para hacer login y obtener el token JWT
import { loginUsuario } from "./auth.js";


document.addEventListener("DOMContentLoaded", () => {
  lottie.loadAnimation({
    container: document.getElementById("lottie-login"),
    renderer: "svg",
    loop: true,
    autoplay: true,
    path: "/static/assets/animaciones/plant.json" // Ajustá la ruta según tu estructura
  });
});



// // Evento submit del formulario de login
document.getElementById("login-form").addEventListener("submit", async (e) => {
   e.preventDefault();
   const username = document.getElementById("username").value;
   const password = document.getElementById("password").value;

   try {
     const { access, refresh } = await loginUsuario(username, password);
     mostrarToast("Login exitoso, ingresando...🌿");
     setTimeout(() => {
        window.location.href = "/dashboard/"; // Redirige a la página principal
      }, 2500);     
     } catch (err) {
     mostrarToast("Usuario o contraseña incorrectos");
     console.error(err);
     }
});

function mostrarToast(mensaje, tipo = "success") {
  const toastBody = document.getElementById("toast-body");
  const toast = document.getElementById("toast");

  toastBody.textContent = mensaje;  toast.classList.remove("bg-success", "bg-danger", "bg-warning", "bg-violeta");

  const claseBg = tipo === "success" ? "bg-violeta" : `bg-${tipo}`;
  toast.classList.add(claseBg);

  // Inicializar y mostrar el toast
  const bsToast = new bootstrap.Toast(toast, { delay: 2000 });
  bsToast.show();

}