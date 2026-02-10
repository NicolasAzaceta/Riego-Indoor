import { mostrarToast } from './api.js'; // Importamos mostrarToast desde api.js

document.addEventListener('DOMContentLoaded', () => {
    const registerSuccessModal = new bootstrap.Modal(document.getElementById('registerSuccessModal'));
    const registerErrorModal = new bootstrap.Modal(document.getElementById('registerErrorModal'));
    const btnAcceptSuccessRegister = document.getElementById('btnAcceptSuccessRegister');
    const registerErrorMessage = document.getElementById('registerErrorMessage');
    const registerForm = document.getElementById('register-form');

    if (registerForm) {
        // Toggle de visibilidad de contraseña
        const togglePassword = document.getElementById('togglePassword');
        const passwordInput = document.getElementById('password');
        const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');
        const confirmPasswordInput = document.getElementById('confirmPassword');

        function setupToggle(button, input) {
            button.addEventListener('click', () => {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                button.querySelector('i').classList.toggle('bi-eye');
                button.querySelector('i').classList.toggle('bi-eye-slash');
            });
        }

        setupToggle(togglePassword, passwordInput);
        setupToggle(toggleConfirmPassword, confirmPasswordInput);

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = passwordInput.value;
            const passwordConfirm = confirmPasswordInput.value;
            const registerErrorMessage = document.getElementById('registerErrorMessage');
            const registerErrorModal = new bootstrap.Modal(document.getElementById('registerErrorModal'));
            const registerSuccessModal = new bootstrap.Modal(document.getElementById('registerSuccessModal'));


            // Validación frontend de contraseñas
            if (password !== passwordConfirm) {
                registerErrorMessage.innerHTML = '❌ Las contraseñas no coinciden.';
                registerErrorModal.show();
                return;
            }

            try {
                const response = await fetch('/api/auth/register/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, email, password, password_confirm: passwordConfirm }),
                });

                const data = await response.json();

                if (response.ok) {
                    registerSuccessModal.show();
                } else {
                    let errorMessage = 'Error al registrar el usuario.';
                    if (data && typeof data === 'object') {
                        errorMessage = Object.values(data).flat().join('<br>');
                    }
                    registerErrorMessage.innerHTML = `❌ ${errorMessage}`;
                    registerErrorModal.show();
                }
            } catch (error) {
                console.error('Error in request:', error);
                registerErrorMessage.innerHTML = '❌ Error de conexión.';
                registerErrorModal.show();
            }
        });
    }

    // Event listener para el botón "Aceptar" del modal de éxito
    if (btnAcceptSuccessRegister) {
        btnAcceptSuccessRegister.addEventListener('click', () => {
            registerSuccessModal.hide();
            window.location.href = '/login/';
        });
    }
});