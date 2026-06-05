# Agente Qwen Coder - Google Colab

## Descripción
Sistema completo para extraer subtítulos incrustados (hardcoded) de videos usando OCR con IA y generar archivos .srt sincronizados.

## Instrucciones de Uso en Google Colab

### Paso 1: Abrir Google Colab
1. Ve a https://colab.research.google.com
2. Haz clic en "Nuevo Notebook"

### Paso 2: Copiar el Código
1. Abre el archivo `qwen_coder_colab.py` en este repositorio
2. Copia TODO el contenido del archivo

### Paso 3: Dividir en Celdas
Copia el código en 8 celdas separadas según los comentarios:

- **CELDA 1/8**: Montar Google Drive y configurar directorios
- **CELDA 2/8**: Instalar dependencias  
- **CELDA 3/8**: Video Processor (código Python)
- **CELDA 4/8**: OCR Engine (código Python)
- **CELDA 5/8**: Subtitle Sync (código Python)
- **CELDA 6/8**: SRT Generator (código Python)
- **CELDA 7/8**: Qwen Coder Agent (código Python)
- **CELDA 8/8**: Ejecución Principal (código Python)

### Paso 4: Ejecutar
1. Ejecuta la CELDA 1 para montar Google Drive
2. Ejecuta la CELDA 2 para instalar dependencias (toma ~2-3 minutos)
3. Ejecuta las CELDAS 3-7 para cargar el código
4. Ejecuta la CELDA 8 para procesar el video

## Configuración

El video de prueba está configurado en:
```
/content/drive/MyDrive/Vimeo_Downloads/Sergei Vasiliev Interview 01/10.mp4
```

Los resultados se guardan en:
```
/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder/
```

### Parámetros Configurables

En la CELDA 8, puedes modificar:

```python
config = {
    'language': 'es',      # 'es' español, 'en' inglés, 'fr' francés, etc.
    'fps': 2,              # frames por segundo (más alto = más preciso pero más lento)
    'use_gpu': True,       # usar GPU de Colab (recomendado)
    'ocr_engine': 'paddle', # 'paddle' (más preciso) o 'tesseract' (más rápido)
    'min_confidence': 0.5,  # confianza mínima para aceptar texto (0.0 a 1.0)
    'merge_threshold': 2.0, # ventana de tiempo para merge de textos (segundos)
}
```

## Características

✅ **Doble Motor OCR**
- PaddleOCR: Mayor precisión, ideal para texto en videos
- Tesseract: Más rápido, buen fallback

✅ **Preprocesamiento Inteligente**
- Conversión a escala de grises
- Umbralización automática (Otsu)
- Reducción de ruido

✅ **Sincronización Temporal**
- Agrupación de textos similares
- Merge de subtítulos superpuestos
- Duración mínima garantizada

✅ **Formato SRT Estándar**
- Compatible con todos los reproductores
- Validación automática de formato
- Codificación UTF-8

## Idiomas Soportados

- Español (es)
- Inglés (en)
- Francés (fr)
- Alemán (de)
- Italiano (it)
- Portugués (pt)

## Requisitos

Google Colab proporciona gratuitamente:
- GPU Tesla T4 o similar
- 12GB RAM
- Almacenamiento temporal

## Notas Importantes

⚠️ **Tiempo de Procesamiento**
- Un video de 10 minutos puede tomar 5-15 minutos
- Depende de: duración, resolución, cantidad de texto

⚠️ **Límites de Colab**
- Sesiones máximas: 12 horas
- Inactividad: 90 minutos máximo
- Guarda siempre los resultados en Google Drive

⚠️ **Calidad del OCR**
- Funciona mejor con texto claro y alto contraste
- Puede tener dificultades con:
  - Texto muy pequeño
  - Fondos complejos
  - Fuentes decorativas
  - Texto inclinado o curvo

## Solución de Problemas

### Error: "Video no encontrado"
- Verifica que Google Drive esté montado
- Confirma la ruta exacta del archivo
- Asegúrate de que el video existe en tu Drive

### Error: "PaddleOCR falló"
- El sistema usa automáticamente Tesseract como fallback
- Si prefieres solo Tesseract, cambia `'ocr_engine': 'tesseract'`

### Resultados vacíos o pocos subtítulos
- Reduce `min_confidence` a 0.3
- Aumenta `fps` a 3 o 4
- Verifica que el video tenga subtítulos visibles

## Archivos Generados

Este repositorio contiene:

1. **qwen_coder_colab.py** - Código completo para Google Colab
2. **README_COLOB.md** - Este archivo de instrucciones

## Soporte

Para problemas o mejoras, revisa la documentación de:
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Tesseract](https://github.com/tesseract-ocr/tesseract)
- [OpenCV](https://opencv.org/)
