import { logoutUsuario } from './auth.js';

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

document.addEventListener("DOMContentLoaded", () => {
  const btnLogout = document.getElementById("btnLogout");
  if (btnLogout) {
    btnLogout.addEventListener("click", (e) => {
      e.preventDefault(); // evita navegación por el href
      mostrarToast("👋 ¡Sesión cerrada! ¡Hasta luego!");
      setTimeout(() => logoutUsuario(), 2000);
    });
  }
});

document.getElementById("btnAgregarPlanta").addEventListener("click", () => {
  window.location.href = "/home/add/";
});


