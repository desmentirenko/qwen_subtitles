"""
AGENTE QWEN CODER - Sistema Autónomo para Extracción de Subtítulos Hardcoded
=============================================================================

Este agente autónomo:
1. DEFINE el objetivo automáticamente
2. EJECUTA código necesario (instalaciones, procesamiento)
3. LEE y EVALÚA resultados
4. DECIDE si cumplió el objetivo
5. ITERA con estrategias alternativas si falla
6. REPORTA el resultado final

Optimizado para Google Colab con auto-ejecución completa.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import re


# Configuración del Agente
CONFIG = {
    'video_path': "/content/drive/MyDrive/Vimeo_Downloads/Sergei Vasiliev Interview 01/10.mp4",
    'output_dir': "/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder",
    'max_iterations': 5,
    'min_subtitle_duration': 1.0,
    'max_subtitle_duration': 7.0,
    'min_confidence_threshold': 0.3,
    'target_subtitles_count_range': (50, 500),  # Rango esperado para video de entrevista
}


class Logger:
    """Sistema de logging con colores para Colab"""
    
    @staticmethod
    def info(msg: str):
        print(f"\033[94m[INFO]\033[0m {msg}")
    
    @staticmethod
    def success(msg: str):
        print(f"\033[92m[SUCCESS]\033[0m {msg}")
    
    @staticmethod
    def warning(msg: str):
        print(f"\033[93m[WARNING]\033[0m {msg}")
    
    @staticmethod
    def error(msg: str):
        print(f"\033[91m[ERROR]\033[0m {msg}")
    
    @staticmethod
    def step(msg: str):
        print(f"\n\033[95m{'='*60}\033[0m")
        print(f"\033[95m[STEP]\033[0m {msg}")
        print(f"\033[95m{'='*60}\033[0m")


class DependencyManager:
    """Gestor automático de dependencias con verificación"""
    
    REQUIRED_PACKAGES = [
        'opencv-python',
        'numpy',
        'pillow',
        'tqdm',
        'paddlepaddle-gpu',
        'paddleocr',
        'pytesseract',
    ]
    
    SYSTEM_PACKAGES = [
        'tesseract-ocr',
        'ffmpeg',
        'libtesseract-dev',
    ]
    
    def __init__(self):
        self.installed = []
        self.failed = []
    
    def install_system_packages(self) -> bool:
        """Instala paquetes del sistema"""
        Logger.step("Instalando paquetes del sistema...")
        
        try:
            cmd = "apt-get update && apt-get install -y " + " ".join(self.SYSTEM_PACKAGES)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                Logger.success("Paquetes del sistema instalados correctamente")
                return True
            else:
                Logger.warning(f"Algunos paquetes fallaron: {result.stderr}")
                return False
        except Exception as e:
            Logger.error(f"Error instalando paquetes: {e}")
            return False
    
    def install_python_packages(self) -> bool:
        """Instala paquetes Python con verificación"""
        Logger.step("Instalando dependencias Python...")
        
        for package in self.REQUIRED_PACKAGES:
            try:
                # Verificar si ya está instalado
                try:
                    if package == 'paddlepaddle-gpu':
                        __import__('paddle')
                    elif package == 'paddleocr':
                        __import__('paddleocr')
                    elif package == 'pytesseract':
                        __import__('pytesseract')
                    elif package == 'opencv-python':
                        __import__('cv2')
                    else:
                        __import__(package.replace('-', '_'))
                    
                    Logger.info(f"✓ {package} ya instalado")
                    continue
                except ImportError:
                    pass
                
                # Instalar
                Logger.info(f"Instalando {package}...")
                cmd = f"pip install --quiet {package}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    Logger.success(f"✓ {package} instalado")
                    self.installed.append(package)
                else:
                    Logger.warning(f"✗ {package} falló: {result.stderr[:200]}")
                    self.failed.append(package)
                    
            except Exception as e:
                Logger.error(f"Error con {package}: {e}")
                self.failed.append(package)
        
        return len(self.failed) == 0
    
    def verify_installations(self) -> Dict[str, bool]:
        """Verifica que todas las instalaciones funcionen"""
        Logger.step("Verificando instalaciones...")
        
        verification = {}
        
        tests = [
            ('cv2', 'OpenCV'),
            ('numpy', 'NumPy'),
            ('PIL', 'Pillow'),
            ('tqdm', 'tqdm'),
            ('paddle', 'PaddlePaddle'),
            ('paddleocr', 'PaddleOCR'),
            ('pytesseract', 'PyTesseract'),
        ]
        
        all_ok = True
        for module, name in tests:
            try:
                __import__(module)
                Logger.success(f"✓ {name} funcional")
                verification[name] = True
            except ImportError as e:
                Logger.error(f"✗ {name} no disponible: {str(e)[:100]}")
                verification[name] = False
                all_ok = False
        
        # Verificar tesseract CLI
        try:
            result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                Logger.success("✓ Tesseract OCR funcional")
                verification['Tesseract'] = True
            else:
                raise Exception("Tesseract no responde")
        except:
            Logger.error("✗ Tesseract OCR no disponible")
            verification['Tesseract'] = False
            all_ok = False
        
        # Verificar ffmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                Logger.success("✓ FFmpeg funcional")
                verification['FFmpeg'] = True
            else:
                raise Exception("FFmpeg no responde")
        except:
            Logger.error("✗ FFmpeg no disponible")
            verification['FFmpeg'] = False
            all_ok = False
        
        return verification


class VideoProcessor:
    """Procesamiento de video con extracción de frames"""
    
    def __init__(self, video_path: str, fps: float = 2.0):
        self.video_path = video_path
        self.fps = fps
        self.frames = []
        self.timestamps = []
        self.duration = 0
        
    def validate_video(self) -> bool:
        """Valida que el video existe y es accesible"""
        if not os.path.exists(self.video_path):
            Logger.error(f"Video no encontrado: {self.video_path}")
            return False
        
        # Obtener duración con ffprobe
        try:
            cmd = f'ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{self.video_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.duration = float(result.stdout.strip())
            Logger.info(f"Duración del video: {self.duration:.2f} segundos")
            return True
        except Exception as e:
            Logger.error(f"Error leyendo video: {e}")
            return False
    
    def extract_frames(self) -> bool:
        """Extrae frames del video"""
        if not self.validate_video():
            return False
        
        Logger.step(f"Extrayendo frames a {self.fps} FPS...")
        
        import cv2
        from tqdm import tqdm
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            Logger.error("No se pudo abrir el video")
            return False
        
        frame_interval = int(cap.get(cv2.CAP_PROP_FPS) / self.fps)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        expected_extracts = total_frames // frame_interval + 1
        
        Logger.info(f"Frames totales en video: {total_frames}")
        Logger.info(f"Frames a extraer: ~{expected_extracts}")
        
        frame_count = 0
        extracted = 0
        
        pbar = tqdm(total=expected_extracts, desc="Extrayendo frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                timestamp = frame_count / cap.get(cv2.CAP_PROP_FPS)
                
                # Preprocesamiento para OCR
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                denoised = cv2.fastNlMeansDenoising(thresh, h=30)
                
                self.frames.append(denoised)
                self.timestamps.append(timestamp)
                extracted += 1
                pbar.update(1)
            
            frame_count += 1
        
        cap.release()
        pbar.close()
        
        Logger.success(f"Frames extraídos: {extracted}")
        return len(self.frames) > 0


class OCREngine:
    """Motor OCR con múltiples estrategias y fallback"""
    
    def __init__(self, language: str = 'es', use_gpu: bool = True):
        self.language = language
        self.use_gpu = use_gpu
        self.paddle_ocr = None
        self.tesseract_ready = False
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Inicializa motores OCR disponibles"""
        Logger.step("Inicializando motores OCR...")
        
        # Intentar PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.language if self.language in ['en', 'ch', 'fr', 'german', 'korean', 'japan'] else 'en',
                use_gpu=self.use_gpu,
                show_log=False
            )
            Logger.success("✓ PaddleOCR inicializado")
        except Exception as e:
            Logger.warning(f"PaddleOCR no disponible: {e}")
            self.paddle_ocr = None
        
        # Verificar Tesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self.tesseract_ready = True
            Logger.success("✓ Tesseract OCR disponible")
        except Exception as e:
            Logger.warning(f"Tesseract no disponible: {e}")
            self.tesseract_ready = False
    
    def extract_text_paddle(self, image) -> List[Dict]:
        """Extrae texto usando PaddleOCR"""
        if self.paddle_ocr is None:
            return []
        
        try:
            result = self.paddle_ocr.ocr(image, cls=True)
            texts = []
            
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        bbox, (text, confidence) = line[0], line[1]
                        if confidence > CONFIG['min_confidence_threshold']:
                            texts.append({
                                'text': text.strip(),
                                'confidence': confidence,
                                'bbox': bbox
                            })
            
            return texts
        except Exception as e:
            Logger.error(f"Error en PaddleOCR: {e}")
            return []
    
    def extract_text_tesseract(self, image) -> List[Dict]:
        """Extrae texto usando Tesseract con fallback"""
        if not self.tesseract_ready:
            return []
        
        try:
            import pytesseract
            from PIL import Image
            import numpy as np
            import cv2
            
            # Convertir a PIL Image
            if isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # Configurar idioma
            lang_map = {'es': 'spa', 'en': 'eng', 'fr': 'fra', 'de': 'deu', 'it': 'ita', 'pt': 'por'}
            tess_lang = lang_map.get(self.language, 'eng')
            
            # Extraer con datos de posición
            data = pytesseract.image_to_data(pil_image, lang=tess_lang, output_type=pytesseract.Output.DICT)
            
            texts = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > CONFIG['min_confidence_threshold'] * 100:
                    texts.append({
                        'text': text,
                        'confidence': conf / 100,
                        'bbox': [data['left'][i], data['top'][i], 
                                data['width'][i], data['height'][i]]
                    })
            
            return texts
        except Exception as e:
            Logger.error(f"Error en Tesseract: {e}")
            return []
    
    def extract_text(self, image, frame_idx: int) -> List[Dict]:
        """Extrae texto usando el mejor motor disponible"""
        # Intentar PaddleOCR primero (más preciso)
        texts = self.extract_text_paddle(image)
        
        # Fallback a Tesseract si Paddle falla o no devuelve resultados
        if not texts and self.tesseract_ready:
            Logger.info(f"Frame {frame_idx}: Fallback a Tesseract")
            texts = self.extract_text_tesseract(image)
        
        return texts


class SubtitleSynchronizer:
    """Sincronización y agrupación de subtítulos"""
    
    def __init__(self, timestamps: List[float]):
        self.timestamps = timestamps
        self.subtitle_groups = []
    
    def group_texts(self, ocr_results: List[List[Dict]]) -> List[Dict]:
        """Agrupa textos consecutivos similares"""
        Logger.step("Sincronizando subtítulos...")
        
        from tqdm import tqdm
        
        grouped = []
        current_group = None
        last_text = ""
        last_timestamp = 0
        
        pbar = tqdm(total=len(ocr_results), desc="Agrupando textos")
        
        for idx, (texts, timestamp) in enumerate(zip(ocr_results, self.timestamps)):
            # Combinar todos los textos del frame
            frame_text = " ".join([t['text'] for t in texts])
            
            if not frame_text.strip():
                pbar.update(1)
                continue
            
            # Determinar si es continuación del grupo anterior
            is_continuation = False
            if current_group:
                # Mismo texto o muy similar
                similarity = self._text_similarity(last_text, frame_text)
                if similarity > 0.7 or (last_text in frame_text or frame_text in last_text):
                    is_continuation = True
            
            if is_continuation and current_group:
                # Actualizar grupo existente
                current_group['end_time'] = timestamp + (self.timestamps[1] - self.timestamps[0] if len(self.timestamps) > 1 else 0.5)
                if frame_text not in current_group['texts']:
                    current_group['texts'].append(frame_text)
                current_group['text'] = self._merge_texts(current_group['texts'])
            else:
                # Guardar grupo anterior si existe
                if current_group:
                    grouped.append(current_group)
                
                # Crear nuevo grupo
                duration = self.timestamps[1] - self.timestamps[0] if len(self.timestamps) > 1 else 0.5
                current_group = {
                    'start_time': timestamp,
                    'end_time': timestamp + duration,
                    'texts': [frame_text],
                    'text': frame_text,
                    'frame_start': idx,
                    'frame_end': idx
                }
            
            last_text = frame_text
            last_timestamp = timestamp
            pbar.update(1)
        
        # Guardar último grupo
        if current_group:
            grouped.append(current_group)
        
        pbar.close()
        
        # Filtrar grupos muy cortos o vacíos
        filtered = [g for g in grouped if g['text'].strip() and 
                   (g['end_time'] - g['start_time']) >= CONFIG['min_subtitle_duration']]
        
        Logger.success(f"Subtítulos sincronizados: {len(filtered)}")
        self.subtitle_groups = filtered
        return filtered
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _merge_texts(self, texts: List[str]) -> str:
        """Combina textos eliminando duplicados"""
        if not texts:
            return ""
        
        # Tomar el texto más completo
        longest = max(texts, key=len)
        return longest


class SRTGenerator:
    """Generador de archivos SRT con validación"""
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Convierte segundos a formato SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    @staticmethod
    def generate_srt(subtitles: List[Dict], output_path: str) -> bool:
        """Genera archivo SRT"""
        Logger.step(f"Generando SRT: {output_path}")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, sub in enumerate(subtitles, 1):
                    start = SRTGenerator.format_timestamp(sub['start_time'])
                    end = SRTGenerator.format_timestamp(sub['end_time'])
                    text = sub['text']
                    
                    # Escribir entrada SRT
                    f.write(f"{idx}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            
            Logger.success(f"SRT generado: {idx} subtítulos")
            return True
            
        except Exception as e:
            Logger.error(f"Error generando SRT: {e}")
            return False
    
    @staticmethod
    def validate_srt(file_path: str) -> Tuple[bool, str]:
        """Valida formato SRT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Patrón básico de SRT
            pattern = r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n.+?\n\n'
            matches = re.findall(pattern, content, re.DOTALL)
            
            if len(matches) == 0:
                return False, "No se encontraron entradas SRT válidas"
            
            return True, f"Formato válido con {len(matches)} subtítulos"
            
        except Exception as e:
            return False, f"Error validando: {e}"


class QualityEvaluator:
    """Evalúa la calidad del resultado y decide si retry"""
    
    def __init__(self):
        self.evaluation_history = []
    
    def evaluate(self, subtitles: List[Dict], video_duration: float) -> Dict:
        """Evalúa calidad de los subtítulos generados"""
        Logger.step("Evaluando calidad del resultado...")
        
        evaluation = {
            'subtitle_count': len(subtitles),
            'video_duration': video_duration,
            'avg_duration_per_subtitle': 0,
            'coverage_percentage': 0,
            'has_empty_texts': False,
            'has_overlapping': False,
            'quality_score': 0,
            'passed': False,
            'issues': []
        }
        
        if not subtitles:
            evaluation['issues'].append("No se generaron subtítulos")
            self.evaluation_history.append(evaluation)
            return evaluation
        
        # Calcular métricas
        total_coverage = sum(s['end_time'] - s['start_time'] for s in subtitles)
        evaluation['coverage_percentage'] = (total_coverage / video_duration) * 100 if video_duration > 0 else 0
        evaluation['avg_duration_per_subtitle'] = total_coverage / len(subtitles)
        
        # Verificar textos vacíos
        empty_count = sum(1 for s in subtitles if not s['text'].strip())
        if empty_count > 0:
            evaluation['has_empty_texts'] = True
            evaluation['issues'].append(f"{empty_count} subtítulos vacíos")
        
        # Verificar solapamientos
        overlapping = 0
        for i in range(len(subtitles) - 1):
            if subtitles[i]['end_time'] > subtitles[i+1]['start_time']:
                overlapping += 1
        
        if overlapping > 0:
            evaluation['has_overlapping'] = True
            evaluation['issues'].append(f"{overlapping} solapamientos detectados")
        
        # Calcular score de calidad (0-100)
        score = 100
        
        # Penalizar por cobertura muy baja o muy alta
        if evaluation['coverage_percentage'] < 10:
            score -= 40
            evaluation['issues'].append("Cobertura muy baja (<10%)")
        elif evaluation['coverage_percentage'] > 90:
            score -= 20
            evaluation['issues'].append("Cobertura sospechosamente alta (>90%)")
        
        # Penalizar por textos vacíos
        if evaluation['has_empty_texts']:
            score -= 20
        
        # Penalizar por solapamientos
        if evaluation['has_overlapping']:
            score -= 15
        
        # Verificar rango esperado de subtítulos
        min_expected, max_expected = CONFIG['target_subtitles_count_range']
        if len(subtitles) < min_expected:
            score -= 15
            evaluation['issues'].append(f"Muy pocos subtítulos ({len(subtitles)} < {min_expected})")
        elif len(subtitles) > max_expected:
            score -= 10
            evaluation['issues'].append(f"Muchos subtítulos ({len(subtitles)} > {max_expected})")
        
        evaluation['quality_score'] = max(0, score)
        evaluation['passed'] = score >= 60 and len(evaluation['issues']) <= 2
        
        Logger.info(f"Score de calidad: {evaluation['quality_score']}/100")
        Logger.info(f"Cobertura: {evaluation['coverage_percentage']:.1f}%")
        Logger.info(f"Subtítulos: {evaluation['subtitle_count']}")
        
        if evaluation['passed']:
            Logger.success("✓ Calidad ACEPTABLE")
        else:
            Logger.warning(f"✗ Calidad INSUFICIENTE - Issues: {len(evaluation['issues'])}")
            for issue in evaluation['issues']:
                Logger.warning(f"  - {issue}")
        
        self.evaluation_history.append(evaluation)
        return evaluation


class QwenCoderAgent:
    """Agente autónomo que coordina todo el proceso"""
    
    STRATEGIES = [
        {'fps': 2, 'ocr_engine': 'paddle', 'min_confidence': 0.5},
        {'fps': 3, 'ocr_engine': 'paddle', 'min_confidence': 0.3},
        {'fps': 4, 'ocr_engine': 'tesseract', 'min_confidence': 0.4},
        {'fps': 2, 'ocr_engine': 'both', 'min_confidence': 0.3},
        {'fps': 5, 'ocr_engine': 'paddle', 'min_confidence': 0.2},
    ]
    
    def __init__(self, config: Dict):
        self.config = config
        self.dependency_manager = DependencyManager()
        self.evaluator = QualityEvaluator()
        self.results = {
            'success': False,
            'iterations': 0,
            'strategy_used': None,
            'output_file': None,
            'evaluation': None,
            'errors': []
        }
    
    def run(self) -> bool:
        """Ejecuta el agente autónomo"""
        Logger.step("🤖 AGENTE QWEN CODER INICIADO")
        Logger.info(f"Video: {self.config['video_path']}")
        Logger.info(f"Output: {self.config['output_dir']}")
        Logger.info(f"Máximo iteraciones: {self.config['max_iterations']}")
        
        # Paso 1: Preparar entorno
        if not self._prepare_environment():
            return False
        
        # Paso 2: Iterar sobre estrategias
        for iteration in range(self.config['max_iterations']):
            self.results['iterations'] = iteration + 1
            
            strategy = self.STRATEGIES[iteration % len(self.STRATEGIES)]
            self.results['strategy_used'] = strategy
            
            Logger.step(f"🔄 ITERACIÓN {iteration + 1}/{self.config['max_iterations']}")
            Logger.info(f"Estrategia: FPS={strategy['fps']}, OCR={strategy['ocr_engine']}, Conf={strategy['min_confidence']}")
            
            # Ejecutar pipeline
            success = self._execute_pipeline(strategy)
            
            if success:
                Logger.success("✅ OBJETIVO CUMPLIDO")
                self.results['success'] = True
                return True
            
            Logger.warning("Iteración no satisfactoria, probando siguiente estrategia...")
        
        Logger.error("❌ No se alcanzó el objetivo después de todas las iteraciones")
        self._generate_report()
        return False
    
    def _prepare_environment(self) -> bool:
        """Prepara el entorno (instalaciones, directorios)"""
        Logger.step("Preparando entorno...")
        
        # Crear directorio de output
        os.makedirs(self.config['output_dir'], exist_ok=True)
        Logger.success(f"Directorio creado: {self.config['output_dir']}")
        
        # Montar Drive si estamos en Colab
        if '/content' in os.getcwd():
            try:
                from google.colab import drive
                drive.mount('/content/drive', force_remount=False)
                Logger.success("Google Drive montado")
            except:
                Logger.info("Drive ya montado o no disponible")
        
        # Instalar dependencias
        if not self.dependency_manager.install_system_packages():
            Logger.warning("Algunos paquetes del sistema fallaron")
        
        if not self.dependency_manager.install_python_packages():
            Logger.warning("Algunos paquetes Python fallaron")
        
        # Verificar instalaciones
        verification = self.dependency_manager.verify_installations()
        
        critical_failed = any([
            not verification.get('OpenCV', False),
            not verification.get('NumPy', False),
            not verification.get('FFmpeg', False),
        ])
        
        if critical_failed:
            Logger.error("Dependencias críticas faltantes")
            return False
        
        return True
    
    def _execute_pipeline(self, strategy: Dict) -> bool:
        """Ejecuta el pipeline completo con una estrategia dada"""
        try:
            # Actualizar configuración
            CONFIG['min_confidence_threshold'] = strategy['min_confidence']
            
            # Procesar video
            processor = VideoProcessor(self.config['video_path'], fps=strategy['fps'])
            if not processor.extract_frames():
                self.results['errors'].append("Fallo extrayendo frames")
                return False
            
            # Inicializar OCR
            use_paddle = strategy['ocr_engine'] in ['paddle', 'both']
            use_tesseract = strategy['ocr_engine'] in ['tesseract', 'both']
            
            ocr_engine = OCREngine(language='es', use_gpu=True)
            if not use_paddle:
                ocr_engine.paddle_ocr = None
            if not use_tesseract:
                ocr_engine.tesseract_ready = False
            
            # Extraer texto de frames
            Logger.step("Extrayendo texto con OCR...")
            ocr_results = []
            
            from tqdm import tqdm
            for idx, (frame, timestamp) in tqdm(enumerate(zip(processor.frames, processor.timestamps)), 
                                                 total=len(processor.frames), 
                                                 desc="Procesando OCR"):
                texts = ocr_engine.extract_text(frame, idx)
                ocr_results.append(texts)
            
            if not any(ocr_results):
                Logger.warning("No se extrajo texto en ningún frame")
                self.results['errors'].append("OCR no extrajo texto")
                return False
            
            # Sincronizar subtítulos
            sync = SubtitleSynchronizer(processor.timestamps)
            subtitles = sync.group_texts(ocr_results)
            
            if not subtitles:
                Logger.warning("No se pudieron sincronizar subtítulos")
                self.results['errors'].append("Fallo sincronizando subtítulos")
                return False
            
            # Generar SRT
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"subtitles_{timestamp}.srt"
            output_path = os.path.join(self.config['output_dir'], output_filename)
            
            if not SRTGenerator.generate_srt(subtitles, output_path):
                self.results['errors'].append("Fallo generando SRT")
                return False
            
            # Validar SRT
            valid, msg = SRTGenerator.validate_srt(output_path)
            if not valid:
                Logger.warning(f"SRT inválido: {msg}")
                self.results['errors'].append(f"SRT inválido: {msg}")
                return False
            
            Logger.success(f"SRT válido: {msg}")
            
            # Evaluar calidad
            evaluation = self.evaluator.evaluate(subtitles, processor.duration)
            self.results['evaluation'] = evaluation
            self.results['output_file'] = output_path
            
            if evaluation['passed']:
                # Éxito!
                self._show_preview(output_path)
                self._generate_report()
                return True
            else:
                Logger.info("Calidad insuficiente, continuando con siguiente estrategia...")
                return False
            
        except Exception as e:
            Logger.error(f"Error en pipeline: {e}")
            import traceback
            traceback.print_exc()
            self.results['errors'].append(str(e))
            return False
    
    def _show_preview(self, srt_path: str, limit: int = 10):
        """Muestra preview del SRT"""
        Logger.step("Preview del resultado:")
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entries = content.split('\n\n')[:limit]
        
        for entry in entries:
            print(entry)
            print("-" * 40)
        
        print(f"... ({len(entries)} de {content.count('\n\n')} mostrados)")
    
    def _generate_report(self):
        """Genera reporte final"""
        report_path = os.path.join(self.config['output_dir'], 'processing_report.json')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'video_path': self.config['video_path'],
            'output_dir': self.config['output_dir'],
            'results': self.results,
            'evaluation_history': self.evaluator.evaluation_history,
            'config': CONFIG
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        Logger.success(f"Reporte guardado: {report_path}")
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN FINAL")
        print("="*60)
        print(f"Estado: {'✅ ÉXITO' if self.results['success'] else '❌ FALLÓ'}")
        print(f"Iteraciones: {self.results['iterations']}")
        print(f"Estrategia final: {self.results['strategy_used']}")
        print(f"Archivo output: {self.results['output_file']}")
        
        if self.results['evaluation']:
            eval_data = self.results['evaluation']
            print(f"Score calidad: {eval_data['quality_score']}/100")
            print(f"Subtítulos: {eval_data['subtitle_count']}")
            print(f"Cobertura: {eval_data['coverage_percentage']:.1f}%")
        
        if self.results['errors']:
            print(f"Errores: {len(self.results['errors'])}")
            for err in self.results['errors'][:3]:
                print(f"  - {err}")
        
        print("="*60)


# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           🤖 AGENTE QWEN CODER - AUTÓNOMO 🤖             ║
    ║     Extracción de Subtítulos Hardcoded con IA + OCR      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Crear y ejecutar agente
    agent = QwenCoderAgent(CONFIG)
    success = agent.run()
    
    # En Colab, ofrecer descarga
    if success and '/content' in os.getcwd():
        try:
            from google.colab import files
            output_file = agent.results['output_file']
            if output_file and os.path.exists(output_file):
                Logger.info("Descargando archivo SRT...")
                files.download(output_file)
        except:
            pass
    
    sys.exit(0 if success else 1)
