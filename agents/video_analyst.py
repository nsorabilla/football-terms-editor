"""
Agente 3 — Analista de video (filtro de calidad)
Evalúa: calidad de imagen, audio audible, contenido relevante, subtítulos coherentes.
"""

import os
import json
import subprocess
import sys
from datetime import datetime

FFMPEG_PATH = r"C:\Users\nicolas.sorabilla\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
FFPROBE_PATH = FFMPEG_PATH.replace("ffmpeg.exe", "ffprobe.exe")

FOOTBALL_KEYWORDS = [
    "fútbol", "football", "gol", "partido", "jugador", "argentina",
    "messi", "cancha", "mundial", "selección", "técnica", "táctica",
    "offside", "penalti", "córner", "arquero", "delantero",
]


def get_ffprobe():
    if os.path.exists(FFPROBE_PATH):
        return FFPROBE_PATH
    import shutil
    return shutil.which("ffprobe")


def analyze_streams(video_path: str) -> dict:
    ffprobe = get_ffprobe()
    if not ffprobe:
        return {"error": "ffprobe no encontrado"}
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}


def check_audio_level(video_path: str) -> float:
    ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
    cmd = [
        ffmpeg, "-i", video_path,
        "-af", "volumedetect", "-vn", "-sn", "-dn",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        for line in result.stderr.split("\n"):
            if "mean_volume" in line:
                val = float(line.split(":")[-1].strip().replace(" dB", ""))
                return val
    except Exception:
        pass
    return -99.0


def transcribe_sample(video_path: str) -> str:
    """Transcribe los primeros 60s para verificar contenido."""
    try:
        import whisper
        ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
        import tempfile
        tmp = tempfile.mktemp(suffix=".wav")
        subprocess.run([
            ffmpeg, "-y", "-i", video_path,
            "-t", "60", "-ac", "1", "-ar", "16000", tmp
        ], capture_output=True, timeout=30)
        model = whisper.load_model("tiny")  # modelo más rápido para análisis
        result = model.transcribe(tmp, language="es")
        return result.get("text", "")
    except Exception as e:
        return f"[Error transcribiendo: {e}]"


def check_relevance(transcript: str) -> tuple[bool, list[str]]:
    t = transcript.lower()
    found = [kw for kw in FOOTBALL_KEYWORDS if kw in t]
    return len(found) >= 2, found


def run(video_path: str) -> dict:
    report = {
        "agent": "Analista de video",
        "timestamp": datetime.now().isoformat(),
        "video": video_path,
        "checks": {},
        "approved": False,
        "issues": [],
    }

    # 1. Streams (resolución, fps, duración)
    streams_data = analyze_streams(video_path)
    video_stream = next((s for s in streams_data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams_data.get("streams", []) if s.get("codec_type") == "audio"), {})

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    fps_raw = video_stream.get("r_frame_rate", "0/1")
    try:
        num, den = fps_raw.split("/")
        fps = round(int(num) / int(den), 1)
    except Exception:
        fps = 0

    duration = float(streams_data.get("format", {}).get("duration", 0))

    report["checks"]["resolution"] = {
        "value": f"{width}x{height}",
        "ok": width >= 720,
        "note": "OK" if width >= 720 else f"Resolución baja ({width}px). Recomendado: 720p+"
    }
    report["checks"]["fps"] = {
        "value": fps,
        "ok": fps >= 24,
        "note": "OK" if fps >= 24 else f"FPS bajo ({fps}). Recomendado: 24+"
    }
    report["checks"]["duration"] = {
        "value": f"{duration:.0f}s",
        "ok": 30 <= duration <= 1800,
        "note": "OK" if 30 <= duration <= 1800 else f"Duración fuera de rango ({duration:.0f}s)"
    }
    report["checks"]["has_audio"] = {
        "ok": bool(audio_stream),
        "note": "OK" if audio_stream else "Sin pista de audio"
    }

    # 2. Nivel de audio
    mean_vol = check_audio_level(video_path)
    report["checks"]["audio_level"] = {
        "value": f"{mean_vol:.1f} dB",
        "ok": mean_vol > -35,
        "note": "OK" if mean_vol > -35 else f"Audio muy bajo ({mean_vol:.1f} dB)"
    }

    # 3. Contenido relevante (transcripción parcial)
    transcript = transcribe_sample(video_path)
    is_relevant, keywords_found = check_relevance(transcript)
    report["checks"]["content_relevance"] = {
        "ok": is_relevant,
        "keywords_found": keywords_found,
        "transcript_sample": transcript[:200],
        "note": "OK" if is_relevant else "No se detectaron suficientes keywords de fútbol"
    }

    # Resumen
    issues = [v["note"] for v in report["checks"].values() if not v.get("ok")]
    report["issues"] = issues
    report["approved"] = len(issues) == 0

    return report


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    if not path:
        print("Uso: python video_analyst.py <ruta_video>")
        sys.exit(1)
    data = run(path)
    print(json.dumps(data, ensure_ascii=False, indent=2))
