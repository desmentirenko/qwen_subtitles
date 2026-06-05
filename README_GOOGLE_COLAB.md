# 🤖 Agente Qwen Coder - Google Colab Edition

## Sistema Autónomo para Extracción de Subtítulos Hardcoded con IA + OCR

Este agente autónomo está diseñado específicamente para ejecutarse en **Google Colab** y realiza:

1. ✅ **DEFINE** el objetivo automáticamente
2. ✅ **EJECUTA** código necesario (instalaciones, procesamiento)
3. ✅ **LEE** y **EVALÚA** resultados
4. ✅ **DECIDE** si cumplió el objetivo
5. ✅ **ITERA** con estrategias alternativas si falla
6. ✅ **REPORTA** el resultado final

---

## 📋 Características Principales

### 🔧 Auto-Gestión de Dependencias
- Instala automáticamente paquetes del sistema (tesseract, ffmpeg)
- Instala paquetes Python requeridos (paddlepaddle-gpu, paddleocr, opencv, etc.)
- Verifica todas las instalaciones antes de proceder

### 🎯 Múltiples Estrategias de OCR
El agente prueba automáticamente diferentes configuraciones:
| Estrategia | FPS | Motor OCR | Confianza |
|------------|-----|-----------|-----------|
| 1 | 2 | PaddleOCR | 0.5 |
| 2 | 3 | PaddleOCR | 0.3 |
| 3 | 4 | Tesseract | 0.4 |
| 4 | 2 | Ambos | 0.3 |
| 5 | 5 | PaddleOCR | 0.2 |

### 📊 Evaluación Inteligente de Calidad
- Score de calidad (0-100)
- Porcentaje de cobertura del video
- Detección de textos vacíos
- Detección de solapamientos
- Validación de rango esperado de subtítulos

### 🔄 Reintentos Automáticos
Si la calidad es insuficiente (< 60/100), el agente:
- Prueba la siguiente estrategia
- Ajusta parámetros automáticamente
- Re-evalúa el resultado

---

## 🚀 Cómo Usar en Google Colab

### Paso 1: Abrir Google Colab
1. Ve a https://colab.research.google.com
2. Crea un nuevo notebook

### Paso 2: Copiar el Código
Copia TODO el contenido de `qwen_coder_agent.py` en una celda grande O divídelo en estas 8 celdas:

#### CELDA 1/8 - Imports y Configuración
```python
# Todo el código hasta la clase Logger
```

#### CELDA 2/8 - DependencyManager
```python
# Clase completa DependencyManager
```

#### CELDA 3/8 - VideoProcessor
```python
# Clase completa VideoProcessor
```

#### CELDA 4/8 - OCREngine
```python
# Clase completa OCREngine
```

#### CELDA 5/8 - SubtitleSynchronizer + SRTGenerator
```python
# Clases SubtitleSynchronizer y SRTGenerator
```

#### CELDA 6/8 - QualityEvaluator
```python
# Clase completa QualityEvaluator
```

#### CELDA 7/8 - QwenCoderAgent
```python
# Clase completa QwenCoderAgent
```

#### CELDA 8/8 - Ejecución Principal
```python
# Todo el código desde if __name__ == "__main__"
```

### Paso 3: Configurar Rutas (Opcional)
Edita la configuración al inicio del archivo:

```python
CONFIG = {
    'video_path': "/content/drive/MyDrive/Vimeo_Downloads/Sergei Vasiliev Interview 01/10.mp4",
    'output_dir': "/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder",
    'max_iterations': 5,
    'min_subtitle_duration': 1.0,
    'max_subtitle_duration': 7.0,
    'min_confidence_threshold': 0.3,
    'target_subtitles_count_range': (50, 500),
}
```

### Paso 4: Ejecutar
1. Ejecuta la última celda
2. El agente se encargará de todo automáticamente

---

## 📁 Estructura de Output

El agente generará los siguientes archivos en tu directorio de output:

```
/content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder/
├── subtitles_20240101_120000.srt    # Archivo de subtítulos
└── processing_report.json           # Reporte detallado del proceso
```

### Formato del Archivo SRT
```srt
1
00:00:01,500 --> 00:00:04,000
Bienvenidos a esta entrevista

2
00:00:05,200 --> 00:00:08,800
Hoy vamos a hablar de tecnología
```

### Reporte JSON
Incluye:
- Timestamp del procesamiento
- Configuración usada
- Estrategia exitosa
- Métricas de calidad
- Historial de evaluaciones
- Errores encontrados

---

## 🎛️ Parámetros Configurables

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `video_path` | Ruta al video de entrada | - |
| `output_dir` | Directorio de salida | - |
| `max_iterations` | Máximo de intentos | 5 |
| `min_subtitle_duration` | Duración mínima (segundos) | 1.0 |
| `max_subtitle_duration` | Duración máxima (segundos) | 7.0 |
| `min_confidence_threshold` | Confianza mínima OCR | 0.3 |
| `target_subtitles_count_range` | Rango esperado de subtítulos | (50, 500) |

---

## 🔍 Proceso Detallado

### 1. Preparación del Entorno
```
[STEP] Preparando entorno...
✓ Directorio creado
✓ Google Drive montado
[STEP] Instalando paquetes del sistema...
✓ Paquetes instalados
[STEP] Instalando dependencias Python...
✓ paddlepaddle-gpu instalado
✓ paddleocr instalado
...
[STEP] Verificando instalaciones...
✓ OpenCV funcional
✓ PaddlePaddle funcional
✓ Tesseract OCR funcional
✓ FFmpeg funcional
```

### 2. Iteración con Estrategias
```
[STEP] 🔄 ITERACIÓN 1/5
[INFO] Estrategia: FPS=2, OCR=paddle, Conf=0.5
[STEP] Extrayendo frames a 2.0 FPS...
[INFO] Duración del video: 1847.32 segundos
[INFO] Frames totales en video: 55419
[INFO] Frames a extraer: ~1847
[SUCCESS] Frames extraídos: 1847
[STEP] Inicializando motores OCR...
✓ PaddleOCR inicializado
✓ Tesseract OCR disponible
[STEP] Extrayendo texto con OCR...
[Procesando OCR: 100%]
[STEP] Sincronizando subtítulos...
[SUCCESS] Subtítulos sincronizados: 287
[STEP] Generando SRT...
[SUCCESS] SRT generado: 287 subtítulos
[SUCCESS] SRT válido: Formato válido con 287 subtítulos
[STEP] Evaluando calidad del resultado...
[INFO] Score de calidad: 85/100
[INFO] Cobertura: 42.3%
[INFO] Subtítulos: 287
[SUCCESS] ✓ Calidad ACEPTABLE
✅ OBJETIVO CUMPLIDO
```

### 3. Resultado Final
```
============================================================
📊 RESUMEN FINAL
============================================================
Estado: ✅ ÉXITO
Iteraciones: 1
Estrategia final: {'fps': 2, 'ocr_engine': 'paddle', 'min_confidence': 0.5}
Archivo output: /content/drive/MyDrive/Vimeo_Downloads/Agente Qwen Coder/subtitles_20240101_120000.srt
Score calidad: 85/100
Subtítulos: 287
Cobertura: 42.3%
============================================================
```

---

## ⚠️ Consideraciones Importantes

### Tiempo de Procesamiento
- Videos largos (> 30 min) pueden tomar 15-60 minutos
- Depende de: duración, resolución, cantidad de texto, GPU disponible

### Uso de GPU en Colab
- Activa GPU: `Entorno de ejecución → Cambiar tipo → GPU`
- PaddleOCR usa GPU automáticamente si está disponible
- Mejora significativa en velocidad (3-5x más rápido)

### Límites de Colab
- Sesión máxima: 12 horas (Colab Free)
- RAM limitada: ~12GB
- Si el video es muy largo, considera procesarlo en segmentos

### Idiomas Soportados
El agente está configurado para español (`es`) pero soporta:
- `es` - Español
- `en` - Inglés
- `fr` - Francés
- `de` - Alemán
- `it` - Italiano
- `pt` - Portugués

Para cambiar el idioma, modifica en `OCREngine`:
```python
ocr_engine = OCREngine(language='en', use_gpu=True)  # Inglés
```

---

## 🐛 Solución de Problemas

### Error: "Video no encontrado"
- Verifica que el video esté en la ruta especificada
- Asegúrate de haber montado Google Drive
- Revisa permisos del archivo

### Error: "No se extrajo texto"
- El video podría no tener subtítulos hardcoded
- Intenta con otra estrategia (el agente lo hace automáticamente)
- Reduce `min_confidence_threshold`

### Error: "Calidad INSUFICIENTE"
- El agente reintentará automáticamente con otras estrategias
- Si todas fallan, revisa el reporte JSON para detalles
- Considera ajustar `target_subtitles_count_range`

### Error: "Memoria agotada"
- Reduce el FPS de extracción en las estrategias
- Procesa videos más cortos
- Usa Colab Pro para más RAM

---

## 📊 Métricas de Calidad

El agente evalúa la calidad basándose en:

| Factor | Peso | Descripción |
|--------|------|-------------|
| Cobertura adecuada | 40% | Entre 10-90% del video |
| Textos no vacíos | 20% | Todos los subtítulos tienen contenido |
| Sin solapamientos | 15% | No hay tiempos superpuestos |
| Cantidad apropiada | 15% | Dentro del rango esperado |
| Sin errores críticos | 10% | Formato SRT válido |

**Score ≥ 60**: Calidad aceptable ✅  
**Score < 60**: Se requiere reintento 🔄

---

## 📄 Licencia

Este código es de uso libre para fines educativos y personales.

---

## 🤝 Contribuciones

Para mejorar el agente:
1. Añade más estrategias a la lista `STRATEGIES`
2. Mejora los algoritmos de sincronización
3. Agrega soporte para más idiomas
4. Optimiza el preprocesamiento de imágenes

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa el archivo `processing_report.json`
2. Verifica los logs de Colab
3. Asegúrate de tener GPU activado
4. Confirma que el video tiene subtítulos hardcoded visibles

---

**¡El Agente Qwen Coder está listo para extraer tus subtítulos!** 🎉
