"""
Agente 6 — Diseñador de miniaturas (brief para Canva)
Genera instrucciones detalladas para crear la miniatura en Canva.
"""

import json
from datetime import datetime


CANVA_SIZE = "1280 x 720 px (YouTube thumbnail)"

COLOR_PALETTES = {
    "argentina": {
        "primary": "#74ACDF",   # celeste argentina
        "secondary": "#FFFFFF",
        "accent": "#F6B40E",    # dorado
        "text": "#FFFFFF",
    },
    "energia": {
        "primary": "#E63946",   # rojo energía
        "secondary": "#1D3557",
        "accent": "#F1FA8C",
        "text": "#FFFFFF",
    },
    "neutral": {
        "primary": "#0A0A0A",
        "secondary": "#1F5D8F",
        "accent": "#FFFFFF",
        "text": "#FFFFFF",
    },
}


def detect_palette(topic: str, transcript: str) -> str:
    text = (topic + transcript).lower()
    if any(w in text for w in ["argentina", "selección", "albiceleste", "mundial"]):
        return "argentina"
    elif any(w in text for w in ["gol", "remate", "peligro", "ataque"]):
        return "energia"
    return "neutral"


def generate_background_suggestion(topic: str, trend_data: dict) -> str:
    topic_lower = topic.lower()
    if "argentina" in topic_lower or "selección" in topic_lower:
        return "Bandera argentina difuminada + estadio de fútbol de fondo"
    elif "messi" in topic_lower:
        return "Estadio con luces + tono azul/dorado"
    elif "mundial" in topic_lower or "copa" in topic_lower:
        return "Trofeo Copa del Mundo de fondo difuminado"
    elif "gol" in topic_lower or "remate" in topic_lower:
        return "Red de arco en primer plano, campo de juego de fondo"
    else:
        return "Campo de fútbol cenital (vista desde arriba) difuminado"


def run(topic: str, title: str, transcript: str = "", trend_data: dict = None) -> dict:
    if trend_data is None:
        trend_data = {}

    palette_key = detect_palette(topic, transcript)
    palette = COLOR_PALETTES[palette_key]
    bg_suggestion = generate_background_suggestion(topic, trend_data)

    # Texto para la miniatura (corto e impactante)
    main_text = topic.upper()
    sub_text = "¿LO SABÍAS?" if "?" in title else "EXPLICADO"

    brief = {
        "agent": "Diseñador de miniaturas",
        "timestamp": datetime.now().isoformat(),
        "canva_size": CANVA_SIZE,
        "topic": topic,
        "palette": palette_key,

        "instrucciones_canva": {
            "paso_1_fondo": {
                "descripcion": bg_suggestion,
                "color_base": palette["primary"],
                "opacidad_imagen": "60-70% (para que el texto se lea bien)",
            },
            "paso_2_foto_tuya": {
                "posicion": "Derecha o centro-derecha",
                "tamanio": "Ocupa 50-60% del alto de la imagen",
                "recorte": "Recortado del fondo (usa Canva > Quitar fondo)",
                "foto_referencia": "La foto adjunta con el escudo del Espanyol",
            },
            "paso_3_texto_principal": {
                "texto": main_text,
                "fuente": "Montserrat ExtraBold o Impact",
                "tamanio": "Grande (90-120pt)",
                "color": palette["text"],
                "posicion": "Izquierda, tercio superior",
                "efecto": "Sombra negra + contorno 2px",
            },
            "paso_4_subtexto": {
                "texto": sub_text,
                "fuente": "Montserrat Bold",
                "tamanio": "Mediano (50-60pt)",
                "color": palette["accent"],
                "posicion": "Debajo del texto principal",
            },
            "paso_5_elementos_extra": {
                "descripcion": "Flecha o emoji llamativo (⚡🔥⚽) en el borde izquierdo",
                "opcional": "Logo Football Terms en esquina inferior derecha (pequeño)",
            },
        },

        "colores": palette,

        "checklist_final": [
            "¿Se lee el texto en 2 segundos?",
            "¿Tu cara está visible y bien iluminada?",
            "¿El fondo no compite con el texto?",
            "¿Hay contraste suficiente (texto claro sobre fondo oscuro o viceversa)?",
            "¿La imagen se ve bien en miniatura pequeña (móvil)?",
        ],

        "exportar": "PNG, 1280x720px, máxima calidad",
    }

    return brief


if __name__ == "__main__":
    data = run("Offside", "¿Qué es el offside? Todo explicado")
    print(json.dumps(data, ensure_ascii=False, indent=2))
