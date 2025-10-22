import { mostrarToast } from './api.js'; // Importamos mostrarToast desde api.js

document.addEventListener('DOMContentLoaded', () => {
    const registerSuccessModal = new bootstrap.Modal(document.getElementById('registerSuccessModal'));
    const registerErrorModal = new bootstrap.Modal(document.getElementById('registerErrorModal'));
    const btnAcceptSuccessRegister = document.getElementById('btnAcceptSuccessRegister');
    const registerErrorMessage = document.getElementById('registerErrorMessage');
    const registerForm = document.getElementById('register-form');

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // Previene el envío tradicional del formulario

            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/api/auth/register/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, email, password }),
                });

                const data = await response.json();

                if (response.ok) {
                    registerSuccessModal.show();
                    // La redirección se manejará con el botón "Aceptar" del modal
                } else {
                    // Manejar errores de la API (ej. nombre de usuario ya existe, email inválido)
                    let errorMessage = 'Error al registrar el usuario.';
                    if (data && typeof data === 'object') {
                        // DRF a menudo devuelve errores como { "campo": ["mensaje de error"] }
                        errorMessage = Object.values(data).flat().join('<br>'); // Usar <br> para saltos de línea en el modal
                    } else if (data && data.detail) {
                        errorMessage = data.detail;
                    }
                    registerErrorMessage.innerHTML = `❌ ${errorMessage}`;
                    registerErrorModal.show();
                }
            } catch (error) {
                console.error('Error en la solicitud de registro:', error);
                registerErrorMessage.innerHTML = '❌ Error de conexión. Intenta de nuevo más tarde.';
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