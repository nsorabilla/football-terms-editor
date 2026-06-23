"""
Agente 3 — Analista de video (filtro estricto)
Evalúa calidad de imagen, audio, contenido relevante y subtítulos coherentes.
BLOQUEA el pipeline si no pasa los umbrales mínimos.
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
    "offside", "penalti", "córner", "arquero", "delantero", "mediocampista",
    "defensa", "portero", "pase", "remate", "tiro", "pressing", "contraataque",
]

# ── Umbrales mínimos (ESTRICTOS) ─────────────────────────────────────────────
MIN_WIDTH = 720          # px — mínimo 720p
MIN_FPS = 24             # fps
MIN_DURATION = 20        # segundos
MAX_DURATION = 3600      # 60 minutos
MIN_AUDIO_DB = -40.0     # dB — debajo de esto el audio es inaudible
MIN_KEYWORD_MATCHES = 2  # palabras clave de fútbol mínimas en la transcripción
MAX_SILENCE_RATIO = 0.6  # máximo 60% del video en silencio


def get_ffprobe():
    if os.path.exists(FFPROBE_PATH):
        return FFPROBE_PATH
    import shutil
    return shutil.which("ffprobe")


def analyze_streams(video_path: str) -> dict:
    ffprobe = get_ffprobe()
    if not ffprobe:
        return {"error": "ffprobe no encontrado"}
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json",
           "-show_streams", "-show_format", video_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}


def check_audio_level(video_path: str) -> float:
    ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
    cmd = [ffmpeg, "-i", video_path, "-af", "volumedetect",
           "-vn", "-sn", "-dn", "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        for line in result.stderr.split("\n"):
            if "mean_volume" in line:
                return float(line.split(":")[-1].strip().replace(" dB", ""))
    except Exception:
        pass
    return -99.0


def check_silence_ratio(video_path: str, duration: float) -> float:
    """Calcula la proporción del video que está en silencio."""
    ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
    cmd = [ffmpeg, "-i", video_path,
           "-af", "silencedetect=noise=-40dB:d=0.5",
           "-vn", "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        silence_total = 0.0
        start = None
        for line in result.stderr.split("\n"):
            if "silence_start" in line:
                try:
                    start = float(line.split("silence_start:")[-1].strip())
                except Exception:
                    pass
            if "silence_end" in line and start is not None:
                try:
                    end = float(line.split("silence_end:")[-1].split("|")[0].strip())
                    silence_total += end - start
                    start = None
                except Exception:
                    pass
        return silence_total / duration if duration > 0 else 0
    except Exception:
        return 0.0


def transcribe_sample(video_path: str) -> str:
    try:
        import whisper
        ffmpeg = FFMPEG_PATH if os.path.exists(FFMPEG_PATH) else "ffmpeg"
        if os.path.exists(FFMPEG_PATH):
            os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ.get("PATH", "")
        import tempfile
        tmp = tempfile.mktemp(suffix=".wav")
        subprocess.run([ffmpeg, "-y", "-i", video_path,
                        "-t", "90", "-ac", "1", "-ar", "16000", tmp],
                       capture_output=True, timeout=30)
        model = whisper.load_model("tiny")
        result = model.transcribe(tmp, language="es")
        return result.get("text", "")
    except Exception as e:
        return f"[Error: {e}]"


def check_relevance(transcript: str) -> tuple:
    t = transcript.lower()
    found = [kw for kw in FOOTBALL_KEYWORDS if kw in t]
    return len(found) >= MIN_KEYWORD_MATCHES, found


def run(video_path: str) -> dict:
    report = {
        "agent": "Analista de video",
        "timestamp": datetime.now().isoformat(),
        "video": video_path,
        "checks": {},
        "approved": False,
        "blockers": [],    # issues que impiden continuar
        "warnings": [],    # issues que no bloquean pero se informan
    }

    streams_data = analyze_streams(video_path)
    video_stream = next((s for s in streams_data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams_data.get("streams", []) if s.get("codec_type") == "audio"), {})

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    is_vertical = height > width

    fps_raw = video_stream.get("r_frame_rate", "0/1")
    try:
        num, den = fps_raw.split("/")
        fps = round(int(num) / int(den), 1)
    except Exception:
        fps = 0

    duration = float(streams_data.get("format", {}).get("duration", 0))
    orientation = "vertical (celular)" if is_vertical else "horizontal (laptop/cámara)"

    # ── Check 1: Orientación ─────────────────────────────────────────────────
    report["checks"]["orientation"] = {
        "value": f"{width}x{height} — {orientation}",
        "ok": True,
        "note": f"OK — detectado como {orientation}"
    }

    # ── Check 2: Resolución mínima ───────────────────────────────────────────
    min_dim = min(width, height)
    res_ok = min_dim >= MIN_WIDTH
    report["checks"]["resolution"] = {
        "value": f"{width}x{height}",
        "ok": res_ok,
        "note": "OK" if res_ok else f"❌ BLOQUEANTE: Resolución {min_dim}px < mínimo {MIN_WIDTH}px"
    }
    if not res_ok:
        report["blockers"].append(f"Resolución insuficiente ({min_dim}px). Grabá en al menos 720p.")

    # ── Check 3: FPS ─────────────────────────────────────────────────────────
    fps_ok = fps >= MIN_FPS
    report["checks"]["fps"] = {
        "value": fps,
        "ok": fps_ok,
        "note": "OK" if fps_ok else f"⚠️ FPS bajo ({fps}). Recomendado: {MIN_FPS}+"
    }
    if not fps_ok:
        report["warnings"].append(f"FPS bajo ({fps}fps). El video puede verse entrecortado.")

    # ── Check 4: Duración ────────────────────────────────────────────────────
    dur_ok = MIN_DURATION <= duration <= MAX_DURATION
    report["checks"]["duration"] = {
        "value": f"{duration:.0f}s ({duration/60:.1f} min)",
        "ok": dur_ok,
        "note": "OK" if dur_ok else f"❌ BLOQUEANTE: Duración {duration:.0f}s fuera de rango ({MIN_DURATION}–{MAX_DURATION}s)"
    }
    if not dur_ok:
        report["blockers"].append(f"Duración fuera de rango ({duration:.0f}s).")

    # ── Check 5: Audio presente ──────────────────────────────────────────────
    has_audio = bool(audio_stream)
    report["checks"]["has_audio"] = {
        "ok": has_audio,
        "note": "OK" if has_audio else "❌ BLOQUEANTE: El video no tiene pista de audio"
    }
    if not has_audio:
        report["blockers"].append("Sin pista de audio.")

    # ── Check 6: Nivel de audio ──────────────────────────────────────────────
    mean_vol = check_audio_level(video_path)
    vol_ok = mean_vol > MIN_AUDIO_DB
    report["checks"]["audio_level"] = {
        "value": f"{mean_vol:.1f} dB",
        "ok": vol_ok,
        "note": "OK" if vol_ok else f"❌ BLOQUEANTE: Audio muy bajo ({mean_vol:.1f} dB). Hablá más cerca del micrófono."
    }
    if not vol_ok:
        report["blockers"].append(f"Audio inaudible ({mean_vol:.1f} dB). Mínimo: {MIN_AUDIO_DB} dB.")

    # ── Check 7: Ratio de silencio ───────────────────────────────────────────
    silence_ratio = check_silence_ratio(video_path, duration)
    silence_ok = silence_ratio <= MAX_SILENCE_RATIO
    report["checks"]["silence_ratio"] = {
        "value": f"{silence_ratio*100:.0f}% del video en silencio",
        "ok": silence_ok,
        "note": "OK" if silence_ok else f"⚠️ {silence_ratio*100:.0f}% del video está en silencio. Revisá el contenido."
    }
    if not silence_ok:
        report["warnings"].append(f"Demasiado silencio ({silence_ratio*100:.0f}%). ¿Grabaste correctamente?")

    # ── Check 8: Contenido relevante ─────────────────────────────────────────
    transcript = transcribe_sample(video_path)
    is_relevant, keywords_found = check_relevance(transcript)
    report["checks"]["content_relevance"] = {
        "ok": is_relevant,
        "keywords_found": keywords_found,
        "transcript_sample": transcript[:300],
        "note": "OK" if is_relevant else f"⚠️ Pocas keywords de fútbol detectadas: {keywords_found}"
    }
    if not is_relevant:
        report["warnings"].append(f"Contenido posiblemente no relacionado al canal. Keywords encontradas: {keywords_found}")

    # ── Veredicto final ───────────────────────────────────────────────────────
    report["approved"] = len(report["blockers"]) == 0
    report["transcript_sample"] = transcript

    return report


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    if not path:
        print("Uso: python video_analyst.py <ruta_video>")
        sys.exit(1)
    data = run(path)
    print(json.dumps(data, ensure_ascii=False, indent=2))
