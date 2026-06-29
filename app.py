"""
Football Terms Editor — MVP
Interfaz visual para editar clips de video automáticamente.
"""

import os
import sys
import glob
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext
import customtkinter as ctk

# ── Configuración visual ─────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Helpers ──────────────────────────────────────────────────────────────────

FFMPEG_PATH = r"C:\Users\nicolas.sorabilla\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

def get_ffmpeg():
    import shutil
    path = shutil.which("ffmpeg")
    if path:
        return path
    if os.path.exists(FFMPEG_PATH):
        return FFMPEG_PATH
    local = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(local):
        return local
    return None


def run_cmd(cmd, log_fn):
    log_fn(f"▶ {' '.join(str(x) for x in cmd)}\n")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace"
    )
    for line in proc.stdout:
        log_fn(line)
    proc.wait()
    return proc.returncode


# ── Pipeline de edición ──────────────────────────────────────────────────────

def step_merge(clips, output_dir, log):
    """1. Une clips re-encodando para garantizar sync perfecto."""
    log("\n📎 Paso 1: Uniendo clips...\n")
    ffmpeg = get_ffmpeg()
    if not ffmpeg:
        log("❌ ffmpeg no encontrado.\n")
        return None

    import tempfile

    log(f"  Clips a procesar: {len(clips)}\n")
    for c in clips:
        log(f"  • {os.path.basename(c)}\n")

    # Paso 1a: re-encodar cada clip a formato uniforme en carpeta TEMP
    # Esto elimina diferencias de codec/framerate y evita problemas con paths especiales
    temp_dir = tempfile.mkdtemp()
    normalized = []
    for i, clip in enumerate(clips):
        out = os.path.join(temp_dir, f"clip_{i:03d}.mp4")
        cmd = [ffmpeg, "-y", "-i", clip,
               "-c:v", "libx264", "-preset", "fast", "-crf", "20",
               "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2",
               "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
               "-vsync", "cfr",   # framerate constante = sync perfecto
               out]
        rc = run_cmd(cmd, log)
        if rc == 0:
            normalized.append(out)
        else:
            log(f"  ⚠️ Error normalizando {os.path.basename(clip)}, se omite.\n")

    if not normalized:
        log("❌ Ningún clip pudo normalizarse.\n")
        return None

    # Paso 1b: unir los clips normalizados con concat (paths simples, sin chars especiales)
    list_file = os.path.join(temp_dir, "list.txt")
    with open(list_file, "w") as f:
        for p in normalized:
            f.write(f"file '{p}'\n")

    merged = os.path.join(output_dir, "01_merged.mp4")
    cmd2 = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", merged]
    rc = run_cmd(cmd2, log)
    if rc != 0:
        log("❌ Error al unir clips normalizados.\n")
        return None

    log(f"  ✅ Merge completado: {merged}\n")
    return merged


def detect_orientation(src, log):
    """Detecta si el video es horizontal (16:9) o vertical (9:16)."""
    ffmpeg = get_ffmpeg()
    ffprobe = ffmpeg.replace("ffmpeg.exe", "ffprobe.exe") if ffmpeg else None
    try:
        import json as _json
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_streams", src],
            capture_output=True, text=True, timeout=15
        )
        data = _json.loads(result.stdout)
        vs = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        w = int(vs.get("width", 1920))
        h = int(vs.get("height", 1080))
        is_vertical = h > w
        log(f"  📐 Resolución detectada: {w}x{h} → {'VERTICAL (celular)' if is_vertical else 'HORIZONTAL (laptop/cámara)'}\n")
        return is_vertical, w, h
    except Exception as e:
        log(f"  ⚠️ No se pudo detectar orientación: {e}. Asumiendo horizontal.\n")
        return False, 1920, 1080


def step_enhance_video(src, output_dir, log):
    """2. Mejora imagen: color, contraste, nitidez. Adapta según orientación."""
    log("\n🎨 Paso 2: Mejorando imagen...\n")
    ffmpeg = get_ffmpeg()
    dst = os.path.join(output_dir, "02_video_enhanced.mp4")

    is_vertical, w, h = detect_orientation(src, log)

    # Filtros de calidad — sutiles y naturales, no artificiales
    # contrast/brightness/saturation leves para no verse "filtrado"
    quality_filters = (
        "eq=contrast=1.08:brightness=0.02:saturation=1.12:gamma=1.03,"
        "unsharp=3:3:0.6:3:3:0"
    )

    if is_vertical:
        vf = f"{quality_filters},scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    else:
        vf = f"{quality_filters},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

    cmd = [ffmpeg, "-y", "-i", src,
           "-vf", vf,
           "-c:v", "libx264", "-preset", "fast", "-crf", "16",
           "-c:a", "copy", dst]
    run_cmd(cmd, log)
    return dst


def step_enhance_audio(src, output_dir, log):
    """3. Mejora audio: reducción de ruido, ecualización de voz, normalización broadcast."""
    log("\n🔊 Paso 3: Mejorando audio...\n")
    ffmpeg = get_ffmpeg()
    dst = os.path.join(output_dir, "03_audio_enhanced.mp4")

    # Cadena de filtros de audio profesional:
    # 1. highpass 100Hz — elimina rumble y ruido de fondo grave
    # 2. afftdn — reducción de ruido por FFT (elimina hiss/hum de fondo)
    # 3. equalizer 3kHz — realza la presencia de voz (+4dB)
    # 4. equalizer 250Hz — reduce barro/muddiness (-2dB)
    # 5. acompressor — compresión suave para nivelar volumen
    # 6. loudnorm — normalización EBU R128 broadcast
    af = (
        "highpass=f=100,"
        "afftdn=nf=-25,"
        "equalizer=f=250:width_type=o:width=2:g=-2,"
        "equalizer=f=3000:width_type=o:width=2:g=4,"
        "equalizer=f=8000:width_type=o:width=2:g=2,"
        "acompressor=threshold=0.089:ratio=3:attack=5:release=50:makeup=2,"
        "loudnorm=I=-14:TP=-1:LRA=9"
    )
    cmd = [ffmpeg, "-y", "-i", src,
           "-af", af,
           "-c:v", "copy",
           "-c:a", "aac", "-b:a", "256k",
           dst]
    run_cmd(cmd, log)
    return dst


def step_subtitles(src, output_dir, log):
    """4. Genera subtítulos adaptados a la orientación del video."""
    log("\n📝 Paso 4: Generando subtítulos (Whisper)...\n")

    ffmpeg = get_ffmpeg()
    if ffmpeg:
        os.environ["PATH"] = os.path.dirname(ffmpeg) + os.pathsep + os.environ.get("PATH", "")

    try:
        import whisper
    except ImportError:
        log("⚠️  Whisper no instalado. Saltando subtítulos.\n")
        return src

    # Detectar orientación para ajustar estilo de subtítulos
    is_vertical, w, h = detect_orientation(src, log)

    audio_path = os.path.join(output_dir, "_audio.wav")
    run_cmd([ffmpeg, "-y", "-i", src, "-ac", "1", "-ar", "16000", audio_path], log)

    log("  🤖 Transcribiendo con Whisper...\n")
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="es", task="transcribe")

    # Corregir nombres y términos de fútbol en los segmentos
    log("  ✏️ Corrigiendo nombres y términos...\n")
    try:
        sys.path.insert(0, BASE_DIR)
        from agents.subtitle_corrector import correct_segments
        segments = correct_segments(result["segments"])
    except Exception as e:
        log(f"  ⚠️ Corrector no disponible: {e}\n")
        segments = result["segments"]

    import tempfile, shutil

    def ts(s):
        h2, r = divmod(int(s), 3600)
        m, sec = divmod(r, 60)
        ms = int((s - int(s)) * 1000)
        return f"{h2:02d}:{m:02d}:{sec:02d},{ms:03d}"

    srt_path = os.path.join(tempfile.gettempdir(), "subtitles_ft.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n{ts(seg['start'])} --> {ts(seg['end'])}\n{seg['text'].strip()}\n\n")

    shutil.copy(srt_path, os.path.join(output_dir, "subtitles.srt"))
    log(f"  ✅ SRT guardado\n")

    dst = os.path.join(output_dir, "04_with_subtitles.mp4")
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")

    if is_vertical:
        # Video vertical (Reels): fuente más grande, margen lateral amplio,
        # posición en el tercio inferior para no tapar la cara
        subtitle_style = (
            "FontName=Arial,FontSize=14,Bold=1,"
            "PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=3,"
            "Alignment=2,MarginL=40,MarginR=40,MarginV=120"
        )
    else:
        # Video horizontal (YouTube): tamaño estándar, parte inferior
        subtitle_style = (
            "FontName=Arial,FontSize=20,Bold=1,"
            "PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2,"
            "Alignment=2,MarginL=60,MarginR=60,MarginV=40"
        )

    cmd = [ffmpeg, "-y", "-i", src,
           "-vf", f"subtitles='{srt_escaped}':force_style='{subtitle_style}'",
           "-c:a", "copy", dst]
    rc = run_cmd(cmd, log)
    if rc != 0:
        log("⚠️  SRT guardado pero no se pudo incrustar. Usá el .srt en tu editor.\n")
        return src
    return dst


def step_export(src, output_dir, log):
    """5. Exporta adaptando según orientación del video."""
    log("\n📤 Paso 5: Exportando versiones finales...\n")
    ffmpeg = get_ffmpeg()

    is_vertical, w, h = detect_orientation(src, log)

    yt_out = os.path.join(output_dir, "FINAL_youtube.mp4")
    if is_vertical:
        # Video vertical → YouTube: agregar barras laterales negras para 16:9
        yt_vf = "scale=608:1080,pad=1920:1080:656:0:black"
    else:
        yt_vf = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

    cmd_yt = [ffmpeg, "-y", "-i", src,
              "-vf", yt_vf,
              "-c:v", "libx264", "-preset", "slow", "-crf", "16",
              "-c:a", "aac", "-b:a", "256k", yt_out]
    run_cmd(cmd_yt, log)

    reels_out = os.path.join(output_dir, "FINAL_reels.mp4")
    if is_vertical:
        # Ya es vertical: solo escalar a 1080x1920
        reels_vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    else:
        # Horizontal → crop central 9:16
        reels_vf = "crop=ih*9/16:ih,scale=1080:1920"

    cmd_reels = [ffmpeg, "-y", "-i", src,
                 "-vf", reels_vf,
                 "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                 "-c:a", "aac", "-b:a", "256k", reels_out]
    run_cmd(cmd_reels, log)

    log(f"\n✅ YouTube:  {yt_out}\n")
    log(f"✅ Reels:    {reels_out}\n")
    return yt_out, reels_out


# ── GUI ──────────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Football Terms Editor — MVP")
        self.geometry("820x740")
        self.resizable(True, True)

        self.clips_dir = tk.StringVar(value="")
        self.output_dir = tk.StringVar(value=os.path.join(BASE_DIR, "output"))
        self.skip_first = tk.IntVar(value=2)   # FIX 1: saltar clips 1 y 2 por defecto
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}

        ctk.CTkLabel(self, text="⚽ Football Terms Editor",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(**pad)

        # Carpeta de clips
        frame1 = ctk.CTkFrame(self)
        frame1.pack(fill="x", **pad)
        ctk.CTkLabel(frame1, text="Carpeta de clips:").pack(side="left", padx=8)
        ctk.CTkEntry(frame1, textvariable=self.clips_dir, width=400).pack(side="left", padx=4)
        ctk.CTkButton(frame1, text="Elegir", width=80,
                      command=self._pick_clips_dir).pack(side="left", padx=4)

        # Carpeta de salida
        frame2 = ctk.CTkFrame(self)
        frame2.pack(fill="x", **pad)
        ctk.CTkLabel(frame2, text="Carpeta de salida:").pack(side="left", padx=8)
        ctk.CTkEntry(frame2, textvariable=self.output_dir, width=400).pack(side="left", padx=4)
        ctk.CTkButton(frame2, text="Elegir", width=80,
                      command=self._pick_output_dir).pack(side="left", padx=4)

        # FIX 1: opción para saltar primeros N clips
        frame3 = ctk.CTkFrame(self)
        frame3.pack(fill="x", **pad)
        ctk.CTkLabel(frame3, text="Ignorar primeros clips (borradores):").pack(side="left", padx=8)
        ctk.CTkEntry(frame3, textvariable=self.skip_first, width=60).pack(side="left", padx=4)
        ctk.CTkLabel(frame3, text="(ej: 2 = empieza desde el clip 3)",
                     text_color="gray").pack(side="left", padx=4)

        # Info clips
        self.clips_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.clips_label.pack(**pad)

        # Botón principal
        self.run_btn = ctk.CTkButton(
            self, text="▶  Procesar videos", height=44,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start_pipeline)
        self.run_btn.pack(**pad)

        # Barra de progreso
        self.progress = ctk.CTkProgressBar(self, width=600)
        self.progress.set(0)
        self.progress.pack(**pad)

        # Log
        ctk.CTkLabel(self, text="Log:").pack(anchor="w", padx=16)
        self.log_box = scrolledtext.ScrolledText(
            self, height=18, bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 10), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _pick_clips_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.clips_dir.set(d)
            clips = self._get_clips(d)
            skip = self.skip_first.get()
            usable = clips[skip:]
            self.clips_label.configure(
                text=f"{len(clips)} clips encontrados — usando {len(usable)} (saltando primeros {skip})")

    def _pick_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir.set(d)

    def _get_clips(self, folder):
        import re
        exts = ("*.mp4", "*.mov", "*.avi", "*.mkv", "*.webm")
        clips = []
        for ext in exts:
            clips.extend(glob.glob(os.path.join(folder, ext)))
        def natural_key(s):
            parts = re.split(r'(\d+)', os.path.basename(s))
            return [int(p) if p.isdigit() else p.lower() for p in parts]
        return sorted(clips, key=natural_key)

    def _log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update_idletasks()

    def _start_pipeline(self):
        clips_dir = self.clips_dir.get()
        output_dir = self.output_dir.get()

        if not clips_dir:
            self._log("⚠️  Elegí una carpeta de clips primero.\n")
            return

        all_clips = self._get_clips(clips_dir)
        skip = self.skip_first.get()
        clips = all_clips[skip:]   # FIX 1: saltar borradores

        if not clips:
            self._log("⚠️  No quedaron clips después de saltear los borradores.\n")
            return

        os.makedirs(output_dir, exist_ok=True)
        self.run_btn.configure(state="disabled", text="Procesando...")
        self.progress.set(0)

        def pipeline():
            try:
                self._log(f"\n🚀 Iniciando pipeline con {len(clips)} clips (saltando primeros {skip})...\n")

                steps = [
                    (step_merge,         [clips, output_dir]),
                    (step_enhance_video, [None, output_dir]),
                    (step_enhance_audio, [None, output_dir]),
                    (step_subtitles,     [None, output_dir]),
                    (step_export,        [None, output_dir]),
                ]
                current = None
                total = len(steps)

                for i, (fn, args) in enumerate(steps):
                    if i > 0:
                        args[0] = current
                    result = fn(*args, self._log)
                    if isinstance(result, tuple):
                        current = result[0]
                    elif result:
                        current = result
                    self.progress.set((i + 1) / total)

                self._log("\n🎉 ¡Pipeline completado!\n")
                self._log(f"📁 Archivos en: {output_dir}\n")
            except Exception as e:
                import traceback
                self._log(f"\n❌ Error: {e}\n{traceback.format_exc()}\n")
            finally:
                self.run_btn.configure(state="normal", text="▶  Procesar videos")

        threading.Thread(target=pipeline, daemon=True).start()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
