"""
Agente 5 — Copywriter
Genera título SEO + descripción para YouTube basado en la transcripción real
del video y las tendencias actuales. Todo coherente con el contenido.
"""

import re
import json
from datetime import datetime


# Hashtags base del canal
CHANNEL_HASHTAGS = ["#FootballTerms", "#FútbolArgentino", "#Argentina"]

# Términos de fútbol para detectar subtemas
SUBTOPICS = {
    "táctica": ["pressing", "contraataque", "táctica", "sistema", "formación", "4-3-3", "4-4-2"],
    "jugador": ["messi", "de paul", "lautaro", "álvarez", "scaloni", "dybala", "mac allister"],
    "competición": ["mundial", "copa", "champions", "liga", "torneo", "clasificación"],
    "técnica": ["pase", "remate", "dribble", "regate", "control", "caño", "tiro"],
    "regla": ["offside", "penal", "córner", "falta", "tarjeta", "var", "fuera de juego"],
    "historia": ["historia", "récord", "campeón", "título", "copa", "1978", "1986", "2022"],
}


def extract_main_topic(transcript: str) -> str:
    """Extrae el tema principal real del video desde la transcripción."""
    if not transcript or transcript.startswith("[Error"):
        return "fútbol argentino"

    transcript_lower = transcript.lower()

    # Detectar subtema dominante
    topic_scores = {}
    for topic, keywords in SUBTOPICS.items():
        score = sum(transcript_lower.count(kw) for kw in keywords)
        if score > 0:
            topic_scores[topic] = score

    dominant = max(topic_scores, key=topic_scores.get) if topic_scores else "fútbol"

    # Extraer palabra/frase más repetida (excluyendo stopwords)
    stopwords = {
        "que", "de", "la", "el", "en", "y", "a", "es", "se", "un", "una",
        "los", "las", "con", "por", "para", "del", "al", "lo", "le", "más",
        "muy", "pero", "si", "me", "te", "nos", "hay", "cuando", "como",
        "este", "esta", "esto", "bueno", "eh", "también", "porque", "así",
        "entonces", "ahora", "aquí", "donde", "todo", "cada", "bien",
    }
    words = re.findall(r'\b[a-záéíóúñ]{4,}\b', transcript_lower)
    freq = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1

    top_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
    main_word = top_words[0][0].capitalize() if top_words else "Fútbol"

    return main_word


def extract_key_sentences(transcript: str, n: int = 4) -> list:
    """Extrae las frases más representativas del video."""
    if not transcript:
        return []
    sentences = [s.strip() for s in re.split(r'[.!?]', transcript) if len(s.strip()) > 40]
    # Priorizar frases con keywords de fútbol
    scored = []
    for s in sentences:
        score = sum(1 for kw in ["argentina", "messi", "mundial", "gol", "fútbol", "jugador"]
                    if kw in s.lower())
        scored.append((score, s))
    scored.sort(reverse=True)
    return [s for _, s in scored[:n]]


def build_title(topic: str, transcript: str, trend_data: dict) -> tuple:
    """Genera título principal y alternativas basados en el contenido real."""
    transcript_lower = transcript.lower() if transcript else ""

    # Detectar si es pregunta, explicación, análisis o ranking
    if any(w in transcript_lower for w in ["qué es", "que es", "cómo", "como funciona", "explicar"]):
        style = "explicacion"
    elif any(w in transcript_lower for w in ["mejor", "peor", "top", "ranking", "número uno"]):
        style = "ranking"
    elif any(w in transcript_lower for w in ["historia", "récord", "pasó", "fue", "ocurrió"]):
        style = "historia"
    else:
        style = "analisis"

    # Detectar jugador/equipo principal mencionado
    featured = None
    for player in ["Messi", "De Paul", "Lautaro", "Álvarez", "Dybala", "Mac Allister", "Scaloni"]:
        if player.lower() in transcript_lower:
            featured = player
            break

    trending_context = ""
    if trend_data.get("results"):
        snippets = [r.get("snippet", "") for r in trend_data["results"][:2] if r.get("snippet")]
        if snippets:
            trending_context = snippets[0][:80]

    # Construir títulos según estilo
    titles = []
    if style == "explicacion":
        titles = [
            f"¿Qué es {topic}? La explicación definitiva | Football Terms",
            f"{topic}: Todo lo que necesitás saber sobre esto",
            f"Así se explica {topic} en el fútbol moderno ⚽",
        ]
    elif style == "ranking":
        titles = [
            f"Los mejores {topic} del fútbol argentino | Football Terms",
            f"TOP: {topic} que marcaron la historia de Argentina",
            f"{topic}: ¿Quién es el mejor? | Football Terms",
        ]
    elif style == "historia":
        titles = [
            f"La historia detrás de {topic} | Football Terms",
            f"{topic}: Lo que nadie te contó | Argentina",
            f"Así fue {topic} en el fútbol argentino",
        ]
    else:
        if featured:
            titles = [
                f"{featured} y {topic}: El análisis que necesitabas | Football Terms",
                f"¿Por qué {featured} domina {topic}? | Football Terms",
                f"{topic} con {featured}: Lo que no sabías",
            ]
        else:
            titles = [
                f"{topic}: El análisis más completo | Football Terms",
                f"Todo sobre {topic} en el fútbol argentino ⚽",
                f"{topic}: ¿Sabías esto? | Football Terms",
            ]

    return titles[0], titles[1:]


def build_description(topic: str, title: str, transcript: str,
                      trend_data: dict, temp_data: dict) -> str:
    """Genera descripción coherente con el video y las tendencias."""

    key_sentences = extract_key_sentences(transcript, 4)
    trending_players = [p[0] for p in temp_data.get("player_ranking", [])[:3]]
    trending_snippets = [r.get("snippet", "") for r in trend_data.get("results", [])[:2]
                         if r.get("snippet")]

    # Intro basada en el contenido real del video
    if key_sentences:
        intro = f"En este video hablo de {topic}. " + key_sentences[0][:120] + "."
    else:
        intro = f"En este video te explico todo sobre {topic} en el fútbol argentino."

    # Puntos clave del video (de las frases reales)
    if len(key_sentences) >= 2:
        puntos = "\n".join(f"✅ {s[:80]}." for s in key_sentences[1:4])
    else:
        puntos = f"✅ Análisis de {topic} en el fútbol actual."

    # Contexto de tendencias
    tendencia_context = ""
    if trending_snippets:
        tendencia_context = f"\n🌐 Contexto actual: {trending_snippets[0][:150]}"

    # Jugadores trending para mencionar naturalmente
    players_mention = ""
    if trending_players:
        players_mention = f"\nEn el contexto del fútbol argentino de hoy, jugadores como {', '.join(trending_players[:2])} son relevantes para este tema."

    # Hashtags específicos al tema
    topic_tags = []
    topic_lower = topic.lower()
    if "messi" in topic_lower: topic_tags.append("#Messi")
    if "mundial" in topic_lower or "copa" in topic_lower: topic_tags.append("#Mundial2026")
    if "argentina" in topic_lower: topic_tags.append("#Argentina")
    if "táctica" in topic_lower or "pressing" in topic_lower: topic_tags.append("#Táctica")
    if "gol" in topic_lower: topic_tags.append("#Gol")
    for p in trending_players[:2]:
        topic_tags.append(f"#{p.replace(' ', '')}")

    all_tags = CHANNEL_HASHTAGS + topic_tags
    all_tags = list(dict.fromkeys(all_tags))  # deduplicar

    description = f"""{intro}
{players_mention}
{tendencia_context}

📌 En este video:
{puntos}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚽ Football Terms — Fútbol explicado para todos
🔔 Suscribite para no perderte ningún video
👍 Si te gustó, dejá tu like y compartí
💬 Comentá qué tema querés que explique
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{' '.join(all_tags)}
""".strip()

    return description, all_tags


def run(transcript: str, trend_data: dict = None, temperature_data: dict = None) -> dict:
    if trend_data is None:
        trend_data = {}
    if temperature_data is None:
        temperature_data = {}

    # Aplicar corrector de subtítulos también a la transcripción
    try:
        from agents.subtitle_corrector import correct_transcript
        transcript = correct_transcript(transcript)
    except Exception:
        pass

    topic = extract_main_topic(transcript)
    title, alt_titles = build_title(topic, transcript, trend_data)
    description, tags = build_description(topic, title, transcript, trend_data, temperature_data)

    return {
        "agent": "Copywriter",
        "timestamp": datetime.now().isoformat(),
        "topic_detected": topic,
        "title": title,
        "alt_titles": alt_titles,
        "description": description,
        "tags": tags,
    }


if __name__ == "__main__":
    import sys
    transcript = sys.argv[1] if len(sys.argv) > 1 else "hoy hablamos de messi y de paul en el mundial 2026"
    data = run(transcript)
    print(json.dumps(data, ensure_ascii=False, indent=2))
