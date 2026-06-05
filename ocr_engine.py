"""
OCR Engine Module
Motor de Reconocimiento Óptico de Caracteres con IA
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pytesseract
from PIL import Image


@dataclass
class OCRResult:
    """Resultado de reconocimiento OCR"""
    text: str
    confidence: float
    timestamp: float
    bounding_box: Optional[Tuple[int, int, int, int]] = None


class OCREngine:
    """
    Motor OCR para extraer texto de frames de video
    Soporta múltiples backends: Tesseract, PaddleOCR (configurable)
    """
    
    def __init__(
        self, 
        language: str = 'spa',
        confidence_threshold: float = 0.5,
        use_gpu: bool = False,
        ocr_engine: str = 'tesseract'
    ):
        """
        Inicializar el motor OCR
        
        Args:
            language: Código de idioma (spa=español, eng=inglés, etc.)
            confidence_threshold: Umbral mínimo de confianza (0.0-1.0)
            use_gpu: Usar aceleración GPU si está disponible
            ocr_engine: Motor a usar ('tesseract' o 'paddle')
        """
        self.language = language
        self.confidence_threshold = confidence_threshold
        self.use_gpu = use_gpu
        self.ocr_engine = ocr_engine
        
        # Configurar Tesseract
        self.tesseract_config = f'--oem 3 --psm 6 -l {language}'
        
        if use_gpu and ocr_engine == 'paddle':
            try:
                from paddleocr import PaddleOCR
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang=language[:2], use_gpu=True)
                print("✓ PaddleOCR inicializado con GPU")
            except ImportError:
                print("⚠ PaddleOCR no disponible, usando Tesseract")
                self.ocr_engine = 'tesseract'
        
        # Verificar disponibilidad de Tesseract
        if ocr_engine == 'tesseract':
            try:
                pytesseract.get_tesseract_version()
                print(f"✓ Tesseract OCR inicializado (idioma: {language})")
            except Exception as e:
                print(f"⚠ Error al verificar Tesseract: {e}")
                raise RuntimeError("Tesseract OCR no está instalado o configurado correctamente")
    
    def recognize_text(self, image: np.ndarray, timestamp: float) -> List[OCRResult]:
        """
        Reconocer texto en una imagen
        
        Args:
            image: Imagen en formato numpy array (RGB)
            timestamp: Timestamp del frame
            
        Returns:
            Lista de OCRResult con el texto detectado
        """
        if self.ocr_engine == 'paddle':
            return self._recognize_with_paddle(image, timestamp)
        else:
            return self._recognize_with_tesseract(image, timestamp)
    
    def _recognize_with_tesseract(
        self, 
        image: np.ndarray, 
        timestamp: float
    ) -> List[OCRResult]:
        """
        Reconocer texto usando Tesseract OCR
        
        Args:
            image: Imagen en formato numpy array
            timestamp: Timestamp del frame
            
        Returns:
            Lista de OCRResult
        """
        results = []
        
        # Convertir numpy array a imagen PIL
        pil_image = Image.fromarray(image)
        
        # Obtener datos detallados de Tesseract
        try:
            data = pytesseract.image_to_data(
                pil_image,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Procesar cada palabra detectada
            n_boxes = len(data['text'])
            current_text = ""
            current_confidence = 0
            current_box = None
            word_count = 0
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
                
                # Filtrar por umbral de confianza
                if conf >= self.confidence_threshold * 100 and text:
                    # Normalizar confianza a 0-1
                    normalized_conf = conf / 100.0
                    
                    # Obtener coordenadas del bounding box
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    # Agrupar palabras cercanas (misma línea)
                    if current_text and abs(y - current_box[1]) < 10:
                        current_text += " " + text
                        current_confidence = (current_confidence * word_count + normalized_conf) / (word_count + 1)
                        word_count += 1
                        current_box = (
                            min(current_box[0], x),
                            min(current_box[1], y),
                            max(current_box[2], x + w),
                            max(current_box[3], y + h)
                        )
                    else:
                        # Guardar texto anterior si existe
                        if current_text:
                            results.append(OCRResult(
                                text=current_text.strip(),
                                confidence=current_confidence,
                                timestamp=timestamp,
                                bounding_box=current_box
                            ))
                        
                        # Iniciar nuevo grupo
                        current_text = text
                        current_confidence = normalized_conf
                        current_box = (x, y, x + w, y + h)
                        word_count = 1
            
            # Agregar el último grupo
            if current_text:
                results.append(OCRResult(
                    text=current_text.strip(),
                    confidence=current_confidence,
                    timestamp=timestamp,
                    bounding_box=current_box
                ))
        
        except Exception as e:
            print(f"Error en OCR Tesseract: {e}")
            return []
        
        return results
    
    def _recognize_with_paddle(
        self, 
        image: np.ndarray, 
        timestamp: float
    ) -> List[OCRResult]:
        """
        Reconocer texto usando PaddleOCR
        
        Args:
            image: Imagen en formato numpy array
            timestamp: Timestamp del frame
            
        Returns:
            Lista de OCRResult
        """
        results = []
        
        try:
            # PaddleOCR espera BGR
            image_bgr = image[:, :, ::-1] if image.ndim == 3 else image
            
            # Ejecutar OCR
            result = self.paddle_ocr.ocr(image_bgr, cls=True)
            
            if result and result[0]:
                for line in result[0]:
                    bbox = line[0]
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    if confidence >= self.confidence_threshold:
                        # Convertir bbox a formato (x1, y1, x2, y2)
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]
                        bounding_box = (
                            min(x_coords),
                            min(y_coords),
                            max(x_coords),
                            max(y_coords)
                        )
                        
                        results.append(OCRResult(
                            text=text,
                            confidence=confidence,
                            timestamp=timestamp,
                            bounding_box=bounding_box
                        ))
        
        except Exception as e:
            print(f"Error en OCR Paddle: {e}")
            return []
        
        return results
    
    def filter_low_confidence(self, results: List[OCRResult]) -> List[OCRResult]:
        """
        Filtrar resultados por umbral de confianza
        
        Args:
            results: Lista de resultados OCR
            
        Returns:
            Lista filtrada
        """
        return [r for r in results if r.confidence >= self.confidence_threshold]
    
    def clean_text(self, text: str) -> str:
        """
        Limpiar texto reconocido (eliminar caracteres especiales, normalizar)
        
        Args:
            text: Texto crudo del OCR
            
        Returns:
            Texto limpio
        """
        import re
        
        # Eliminar caracteres especiales no imprimibles
        cleaned = re.sub(r'[^\w\s.,;:!?¿¡\'\"()-]', '', text)
        
        # Normalizar espacios múltiples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Eliminar espacios al inicio y final
        cleaned = cleaned.strip()
        
        return cleaned
