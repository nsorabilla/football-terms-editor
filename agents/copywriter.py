"""
Agente 5 — Copywriter
Genera título SEO + descripción para YouTube basado en transcripción y tendencias.
"""

import json
import re
from datetime import datetime


# Templates SEO para fútbol argentino
TITLE_TEMPLATES = [
    "¿{TEMA}? Todo lo que necesitás saber 🔵⚪",
    "{TEMA}: La explicación definitiva | Football Terms",
    "Así funciona {TEMA} en el fútbol moderno",
    "{TEMA} | ¿Qué es y para qué sirve?",
    "El secreto de {TEMA} que nadie te explicó",
]

DESCRIPTION_TEMPLATE = """
{INTRO}

⚽ En este video te explico {TEMA} de forma clara y sencilla.

📌 Lo que vas a aprender:
{PUNTOS}

🔔 Suscribite para más contenido de fútbol argentino y mundial.
👍 Si te gustó, dale like y compartilo.

---
#fútbol #Argentina #FootballTerms #{TAG1} #{TAG2} #{TAG3}
""".strip()


def extract_topic(transcript: str, trend_data: dict) -> str:
    """Extrae el tema principal del video."""
    # Palabras más frecuentes en la transcripción (excluyendo stopwords)
    stopwords = {"que", "de", "la", "el", "en", "y", "a", "es", "se", "un", "una",
                 "los", "las", "con", "por", "para", "del", "al", "lo", "le", "más"}
    words = re.findall(r'\b[a-záéíóúñ]{4,}\b', transcript.lower())
    freq = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
    if top:
        return top[0][0].capitalize()
    return "fútbol argentino"


def generate_points(transcript: str) -> str:
    sentences = [s.strip() for s in transcript.split(".") if len(s.strip()) > 30]
    points = sentences[:4]
    return "\n".join(f"• {p}." for p in points) if points else "• Conceptos clave del fútbol moderno."


def run(transcript: str, trend_data: dict = None, temperature_data: dict = None) -> dict:
    if trend_data is None:
        trend_data = {}
    if temperature_data is None:
        temperature_data = {}

    topic = extract_topic(transcript, trend_data)

    # Trending players para tags
    player_ranking = temperature_data.get("player_ranking", [])
    top_players = [p[0] for p in player_ranking[:3]] if player_ranking else ["Messi", "Argentina", "Mundial"]
    tags = [p.replace(" ", "") for p in top_players]

    # Título — usar template más SEO
    import random
    title_template = random.choice(TITLE_TEMPLATES)
    title = title_template.replace("{TEMA}", topic)

    # Descripción
    intro_snippets = [r["snippet"] for r in trend_data.get("results", []) if r.get("snippet")]
    intro = intro_snippets[0][:150] + "..." if intro_snippets else f"Todo sobre {topic} en el fútbol actual."

    points = generate_points(transcript)

    description = DESCRIPTION_TEMPLATE.format(
        INTRO=intro,
        TEMA=topic,
        PUNTOS=points,
        TAG1=tags[0] if len(tags) > 0 else "Argentina",
        TAG2=tags[1] if len(tags) > 1 else "fútbol",
        TAG3=tags[2] if len(tags) > 2 else "Mundial2026",
    )

    # Variantes de título (A/B testing)
    alt_titles = []
    for tmpl in TITLE_TEMPLATES:
        alt = tmpl.replace("{TEMA}", topic)
        if alt != title:
            alt_titles.append(alt)

    return {
        "agent": "Copywriter",
        "timestamp": datetime.now().isoformat(),
        "topic_detected": topic,
        "title": title,
        "alt_titles": alt_titles[:2],
        "description": description,
        "tags": tags + ["fútbol", "Argentina", "FootballTerms", "Mundial2026"],
    }


if __name__ == "__main__":
    import sys
    transcript = sys.argv[1] if len(sys.argv) > 1 else "fútbol argentina jugadores partido"
    data = run(transcript)
    print(json.dumps(data, ensure_ascii=False, indent=2))
