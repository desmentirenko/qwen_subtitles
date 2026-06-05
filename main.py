#!/usr/bin/env python3
"""
Agente Qwen Coder - Punto de Entrada Principal
CLI para extracción de subtítulos hardcoded con OCR
"""

import argparse
import sys
from pathlib import Path


def main():
    """Función principal de la CLI"""
    
    parser = argparse.ArgumentParser(
        description='🎬 Agente Qwen Coder - Extraer subtítulos hardcoded de videos usando OCR',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --video mi_video.mp4 --output subtitulos.srt
  %(prog)s -v video.mp4 -o salida.srt --language eng
  %(prog)s --video tutorial.mp4 --preview --fps 1
  %(prog)s --batch ./videos/ --output-dir ./subtitles/
        """
    )
    
    # Argumentos principales
    parser.add_argument(
        '-v', '--video',
        type=str,
        help='Ruta al archivo de video'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='subtitles.srt',
        help='Ruta para el archivo .srt de salida (default: subtitles.srt)'
    )
    
    parser.add_argument(
        '-l', '--language',
        type=str,
        default='spa',
        choices=['spa', 'eng', 'fra', 'deu', 'ita', 'por'],
        help='Idioma del OCR (default: spa)'
    )
    
    # Opciones de procesamiento
    parser.add_argument(
        '--fps',
        type=float,
        default=2.0,
        help='Frames por segundo a extraer (default: 2.0)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.6,
        help='Umbral de confianza mínimo 0.0-1.0 (default: 0.6)'
    )
    
    parser.add_argument(
        '--min-duration',
        type=float,
        default=1.0,
        help='Duración mínima de subtítulo en segundos (default: 1.0)'
    )
    
    parser.add_argument(
        '--max-duration',
        type=float,
        default=6.0,
        help='Duración máxima de subtítulo en segundos (default: 6.0)'
    )
    
    # Opciones avanzadas
    parser.add_argument(
        '--gpu',
        action='store_true',
        help='Usar aceleración GPU si está disponible'
    )
    
    parser.add_argument(
        '--ocr-engine',
        type=str,
        default='tesseract',
        choices=['tesseract', 'paddle'],
        help='Motor OCR a usar (default: tesseract)'
    )
    
    # Modos especiales
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Modo preview (solo primeros 30 segundos)'
    )
    
    parser.add_argument(
        '--debug-frames',
        action='store_true',
        help='Guardar frames procesados para depuración'
    )
    
    parser.add_argument(
        '--batch',
        type=str,
        help='Directorio con múltiples videos para procesar por lotes'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./subtitles',
        help='Directorio para salida en modo batch (default: ./subtitles)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.video and not args.batch:
        parser.print_help()
        print("\n❌ Error: Debe especificar --video o --batch")
        sys.exit(1)
    
    # Importar agente
    try:
        from qwen_coder_agent import QwenCoderAgent
    except ImportError as e:
        print(f"❌ Error al importar módulos: {e}")
        print("\nAsegúrese de instalar las dependencias:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Modo batch
    if args.batch:
        batch_dir = Path(args.batch)
        
        if not batch_dir.exists():
            print(f"❌ Directorio no encontrado: {args.batch}")
            sys.exit(1)
        
        # Buscar videos
        video_extensions = ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.webm']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(batch_dir.glob(ext))
        
        if not video_files:
            print(f"❌ No se encontraron videos en: {args.batch}")
            sys.exit(1)
        
        print(f"📁 Videos encontrados: {len(video_files)}")
        
        # Inicializar agente
        agent = QwenCoderAgent(
            fps_extraction=args.fps,
            confidence_threshold=args.confidence,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            language=args.language,
            use_gpu=args.gpu,
            ocr_engine=args.ocr_engine
        )
        
        # Procesar por lotes
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = agent.batch_extract(
            video_paths=[str(v) for v in video_files],
            output_dir=str(output_dir),
            preview=args.preview,
            save_preview_frames=args.debug_frames
        )
        
        print(f"\n✅ Procesamiento por lotes completado")
        print(f"   Archivos generados: {len(generated_files)}")
        
        return
    
    # Modo single video
    video_path = Path(args.video)
    
    if not video_path.exists():
        print(f"❌ Archivo de video no encontrado: {args.video}")
        sys.exit(1)
    
    # Inicializar agente
    agent = QwenCoderAgent(
        fps_extraction=args.fps,
        confidence_threshold=args.confidence,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        language=args.language,
        use_gpu=args.gpu,
        ocr_engine=args.ocr_engine
    )
    
    # Extraer subtítulos
    try:
        output_file = agent.extract_subtitles(
            video_path=str(video_path),
            output_path=args.output,
            preview=args.preview,
            save_preview_frames=args.debug_frames
        )
        
        if output_file:
            print(f"\n📄 Archivo generado: {output_file}")
        else:
            print("\n⚠ No se generó ningún archivo de subtítulos")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
