// Función para hacer login y obtener el token JWT
import { loginUsuario } from "./auth.js";

// // Evento submit del formulario de login
document.getElementById("login-form").addEventListener("submit", async (e) => {
   e.preventDefault();
   const username = document.getElementById("username").value;
   const password = document.getElementById("password").value;

   try {
     const { access, refresh } = await loginUsuario(username, password);
     mostrarToast("Login exitoso, ingresando...🌿");
     setTimeout(() => {
        window.location.href = "/home/dashboard/"; // Redirige a la página principal
      }, 2500);     
     } catch (err) {
     mostrarToast("Usuario o contraseña incorrectos");
     console.error(err);
     }
});

function mostrarToast(mensaje, tipo = "success") {
  const toastBody = document.getElementById("toast-body");
  const toast = document.getElementById("toast");

  toastBody.textContent = mensaje;
  toast.classList.remove("bg-success", "bg-danger", "bg-warning");
  toast.classList.add(`bg-${tipo}`);

  // Inicializar y mostrar el toast
  const bsToast = new bootstrap.Toast(toast, { delay: 2000 });
  bsToast.show();

}