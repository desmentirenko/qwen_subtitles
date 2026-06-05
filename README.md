# Agente Qwen Coder - Extractor de Subtítulos Hardcoded con OCR

## Descripción
Sistema inteligente que extrae subtítulos incrustados (hardcoded) de videos utilizando Reconocimiento Óptico de Caracteres (OCR) con IA, sincroniza los textos detectados y genera archivos de subtítulos en formato .srt.

## Características
- 🎬 Extracción automática de frames de video
- 🤖 OCR basado en IA para reconocimiento de texto
- ⏱️ Sincronización temporal precisa de subtítulos
- 📝 Generación de archivos .srt compatibles
- 🔍 Detección de cambios de texto entre frames
- 🧹 Limpieza y filtrado de texto detectado

## Requisitos
- Python 3.8+
- FFmpeg
- OpenCV
- Tesseract OCR o PaddleOCR
- Dependencias de Python (ver requirements.txt)

## Instalación

```bash
pip install -r requirements.txt
```

Asegúrate de tener instalado:
- **FFmpeg**: `sudo apt-get install ffmpeg` (Linux) o descargar de https://ffmpeg.org/
- **Tesseract OCR**: `sudo apt-get install tesseract-ocr` (Linux) o descargar de https://github.com/tesseract-ocr/tesseract

## Uso Básico

```python
from qwen_coder_agent import QwenCoderAgent

# Inicializar el agente
agent = QwenCoderAgent()

# Extraer subtítulos de un video
agent.extract_subtitles(
    video_path="video.mp4",
    output_path="subtitulos.srt",
    language="spa"  # español, eng para inglés, etc.
)
```

## Uso desde CLI

```bash
python main.py --video video.mp4 --output subtitulos.srt --language spa
```

## Estructura del Proyecto

```
/workspace/
├── main.py                 # Punto de entrada principal
├── qwen_coder_agent.py     # Clase principal del agente
├── video_processor.py      # Procesamiento de video y extracción de frames
├── ocr_engine.py          # Motor OCR con IA
├── subtitle_sync.py       # Sincronización y agrupación temporal
├── srt_generator.py       # Generador de archivos .srt
├── requirements.txt       # Dependencias
└── README.md              # Este archivo
```

## Configuración Avanzada

```python
agent = QwenCoderAgent(
    fps_extraction=2,           # Frames por segundo a extraer
    confidence_threshold=0.7,   # Umbral de confianza del OCR
    min_duration=1.0,           # Duración mínima de subtítulo (segundos)
    max_duration=6.0,           # Duración máxima de subtítulo (segundos)
    use_gpu=True                # Usar GPU si está disponible
)
```

## Formato de Salida (.srt)

```
1
00:00:01,500 --> 00:00:04,000
Bienvenidos a este tutorial

2
00:00:04,500 --> 00:00:07,000
Hoy aprenderemos sobre IA
```

## Licencia
MIT License
