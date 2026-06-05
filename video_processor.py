"""
Video Processor Module
Procesamiento de video y extracción de frames para OCR
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple
from tqdm import tqdm


class VideoProcessor:
    """
    Clase para procesar videos y extraer frames para análisis OCR
    """
    
    def __init__(self, fps_extraction: float = 2.0):
        """
        Inicializar el procesador de video
        
        Args:
            fps_extraction: Frames por segundo a extraer del video
        """
        self.fps_extraction = fps_extraction
        self.video_path = None
        self.video_capture = None
        self.total_frames = 0
        self.fps_original = 0
        self.frame_interval = 1
        
    def open_video(self, video_path: str) -> bool:
        """
        Abrir un archivo de video
        
        Args:
            video_path: Ruta al archivo de video
            
        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        self.video_path = Path(video_path)
        
        if not self.video_path.exists():
            raise FileNotFoundError(f"El archivo de video no existe: {video_path}")
        
        self.video_capture = cv2.VideoCapture(str(self.video_path))
        
        if not self.video_capture.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")
        
        # Obtener información del video
        self.fps_original = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calcular intervalo de frames basado en FPS de extracción
        if self.fps_original > 0:
            self.frame_interval = max(1, int(self.fps_original / self.fps_extraction))
        
        return True
    
    def close_video(self):
        """Cerrar el archivo de video"""
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
    
    def extract_frames(self) -> Generator[Tuple[np.ndarray, float], None, None]:
        """
        Extraer frames del video para procesamiento OCR
        
        Yields:
            Tupla (frame, timestamp) donde:
                - frame: Imagen del frame (numpy array)
                - timestamp: Tiempo en segundos desde el inicio
        """
        if self.video_capture is None or not self.video_capture.isOpened():
            raise RuntimeError("El video no está abierto. Llame a open_video() primero.")
        
        frame_count = 0
        extracted_count = 0
        
        # Barra de progreso
        pbar = tqdm(total=self.total_frames, desc="Extrayendo frames", unit="frame")
        
        while True:
            ret, frame = self.video_capture.read()
            
            if not ret:
                break
            
            frame_count += 1
            pbar.update(1)
            
            # Extraer solo los frames según el intervalo calculado
            if frame_count % self.frame_interval == 0:
                # Calcular timestamp
                timestamp = frame_count / self.fps_original
                
                # Convertir BGR a RGB para mejor compatibilidad con OCR
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                yield frame_rgb, timestamp
                extracted_count += 1
        
        pbar.close()
        
        print(f"\nFrames extraídos: {extracted_count} de {self.total_frames} totales")
    
    def preprocess_frame_for_ocr(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocesar un frame para optimizar el reconocimiento OCR
        
        Args:
            frame: Frame original en formato RGB
            
        Returns:
            Frame preprocesado optimizado para OCR
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Aplicar desenfoque gaussiano para reducir ruido
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Mejorar contraste usando ecualización adaptativa
        enhanced = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Escalar para mejorar reconocimiento de texto pequeño
        height, width = enhanced.shape
        scale_factor = 1.5
        resized = cv2.resize(
            enhanced, 
            (int(width * scale_factor), int(height * scale_factor)),
            interpolation=cv2.INTER_CUBIC
        )
        
        return resized
    
    def get_video_info(self) -> dict:
        """
        Obtener información del video actual
        
        Returns:
            Diccionario con información del video
        """
        if self.video_capture is None:
            return {}
        
        width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = self.total_frames / self.fps_original if self.fps_original > 0 else 0
        
        return {
            'path': str(self.video_path),
            'width': width,
            'height': height,
            'fps': self.fps_original,
            'total_frames': self.total_frames,
            'duration_seconds': round(duration, 2),
            'extraction_fps': self.fps_extraction,
            'frame_interval': self.frame_interval
        }
