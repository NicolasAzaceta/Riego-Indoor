import { fetchProtegido } from './auth.js';

let imagenIdParaEliminar = null;
let deleteModal = null;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    const modalElement = document.getElementById('deleteImageModal');
    if (modalElement) {
        // Asumimos que bootstrap está disponible globalmente ya que se carga via CDN en el template
        if (typeof bootstrap !== 'undefined') {
            deleteModal = new bootstrap.Modal(modalElement);
        }
    }

    const btnConfirm = document.getElementById('btnConfirmDeleteImage');
    if (btnConfirm) {
        btnConfirm.addEventListener('click', confirmarEliminacion);
    }
});

// Función global para eliminar imágenes (llamada desde el HTML generado dinámicamente)
window.eliminarImagen = function (imagenId) {
    imagenIdParaEliminar = imagenId;

    // Si el modal no se inicializó (por ej. si el script corrió antes del DOMContentLoaded)
    if (!deleteModal) {
        const modalElement = document.getElementById('deleteImageModal');
        if (modalElement && typeof bootstrap !== 'undefined') {
            deleteModal = new bootstrap.Modal(modalElement);
        }
    }

    if (deleteModal) {
        deleteModal.show();
    } else {
        // Fallback porsiacaso
        if (confirm('¿Estás seguro de que deseas eliminar esta imagen?')) {
            confirmarEliminacion();
        }
    }
}

async function confirmarEliminacion() {
    if (!imagenIdParaEliminar) return;

    const btnConfirm = document.getElementById('btnConfirmDeleteImage');
    const originalText = btnConfirm ? btnConfirm.innerHTML : 'Eliminar';

    if (btnConfirm) {
        btnConfirm.disabled = true;
        btnConfirm.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Eliminando...';
    }

    const plantId = new URLSearchParams(window.location.search).get('id');

    try {
        const response = await fetchProtegido(`/api/plantas/${plantId}/imagenes/${imagenIdParaEliminar}/`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Error desconocido' }));
            throw new Error(errorData.error || 'Error al eliminar la imagen');
        }

        // Ocultar modal si existe
        if (deleteModal) {
            deleteModal.hide();
        }

        // Mostrar toast de éxito
        if (window.mostrarToast) {
            window.mostrarToast('🗑️ Imagen eliminada correctamente', 'success');
        }

        // Recargar página para reflejar cambios (solicitud explícita del usuario)
        // Damos un pequeño delay para que se llegue a ver el toast o la transición del modal
        setTimeout(() => {
            window.location.reload();
        }, 1000);

    } catch (error) {
        console.error('Error al eliminar imagen:', error);
        if (window.mostrarToast) {
            window.mostrarToast(`❌ ${error.message}`, 'danger');
        }

        // Restaurar botón y ocultar modal solo en error
        if (btnConfirm) {
            btnConfirm.disabled = false;
            btnConfirm.innerHTML = originalText;
        }
        if (deleteModal) deleteModal.hide();
    }
}
