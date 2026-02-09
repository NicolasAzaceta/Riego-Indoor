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
    try:
        storage_service = PlantImageStorageService()
        storage_service.delete_image(instance.gcs_blob_name)
        logger.info(f"Imagen {instance.gcs_blob_name} eliminada de GCS por signal")
    except Exception as e:
        logger.error(f"Error al eliminar imagen {instance.gcs_blob_name} de GCS en signal: {e}")
