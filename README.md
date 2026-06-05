# Football Terms Editor — MVP

App de escritorio para editar clips de video automáticamente.

## Qué hace

1. **Une clips** — junta todos los videos de una carpeta en orden cronológico
2. **Mejora imagen** — brillo, contraste y saturación automáticos
3. **Mejora audio** — normalización EBU R128 + reducción de ruido + corte de silencios
4. **Subtítulos** — transcripción automática en español con Whisper
5. **Exporta dos versiones** — YouTube 16:9 y Reels/TikTok 9:16

## Requisitos

- Python 3.10+
- ffmpeg instalado ([descargar](https://ffmpeg.org/download.html))

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python app.py
```

1. Elegí la carpeta con los clips (nombrados en orden numérico)
2. Elegí carpeta de salida
3. Click en **Procesar videos**
4. Los archivos finales aparecen en `output/`

## Archivos de salida

| Archivo | Descripción |
|---|---|
| `01_merged.mp4` | Clips unidos sin editar |
| `02_video_enhanced.mp4` | Con mejoras de imagen |
| `03_audio_enhanced.mp4` | Con mejoras de audio |
| `04_with_subtitles.mp4` | Con subtítulos incrustados |
| `FINAL_youtube.mp4` | ✅ Listo para YouTube (1080p 16:9) |
| `FINAL_reels.mp4` | ✅ Listo para Reels (1080x1920 9:16) |
