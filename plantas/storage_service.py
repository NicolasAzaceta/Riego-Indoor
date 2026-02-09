"""
Servicio para gestionar uploads de imágenes a Google Cloud Storage.
Maneja validación, resize, upload y eliminación de imágenes de plantas.
"""

import logging
import uuid
from io import BytesIO
from google.cloud import storage
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)


class PlantImageStorageService:
    """Servicio para gestionar uploads de imágenes a Google Cloud Storage"""
    
    # Configuración
    MAX_IMAGE_SIZE_MB = 5
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
    MAX_DIMENSIONS = (1200, 1200)  # Máximo 1200x1200px
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    JPEG_QUALITY = 85
    
    def __init__(self):
        """
        Inicializa el cliente de Google Cloud Storage.
        Lee credenciales desde el archivo configurado en settings.
        """
        try:
            credentials_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
            self.client = storage.Client.from_service_account_json(credentials_path)
            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
            logger.info(f"GCS Client inicializado con bucket: {settings.GCS_BUCKET_NAME}")
        except Exception as e:
            logger.error(f"Error al inicializar GCS Client: {e}")
            raise
    
    def _validate_file(self, file):
        """
        Valida que el archivo sea una imagen válida.
        
        Args:
            file: UploadedFile de Django
            
        Raises:
            ValueError: Si el archivo no es válido
        """
        # Validar tipo MIME
        if not file.content_type or not file.content_type.startswith('image/'):
            raise ValueError("El archivo debe ser una imagen")
        
        # Validar tamaño
        if file.size > self.MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"La imagen no puede superar {self.MAX_IMAGE_SIZE_MB}MB")
        
        # Validar extensión
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Formato no permitido. Use: {', '.join(self.ALLOWED_EXTENSIONS)}")
    
    def _process_image(self, file):
        """
        Procesa la imagen: abre, redimensiona si es necesario, y optimiza.
        
        Args:
            file: UploadedFile de Django
            
        Returns:
            tuple: (BytesIO con imagen procesada, formato)
        """
        try:
            # Abrir imagen
            image = Image.open(file)
            
            # Convertir RGBA a RGB si es necesario (para JPEG)
            if image.mode == 'RGBA':
                # Crear fondo blanco
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])  # 3 es el canal alpha
                image = background
            elif image.mode not in ('RGB', 'L'):  # L es grayscale
                image = image.convert('RGB')
            
            # Redimensionar si excede las dimensiones máximas
            image.thumbnail(self.MAX_DIMENSIONS, Image.Resampling.LANCZOS)
            
            # Determinar formato de salida
            original_format = image.format or 'JPEG'
            output_format = 'JPEG' if original_format.upper() not in ['PNG', 'WEBP'] else original_format
            
            # Convertir a bytes
            output = BytesIO()
            if output_format == 'JPEG':
                image.save(output, format='JPEG', quality=self.JPEG_QUALITY, optimize=True)
            else:
                image.save(output, format=output_format, optimize=True)
            
            output.seek(0)
            
            logger.info(f"Imagen procesada: {image.size}, formato: {output_format}")
            return output, output_format
            
        except Exception as e:
            logger.error(f"Error al procesar imagen: {e}")
            raise ValueError(f"No se pudo procesar la imagen: {str(e)}")
    
    def upload_image(self, file, plant_id):
        """
        Sube una imagen a GCS y retorna la URL pública.
        
        Args:
            file: Archivo UploadedFile de Django
            plant_id: ID de la planta asociada
            
        Returns:
            tuple: (public_url, blob_name)
            
        Raises:
            ValueError: Si la validación falla
            Exception: Si ocurre un error en el upload
        """
        # Validar archivo
        self._validate_file(file)
        
        # Procesar imagen
        processed_image, image_format = self._process_image(file)
        
        # Generar nombre único
        file_extension = image_format.lower()
        if file_extension == 'jpeg':
            file_extension = 'jpg'
        
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        blob_name = f"plantas/{plant_id}/{unique_filename}"
        
        # Subir a GCS
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_file(
                processed_image,
                content_type=f"image/{file_extension}",
                timeout=30
            )
            
            # Obtener URL pública
            public_url = blob.public_url
            
            logger.info(f"Imagen subida exitosamente a GCS: {blob_name}")
            return public_url, blob_name
            
        except Exception as e:
            logger.error(f"Error al subir imagen a GCS: {e}")
            raise Exception(f"Error al subir imagen: {str(e)}")
    
    def delete_image(self, blob_name):
        """
        Elimina una imagen de GCS.
        
        Args:
            blob_name: Nombre del blob en GCS
            
        Returns:
            bool: True si se eliminó exitosamente, False si ocurrió un error
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Imagen eliminada de GCS: {blob_name}")
            return True
        except Exception as e:
            logger.warning(f"Error al eliminar imagen {blob_name} de GCS: {e}")
            # No lanzamos excepción porque la imagen podría ya no existir
            return False
