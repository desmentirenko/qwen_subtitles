# ╔══════════════════════════════════════════════════════════╗
# ║     🤖 AGENTE QWEN CODER - VERSIÓN MEJORADA 🤖            ║
# ║  Extracción de Subtítulos Hardcoded con IA + OCR         ║
# ║  CON DEBUG COMPLETO Y GUARDADO DE ARCHIVOS               ║
# ╚══════════════════════════════════════════════════════════╝

import os
import sys
import json
import time
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Configurar paths ANTES de importar otras librerías
CONFIG = {
    'video_path': "/content/drive/MyDrive/Vimeo_Downloads/Sergei Vasiliev Interview 08-10.mp4",
    'output_dir': "/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder",
    'max_iterations': 5,
    'min_score': 60,
}

# Crear directorios para guardar TODO
OUTPUT_DIR = Path(CONFIG['output_dir'])
FRAMES_DIR = OUTPUT_DIR / "frames"
OCR_RESULTS_DIR = OUTPUT_DIR / "ocr_results"
DEBUG_DIR = OUTPUT_DIR / "debug"
LOGS_DIR = OUTPUT_DIR / "logs"

for dir_path in [FRAMES_DIR, OCR_RESULTS_DIR, DEBUG_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

print("="*70)
print("📁 DIRECTORIOS CREADOS:")
print(f"   Output: {OUTPUT_DIR}")
print(f"   Frames: {FRAMES_DIR}")
print(f"   OCR Results: {OCR_RESULTS_DIR}")
print(f"   Debug: {DEBUG_DIR}")
print(f"   Logs: {LOGS_DIR}")
print("="*70)

# CELDA 2: Instalación de dependencias
print("\n" + "="*70)
print("[STEP] Preparando entorno...")
print("="*70)

# Montar Google Drive
from google.colab import drive
drive.mount('/content/drive', force_remount=False)

# Instalar paquetes del sistema
print("\nInstalando paquetes del sistema...")
subprocess.run(['apt-get', 'update', '-qq'], capture_output=True)
subprocess.run(['apt-get', 'install', '-y', '-qq', 'tesseract-ocr', 'tesseract-ocr-spa', 'tesseract-ocr-eng', 'ffmpeg', 'libsm6', 'libxext6'], capture_output=True)
print("✓ Paquetes del sistema instalados")

# Instalar dependencias Python
print("\nInstalando dependencias Python...")
!pip install -q opencv-python-headless numpy pillow tqdm paddlepaddle-gpu paddleocr pytesseract

# Verificar instalaciones
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
print("✓ Todas las dependencias instaladas correctamente")

# CELDA 3: Video Processor
print("\n" + "="*70)
print("[STEP] Inicializando Video Processor...")
print("="*70)

class VideoProcessor:
    """Procesa video y extrae frames"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = None
        self.fps = 0
        self.total_frames = 0
        self.duration = 0
        self.width = 0
        self.height = 0
        self._initialize()
    
    def _initialize(self):
        """Inicializa captura de video"""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {self.video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Video cargado: {self.width}x{self.height}, {self.fps:.2f} FPS, {self.duration:.2f}s")
    
    def extract_frames(self, fps_target: float, output_dir: Path, save_all: bool = True) -> List[Tuple[str, float]]:
        """
        Extrae frames del video
        Args:
            fps_target: Frames por segundo a extraer
            output_dir: Directorio donde guardar frames
            save_all: Si True, guarda todos los frames extraídos
        Returns:
            Lista de tuplas (path_frame, timestamp)
        """
        interval = self.fps / fps_target
        frame_paths = []
        frame_count = 0
        saved_count = 0
        
        pbar = tqdm(total=int(self.duration * fps_target), desc="Extrayendo frames")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Calcular si debemos guardar este frame
            if frame_count % interval < 1:
                timestamp = frame_count / self.fps
                
                if save_all:
                    # Guardar frame
                    frame_filename = f"frame_{saved_count:05d}_{timestamp:07.3f}s.jpg"
                    frame_path = output_dir / frame_filename
                    cv2.imwrite(str(frame_path), frame)
                    frame_paths.append((str(frame_path), timestamp))
                    saved_count += 1
                else:
                    # Solo retornar frame en memoria
                    frame_paths.append((frame, timestamp))
                
                pbar.update(1)
            
            frame_count += 1
        
        pbar.close()
        print(f"✓ Frames extraídos: {saved_count}")
        return frame_paths
    
    def close(self):
        """Libera recursos"""
        if self.cap:
            self.cap.release()

# CELDA 4: OCR Engine Mejorado
print("\n" + "="*70)
print("[STEP] Inicializando OCR Engine...")
print("="*70)

class OCREngine:
    """Motor OCR con múltiples backends y debug"""
    
    def __init__(self, language: str = 'es', use_gpu: bool = True):
        self.language = language
        self.use_gpu = use_gpu
        self.paddle_ocr = None
        self.tesseract_lang = self._map_language(language)
        self._initialize_engines()
    
    def _map_language(self, lang: str) -> str:
        """Mapea idioma a código Tesseract"""
        mapping = {
            'es': 'spa',
            'en': 'eng',
            'fr': 'fra',
            'de': 'deu',
            'it': 'ita',
            'pt': 'por'
        }
        return mapping.get(lang, 'eng')
    
    def _initialize_engines(self):
        """Inicializa motores OCR"""
        # Intentar PaddleOCR primero
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.language if self.language in ['ch', 'en', 'fr', 'de', 'japan', 'korean'] else 'en',
                use_gpu=self.use_gpu,
                show_log=False  # Evitar logs molestos
            )
            print("✓ PaddleOCR inicializado")
        except Exception as e:
            print(f"⚠ PaddleOCR no disponible: {e}")
            self.paddle_ocr = None
        
        # Verificar Tesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            print("✓ Tesseract OCR disponible")
        except Exception as e:
            print(f"⚠ Tesseract no disponible: {e}")
    
    def preprocess_image(self, image_path: str, debug_dir: Path, frame_id: int) -> np.ndarray:
        """
        Preprocesa imagen para mejorar OCR
        Guarda versiones intermedias para debug
        """
        # Leer imagen original
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Guardar original para debug
        debug_original = debug_dir / f"frame_{frame_id:05d}_original.jpg"
        cv2.imwrite(str(debug_original), img)
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        debug_gray = debug_dir / f"frame_{frame_id:05d}_gray.jpg"
        cv2.imwrite(str(debug_gray), gray)
        
        # Aplicar Gaussian blur
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Thresholding adaptativo
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        debug_thresh = debug_dir / f"frame_{frame_id:05d}_thresh.jpg"
        cv2.imwrite(str(debug_thresh), thresh)
        
        # Denoising
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        debug_denoised = debug_dir / f"frame_{frame_id:05d}_denoised.jpg"
        cv2.imwrite(str(debug_denoised), denoised)
        
        return denoised
    
    def extract_text_paddle(self, image_path: str) -> List[Dict]:
        """Extrae texto usando PaddleOCR"""
        if self.paddle_ocr is None:
            return []
        
        try:
            result = self.paddle_ocr.ocr(image_path, cls=True)
            if not result or not result[0]:
                return []
            
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    bbox = line[0]
                    text = line[1][0] if isinstance(line[1], tuple) else line[1]
                    confidence = line[1][1] if isinstance(line[1], tuple) else 0.9
                    
                    texts.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
            
            return texts
        except Exception as e:
            print(f"⚠ Error en PaddleOCR: {e}")
            return []
    
    def extract_text_tesseract(self, image_path: str) -> List[Dict]:
        """Extrae texto usando Tesseract"""
        try:
            import pytesseract
            from PIL import Image
            
            # Preprocesar imagen
            preprocessed = self.preprocess_image(image_path, DEBUG_DIR, 0)
            if preprocessed is None:
                return []
            
            # Convertir a PIL
            pil_img = Image.fromarray(preprocessed)
            
            # Obtener datos detallados
            data = pytesseract.image_to_data(
                pil_img, 
                lang=self.tesseract_lang,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )
            
            texts = []
            for i, text in enumerate(data['text']):
                text = text.strip()
                if text and int(data['conf'][i]) > 30:  # Filtrar baja confianza
                    texts.append({
                        'text': text,
                        'confidence': int(data['conf'][i]) / 100.0,
                        'bbox': {
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
            
            return texts
        except Exception as e:
            print(f"⚠ Error en Tesseract: {e}")
            return []
    
    def extract_text(self, image_path: str, engine: str = 'auto') -> List[Dict]:
        """
        Extrae texto de una imagen
        Args:
            image_path: Path a la imagen
            engine: 'paddle', 'tesseract', o 'auto'
        Returns:
            Lista de diccionarios con texto, confianza y bbox
        """
        results = []
        
        if engine == 'auto' or engine == 'paddle':
            results = self.extract_text_paddle(image_path)
            if results or engine != 'auto':
                return results
        
        if engine == 'auto' or engine == 'tesseract':
            results = self.extract_text_tesseract(image_path)
        
        return results

# CELDA 5: Subtitle Sync
print("\n" + "="*70)
print("[STEP] Inicializando Subtitle Sync...")
print("="*70)

class SubtitleSync:
    """Sincroniza textos extraídos y genera segmentos"""
    
    def __init__(self, merge_threshold: float = 2.0, min_duration: float = 0.5):
        self.merge_threshold = merge_threshold  # Segundos para merge
        self.min_duration = min_duration
    
    def group_texts(self, ocr_results: List[Dict]) -> List[Dict]:
        """
        Agrupa textos similares en el tiempo
        Args:
            ocr_results: Lista de resultados OCR con timestamps
        Returns:
            Lista de grupos de texto
        """
        if not ocr_results:
            return []
        
        # Ordenar por timestamp
        sorted_results = sorted(ocr_results, key=lambda x: x['timestamp'])
        
        groups = []
        current_group = {
            'texts': [sorted_results[0]],
            'start_time': sorted_results[0]['timestamp'],
            'end_time': sorted_results[0]['timestamp'],
            'combined_text': sorted_results[0]['text']
        }
        
        for i in range(1, len(sorted_results)):
            current = sorted_results[i]
            prev_end = current_group['end_time']
            
            # Si está dentro del threshold, agregar al grupo
            if current['timestamp'] - prev_end <= self.merge_threshold:
                # Verificar si el texto es similar (para evitar duplicados)
                if not self._is_duplicate(current['text'], current_group['combined_text']):
                    current_group['texts'].append(current)
                    current_group['end_time'] = current['timestamp']
                    current_group['combined_text'] += ' ' + current['text']
            else:
                # Guardar grupo actual y comenzar nuevo
                if current_group['texts']:
                    groups.append(current_group)
                
                current_group = {
                    'texts': [current],
                    'start_time': current['timestamp'],
                    'end_time': current['timestamp'],
                    'combined_text': current['text']
                }
        
        # Agregar último grupo
        if current_group['texts']:
            groups.append(current_group)
        
        return groups
    
    def _is_duplicate(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Verifica si dos textos son similares"""
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return True
        
        # Simple similarity check
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity >= threshold
    
    def create_segments(self, groups: List[Dict]) -> List[Dict]:
        """
        Crea segmentos de subtítulos con tiempos ajustados
        """
        segments = []
        
        for i, group in enumerate(groups):
            start_time = group['start_time']
            end_time = group['end_time']
            
            # Ajustar endTime al siguiente grupo o agregar buffer
            if i < len(groups) - 1:
                next_start = groups[i + 1]['start_time']
                end_time = min(end_time + 0.5, next_start - 0.1)
            else:
                end_time += 1.0
            
            # Limpiar texto combinado
            combined_text = ' '.join(group['combined_text'].split())
            
            if combined_text and (end_time - start_time) >= self.min_duration:
                segments.append({
                    'index': len(segments) + 1,
                    'start': start_time,
                    'end': end_time,
                    'text': combined_text,
                    'confidence': sum(t['confidence'] for t in group['texts']) / len(group['texts'])
                })
        
        return segments

# CELDA 6: SRT Generator
print("\n" + "="*70)
print("[STEP] Inicializando SRT Generator...")
print("="*70)

class SRTGenerator:
    """Genera archivos SRT"""
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Convierte segundos a formato SRT HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def generate(subtitles: List[Dict], output_path: str) -> bool:
        """
        Genera archivo SRT
        Returns:
            True si éxito, False si fallo
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for sub in subtitles:
                    f.write(f"{sub['index']}\n")
                    f.write(f"{SRTGenerator.format_timestamp(sub['start'])} --> {SRTGenerator.format_timestamp(sub['end'])}\n")
                    
                    # Dividir texto largo en múltiples líneas
                    text = sub['text']
                    if len(text) > 40:
                        words = text.split()
                        lines = []
                        current_line = []
                        
                        for word in words:
                            current_line.append(word)
                            if len(' '.join(current_line)) > 40:
                                lines.append(' '.join(current_line[:-1]))
                                current_line = [word]
                        
                        if current_line:
                            lines.append(' '.join(current_line))
                        
                        f.write('\n'.join(lines[:2]) + '\n')  # Máximo 2 líneas
                    else:
                        f.write(text + '\n')
                    
                    f.write('\n')
            
            print(f"✓ Archivo SRT generado: {output_path}")
            return True
        except Exception as e:
            print(f"✗ Error generando SRT: {e}")
            return False
    
    @staticmethod
    def validate_srt(file_path: str) -> Tuple[bool, str]:
        """Valida formato SRT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificaciones básicas
            if not content.strip():
                return False, "Archivo vacío"
            
            if '-->' not in content:
                return False, "No se encontraron timestamps"
            
            lines = content.strip().split('\n')
            if len(lines) < 4:
                return False, "Formato inválido"
            
            return True, "SRT válido"
        except Exception as e:
            return False, f"Error validando: {e}"

# CELDA 7: Qwen Coder Agent Principal
print("\n" + "="*70)
print("[STEP] Inicializando Agente Qwen Coder...")
print("="*70)

class QwenCoderAgent:
    """Agente autónomo para extracción de subtítulos"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.video_path = config['video_path']
        self.output_dir = Path(config['output_dir'])
        self.max_iterations = config.get('max_iterations', 5)
        self.min_score = config.get('min_score', 60)
        
        # Estrategias de iteración
        self.strategies = [
            {'fps': 2, 'ocr': 'paddle', 'confidence': 0.5, 'merge': 2.0},
            {'fps': 3, 'ocr': 'paddle', 'confidence': 0.3, 'merge': 2.5},
            {'fps': 4, 'ocr': 'tesseract', 'confidence': 0.4, 'merge': 2.0},
            {'fps': 2, 'ocr': 'both', 'confidence': 0.4, 'merge': 2.0},
            {'fps': 5, 'ocr': 'paddle', 'confidence': 0.3, 'merge': 3.0},
        ]
        
        # Historial de ejecución
        self.execution_log = []
    
    def run(self):
        """Ejecuta el agente"""
        print("\n" + "="*70)
        print("╔══════════════════════════════════════════════════════════╗")
        print("║           🤖 AGENTE QWEN CODER - AUTÓNOMO 🤖             ║")
        print("║     Extracción de Subtítulos Hardcoded con IA + OCR      ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print("="*70)
        
        print(f"\n[INFO] Video: {self.video_path}")
        print(f"[INFO] Output: {self.output_dir}")
        print(f"[INFO] Máximo iteraciones: {self.max_iterations}")
        
        # Verificar video
        if not os.path.exists(self.video_path):
            print(f"✗ ERROR: Video no encontrado: {self.video_path}")
            return False
        
        # Inicializar procesador de video
        print("\n[STEP] Cargando video...")
        video_processor = VideoProcessor(self.video_path)
        
        # Inicializar motor OCR
        print("\n[STEP] Inicializando OCR...")
        ocr_engine = OCREngine(language='es', use_gpu=True)
        
        # Inicializar sincronizador
        subtitle_sync = SubtitleSync()
        
        # Iterar sobre estrategias
        success = False
        for iteration in range(self.max_iterations):
            strategy = self.strategies[iteration % len(self.strategies)]
            
            print(f"\n{'='*70}")
            print(f"[ITERACIÓN {iteration + 1}/{self.max_iterations}]")
            print(f"Estrategia: FPS={strategy['fps']}, OCR={strategy['ocr']}, Conf={strategy['confidence']}")
            print(f"{'='*70}")
            
            # Crear directorio para esta iteración
            iter_dir = self.output_dir / f"iteration_{iteration + 1}"
            iter_frames_dir = iter_dir / "frames"
            iter_ocr_dir = iter_dir / "ocr"
            iter_debug_dir = iter_dir / "debug"
            
            for d in [iter_frames_dir, iter_ocr_dir, iter_debug_dir]:
                d.mkdir(parents=True, exist_ok=True)
            
            # Extraer frames
            print(f"\n[STEP] Extrayendo frames a {strategy['fps']} FPS...")
            frame_paths = video_processor.extract_frames(
                strategy['fps'], 
                iter_frames_dir,
                save_all=True
            )
            
            # Guardar log de frames
            frames_log = {
                'total_frames': len(frame_paths),
                'fps_target': strategy['fps'],
                'video_duration': video_processor.duration,
                'frames': [{'path': fp[0], 'timestamp': fp[1]} for fp in frame_paths]
            }
            
            with open(iter_dir / 'frames_log.json', 'w') as f:
                json.dump(frames_log, f, indent=2)
            
            print(f"✓ Frames extraídos: {len(frame_paths)}")
            
            # Procesar OCR
            print(f"\n[STEP] Procesando OCR...")
            ocr_results = []
            
            for idx, (frame_path, timestamp) in enumerate(tqdm(frame_paths, desc="OCR")):
                # Determinar motor OCR
                if strategy['ocr'] == 'both':
                    texts = ocr_engine.extract_text(frame_path, 'paddle')
                    if not texts:
                        texts = ocr_engine.extract_text(frame_path, 'tesseract')
                else:
                    texts = ocr_engine.extract_text(frame_path, strategy['ocr'])
                
                # Filtrar por confianza
                filtered_texts = [t for t in texts if t['confidence'] >= strategy['confidence']]
                
                if filtered_texts:
                    for text_data in filtered_texts:
                        ocr_result = {
                            'frame_id': idx,
                            'frame_path': frame_path,
                            'timestamp': timestamp,
                            'text': text_data['text'],
                            'confidence': text_data['confidence'],
                            'bbox': text_data.get('bbox', {})
                        }
                        ocr_results.append(ocr_result)
                        
                        # Guardar resultado individual
                        result_file = iter_ocr_dir / f"frame_{idx:05d}_result.json"
                        with open(result_file, 'w', encoding='utf-8') as f:
                            json.dump(ocr_result, f, ensure_ascii=False, indent=2)
            
            # Guardar todos los resultados OCR
            all_ocr_results_file = iter_dir / 'all_ocr_results.json'
            with open(all_ocr_results_file, 'w', encoding='utf-8') as f:
                json.dump(ocr_results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✓ Textos extraídos: {len(ocr_results)}")
            
            # Evaluar resultados
            if len(ocr_results) == 0:
                print(f"⚠ No se extrajo texto. Probando siguiente estrategia...")
                self.execution_log.append({
                    'iteration': iteration + 1,
                    'strategy': strategy,
                    'frames_extracted': len(frame_paths),
                    'texts_found': 0,
                    'success': False
                })
                continue
            
            # Sincronizar y agrupar
            print(f"\n[STEP] Sincronizando subtítulos...")
            groups = subtitle_sync.group_texts(ocr_results)
            segments = subtitle_sync.create_segments(groups)
            
            print(f"✓ Segmentos creados: {len(segments)}")
            
            # Calcular score de calidad
            score = self._calculate_quality_score(segments, ocr_results, strategy)
            print(f"✓ Score de calidad: {score}/100")
            
            # Guardar segmentos
            segments_file = iter_dir / 'segments.json'
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)
            
            # Generar SRT
            srt_path = iter_dir / 'subtitles.srt'
            srt_success = SRTGenerator.generate(segments, str(srt_path))
            
            if srt_success:
                # Validar SRT
                is_valid, validation_msg = SRTGenerator.validate_srt(str(srt_path))
                print(f"✓ Validación SRT: {validation_msg}")
                
                # Copiar a directorio principal si es exitoso
                if score >= self.min_score:
                    final_srt_path = self.output_dir / 'final_subtitles.srt'
                    import shutil
                    shutil.copy(str(srt_path), str(final_srt_path))
                    
                    # Guardar reporte final
                    report = {
                        'success': True,
                        'iteration': iteration + 1,
                        'strategy': strategy,
                        'score': score,
                        'segments_count': len(segments),
                        'video_path': self.video_path,
                        'output_path': str(final_srt_path),
                        'execution_log': self.execution_log
                    }
                    
                    with open(self.output_dir / 'processing_report.json', 'w') as f:
                        json.dump(report, f, indent=2)
                    
                    print(f"\n{'='*70}")
                    print(f"✅ ¡PROCESO EXITOSO!")
                    print(f"   Score: {score}/100")
                    print(f"   Segmentos: {len(segments)}")
                    print(f"   Archivo: {final_srt_path}")
                    print(f"{'='*70}")
                    
                    success = True
                    break
                else:
                    print(f"⚠ Score {score} < {self.min_score}. Continuando...")
            else:
                print(f"⚠ Error generando SRT. Continuando...")
            
            # Log de iteración
            self.execution_log.append({
                'iteration': iteration + 1,
                'strategy': strategy,
                'frames_extracted': len(frame_paths),
                'texts_found': len(ocr_results),
                'segments_created': len(segments),
                'score': score,
                'success': False
            })
        
        # Limpieza
        video_processor.close()
        
        if not success:
            print(f"\n{'='*70}")
            print(f"❌ NO SE LOGRÓ EXTRAER SUBTÍTULOS SATISFACTORIAMENTE")
            print(f"   Se intentaron {self.max_iterations} estrategias")
            print(f"   Revisa los logs en: {self.output_dir}")
            print(f"{'='*70}")
            
            # Guardar reporte final fallido
            report = {
                'success': False,
                'iterations_attempted': self.max_iterations,
                'execution_log': self.execution_log
            }
            
            with open(self.output_dir / 'processing_report.json', 'w') as f:
                json.dump(report, f, indent=2)
        
        return success
    
    def _calculate_quality_score(self, segments: List[Dict], ocr_results: List[Dict], strategy: Dict) -> int:
        """Calcula score de calidad 0-100"""
        if not segments:
            return 0
        
        score = 0
        
        # Factor 1: Cantidad de segmentos (20 pts)
        seg_count_score = min(len(segments) * 2, 20)
        score += seg_count_score
        
        # Factor 2: Confianza promedio (30 pts)
        avg_confidence = sum(s['confidence'] for s in segments) / len(segments)
        score += int(avg_confidence * 30)
        
        # Factor 3: Duración total cubierta (20 pts)
        total_duration = sum(s['end'] - s['start'] for s in segments)
        coverage_ratio = min(total_duration / 120, 1.0)  # Asumiendo video ~2min
        score += int(coverage_ratio * 20)
        
        # Factor 4: Longitud promedio de texto (15 pts)
        avg_length = sum(len(s['text']) for s in segments) / len(segments)
        length_score = min(avg_length / 30, 1.0) * 15
        score += int(length_score)
        
        # Factor 5: Consistencia temporal (15 pts)
        overlaps = 0
        for i in range(len(segments) - 1):
            if segments[i]['end'] > segments[i+1]['start']:
                overlaps += 1
        
        overlap_penalty = min(overlaps / len(segments), 0.5) * 15
        score += int(15 - overlap_penalty)
        
        return min(score, 100)

# CELDA 8: Ejecutar Agente
print("\n" + "="*70)
print("[STEP] EJECUTANDO AGENTE QWEN CODER...")
print("="*70)

# Crear y ejecutar agente
agent = QwenCoderAgent(CONFIG)
success = agent.run()

# Mostrar resumen final
print("\n" + "="*70)
print("📊 RESUMEN FINAL")
print("="*70)

report_path = OUTPUT_DIR / 'processing_report.json'
if report_path.exists():
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Mostrar primeros subtítulos si existen
    if report.get('success'):
        print("\n" + "="*70)
        print("📝 PRIMEROS SUBTÍTULOS GENERADOS:")
        print("="*70)
        
        srt_path = OUTPUT_DIR / 'final_subtitles.srt'
        if srt_path.exists():
            with open(srt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:20]  # Primeras 20 líneas
                print(''.join(lines))

print("\n✅ Todos los archivos guardados en:", OUTPUT_DIR)
print("   - frames/: Frames extraídos del video")
print("   - ocr_results/: Resultados OCR por frame")
print("   - debug/: Imágenes de debug (preprocesamiento)")
print("   - iteration_X/: Resultados por iteración")
print("   - processing_report.json: Reporte completo")
print("   - final_subtitles.srt: Subtítulos finales (si exitoso)")
