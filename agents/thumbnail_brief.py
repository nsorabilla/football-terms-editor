"""
Agente 6 — Generador de prompt para miniatura
Produce un prompt listo para usar en Midjourney, DALL-E, Canva AI, etc.
También genera el guideline paso a paso para hacerlo en Canva manualmente.
"""

import json
from datetime import datetime


def detect_palette(topic: str, transcript: str) -> dict:
    text = (topic + transcript).lower()
    if any(w in text for w in ["argentina", "selección", "albiceleste", "mundial"]):
        return {"name": "argentina", "primary": "#74ACDF", "accent": "#F6B40E", "text": "#FFFFFF"}
    elif any(w in text for w in ["gol", "remate", "ataque", "peligro"]):
        return {"name": "energía", "primary": "#E63946", "accent": "#F1FA8C", "text": "#FFFFFF"}
    elif any(w in text for w in ["defensa", "táctica", "presión", "pressing"]):
        return {"name": "táctica", "primary": "#1D3557", "accent": "#A8DADC", "text": "#FFFFFF"}
    else:
        return {"name": "neutro", "primary": "#0A0A0A", "accent": "#FFFFFF", "text": "#FFFFFF"}


def generate_ai_prompt(topic: str, title: str, palette: dict, trend_data: dict) -> str:
    """Prompt listo para Midjourney / DALL-E / Adobe Firefly."""
    trending_snippets = [r.get("snippet", "")[:60] for r in trend_data.get("results", [])[:2]]
    context = " ".join(trending_snippets)

    bg_element = "Argentine football stadium with blue and white flags"
    if "messi" in topic.lower():
        bg_element = "football stadium lights, golden hour atmosphere"
    elif "mundial" in topic.lower() or "copa" in topic.lower():
        bg_element = "FIFA World Cup trophy with stadium lights"
    elif "gol" in topic.lower():
        bg_element = "football goal net close-up with stadium lights"
    elif "táctica" in topic.lower() or "pressing" in topic.lower():
        bg_element = "aerial view of football field with tactical lines"

    prompt = (
        f"YouTube thumbnail background, {bg_element}, "
        f"dramatic lighting, high contrast, cinematic, "
        f"color palette: {palette['primary']} and {palette['accent']}, "
        f"bold typography space on left side for text '{topic.upper()}', "
        f"no people, no faces, professional sports media style, "
        f"8K ultra detailed, photorealistic"
    )
    return prompt


def run(topic: str, title: str, transcript: str = "", trend_data: dict = None) -> dict:
    if trend_data is None:
        trend_data = {}

    palette = detect_palette(topic, transcript)
    ai_prompt = generate_ai_prompt(topic, title, palette, trend_data)

    main_text = topic.upper()
    sub_text = "¿LO SABÍAS?" if "?" in title else "EXPLICADO"

    brief = {
        "agent": "Diseñador de miniaturas",
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "palette": palette,

        "prompt_para_ia": {
            "descripcion": "Copiá este prompt en Midjourney, DALL-E, Adobe Firefly o Canva AI para generar el fondo",
            "prompt": ai_prompt,
            "uso": [
                "Midjourney: /imagine " + ai_prompt,
                "DALL-E: pegá el prompt directamente",
                "Canva AI: usá 'Generar imagen' y pegá el prompt",
                "Adobe Firefly: pegá en 'Text to image'",
            ]
        },

        "guideline_canva": {
            "tamanio": "1280 x 720 px",
            "pasos": [
                {
                    "paso": "1. Fondo",
                    "accion": "Subí la imagen generada por IA o elegí un fondo de Canva relacionado al tema",
                    "ajuste": f"Reducí opacidad al 65% y agregá un overlay de color {palette['primary']} al 40%"
                },
                {
                    "paso": "2. Tu foto",
                    "accion": "Subí tu foto (la del Espanyol adjunta)",
                    "ajuste": "Usá 'Quitar fondo' en Canva → posicionala a la derecha, que ocupe 55% del alto"
                },
                {
                    "paso": "3. Texto principal",
                    "accion": f"Escribí: {main_text}",
                    "fuente": "Montserrat ExtraBold o Impact",
                    "tamanio": "90-110pt",
                    "color": palette["text"],
                    "posicion": "Tercio superior izquierdo",
                    "efecto": "Sombra negra + contorno 2px negro"
                },
                {
                    "paso": "4. Subtexto",
                    "accion": f"Escribí: {sub_text}",
                    "fuente": "Montserrat Bold",
                    "tamanio": "50pt",
                    "color": palette["accent"],
                    "posicion": "Debajo del texto principal"
                },
                {
                    "paso": "5. Detalle final",
                    "accion": "Agregá un emoji o ícono llamativo (⚽ ⚡ 🔥) en el borde izquierdo inferior",
                    "opcional": "Logo Football Terms pequeño en esquina inferior derecha"
                },
            ],
            "colores": palette,
            "checklist": [
                "¿Se lee el texto en menos de 2 segundos?",
                "¿Tu cara es visible y está bien iluminada?",
                "¿El fondo no compite con el texto?",
                "¿Hay contraste suficiente entre texto y fondo?",
                "¿Se ve bien en miniatura pequeña (móvil)?",
                "¿El título no repite exactamente el texto de la miniatura?",
            ],
            "exportar": "PNG, 1280x720px, máxima calidad"
        }
    }

    return brief


if __name__ == "__main__":
    data = run("Offside", "¿Qué es el offside? Todo explicado")
    print(json.dumps(data, ensure_ascii=False, indent=2))
