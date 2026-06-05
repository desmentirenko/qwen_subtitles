"""
Qwen Coder Agent - Agente Principal
Orquestador para extracción de subtítulos hardcoded con OCR
"""

from typing import List, Dict, Optional
from pathlib import Path
from tqdm import tqdm

from video_processor import VideoProcessor
from ocr_engine import OCREngine, OCRResult
from subtitle_sync import SubtitleSync, SubtitleSegment
from srt_generator import SRTGenerator


class QwenCoderAgent:
    """
    Agente principal para extracción de subtítulos hardcoded de videos
    usando OCR con IA
    """
    
    def __init__(
        self,
        fps_extraction: float = 2.0,
        confidence_threshold: float = 0.6,
        min_duration: float = 1.0,
        max_duration: float = 6.0,
        language: str = 'spa',
        use_gpu: bool = False,
        ocr_engine: str = 'tesseract'
    ):
        """
        Inicializar el Agente Qwen Coder
        
        Args:
            fps_extraction: Frames por segundo a extraer del video
            confidence_threshold: Umbral de confianza mínimo para OCR (0.0-1.0)
            min_duration: Duración mínima de subtítulo en segundos
            max_duration: Duración máxima de subtítulo en segundos
            language: Código de idioma para OCR (spa=español, eng=inglés)
            use_gpu: Usar aceleración GPU si está disponible
            ocr_engine: Motor OCR a usar ('tesseract' o 'paddle')
        """
        print("🚀 Inicializando Agente Qwen Coder...")
        
        # Configuración
        self.fps_extraction = fps_extraction
        self.confidence_threshold = confidence_threshold
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.language = language
        self.use_gpu = use_gpu
        self.ocr_engine_type = ocr_engine
        
        # Inicializar componentes
        self.video_processor = VideoProcessor(fps_extraction=fps_extraction)
        
        self.ocr_engine = OCREngine(
            language=language,
            confidence_threshold=confidence_threshold,
            use_gpu=use_gpu,
            ocr_engine=ocr_engine
        )
        
        self.subtitle_sync = SubtitleSync(
            min_duration=min_duration,
            max_duration=max_duration,
            gap_threshold=0.5,
            similarity_threshold=0.8
        )
        
        self.srt_generator = SRTGenerator(encoding='utf-8')
        
        print("✓ Agente Qwen Coder listo\n")
    
    def extract_subtitles(
        self,
        video_path: str,
        output_path: str,
        preview: bool = False,
        save_preview_frames: bool = False
    ) -> str:
        """
        Extraer subtítulos hardcoded de un video y generar archivo .srt
        
        Args:
            video_path: Ruta al archivo de video
            output_path: Ruta para el archivo .srt de salida
            preview: Modo preview (procesa solo primeros 30 segundos)
            save_preview_frames: Guardar frames procesados para depuración
            
        Returns:
            Ruta del archivo .srt generado
        """
        print(f"📹 Procesando video: {video_path}")
        print(f"📍 Salida: {output_path}\n")
        
        try:
            # Abrir video
            self.video_processor.open_video(video_path)
            
            # Mostrar información del video
            video_info = self.video_processor.get_video_info()
            self._print_video_info(video_info)
            
            # Limitar tiempo en modo preview
            max_timestamp = 30 if preview else None
            
            # Extraer frames y procesar con OCR
            ocr_results = self._process_frames_with_ocr(
                max_timestamp=max_timestamp,
                save_frames=save_preview_frames
            )
            
            if not ocr_results:
                print("⚠ No se detectó texto en el video")
                return ""
            
            print(f"\n✓ Textos detectados: {len(ocr_results)}")
            
            # Sincronizar y agrupar segmentos
            print("\n🔄 Sincronizando subtítulos...")
            segments = self.subtitle_sync.group_by_timestamp(ocr_results)
            
            if not segments:
                print("⚠ No se pudieron sincronizar subtítulos válidos")
                return ""
            
            print(f"✓ Segmentos sincronizados: {len(segments)}")
            
            # Generar archivo SRT
            print(f"\n💾 Generando archivo SRT...")
            output_file = self.srt_generator.generate_file(
                segments=segments,
                output_path=output_path
            )
            
            # Validar archivo generado
            if self.srt_generator.validate_srt(output_file):
                print("✓ Archivo SRT válido")
            else:
                print("⚠ Advertencia: El archivo SRT podría tener problemas de formato")
            
            print(f"\n✅ ¡Proceso completado exitosamente!")
            
            return output_file
            
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            raise
        finally:
            # Cerrar video
            self.video_processor.close_video()
    
    def _process_frames_with_ocr(
        self,
        max_timestamp: Optional[float] = None,
        save_frames: bool = False
    ) -> List[Dict]:
        """
        Procesar frames extraídos con OCR
        
        Args:
            max_timestamp: Timestamp máximo para procesar (para modo preview)
            save_frames: Guardar frames procesados
            
        Returns:
            Lista de resultados OCR
        """
        ocr_results = []
        frame_count = 0
        
        # Barra de progreso para frames
        frames_iterable = self.video_processor.extract_frames()
        
        for frame, timestamp in frames_iterable:
            # Verificar límite de tiempo
            if max_timestamp and timestamp > max_timestamp:
                print(f"\n⏱ Límite de preview alcanzado ({max_timestamp}s)")
                break
            
            frame_count += 1
            
            # Preprocesar frame para OCR
            preprocessed_frame = self.video_processor.preprocess_frame_for_ocr(frame)
            
            # Ejecutar OCR
            results = self.ocr_engine.recognize_text(preprocessed_frame, timestamp)
            
            # Filtrar y agregar resultados
            for result in results:
                if result.confidence >= self.confidence_threshold and result.text.strip():
                    # Limpiar texto
                    cleaned_text = self.ocr_engine.clean_text(result.text)
                    
                    if cleaned_text:
                        ocr_results.append({
                            'text': cleaned_text,
                            'confidence': result.confidence,
                            'timestamp': timestamp,
                            'bounding_box': result.bounding_box
                        })
            
            # Guardar frame para depuración (opcional)
            if save_frames and frame_count <= 5:
                self._save_debug_frame(frame, frame_count, timestamp)
        
        return ocr_results
    
    def _print_video_info(self, video_info: Dict):
        """Mostrar información del video"""
        print("Información del video:")
        print(f"  📁 Archivo: {video_info.get('path', 'N/A')}")
        print(f"  📺 Resolución: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
        print(f"  ⏱️ Duración: {video_info.get('duration_seconds', 0)}s")
        print(f"  🎬 FPS original: {video_info.get('fps', 0)}")
        print(f"  📸 FPS extracción: {video_info.get('extraction_fps', 0)}")
        print(f"  🔢 Frames totales: {video_info.get('total_frames', 0)}")
        print(f"  🔽 Intervalo: cada {video_info.get('frame_interval', 1)} frames")
        print()
    
    def _save_debug_frame(self, frame, frame_num: int, timestamp: float):
        """Guardar frame para depuración"""
        try:
            import cv2
            from pathlib import Path
            
            debug_dir = Path("debug_frames")
            debug_dir.mkdir(exist_ok=True)
            
            # Convertir RGB a BGR para guardar
            frame_bgr = frame[:, :, ::-1]
            
            filename = debug_dir / f"frame_{frame_num:04d}_t{timestamp:.2f}s.png"
            cv2.imwrite(str(filename), frame_bgr)
            
        except Exception as e:
            print(f"⚠ No se pudo guardar frame de debug: {e}")
    
    def batch_extract(
        self,
        video_paths: List[str],
        output_dir: str,
        **kwargs
    ) -> List[str]:
        """
        Extraer subtítulos de múltiples videos
        
        Args:
            video_paths: Lista de rutas de videos
            output_dir: Directorio para archivos de salida
            **kwargs: Argumentos adicionales para extract_subtitles
            
        Returns:
            Lista de rutas de archivos SRT generados
        """
        from pathlib import Path
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for i, video_path in enumerate(video_paths, start=1):
            print(f"\n{'='*60}")
            print(f"Video {i}/{len(video_paths)}")
            print(f"{'='*60}\n")
            
            # Generar nombre de archivo de salida
            video_name = Path(video_path).stem
            output_path = output_dir / f"{video_name}.srt"
            
            try:
                srt_path = self.extract_subtitles(
                    video_path=video_path,
                    output_path=str(output_path),
                    **kwargs
                )
                
                if srt_path:
                    generated_files.append(srt_path)
                    
            except Exception as e:
                print(f"❌ Error procesando {video_path}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"📊 Resumen del procesamiento por lotes")
        print(f"{'='*60}")
        print(f"Videos procesados: {len(video_paths)}")
        print(f"Archivos SRT generados: {len(generated_files)}")
        
        return generated_files
    
    def get_statistics(self, ocr_results: List[Dict]) -> Dict:
        """
        Obtener estadísticas del procesamiento OCR
        
        Args:
            ocr_results: Lista de resultados OCR
            
        Returns:
            Diccionario con estadísticas
        """
        if not ocr_results:
            return {}
        
        confidences = [r['confidence'] for r in ocr_results]
        timestamps = [r['timestamp'] for r in ocr_results]
        
        import numpy as np
        
        stats = {
            'total_detections': len(ocr_results),
            'avg_confidence': float(np.mean(confidences)),
            'min_confidence': float(np.min(confidences)),
            'max_confidence': float(np.max(confidences)),
            'time_range_start': float(min(timestamps)),
            'time_range_end': float(max(timestamps)),
            'unique_texts': len(set(r['text'] for r in ocr_results))
        }
        
        return stats


# Función de conveniencia para uso rápido
def extract_subtitles_from_video(
    video_path: str,
    output_path: str,
    language: str = 'spa',
    **kwargs
) -> str:
    """
    Función rápida para extraer subtítulos de un video
    
    Args:
        video_path: Ruta al video
        output_path: Ruta para el archivo .srt
        language: Idioma del OCR
        **kwargs: Parámetros adicionales para QwenCoderAgent
        
    Returns:
        Ruta del archivo .srt generado
    """
    agent = QwenCoderAgent(language=language, **kwargs)
    return agent.extract_subtitles(video_path, output_path)
