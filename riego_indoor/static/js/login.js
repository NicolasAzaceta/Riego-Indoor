// Función para validar que el backend está activo y responde correctamente
// function validarInicio() {
//   fetch('http://127.0.0.1:8000/home/', {
//     method: 'GET',
//     headers: {
//       'Content-Type': 'application/json'
//     }
//   })
//   .then(response => {
//     if (!response.ok) {
//       throw new Error(`Error al conectar con /home/: ${response.status}`);
//     }
//     return response.json(); // o .text() si el backend devuelve HTML plano
//   })
//   .then(data => {
//     console.log('Respuesta de /home/:', data);
//     // Podés mostrar un mensaje visual o habilitar el formulario de login
//     document.getElementById('estado-backend').textContent = 'Backend activo ✅';
//   })
//   .catch(error => {
//     console.error('Fallo en la conexión con /home/:', error);
//     document.getElementById('estado-backend').textContent = 'Backend inactivo ❌';
//   });
// }

// // Ejecutar la validación al cargar la página
// window.addEventListener('DOMContentLoaded', validarInicio);

// Función para hacer login y obtener el token JWT
async function loginUsuario(username, password) {
  const response = await fetch("http://127.0.0.1:8000/api/auth/token/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    throw new Error("Usuario o contraseña incorrectos");
  }

  return await response.json(); // Devuelve { access, refresh }
}

// Evento submit del formulario de login
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const { access } = await loginUsuario(username, password);
    localStorage.setItem("token", access); // Guarda el token para usarlo después
    alert("Login exitoso");
    window.location.href = "index.html"; // Redirige a la página principal
  } catch (err) {
    alert("Usuario o contraseña incorrectos");
    console.error(err);
  }
});

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const { access } = await loginUsuario(username, password);
    localStorage.setItem("token", access);
    alert("Login exitoso");
    window.location.href = "index.html";
  } catch (err) {
    alert("Usuario o contraseña incorrectos");
    console.error(err);
  }
});