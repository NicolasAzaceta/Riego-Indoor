document.getElementById("register-form").addEventListener("submit", function (e) {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  fetch("/api/auth/register/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, email, password })
  })
    .then(res => res.json())
    .then(data => {
      const msg = document.getElementById("register-message");
      if (data.message) {
        msg.textContent = "✅ Usuario creado correctamente";
        msg.className = "text-success";
      } else if (data.error) {
        msg.textContent = `❌ ${data.error}`;
        msg.className = "text-danger";
      }
    })
    .catch(err => {
      console.error("Error al registrar:", err);
      document.getElementById("register-message").textContent = "❌ Error inesperado";
    });
});