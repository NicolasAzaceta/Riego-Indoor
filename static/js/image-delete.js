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
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al eliminar la imagen');
        }

        mostrarToast('🗑️ Imagen eliminada correctamente', 'success');

        // Recargar galería
        setTimeout(() => {
            cargarDatosPagina(plantId);
        }, 500);

    } catch (error) {
        console.error('Error al eliminar imagen:', error);
        mostrarToast(`❌ ${error.message}`, 'danger');
    }
}
