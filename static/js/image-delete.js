import { fetchProtegido } from './auth.js';

// Función global para eliminar imágenes (llamada desde el HTML generado dinámicamente)
window.eliminarImagen = async function (imagenId) {
    if (!confirm('¿Estás seguro de que deseas eliminar esta imagen?')) {
        return;
    }

    const plantId = new URLSearchParams(window.location.search).get('id');

    try {
        const response = await fetchProtegido(`/api/plantas/${plantId}/imagenes/${imagenId}/`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Error desconocido' }));
            throw new Error(errorData.error || 'Error al eliminar la imagen');
        }

        // Mostrar toast de éxito
        if (window.mostrarToast) {
            window.mostrarToast('🗑️ Imagen eliminada correctamente', 'success');
        }

        // Recargar galería
        if (window.cargarDatosPagina) {
            setTimeout(() => {
                window.cargarDatosPagina(plantId);
            }, 500);
        }

    } catch (error) {
        console.error('Error al eliminar imagen:', error);
        if (window.mostrarToast) {
            window.mostrarToast(`❌ ${error.message}`, 'danger');
        }
    }
}
