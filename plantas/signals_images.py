"""
Signals para gestionar eliminación automática de imágenes de GCS
cuando se elimina una planta.
"""

import logging
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import ImagenPlanta
from .storage_service import PlantImageStorageService

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=ImagenPlanta)
def delete_image_from_gcs(sender, instance, **kwargs):
    """
    Signal para eliminar automáticamente la imagen de GCS cuando
    se elimina el registro de ImagenPlanta en la base de datos.
    
    Esto también se activa cuando se elimina la Planta (CASCADE).
    """
    if not instance.gcs_blob_name:
        return

    try:
        storage_service = PlantImageStorageService()
        
        # Intentar eliminar. Si no existe, delete_image podría lanzar excepción
        # o devolver False dependiendo de la implementación.
        # Aquí asumimos que storage_service.delete_image maneja la lógica.
        storage_service.delete_image(instance.gcs_blob_name)
        
    except Exception as e:
        # Si es un error de "no encontrado", es benigno (ya se borró o nunca existió)
        if "Not Found" in str(e) or "404" in str(e):
            logger.info(f"Imagen {instance.gcs_blob_name} no encontrada en GCS (probablemente ya eliminada)")
        else:
            logger.error(f"Error al eliminar imagen {instance.gcs_blob_name} de GCS en signal: {e}")
