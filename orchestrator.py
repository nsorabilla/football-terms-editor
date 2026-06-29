"""
Football Terms — Orquestador de Agentes
Soporta 1 video solo, o 2 videos que se unen antes de procesar.
"""

import os
import sys
import json
import threading
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, scrolledtext
from datetime import datetime
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

FFMPEG_PATH = r"C:\Users\nicolas.sorabilla\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def get_ffmpeg():
    import shutil
    if os.path.exists(FFMPEG_PATH):
        return FFMPEG_PATH
    return shutil.which("ffmpeg")


def merge_two_videos(video1: str, video2: str, out_dir: str, log) -> str:
    """Une dos videos re-encodando a formato uniforme."""
    ffmpeg = get_ffmpeg()
    if not ffmpeg:
        log("❌ ffmpeg no encontrado.\n")
        return video1

    log(f"  🔗 Uniendo:\n    1. {os.path.basename(video1)}\n    2. {os.path.basename(video2)}\n")
    tmp = tempfile.mkdtemp()

    # Normalizar ambos a 30fps / aac / h264
    clips_norm = []
    for i, clip in enumerate([video1, video2], 1):
        out = os.path.join(tmp, f"clip_{i}.mp4")
        cmd = [ffmpeg, "-y", "-i", clip,
               "-c:v", "libx264", "-preset", "fast", "-crf", "20",
               "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2",
               "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
               "-vsync", "cfr", out]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if os.path.exists(out):
            clips_norm.append(out)
            log(f"  ✅ Video {i} normalizado\n")
        else:
            log(f"  ❌ Error normalizando video {i}\n")

    if len(clips_norm) < 2:
        log("  ⚠️ Solo se normalizó un video, usando ese.\n")
        return clips_norm[0] if clips_norm else video1

    list_file = os.path.join(tmp, "list.txt")
    with open(list_file, "w") as f:
        for p in clips_norm:
            f.write(f"file '{p}'\n")

    merged = os.path.join(out_dir, "00_merged_input.mp4")
    cmd2 = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", list_file, "-c", "copy", merged]
    subprocess.run(cmd2, capture_output=True, timeout=300)
    log(f"  ✅ Videos unidos → {os.path.basename(merged)}\n")
    return merged


def transcribe_video(video_path: str, log) -> str:
    log("  🎙️ Transcribiendo video con Whisper...\n")
    try:
        ffmpeg = get_ffmpeg()
        if ffmpeg:
            os.environ["PATH"] = os.path.dirname(ffmpeg) + os.pathsep + os.environ.get("PATH", "")
        import whisper
        tmp = tempfile.mktemp(suffix=".wav")
        subprocess.run([ffmpeg, "-y", "-i", video_path,
                        "-t", "120", "-ac", "1", "-ar", "16000", tmp],
                       capture_output=True, timeout=60)
        model = whisper.load_model("tiny")
        result = model.transcribe(tmp, language="es")
        return result.get("text", "")
    except Exception as e:
        log(f"  ⚠️ Error en transcripción: {e}\n")
        return ""


class OrchestratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚽ Football Terms — Pipeline de Agentes")
        self.geometry("920x820")
        self.resizable(True, True)

        self.video1_path = tk.StringVar()
        self.video2_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.path.join(BASE_DIR, "output"))
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 5}

        ctk.CTkLabel(self, text="⚽ Football Terms — Pipeline de Agentes",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(**pad)
        ctk.CTkLabel(self, text="Subí 1 o 2 videos — los 6 agentes hacen todo el trabajo",
                     text_color="gray").pack(pady=(0, 6))

        # ── Video 1 (obligatorio) ─────────────────────────────────────────────
        box1 = ctk.CTkFrame(self, border_width=1)
        box1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(box1, text="🎬 Video 1  (obligatorio)",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
        row1 = ctk.CTkFrame(box1, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkEntry(row1, textvariable=self.video1_path, width=620).pack(side="left", padx=4)
        ctk.CTkButton(row1, text="Elegir", width=80,
                      command=self._pick_video1).pack(side="left", padx=4)
        ctk.CTkButton(row1, text="✕", width=36, fg_color="#555",
                      command=lambda: self.video1_path.set("")).pack(side="left")

        # ── Video 2 (opcional) ───────────────────────────────────────────────
        box2 = ctk.CTkFrame(self, border_width=1)
        box2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(box2, text="🎬 Video 2  (opcional — se une al Video 1)",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
        row2 = ctk.CTkFrame(box2, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkEntry(row2, textvariable=self.video2_path, width=620).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Elegir", width=80,
                      command=self._pick_video2).pack(side="left", padx=4)
        ctk.CTkButton(row2, text="✕", width=36, fg_color="#555",
                      command=lambda: self.video2_path.set("")).pack(side="left")

        # ── Carpeta de salida ────────────────────────────────────────────────
        f_out = ctk.CTkFrame(self)
        f_out.pack(fill="x", **pad)
        ctk.CTkLabel(f_out, text="📁 Salida:").pack(side="left", padx=8)
        ctk.CTkEntry(f_out, textvariable=self.output_dir, width=580).pack(side="left", padx=4)
        ctk.CTkButton(f_out, text="Elegir", width=80,
                      command=self._pick_output).pack(side="left", padx=4)

        # ── Estado de agentes ────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Estado de agentes:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(8, 2))

        agents_frame = ctk.CTkFrame(self)
        agents_frame.pack(fill="x", padx=16, pady=4)

        self.agent_labels = {}
        agents = [
            ("merge",       "0. Unión de videos"),
            ("trend",       "1. Analista de tendencias"),
            ("temperature", "2. Analista de temperatura"),
            ("video_check", "3. Analista de video (filtro)"),
            ("editor",      "4. Editor de videos"),
            ("copy",        "5. Copywriter"),
            ("thumbnail",   "6. Diseñador de miniatura"),
        ]
        # 2 columnas
        cols_frame = ctk.CTkFrame(agents_frame, fg_color="transparent")
        cols_frame.pack(fill="x", padx=8, pady=4)
        left_col = ctk.CTkFrame(cols_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)
        right_col = ctk.CTkFrame(cols_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True)

        for idx, (key, name) in enumerate(agents):
            col = left_col if idx < 4 else right_col
            lbl = ctk.CTkLabel(col, text=f"⬜ {name}", anchor="w")
            lbl.pack(anchor="w", padx=8, pady=2)
            self.agent_labels[key] = lbl

        # ── Botón ────────────────────────────────────────────────────────────
        self.run_btn = ctk.CTkButton(
            self, text="▶  Iniciar pipeline completo", height=44,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start)
        self.run_btn.pack(pady=8)

        self.progress = ctk.CTkProgressBar(self, width=750)
        self.progress.set(0)
        self.progress.pack(pady=4)

        # ── Log ──────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Log:", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=16)
        self.log_box = scrolledtext.ScrolledText(
            self, height=10, bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 9), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def _pick_video1(self):
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv")])
        if f:
            self.video1_path.set(f)

    def _pick_video2(self):
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv")])
        if f:
            self.video2_path.set(f)

    def _pick_output(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir.set(d)

    def _set_agent(self, key, status):
        icons = {"waiting": "⬜", "running": "🔄", "ok": "✅", "warn": "⚠️", "error": "❌", "skip": "⏭️"}
        names = {
            "merge":       "0. Unión de videos",
            "trend":       "1. Analista de tendencias",
            "temperature": "2. Analista de temperatura",
            "video_check": "3. Analista de video (filtro)",
            "editor":      "4. Editor de videos",
            "copy":        "5. Copywriter",
            "thumbnail":   "6. Diseñador de miniatura",
        }
        self.agent_labels[key].configure(text=f"{icons.get(status,'⬜')} {names[key]}")

    def _log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update_idletasks()

    def _start(self):
        v1 = self.video1_path.get()
        if not v1 or not os.path.exists(v1):
            self._log("⚠️  Elegí al menos el Video 1.\n")
            return
        v2 = self.video2_path.get()
        if v2 and not os.path.exists(v2):
            self._log("⚠️  El Video 2 seleccionado no existe. Limpialo o elegí otro.\n")
            return

        self.run_btn.configure(state="disabled", text="Procesando...")
        self.progress.set(0)
        for key in self.agent_labels:
            self._set_agent(key, "waiting")
        threading.Thread(target=self._pipeline, daemon=True).start()

    def _pipeline(self):
        v1 = self.video1_path.get()
        v2 = self.video2_path.get().strip()
        out_dir = self.output_dir.get()
        os.makedirs(out_dir, exist_ok=True)
        report = {"timestamp": datetime.now().isoformat()}
        total = 7

        def safe_run(agent_key, fn, *args, fallback=None):
            """Corre un paso del pipeline. Si falla, loguea y continúa."""
            try:
                return fn(*args)
            except Exception as e:
                import traceback
                self._log(f"  ⚠️ Error en {agent_key}: {e}\n")
                self._set_agent(agent_key, "warn")
                return fallback

        try:
            # ── Paso 0: Unir videos (si hay 2) ──────────────────────────────
            if v2:
                self._set_agent("merge", "running")
                self._log("\n🔗 Uniendo Video 1 + Video 2...\n")
                merged = safe_run("merge", merge_two_videos, v1, v2, out_dir, self._log, fallback=v1)
                video = merged if merged and os.path.exists(merged) else v1
                report["videos"] = [v1, v2]
                self._set_agent("merge", "ok")
            else:
                video = v1
                report["videos"] = [v1]
                self._set_agent("merge", "skip")
                self._log("\n▶ Un solo video — saltando unión.\n")
            self.progress.set(1 / total)

            # ── Agente 1: Tendencias ─────────────────────────────────────────
            self._set_agent("trend", "running")
            self._log("\n🔍 Agente 1: Buscando tendencias de fútbol...\n")
            from agents.trend_analyst import run as trend_run
            trend_data = safe_run("trend", trend_run, fallback={"results": []})
            report["tendencias"] = trend_data
            self._log(f"  ✅ {len(trend_data.get('results', []))} resultados\n")
            self._set_agent("trend", "ok")
            self.progress.set(2 / total)

            # ── Agente 2: Temperatura ────────────────────────────────────────
            self._set_agent("temperature", "running")
            self._log("\n🌡️ Agente 2: Analizando temperatura de redes...\n")
            from agents.temperature_analyst import run as temp_run
            temp_data = safe_run("temperature", temp_run, fallback={"player_ranking": [], "results": []})
            report["temperatura"] = temp_data
            ranking = temp_data.get("player_ranking", [])
            if ranking:
                self._log(f"  ✅ Top: {', '.join(p[0] for p in ranking[:3])}\n")
            self._set_agent("temperature", "ok")
            self.progress.set(3 / total)

            # ── Agente 3: Análisis de video ──────────────────────────────────
            self._set_agent("video_check", "running")
            self._log("\n🔬 Agente 3: Analizando calidad del video...\n")
            from agents.video_analyst import run as video_run
            video_report = safe_run("video_check", video_run, video,
                                    fallback={"approved": True, "blockers": [], "warnings": []})
            report["analisis_video"] = video_report

            if video_report.get("approved", True):
                warnings = video_report.get("warnings", [])
                self._log("  ✅ Video aprobado\n")
                for w in warnings:
                    self._log(f"  ⚠️ {w}\n")
                self._set_agent("video_check", "ok" if not warnings else "warn")
            else:
                self._set_agent("video_check", "error")
                self._log("  ❌ Video RECHAZADO — problemas bloqueantes:\n")
                for b in video_report.get("blockers", []):
                    self._log(f"     • {b}\n")
                self._log("\n🛑 Pipeline detenido. Corregí el video y volvé a intentar.\n")
                return
            self.progress.set(4 / total)

            # Transcripción compartida
            transcript = transcribe_video(video, self._log)
            report["transcript"] = transcript

            # ── Agente 4: Editor de videos ───────────────────────────────────
            self._set_agent("editor", "running")
            self._log("\n🎬 Agente 4: Editando video...\n")
            from app import step_enhance_video, step_enhance_audio, step_subtitles, step_export
            src = video
            src = safe_run("editor", step_enhance_video, src, out_dir, self._log, fallback=src) or src
            src = safe_run("editor", step_enhance_audio, src, out_dir, self._log, fallback=src) or src
            src = safe_run("editor", step_subtitles,     src, out_dir, self._log, fallback=src) or src
            export_result = safe_run("editor", step_export, src, out_dir, self._log,
                                     fallback=(src, src))
            yt_out, reels_out = export_result if isinstance(export_result, tuple) else (src, src)
            report["editor"] = {"youtube": yt_out, "reels": reels_out}
            self._set_agent("editor", "ok")
            self.progress.set(5 / total)

            # ── Agente 5: Copywriter ─────────────────────────────────────────
            self._set_agent("copy", "running")
            self._log("\n✍️ Agente 5: Generando título y descripción...\n")
            from agents.copywriter import run as copy_run
            copy_data = safe_run("copy", copy_run, transcript, trend_data, temp_data,
                                 fallback={"title": "Video Football Terms", "alt_titles": [],
                                           "description": "", "tags": [], "topic_detected": "fútbol"})
            report["copy"] = copy_data
            self._log(f"  ✅ Título: {copy_data['title']}\n")
            self._set_agent("copy", "ok")
            self.progress.set(6 / total)

            # ── Agente 6: Miniatura ──────────────────────────────────────────
            self._set_agent("thumbnail", "running")
            self._log("\n🎨 Agente 6: Generando brief de miniatura...\n")
            from agents.thumbnail_brief import run as thumb_run
            thumb_data = safe_run("thumbnail", thumb_run,
                                  copy_data["topic_detected"], copy_data["title"],
                                  transcript, trend_data,
                                  fallback={"paleta": "neutro", "prompt_para_ia": {}, "guideline_canva": {}})
            report["miniatura"] = thumb_data
            self._log(f"  ✅ Brief generado\n")
            self._set_agent("thumbnail", "ok")
            self.progress.set(7 / total)

            # ── Resumen final ────────────────────────────────────────────────
            self._save_summary(out_dir, report, copy_data, thumb_data, temp_data,
                               yt_out, reels_out, v1, v2)

        except Exception as e:
            import traceback
            self._log(f"\n❌ Error inesperado: {e}\n{traceback.format_exc()}\n")
        finally:
            self.run_btn.configure(state="normal", text="▶  Iniciar pipeline completo")

    def _save_summary(self, out_dir, report, copy_data, thumb_data, temp_data,
                      yt_out, reels_out, v1, v2):
        report_path = os.path.join(out_dir, "reporte_agentes.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        summary_path = os.path.join(out_dir, "RESUMEN_FINAL.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("FOOTBALL TERMS — RESUMEN DEL PIPELINE\n")
            f.write(f"Video 1: {v1}\n")
            if v2:
                f.write(f"Video 2: {v2}\n")
            f.write(f"Fecha: {report['timestamp']}\n")
            f.write("=" * 60 + "\n\n")

            f.write("📌 TÍTULO PARA YOUTUBE\n")
            f.write(f"{copy_data['title']}\n\n")
            f.write("📌 TÍTULOS ALTERNATIVOS\n")
            for t in copy_data.get("alt_titles", []):
                f.write(f"  • {t}\n")
            f.write("\n")

            f.write("📝 DESCRIPCIÓN\n")
            f.write(copy_data["description"] + "\n\n")

            f.write("🔖 TAGS\n")
            f.write(", ".join(copy_data.get("tags", [])) + "\n\n")

            f.write("🎨 PROMPT PARA IA (fondo de miniatura)\n")
            prompts = thumb_data.get("prompt_para_ia", {})
            f.write(f"  Midjourney: {prompts.get('midjourney', '')}\n")
            f.write(f"  DALL-E:     {prompts.get('dalle', '')}\n")
            f.write(f"  Canva AI:   {prompts.get('canva_ai', '')}\n\n")

            f.write("📋 GUIDELINE CANVA — PASO A PASO\n")
            guide = thumb_data.get("guideline_canva", {})
            f.write(f"  Tamaño: {guide.get('tamanio_canvas', '1280x720px')}\n\n")
            for paso in guide.get("pasos", []):
                f.write(f"\n  {paso.get('paso', '')}\n")
                for k, v in paso.items():
                    if k != "paso":
                        f.write(f"    {k}: {v}\n")

            f.write("\n✅ CHECKLIST MINIATURA\n")
            for item in guide.get("checklist", []):
                f.write(f"  ☐ {item}\n")

            f.write("\n🌡️ TOP JUGADORES EN TENDENCIA\n")
            for p, c in temp_data.get("player_ranking", [])[:5]:
                f.write(f"  {p}: {c} menciones\n")

            f.write("\n📁 ARCHIVOS GENERADOS\n")
            f.write(f"  YouTube: {yt_out}\n")
            f.write(f"  Reels:   {reels_out}\n")
            f.write(f"  SRT:     {os.path.join(out_dir, 'subtitles.srt')}\n")

        self._log(f"\n🎉 ¡Pipeline completo!\n")
        self._log(f"📄 Abriendo resumen...\n")
        os.startfile(summary_path)


if __name__ == "__main__":
    app = OrchestratorApp()
    app.mainloop()
