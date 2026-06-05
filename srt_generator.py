"""
SRT Generator Module
Generador de archivos de subtítulos en formato .srt
"""

from typing import List, Optional
from pathlib import Path
from datetime import timedelta


class SRTGenerator:
    """
    Clase para generar archivos de subtítulos en formato SubRip (.srt)
    """
    
    def __init__(self, encoding: str = 'utf-8'):
        """
        Inicializar el generador SRT
        
        Args:
            encoding: Codificación del archivo de salida
        """
        self.encoding = encoding
    
    def format_timestamp(self, seconds: float) -> str:
        """
        Convertir segundos a formato de timestamp SRT (HH:MM:SS,mmm)
        
        Args:
            seconds: Tiempo en segundos
            
        Returns:
            String en formato SRT timestamp
        """
        # Asegurar que no sea negativo
        if seconds < 0:
            seconds = 0
        
        # Calcular horas, minutos, segundos y milisegundos
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds * 1000) % 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def generate_entry(
        self, 
        index: int, 
        start_time: float, 
        end_time: float, 
        text: str
    ) -> str:
        """
        Generar una entrada individual de subtítulo
        
        Args:
            index: Número de índice del subtítulo
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
            text: Texto del subtítulo
            
        Returns:
            String formateado como entrada SRT
        """
        start_ts = self.format_timestamp(start_time)
        end_ts = self.format_timestamp(end_time)
        
        # Formatear entrada SRT
        entry = f"{index}\n{start_ts} --> {end_ts}\n{text}\n"
        
        return entry
    
    def generate_file(
        self, 
        segments: List[object], 
        output_path: str,
        max_line_length: int = 42,
        max_lines: int = 2
    ) -> str:
        """
        Generar archivo SRT completo a partir de segmentos
        
        Args:
            segments: Lista de objetos SubtitleSegment
            output_path: Ruta del archivo de salida
            max_line_length: Longitud máxima por línea
            max_lines: Número máximo de líneas por subtítulo
            
        Returns:
            Ruta del archivo generado
        """
        output_file = Path(output_path)
        
        # Crear directorio si no existe
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        entries = []
        
        for i, segment in enumerate(segments, start=1):
            # Formatear texto para cumplir con estándares SRT
            formatted_text = self._format_subtitle_text(
                segment.text,
                max_line_length,
                max_lines
            )
            
            entry = self.generate_entry(
                index=i,
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=formatted_text
            )
            
            entries.append(entry)
        
        # Unir todas las entradas con línea en blanco entre ellas
        content = '\n'.join(entries)
        
        # Escribir archivo
        with open(output_file, 'w', encoding=self.encoding) as f:
            f.write(content)
        
        print(f"✓ Archivo SRT generado: {output_path}")
        print(f"  Total de subtítulos: {len(entries)}")
        
        return str(output_file)
    
    def _format_subtitle_text(
        self, 
        text: str, 
        max_line_length: int = 42,
        max_lines: int = 2
    ) -> str:
        """
        Formatear texto de subtítulo para cumplir con estándares
        
        Args:
            text: Texto original
            max_line_length: Longitud máxima por línea
            max_lines: Número máximo de líneas
            
        Returns:
            Texto formateado
        """
        if not text:
            return ""
        
        # Dividir por saltos de línea existentes
        lines = text.split('\n')
        
        # Limitar número de líneas
        if len(lines) > max_lines:
            lines = lines[:max_lines]
        
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Si la línea es demasiado larga, dividirla
            if len(line) > max_line_length:
                wrapped = self._wrap_text(line, max_line_length)
                formatted_lines.extend(wrapped)
            else:
                formatted_lines.append(line)
        
        # Limitar nuevamente después del wrapping
        if len(formatted_lines) > max_lines:
            formatted_lines = formatted_lines[:max_lines]
        
        return '\n'.join(formatted_lines)
    
    def _wrap_text(self, text: str, max_length: int) -> List[str]:
        """
        Dividir texto largo en múltiples líneas
        
        Args:
            text: Texto a dividir
            max_length: Longitud máxima por línea
            
        Returns:
            Lista de líneas
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Verificar si agregar la palabra excede el límite
            if len(current_line) + len(word) + 1 <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                # Guardar línea actual e iniciar nueva
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        # Agregar última línea
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def validate_srt(self, file_path: str) -> bool:
        """
        Validar que un archivo SRT tenga formato correcto
        
        Args:
            file_path: Ruta del archivo SRT
            
        Returns:
            True si es válido, False en caso contrario
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False
            
            with open(path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Verificaciones básicas
            if not content.strip():
                return False
            
            # Debe contener al menos un timestamp
            if '-->' not in content:
                return False
            
            # Debe comenzar con un número
            lines = content.strip().split('\n')
            if not lines[0].strip().isdigit():
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validando SRT: {e}")
            return False
    
    def merge_srt_files(
        self, 
        file_paths: List[str], 
        output_path: str
    ) -> str:
        """
        Fusionar múltiples archivos SRT en uno solo
        
        Args:
            file_paths: Lista de rutas de archivos SRT
            output_path: Ruta del archivo de salida
            
        Returns:
            Ruta del archivo fusionado
        """
        all_entries = []
        global_index = 1
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                print(f"⚠ Archivo no encontrado: {file_path}")
                continue
            
            with open(path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Separar entradas individuales
            entries = content.strip().split('\n\n')
            
            for entry in entries:
                if entry.strip():
                    lines = entry.strip().split('\n')
                    
                    if len(lines) >= 3:
                        # Extraer timestamp
                        timestamp_line = lines[1]
                        
                        # Extraer texto (puede ser múltiples líneas)
                        text_lines = lines[2:]
                        text = '\n'.join(text_lines)
                        
                        # Crear nueva entrada con índice global
                        new_entry = f"{global_index}\n{timestamp_line}\n{text}"
                        all_entries.append(new_entry)
                        global_index += 1
        
        # Escribir archivo fusionado
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding=self.encoding) as f:
            f.write('\n\n'.join(all_entries))
        
        print(f"✓ Archivos SRT fusionados: {output_path}")
        print(f"  Total de subtítulos: {len(all_entries)}")
        
        return str(output_file)
