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

  const btnLogin = document.getElementById("btnLogin");
  const spinner = document.getElementById("loginSpinner");
  const btnText = document.getElementById("btnLoginText");
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  // Estado de carga
  btnLogin.disabled = true;
  spinner.classList.remove("d-none");
  btnText.textContent = "Ingresando...";

  try {
    const { access, refresh } = await loginUsuario(username, password);
    // Mantener spinner mientras redirige
    mostrarToast("Login exitoso, ingresando...🌿");
    setTimeout(() => {
      window.location.href = "/dashboard/"; // Redirige a la página principal
    }, 1500); // Reducido a 1.5s para que sea más ágil     
  } catch (err) {
    // Restaurar estado si hay error
    mostrarToast(err.message || "Usuario o contraseña incorrectos", "danger");
    console.error(err);
    btnLogin.disabled = false;
    spinner.classList.add("d-none");
    btnText.innerHTML = '<i class="bi bi-box-arrow-in-right me-2"></i>Entrar'; // Restaurar ícono
  }
});

function mostrarToast(mensaje, tipo = "success") {
  const toastBody = document.getElementById("toast-body");
  const toast = document.getElementById("toast");

  toastBody.textContent = mensaje; toast.classList.remove("bg-success", "bg-danger", "bg-warning", "bg-violeta");

  const claseBg = tipo === "success" ? "bg-violeta" : `bg-${tipo}`;
  toast.classList.add(claseBg);

  // Inicializar y mostrar el toast
  const bsToast = new bootstrap.Toast(toast, { delay: 2000 });
  bsToast.show();

}