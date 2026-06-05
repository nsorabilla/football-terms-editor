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
    """Devuelve el path a ffmpeg."""
    import shutil
    # 1. PATH del sistema
    path = shutil.which("ffmpeg")
    if path:
        return path
    # 2. Path conocido de winget
    if os.path.exists(FFMPEG_PATH):
        return FFMPEG_PATH
    # 3. Carpeta local del proyecto
    local = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.exists(local):
        return local
    return None


def run_cmd(cmd, log_fn):
    """Corre un comando y loguea stdout/stderr en tiempo real."""
    log_fn(f"▶ {' '.join(cmd)}\n")
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
    """1. Une todos los clips en un solo video."""
    log("\n📎 Paso 1: Uniendo clips...\n")
    ffmpeg = get_ffmpeg()
    if not ffmpeg:
        log("❌ ffmpeg no encontrado. Instalalo desde https://ffmpeg.org\n")
        return None

    list_file = os.path.join(output_dir, "_clip_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

    merged = os.path.join(output_dir, "01_merged.mp4")
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
           "-i", list_file, "-c", "copy", merged]
    rc = run_cmd(cmd, log)
    if rc != 0:
        # fallback: re-encode
        cmd2 = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
                "-i", list_file, "-c:v", "libx264", "-c:a", "aac", merged]
        run_cmd(cmd2, log)
    return merged


def step_enhance_video(src, output_dir, log):
    """2. Mejora imagen: brillo/contraste/saturación."""
    log("\n🎨 Paso 2: Mejorando imagen...\n")
    ffmpeg = get_ffmpeg()
    dst = os.path.join(output_dir, "02_video_enhanced.mp4")
    # eq: contraste+10%, brillo+3%, saturación+20%
    vf = "eq=contrast=1.1:brightness=0.03:saturation=1.2,unsharp=5:5:0.8:3:3:0"
    cmd = [ffmpeg, "-y", "-i", src,
           "-vf", vf,
           "-c:v", "libx264", "-preset", "fast", "-crf", "18",
           "-c:a", "copy", dst]
    run_cmd(cmd, log)
    return dst


def step_enhance_audio(src, output_dir, log):
    """3. Mejora audio: normalización, reducción de ruido, corte de silencios."""
    log("\n🔊 Paso 3: Mejorando audio...\n")
    ffmpeg = get_ffmpeg()
    dst = os.path.join(output_dir, "03_audio_enhanced.mp4")
    # loudnorm (EBU R128) + highpass 80Hz + silenceremove
    af = (
        "highpass=f=80,"
        "loudnorm=I=-16:TP=-1.5:LRA=11,"
        "silenceremove=start_periods=1:start_duration=0.3:start_threshold=-50dB"
        ":stop_periods=-1:stop_duration=0.3:stop_threshold=-50dB"
    )
    cmd = [ffmpeg, "-y", "-i", src,
           "-af", af,
           "-c:v", "copy", dst]
    run_cmd(cmd, log)
    return dst


def step_subtitles(src, output_dir, log):
    """4. Genera subtítulos con Whisper y los incrusta."""
    log("\n📝 Paso 4: Generando subtítulos (Whisper)...\n")

    # Agregar ffmpeg al PATH para que Whisper lo encuentre
    ffmpeg = get_ffmpeg()
    if ffmpeg:
        ffmpeg_dir = os.path.dirname(ffmpeg)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

    try:
        import whisper
    except ImportError:
        log("⚠️  Whisper no instalado. Saltando subtítulos.\n")
        return src

    # Extraer audio para Whisper
    audio_path = os.path.join(output_dir, "_audio.wav")
    run_cmd([ffmpeg, "-y", "-i", src, "-ac", "1", "-ar", "16000", audio_path], log)

    log("  🤖 Transcribiendo con Whisper (puede tardar)...\n")
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="es", task="transcribe")

    # Guardar SRT en carpeta TEMP para evitar paths con caracteres especiales
    import tempfile
    srt_path = os.path.join(tempfile.gettempdir(), "subtitles_ft.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], 1):
            def ts(s):
                h, r = divmod(int(s), 3600)
                m, sec = divmod(r, 60)
                ms = int((s - int(s)) * 1000)
                return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
            f.write(f"{i}\n{ts(seg['start'])} --> {ts(seg['end'])}\n{seg['text'].strip()}\n\n")

    # Copiar SRT también a la carpeta de salida para referencia
    import shutil
    shutil.copy(srt_path, os.path.join(output_dir, "subtitles.srt"))
    log(f"  ✅ SRT guardado en {output_dir}\\subtitles.srt\n")

    # Incrustar subtítulos (usar path TEMP sin caracteres especiales)
    dst = os.path.join(output_dir, "04_with_subtitles.mp4")
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    cmd = [ffmpeg, "-y", "-i", src,
           "-vf", f"subtitles='{srt_escaped}':force_style='FontName=Arial,FontSize=18,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2'",
           "-c:a", "copy", dst]
    rc = run_cmd(cmd, log)
    if rc != 0:
        log("⚠️  No se pudieron incrustar subtítulos en el video. El SRT está guardado por separado.\n")
        return src
    return dst


def step_export(src, output_dir, log):
    """5. Exporta versión YouTube (16:9) y Reels (9:16)."""
    log("\n📤 Paso 5: Exportando versiones finales...\n")
    ffmpeg = get_ffmpeg()

    # YouTube — mantiene el aspect ratio original, asegura 1080p max
    yt_out = os.path.join(output_dir, "FINAL_youtube.mp4")
    cmd_yt = [ffmpeg, "-y", "-i", src,
              "-vf", "scale=-2:1080",
              "-c:v", "libx264", "-preset", "slow", "-crf", "18",
              "-c:a", "aac", "-b:a", "192k", yt_out]
    run_cmd(cmd_yt, log)

    # Reels — crop central 9:16
    reels_out = os.path.join(output_dir, "FINAL_reels.mp4")
    cmd_reels = [ffmpeg, "-y", "-i", src,
                 "-vf", "crop=ih*9/16:ih,scale=1080:1920",
                 "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                 "-c:a", "aac", "-b:a", "192k", reels_out]
    run_cmd(cmd_reels, log)

    log(f"\n✅ YouTube:  {yt_out}\n")
    log(f"✅ Reels:    {reels_out}\n")
    return yt_out, reels_out


# ── GUI ──────────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Football Terms Editor — MVP")
        self.geometry("800x700")
        self.resizable(True, True)

        self.clips_dir = tk.StringVar(value="")
        self.output_dir = tk.StringVar(
            value=os.path.join(BASE_DIR, "output"))
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}

        # Título
        ctk.CTkLabel(self, text="⚽ Football Terms Editor",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(**pad)

        # Carpeta de clips
        frame1 = ctk.CTkFrame(self)
        frame1.pack(fill="x", **pad)
        ctk.CTkLabel(frame1, text="Carpeta de clips:").pack(side="left", padx=8)
        ctk.CTkEntry(frame1, textvariable=self.clips_dir, width=420).pack(
            side="left", padx=4)
        ctk.CTkButton(frame1, text="Elegir", width=80,
                      command=self._pick_clips_dir).pack(side="left", padx=4)

        # Carpeta de salida
        frame2 = ctk.CTkFrame(self)
        frame2.pack(fill="x", **pad)
        ctk.CTkLabel(frame2, text="Carpeta de salida:").pack(side="left", padx=8)
        ctk.CTkEntry(frame2, textvariable=self.output_dir, width=420).pack(
            side="left", padx=4)
        ctk.CTkButton(frame2, text="Elegir", width=80,
                      command=self._pick_output_dir).pack(side="left", padx=4)

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
            self.clips_label.configure(
                text=f"{len(clips)} clips encontrados en orden cronológico")

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
        # Orden natural: 1, 2, 3... 13 (no alfabético)
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

        clips = self._get_clips(clips_dir)
        if not clips:
            self._log("⚠️  No se encontraron videos en esa carpeta.\n")
            return

        os.makedirs(output_dir, exist_ok=True)
        self.run_btn.configure(state="disabled", text="Procesando...")
        self.progress.set(0)

        def pipeline():
            try:
                self._log(f"\n🚀 Iniciando pipeline con {len(clips)} clips...\n")
                self._log("Clips encontrados:\n")
                for c in clips:
                    self._log(f"  • {os.path.basename(c)}\n")

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
                self._log(f"\n❌ Error: {e}\n")
            finally:
                self.run_btn.configure(state="normal", text="▶  Procesar videos")

        threading.Thread(target=pipeline, daemon=True).start()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
