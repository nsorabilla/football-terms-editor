"""
Agente 6 — Brief de miniatura para YouTube
Genera: prompt específico para IA + guideline detallado para Canva con tu foto.
"""

import json
from datetime import datetime


# Paletas del canal Football Terms
PALETTES = {
    "argentina":  {"bg": "#0D47A1", "accent": "#FFD700", "text": "#FFFFFF", "overlay": "azul Argentina"},
    "mundial":    {"bg": "#1B1B2F", "accent": "#E94560", "text": "#FFFFFF", "overlay": "oscuro dramático"},
    "energía":    {"bg": "#B71C1C", "accent": "#FFEB3B", "text": "#FFFFFF", "overlay": "rojo energético"},
    "táctica":    {"bg": "#1A237E", "accent": "#00E5FF", "text": "#FFFFFF", "overlay": "azul táctico"},
    "neutral":    {"bg": "#212121", "accent": "#FFFFFF", "text": "#FFFFFF", "overlay": "negro cinematográfico"},
}


def detect_context(topic: str, transcript: str, trend_data: dict) -> dict:
    """Detecta tema, jugadores mencionados y contexto para personalizar todo."""
    text = (topic + " " + transcript).lower()
    trending = [r.get("snippet", "") for r in trend_data.get("results", [])[:3]]

    # Paleta
    if any(w in text for w in ["argentina", "selección", "albiceleste"]):
        palette_key = "argentina"
    elif any(w in text for w in ["mundial", "copa del mundo", "world cup"]):
        palette_key = "mundial"
    elif any(w in text for w in ["gol", "remate", "ataque", "explosivo"]):
        palette_key = "energía"
    elif any(w in text for w in ["táctica", "pressing", "sistema", "formación"]):
        palette_key = "táctica"
    else:
        palette_key = "neutral"

    # Jugadores mencionados
    players_found = []
    for p in ["Messi", "Di María", "De Paul", "Lautaro", "Álvarez", "Dybala",
              "Mac Allister", "Enzo Fernández", "Scaloni"]:
        if p.lower() in text:
            players_found.append(p)

    # Elemento visual de fondo
    if "messi" in text:
        bg_element = "football stadium at night with golden lights and blue confetti"
    elif "mundial" in text or "copa" in text:
        bg_element = "FIFA World Cup 2026 trophy with dramatic lighting and stadium crowd"
    elif "argentina" in text:
        bg_element = "Argentine football stadium with blue and white flags waving, dramatic sky"
    elif "táctica" in text or "formación" in text:
        bg_element = "tactical football field diagram with glowing lines on dark background"
    elif "gol" in text:
        bg_element = "close-up of football goal net with stadium lights in background, dramatic"
    elif "pressing" in text:
        bg_element = "intense football match moment, players in motion blur, stadium atmosphere"
    else:
        bg_element = "professional football stadium aerial view, night match, lights on"

    return {
        "palette_key": palette_key,
        "palette": PALETTES[palette_key],
        "players": players_found,
        "bg_element": bg_element,
        "trending_context": trending[0][:100] if trending else "",
    }


def build_ai_prompt(topic: str, ctx: dict) -> dict:
    """Genera prompts específicos para distintas IAs."""
    bg = ctx["bg_element"]
    palette = ctx["palette"]
    color_desc = f"dominant colors: {palette['bg']} background with {palette['accent']} accents"

    base_prompt = (
        f"YouTube thumbnail background only, NO text, NO people, NO faces, "
        f"{bg}, {color_desc}, "
        f"cinematic dramatic lighting, high contrast, professional sports photography style, "
        f"space on LEFT THIRD for text overlay, "
        f"ultra detailed, 8K, photorealistic"
    )

    return {
        "midjourney": f"/imagine prompt: {base_prompt} --ar 16:9 --v 6 --style raw",
        "dalle": base_prompt,
        "canva_ai": f"Generate image: {base_prompt}",
        "adobe_firefly": base_prompt,
        "nota": "Estos prompts generan SOLO el fondo. Tu foto se superpone encima en Canva.",
    }


def build_canva_guide(topic: str, title: str, ctx: dict) -> dict:
    """Guideline detallado paso a paso para Canva."""
    palette = ctx["palette"]
    players = ctx["players"]
    main_text = topic.upper()

    # Texto secundario basado en contexto
    if players:
        sub_text = f"con {players[0]}" if len(players) == 1 else f"{players[0]} · {players[1]}"
    else:
        sub_text = "EXPLICADO"

    return {
        "tamanio_canvas": "1280 x 720 px (YouTube thumbnail estándar)",
        "pasos": [
            {
                "paso": "1️⃣  Fondo generado por IA",
                "que_hacer": "Subí la imagen que generaste con el prompt de arriba (Midjourney/DALL-E/Canva AI)",
                "como": "Elementos → Subir imagen → ponerla como fondo completo",
                "ajuste": f"Opacidad: 80%. Luego agregá un rectángulo negro encima con opacidad 35% para que el texto se lea bien",
            },
            {
                "paso": "2️⃣  Tu foto (OBLIGATORIO)",
                "que_hacer": "Subí la foto tuya con el escudo del Espanyol de fondo azul",
                "como": "Subir imagen → seleccionarla → Efectos → 'Quitar fondo' (Canva lo hace automático)",
                "posicion": "Lado DERECHO de la imagen, pegada al borde",
                "tamanio": "Que tu cara y torso ocupen el 55-65% del alto total de la imagen",
                "ajuste": "Si queda con borde raro, usá 'Ajustar' para recortar mejor",
            },
            {
                "paso": "3️⃣  Texto principal",
                "que_hacer": f"Escribí: {main_text}",
                "fuente": "Montserrat ExtraBold / Anton / Impact (cualquiera de las 3)",
                "tamanio": "100-120pt",
                "color": palette["text"],
                "posicion": "Tercio IZQUIERDO superior — que no tape tu cara",
                "efecto": "Texto → Efectos → Sombra (color negro, desplazamiento 4px) + Contorno negro 2px",
            },
            {
                "paso": "4️⃣  Texto secundario",
                "que_hacer": f"Escribí: {sub_text}",
                "fuente": "Montserrat Bold",
                "tamanio": "48-55pt",
                "color": palette["accent"],
                "posicion": "Debajo del texto principal",
                "efecto": "Sin sombra, solo el color de acento para que contraste",
            },
            {
                "paso": "5️⃣  Franja de color (opcional pero recomendado)",
                "que_hacer": f"Agregá un rectángulo horizontal angosto ({palette['accent']}) detrás del texto principal",
                "como": "Elementos → Formas → Rectángulo → color {palette['accent']} → opacidad 90% → mandalo atrás del texto",
                "efecto": "Le da un look más profesional y facilita la lectura",
            },
            {
                "paso": "6️⃣  Revisión final",
                "que_hacer": "Achicá la vista al 25% para simular cómo se ve en YouTube móvil",
                "checklist": [
                    "¿Tu cara se ve clara y reconocible?",
                    "¿El texto se lee en menos de 2 segundos?",
                    "¿El color de acento genera contraste suficiente?",
                    "¿No hay elementos que compitan entre sí?",
                ],
            },
        ],
        "colores": {
            "fondo_principal": palette["bg"],
            "acento": palette["accent"],
            "texto": palette["text"],
            "overlay": palette["overlay"],
        },
        "exportar": "Compartir → Descargar → PNG → 'Tamaño original' → Calidad máxima",
    }


def run(topic: str, title: str, transcript: str = "", trend_data: dict = None) -> dict:
    if trend_data is None:
        trend_data = {}

    ctx = detect_context(topic, transcript, trend_data)
    ai_prompts = build_ai_prompt(topic, ctx)
    canva_guide = build_canva_guide(topic, title, ctx)

    return {
        "agent": "Diseñador de miniaturas",
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "jugadores_detectados": ctx["players"],
        "paleta": ctx["palette_key"],
        "prompt_para_ia": ai_prompts,
        "guideline_canva": canva_guide,
    }


if __name__ == "__main__":
    data = run("Offside", "¿Qué es el offside? Todo explicado",
               "hoy hablo del offside en argentina y messi")
    print(json.dumps(data, ensure_ascii=False, indent=2))
