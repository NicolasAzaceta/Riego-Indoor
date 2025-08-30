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