"""
Football Terms — Orquestador de Agentes
Corre los 6 agentes en secuencia y genera un reporte final.
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

# Agregar carpeta raíz al path
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


def transcribe_video(video_path: str, log) -> str:
    log("  🎙️ Transcribiendo video con Whisper...\n")
    try:
        ffmpeg = get_ffmpeg()
        if ffmpeg:
            os.environ["PATH"] = os.path.dirname(ffmpeg) + os.pathsep + os.environ.get("PATH", "")
        import whisper
        tmp = tempfile.mktemp(suffix=".wav")
        subprocess.run([
            ffmpeg, "-y", "-i", video_path,
            "-t", "120", "-ac", "1", "-ar", "16000", tmp
        ], capture_output=True, timeout=60)
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
        self.geometry("900x780")
        self.resizable(True, True)

        self.video_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.path.join(BASE_DIR, "output"))
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        ctk.CTkLabel(self, text="⚽ Football Terms — Pipeline de Agentes",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(**pad)
        ctk.CTkLabel(self, text="Subí tu video y los 6 agentes hacen todo el trabajo",
                     text_color="gray").pack(pady=(0, 8))

        # Video input
        f1 = ctk.CTkFrame(self)
        f1.pack(fill="x", **pad)
        ctk.CTkLabel(f1, text="Video:").pack(side="left", padx=8)
        ctk.CTkEntry(f1, textvariable=self.video_path, width=500).pack(side="left", padx=4)
        ctk.CTkButton(f1, text="Elegir", width=80,
                      command=self._pick_video).pack(side="left", padx=4)

        # Output dir
        f2 = ctk.CTkFrame(self)
        f2.pack(fill="x", **pad)
        ctk.CTkLabel(f2, text="Salida: ").pack(side="left", padx=8)
        ctk.CTkEntry(f2, textvariable=self.output_dir, width=500).pack(side="left", padx=4)
        ctk.CTkButton(f2, text="Elegir", width=80,
                      command=self._pick_output).pack(side="left", padx=4)

        # Estado de agentes
        ctk.CTkLabel(self, text="Estado de agentes:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(8, 2))

        agents_frame = ctk.CTkFrame(self)
        agents_frame.pack(fill="x", padx=16, pady=4)

        self.agent_labels = {}
        agents = [
            ("trend",       "1. Analista de tendencias"),
            ("temperature", "2. Analista de temperatura"),
            ("video_check", "3. Analista de video (filtro)"),
            ("editor",      "4. Editor de videos"),
            ("copy",        "5. Copywriter"),
            ("thumbnail",   "6. Diseñador de miniatura"),
        ]
        for key, name in agents:
            row = ctk.CTkFrame(agents_frame)
            row.pack(fill="x", padx=8, pady=2)
            lbl = ctk.CTkLabel(row, text=f"⬜ {name}", anchor="w", width=350)
            lbl.pack(side="left", padx=8)
            self.agent_labels[key] = lbl

        # Botón
        self.run_btn = ctk.CTkButton(
            self, text="▶  Iniciar pipeline completo", height=44,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start)
        self.run_btn.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self, width=700)
        self.progress.set(0)
        self.progress.pack(pady=4)

        # Log
        ctk.CTkLabel(self, text="Log:", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=16)
        self.log_box = scrolledtext.ScrolledText(
            self, height=12, bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 9), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _pick_video(self):
        f = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv")])
        if f:
            self.video_path.set(f)

    def _pick_output(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir.set(d)

    def _set_agent(self, key, status):
        icons = {"waiting": "⬜", "running": "🔄", "ok": "✅", "warn": "⚠️", "error": "❌"}
        names = {
            "trend":       "1. Analista de tendencias",
            "temperature": "2. Analista de temperatura",
            "video_check": "3. Analista de video (filtro)",
            "editor":      "4. Editor de videos",
            "copy":        "5. Copywriter",
            "thumbnail":   "6. Diseñador de miniatura",
        }
        icon = icons.get(status, "⬜")
        self.agent_labels[key].configure(text=f"{icon} {names[key]}")

    def _log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update_idletasks()

    def _start(self):
        video = self.video_path.get()
        if not video or not os.path.exists(video):
            self._log("⚠️  Elegí un video primero.\n")
            return
        self.run_btn.configure(state="disabled", text="Procesando...")
        self.progress.set(0)
        for key in self.agent_labels:
            self._set_agent(key, "waiting")
        threading.Thread(target=self._pipeline, daemon=True).start()

    def _pipeline(self):
        video = self.video_path.get()
        out_dir = self.output_dir.get()
        os.makedirs(out_dir, exist_ok=True)
        report = {"video": video, "timestamp": datetime.now().isoformat()}
        total = 6

        try:
            # ── Agente 1: Tendencias ─────────────────────────────────────────
            self._set_agent("trend", "running")
            self._log("\n🔍 Agente 1: Buscando tendencias de fútbol...\n")
            from agents.trend_analyst import run as trend_run
            trend_data = trend_run()
            report["tendencias"] = trend_data
            self._log(f"  ✅ {len(trend_data.get('results', []))} resultados encontrados\n")
            self._set_agent("trend", "ok")
            self.progress.set(1 / total)

            # ── Agente 2: Temperatura ────────────────────────────────────────
            self._set_agent("temperature", "running")
            self._log("\n🌡️ Agente 2: Analizando temperatura de redes...\n")
            from agents.temperature_analyst import run as temp_run
            temp_data = temp_run()
            report["temperatura"] = temp_data
            ranking = temp_data.get("player_ranking", [])
            if ranking:
                top = ", ".join(f"{p[0]} ({p[1]})" for p in ranking[:3])
                self._log(f"  ✅ Top jugadores: {top}\n")
            self._set_agent("temperature", "ok")
            self.progress.set(2 / total)

            # ── Agente 3: Análisis de video ──────────────────────────────────
            self._set_agent("video_check", "running")
            self._log("\n🔬 Agente 3: Analizando calidad del video...\n")
            from agents.video_analyst import run as video_run
            video_report = video_run(video)
            report["analisis_video"] = video_report
            if video_report["approved"]:
                self._log("  ✅ Video aprobado — calidad OK\n")
                self._set_agent("video_check", "ok")
            else:
                issues = "; ".join(video_report["issues"])
                self._log(f"  ⚠️ Video con advertencias: {issues}\n")
                self._set_agent("video_check", "warn")
            self.progress.set(3 / total)

            # Transcripción compartida (usada por agente 5)
            transcript = transcribe_video(video, self._log)
            report["transcript"] = transcript

            # ── Agente 4: Editor de videos ───────────────────────────────────
            self._set_agent("editor", "running")
            self._log("\n🎬 Agente 4: Editando video...\n")
            editor_script = os.path.join(BASE_DIR, "app.py")
            # Llamar al pipeline de edición directamente
            from app import step_merge, step_enhance_video, step_enhance_audio, step_subtitles, step_export
            import glob, re

            def natural_key(s):
                parts = re.split(r'(\d+)', os.path.basename(s))
                return [int(p) if p.isdigit() else p.lower() for p in parts]

            # Si el video ya es el merged final, usarlo directamente
            src = video
            src = step_enhance_video(src, out_dir, self._log) or src
            src = step_enhance_audio(src, out_dir, self._log) or src
            src = step_subtitles(src, out_dir, self._log) or src
            yt_out, reels_out = step_export(src, out_dir, self._log)
            report["editor"] = {"youtube": yt_out, "reels": reels_out}
            self._set_agent("editor", "ok")
            self.progress.set(4 / total)

            # ── Agente 5: Copywriter ─────────────────────────────────────────
            self._set_agent("copy", "running")
            self._log("\n✍️ Agente 5: Generando título y descripción...\n")
            from agents.copywriter import run as copy_run
            copy_data = copy_run(transcript, trend_data, temp_data)
            report["copy"] = copy_data
            self._log(f"  ✅ Título: {copy_data['title']}\n")
            self._set_agent("copy", "ok")
            self.progress.set(5 / total)

            # ── Agente 6: Miniatura ──────────────────────────────────────────
            self._set_agent("thumbnail", "running")
            self._log("\n🎨 Agente 6: Generando brief de miniatura para Canva...\n")
            from agents.thumbnail_brief import run as thumb_run
            thumb_data = thumb_run(
                copy_data["topic_detected"],
                copy_data["title"],
                transcript,
                trend_data
            )
            report["miniatura"] = thumb_data
            self._log(f"  ✅ Brief generado — paleta: {thumb_data['palette']}\n")
            self._set_agent("thumbnail", "ok")
            self.progress.set(6 / total)

            # ── Guardar reporte ──────────────────────────────────────────────
            report_path = os.path.join(out_dir, "reporte_agentes.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            # ── Guardar resumen legible ──────────────────────────────────────
            summary_path = os.path.join(out_dir, "RESUMEN_FINAL.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("FOOTBALL TERMS — RESUMEN DEL PIPELINE\n")
                f.write(f"Video: {video}\n")
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

                f.write("🎨 BRIEF MINIATURA (CANVA)\n")
                instrucciones = thumb_data.get("instrucciones_canva", {})
                for paso, detalle in instrucciones.items():
                    f.write(f"\n  {paso.replace('_', ' ').upper()}:\n")
                    if isinstance(detalle, dict):
                        for k, v in detalle.items():
                            f.write(f"    {k}: {v}\n")
                    else:
                        f.write(f"    {detalle}\n")

                f.write("\n✅ CHECKLIST MINIATURA\n")
                for item in thumb_data.get("checklist_final", []):
                    f.write(f"  ☐ {item}\n")

                f.write("\n🌡️ TOP JUGADORES EN TENDENCIA\n")
                for p, c in temp_data.get("player_ranking", [])[:5]:
                    f.write(f"  {p}: {c} menciones\n")

                f.write("\n📁 ARCHIVOS GENERADOS\n")
                f.write(f"  YouTube: {yt_out}\n")
                f.write(f"  Reels:   {reels_out}\n")
                f.write(f"  SRT:     {os.path.join(out_dir, 'subtitles.srt')}\n")

            self._log(f"\n🎉 ¡Pipeline completo!\n")
            self._log(f"📄 Resumen en: {summary_path}\n")
            self._log(f"📁 Videos en: {out_dir}\n")

            # Abrir resumen automáticamente
            os.startfile(summary_path)

        except Exception as e:
            import traceback
            self._log(f"\n❌ Error: {e}\n{traceback.format_exc()}\n")
        finally:
            self.run_btn.configure(state="normal", text="▶  Iniciar pipeline completo")


if __name__ == "__main__":
    app = OrchestratorApp()
    app.mainloop()
