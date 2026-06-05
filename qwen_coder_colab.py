# ==============================================================================
# AGENTE QWEN CODER - Google Colab Notebook
# Extrae subtítulos incrustados (hardcoded) de videos usando OCR con IA
# 
# INSTRUCCIONES DE USO:
# 1. Abre Google Colab: https://colab.research.google.com
# 2. Crea un nuevo notebook
# 3. Copia cada CELDA en una celda separada de Colab
# 4. Ejecuta las celdas en orden secuencial
# 5. Los resultados se guardarán en tu Google Drive
# ==============================================================================

# ==============================================================================
# CELDA 1/8: MONTAR GOOGLE DRIVE Y CONFIGURAR DIRECTORIOS
# ==============================================================================
"""
from google.colab import drive
import os

# Montar Google Drive
print("🔗 Montando Google Drive...")
drive.mount('/content/drive')

# Crear directorio de salida
output_dir = "/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder"
os.makedirs(output_dir, exist_ok=True)
print(f"✓ Directorio creado: {output_dir}")

# Verificar video
video_path = "/content/drive/MyDrive/Vimeo_Downloads/Sergei Vasiliev Interview 01/10.mp4"
if os.path.exists(video_path):
    print(f"✓ Video encontrado: {video_path}")
else:
    print(f"⚠️ ADVERTENCIA: Video no encontrado en {video_path}")
    print("   Verifica que la ruta es correcta en tu Google Drive")
"""


# ==============================================================================
# CELDA 2/8: INSTALAR DEPENDENCIAS
# ==============================================================================
"""
print("📦 Instalando dependencias...")

# Instalar paquetes Python
!pip install opencv-python-headless pillow numpy pandas tqdm pytesseract -q

# Instalar Tesseract OCR
!apt-get install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng > /dev/null 2>&1

# Instalar PaddleOCR (más preciso para texto en videos)
!pip install paddlepaddle paddleocr -q

print("✓ Dependencias instaladas correctamente")
"""


# ==============================================================================
# CELDA 3/8: VIDEO PROCESSOR
# ==============================================================================

import cv2
import numpy as np
from typing import List, Tuple
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Procesa videos y extrae frames para OCR"""
    
    def __init__(self, fps: float = 2.0):
        self.fps = fps
        
    def extract_frames(self, video_path: str) -> List[Tuple[np.ndarray, float]]:
        """Extrae frames del video con timestamps"""
        logger.info(f"Extrayendo frames de {video_path} a {self.fps} fps")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / video_fps
        
        logger.info(f"Video: {total_frames} frames, {video_fps:.2f} fps, {duration:.2f}s")
        
        frame_interval = max(1, int(video_fps / self.fps))
        
        frames_with_timestamps = []
        frame_count = 0
        
        pbar = tqdm(total=total_frames, desc="🎬 Extrayendo frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp = frame_count / video_fps
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames_with_timestamps.append((frame_rgb, timestamp))
                
            frame_count += 1
            pbar.update(1)
            
        cap.release()
        pbar.close()
        
        logger.info(f"✓ Frames extraídos: {len(frames_with_timestamps)}")
        return frames_with_timestamps
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocesa frame para mejorar OCR"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((1, 1), np.uint8)
        denoised = cv2.morphologyOps(thresh, cv2.MORPH_CLOSE, kernel)
        return denoised


# ==============================================================================
# CELDA 4/8: OCR ENGINE
# ==============================================================================

from typing import Dict, Optional


class OCREngine:
    """Motor OCR para extraer texto de imágenes"""
    
    def __init__(self, engine: str = 'paddle', language: str = 'es', use_gpu: bool = True):
        self.engine = engine
        self.language = language
        self.use_gpu = use_gpu
        
        if engine == 'paddle':
            self._init_paddle()
        else:
            self._init_tesseract()
            
    def _init_paddle(self):
        """Inicializar PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            
            lang_map = {'es': 'es', 'en': 'en', 'fr': 'fr', 'de': 'german', 'it': 'it', 'pt': 'pt'}
            lang = lang_map.get(self.language, 'en')
            
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=self.use_gpu,
                show_log=False
            )
            logger.info("✓ PaddleOCR inicializado")
        except Exception as e:
            logger.warning(f"PaddleOCR falló: {e}. Usando Tesseract.")
            self.engine = 'tesseract'
            self._init_tesseract()
    
    def _init_tesseract(self):
        """Inicializar Tesseract OCR"""
        import pytesseract
        
        lang_map = {'es': 'spa', 'en': 'eng', 'fr': 'fra', 'de': 'deu', 'it': 'ita', 'pt': 'por'}
        self.tesseract_lang = lang_map.get(self.language, 'eng')
        logger.info(f"✓ Tesseract OCR inicializado ({self.tesseract_lang})")
    
    def detect_text(self, image: np.ndarray, min_confidence: float = 0.5) -> List[Dict]:
        """Detecta texto en una imagen"""
        if self.engine == 'paddle':
            return self._detect_with_paddle(image, min_confidence)
        else:
            return self._detect_with_tesseract(image, min_confidence)
    
    def _detect_with_paddle(self, image: np.ndarray, min_confidence: float) -> List[Dict]:
        """Detectar texto con PaddleOCR"""
        try:
            result = self.ocr.ocr(image, cls=True)
            
            detections = []
            if result and result[0]:
                for line in result[0]:
                    bbox, (text, confidence) = line
                    if confidence >= min_confidence and text.strip():
                        detections.append({
                            'text': text.strip(),
                            'confidence': confidence,
                            'bbox': bbox,
                        })
            return detections
        except Exception as e:
            logger.error(f"Error PaddleOCR: {e}")
            return []
    
    def _detect_with_tesseract(self, image: np.ndarray, min_confidence: float) -> List[Dict]:
        """Detectar texto con Tesseract"""
        import pytesseract
        
        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_lang,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            detections = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf >= int(min_confidence * 100):
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                    
                    detections.append({
                        'text': text,
                        'confidence': conf / 100.0,
                        'bbox': bbox,
                    })
            
            return detections
        except Exception as e:
            logger.error(f"Error Tesseract: {e}")
            return []


# ==============================================================================
# CELDA 5/8: SUBTITLE SYNC
# ==============================================================================

from collections import defaultdict


class SubtitleSync:
    """Sincroniza detecciones de texto en subtítulos coherentes"""
    
    def __init__(self, merge_threshold: float = 2.0, min_duration: float = 0.5):
        self.merge_threshold = merge_threshold
        self.min_duration = min_duration
    
    def sync_detections(
        self, 
        all_detections: List[Dict],
        frame_timestamps: List[float]
    ) -> List[Dict]:
        """Sincroniza detecciones de texto a través de frames"""
        if not all_detections:
            return []
        
        groups = self._group_similar_texts(all_detections)
        
        subtitles = []
        for group in groups:
            subtitle = self._create_subtitle_from_group(group)
            if subtitle:
                subtitles.append(subtitle)
        
        subtitles.sort(key=lambda x: x['start'])
        subtitles = self._merge_overlapping_subtitles(subtitles)
        
        return subtitles
    
    def _group_similar_texts(self, detections: List[Dict]) -> List[List[Dict]]:
        """Agrupa detecciones con texto similar"""
        groups = []
        used = set()
        
        for i, det in enumerate(detections):
            if i in used:
                continue
                
            group = [det]
            used.add(i)
            
            for j, other_det in enumerate(detections[i+1:], start=i+1):
                if j in used:
                    continue
                
                similarity = self._text_similarity(det['text'], other_det['text'])
                time_diff = abs(other_det['timestamp'] - det['timestamp'])
                
                if similarity > 0.7 and time_diff < self.merge_threshold:
                    group.append(other_det)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre textos"""
        text1, text2 = text1.lower().strip(), text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0.0
        
        common = sum(1 for a, b in zip(text1, text2) if a == b)
        return common / max_len
    
    def _create_subtitle_from_group(self, group: List[Dict]) -> Optional[Dict]:
        """Crea subtítulo desde grupo de detecciones"""
        if not group:
            return None
        
        timestamps = [d['timestamp'] for d in group]
        start_time = min(timestamps)
        end_time = max(timestamps) + 1.0
        
        if end_time - start_time < self.min_duration:
            end_time = start_time + self.min_duration
        
        best_det = max(group, key=lambda x: x['confidence'])
        avg_confidence = np.mean([d['confidence'] for d in group])
        
        return {
            'text': best_det['text'],
            'start': start_time,
            'end': end_time,
            'confidence': avg_confidence,
            'detection_count': len(group),
        }
    
    def _merge_overlapping_subtitles(self, subtitles: List[Dict]) -> List[Dict]:
        """Merge de subtítulos superpuestos"""
        if len(subtitles) <= 1:
            return subtitles
        
        merged = []
        current = subtitles[0].copy()
        
        for next_sub in subtitles[1:]:
            if next_sub['start'] < current['end']:
                current['end'] = max(current['end'], next_sub['end'])
                
                if self._text_similarity(current['text'], next_sub['text']) <= 0.8:
                    current['text'] = current['text'] + " | " + next_sub['text']
            else:
                merged.append(current)
                current = next_sub.copy()
        
        merged.append(current)
        return merged


# ==============================================================================
# CELDA 6/8: SRT GENERATOR
# ==============================================================================

class SRTGenerator:
    """Genera archivos de subtítulos en formato .srt"""
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Convierte segundos a formato SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    @staticmethod
    def generate_srt(subtitles: List[Dict], output_path: str) -> int:
        """Genera archivo SRT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles, start=1):
                f.write(f"{i}\n")
                start = SRTGenerator.format_timestamp(sub['start'])
                end = SRTGenerator.format_timestamp(sub['end'])
                f.write(f"{start} --> {end}\n")
                f.write(f"{sub['text']}\n\n")
        
        return len(subtitles)
    
    @staticmethod
    def validate_srt(file_path: str) -> bool:
        """Valida formato SRT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return False
            
            blocks = content.strip().split('\n\n')
            if len(blocks) == 0:
                return False
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    return False
                
                if not lines[0].isdigit():
                    return False
                
                if '-->' not in lines[1]:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validando SRT: {e}")
            return False


# ==============================================================================
# CELDA 7/8: QWEN CODER AGENT (ORQUESTADOR PRINCIPAL)
# ==============================================================================

import time
from typing import Dict, Any


class QwenCoderAgent:
    """Agente principal para extracción de subtítulos hardcoded"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.language = self.config.get('language', 'es')
        self.fps = self.config.get('fps', 2.0)
        self.use_gpu = self.config.get('use_gpu', True)
        self.ocr_engine = self.config.get('ocr_engine', 'paddle')
        self.min_confidence = self.config.get('min_confidence', 0.5)
        self.merge_threshold = self.config.get('merge_threshold', 2.0)
        
        self.video_processor = VideoProcessor(fps=self.fps)
        self.ocr_engine_instance = OCREngine(
            engine=self.ocr_engine,
            language=self.language,
            use_gpu=self.use_gpu
        )
        self.subtitle_sync = SubtitleSync(
            merge_threshold=self.merge_threshold,
            min_duration=0.5
        )
    
    def process_video(self, video_path: str, output_path: str) -> Dict[str, Any]:
        """Procesa video completo y genera archivo SRT"""
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("🤖 AGENTE QWEN CODER - Extracción de Subtítulos Hardcoded")
        logger.info("=" * 60)
        logger.info(f"📹 Video: {video_path}")
        logger.info(f"💾 Salida: {output_path}")
        logger.info(f"⚙️ Configuración: {self.config}")
        logger.info("=" * 60)
        
        # Paso 1: Extraer frames
        logger.info("\n[1/4] 🎬 Extrayendo frames del video...")
        frames_with_timestamps = self.video_processor.extract_frames(video_path)
        
        if not frames_with_timestamps:
            raise ValueError("No se pudieron extraer frames del video")
        
        # Paso 2: Procesar con OCR
        logger.info("\n[2/4] 🔍 Procesando frames con OCR...")
        all_detections = []
        
        for frame, timestamp in tqdm(frames_with_timestamps, desc="🔍 OCR"):
            processed_frame = self.video_processor.preprocess_frame(frame)
            detections = self.ocr_engine_instance.detect_text(
                processed_frame,
                min_confidence=self.min_confidence
            )
            
            for det in detections:
                det['timestamp'] = timestamp
                all_detections.append(det)
        
        logger.info(f"✓ Detecciones totales: {len(all_detections)}")
        
        # Paso 3: Sincronizar
        logger.info("\n[3/4] ⏱️ Sincronizando subtítulos...")
        frame_timestamps = [ts for _, ts in frames_with_timestamps]
        subtitles = self.subtitle_sync.sync_detections(all_detections, frame_timestamps)
        
        logger.info(f"✓ Subtítulos sincronizados: {len(subtitles)}")
        
        # Paso 4: Generar SRT
        logger.info("\n[4/4] 📝 Generando archivo SRT...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        count = SRTGenerator.generate_srt(subtitles, output_path)
        is_valid = SRTGenerator.validate_srt(output_path)
        
        if not is_valid:
            logger.warning("⚠️ El archivo SRT podría tener errores")
        
        total_time = time.time() - start_time
        
        stats = {
            'frames_processed': len(frames_with_timestamps),
            'text_lines_detected': len(all_detections),
            'subtitles_generated': count,
            'total_time': total_time,
            'output_file': output_path,
            'is_valid': is_valid,
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ PROCESAMIENTO COMPLETADO")
        logger.info("=" * 60)
        logger.info(f"📊 Frames procesados: {stats['frames_processed']}")
        logger.info(f"📝 Líneas detectadas: {stats['text_lines_detected']}")
        logger.info(f"🎬 Subtítulos generados: {stats['subtitles_generated']}")
        logger.info(f"⏱️ Tiempo total: {total_time:.2f}s")
        logger.info(f"💾 Archivo: {output_path}")
        logger.info("=" * 60)
        
        return stats


# ==============================================================================
# CELDA 8/8: EJECUCIÓN PRINCIPAL
# ==============================================================================

# Definir rutas
video_path = "/content/drive/MyDrive/Vimeo_Downloads/Sergei Vasiliev Interview 01/10.mp4"
output_dir = "/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder"
output_srt_path = os.path.join(output_dir, "Sergei_Vasiliev_Interview_01.srt")

# Verificar video
if not os.path.exists(video_path):
    print(f"❌ ERROR: Video no encontrado en {video_path}")
    print("\nVerifica:")
    print("1. Que Google Drive está montado (ejecuta CELDA 1)")
    print("2. Que la ruta del video es correcta")
    print("3. Que el archivo existe en tu Google Drive")
else:
    print(f"✓ Video encontrado: {video_path}")
    print(f"✓ Salida SRT: {output_srt_path}")
    
    # Configurar agente
    config = {
        'language': 'es',      # 'es' español, 'en' inglés
        'fps': 2,              # frames por segundo
        'use_gpu': True,       # usar GPU de Colab
        'ocr_engine': 'paddle', # 'paddle' o 'tesseract'
        'min_confidence': 0.5,
        'merge_threshold': 2.0,
    }
    
    # Crear y ejecutar agente
    agent = QwenCoderAgent(config=config)
    
    print("\n🎬 Iniciando procesamiento del video...")
    print("⏰ Esto puede tomar varios minutos según la duración del video\n")
    
    result = agent.process_video(
        video_path=video_path,
        output_path=output_srt_path
    )
    
    # Mostrar resultados
    print(f"\n✅ ¡PROCESAMIENTO COMPLETADO!")
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   • Frames procesados: {result['frames_processed']}")
    print(f"   • Líneas detectadas: {result['text_lines_detected']}")
    print(f"   • Subtítulos generados: {result['subtitles_generated']}")
    print(f"   • Tiempo total: {result['total_time']:.2f}s")
    print(f"   • Archivo válido: {result['is_valid']}")
    print(f"\n💾 Archivo guardado: {result['output_file']}")
    
    # Previsualizar
    print("\n" + "=" * 60)
    print("📝 PRIMEROS 10 SUBTÍTULOS:")
    print("=" * 60)
    
    with open(output_srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        subtitles = content.split('\n\n')
        
        for i, sub in enumerate(subtitles[:10], start=1):
            print(f"\n[{i}]")
            print(sub)
            print("-" * 40)
    
    # Descargar
    print("\n" + "=" * 60)
    print("📥 Descargando archivo SRT...")
    print("=" * 60)
    
    from google.colab import files
    files.download(output_srt_path)
    
    print(f"\n💡 El archivo también está en tu Google Drive:")
    print(f"   {output_srt_path}")
