"""
Corrector de subtítulos — post-procesado de transcripción Whisper.
Corrige nombres de jugadores, equipos y términos de fútbol que Whisper malinterpreta.
"""

import re

# ── Diccionario de correcciones conocidas ─────────────────────────────────────
# Formato: "error común": "corrección correcta"
CORRECTIONS = {
    # Jugadores argentinos
    "lionel andres": "Lionel Andrés",
    "leo mesi": "Lionel Messi",
    "mesi": "Messi",
    "de pol": "De Paul",
    "depol": "De Paul",
    "rodrigo de pol": "Rodrigo De Paul",
    "rodrigo depol": "Rodrigo De Paul",
    "lautaro martines": "Lautaro Martínez",
    "lautaro martinez": "Lautaro Martínez",
    "julián álvares": "Julián Álvarez",
    "julian alvares": "Julián Álvarez",
    "julian alvarez": "Julián Álvarez",
    "mac alister": "Mac Allister",
    "macalister": "Mac Allister",
    "mac allister": "Mac Allister",
    "enzo fernandes": "Enzo Fernández",
    "enzo fernandez": "Enzo Fernández",
    "di maria": "Di María",
    "di marìa": "Di María",
    "angel di maria": "Ángel Di María",
    "angel fideo": "Ángel Di María",
    "dybala": "Dybala",
    "paulo dybala": "Paulo Dybala",
    "la joya": "La Joya Dybala",
    "molina": "Nahuel Molina",
    "licha martinez": "Lisandro Martínez",
    "lisandro martines": "Lisandro Martínez",
    "cuti romero": "Cristian Romero",
    "cristian romero": "Cristian Romero",
    "tagliafico": "Nicolás Tagliafico",
    "scalone": "Scaloni",
    "scaloni": "Lionel Scaloni",
    "el toro": "Lautaro Martínez",

    # Equipos
    "river plate": "River Plate",
    "boca juniors": "Boca Juniors",
    "barcelon": "Barcelona",
    "inter de milan": "Inter de Milán",
    "real madrit": "Real Madrid",
    "manchester city": "Manchester City",
    "psg": "PSG",
    "paris san german": "Paris Saint-Germain",
    "paris saint german": "Paris Saint-Germain",

    # Términos de fútbol
    "offsayd": "offside",
    "off side": "offside",
    "penalti": "penal",
    "penalty": "penal",
    "córner": "córner",
    "corner": "córner",
    "cobro de esquina": "córner",
    "tiro de esquina": "córner",
    "pressing": "pressing",
    "presing": "pressing",
    "contragolpe": "contraataque",
    "contra ataque": "contraataque",
    "fuera de juego": "offside",
    "linea": "línea",
    "goleador": "goleador",
    "arquero": "arquero",
    "portero": "portero",
    "delantero centro": "delantero centro",
    "mediocampista": "mediocampista",
    "volante": "volante",
    "lateral": "lateral",
    "libero": "líbero",
    "balon": "balón",
    "pelota": "pelota",

    # Competiciones
    "mundial 2026": "Mundial 2026",
    "copa del mundo": "Copa del Mundo",
    "copa america": "Copa América",
    "copa libertadores": "Copa Libertadores",
    "champions league": "Champions League",
    "liga de campeones": "Champions League",
    "premier league": "Premier League",
    "la liga": "La Liga",
    "serie a": "Serie A",

    # Errores comunes de Whisper en español
    "eh": "",           # muletilla
    "este este": "este",
    "bueno bueno": "bueno",
}

# Jugadores para detectar contexto y corregir apellidos ambiguos
PLAYER_CONTEXT = {
    "messi": ["lionel", "leo", "la pulga", "10", "argentina"],
    "de paul": ["rodrigo", "atlético", "volante", "8"],
    "lautaro": ["martínez", "toro", "inter", "9"],
    "álvarez": ["julián", "araña", "city", "manchester"],
}


def apply_corrections(text: str) -> str:
    """Aplica correcciones del diccionario, respetando mayúsculas."""
    result = text

    # Ordenar por longitud descendente para aplicar frases largas primero
    sorted_corrections = sorted(CORRECTIONS.items(), key=lambda x: len(x[0]), reverse=True)

    for wrong, right in sorted_corrections:
        if not right:  # eliminar muletillas
            pattern = r'\b' + re.escape(wrong) + r'\b'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        else:
            pattern = r'\b' + re.escape(wrong) + r'\b'
            result = re.sub(pattern, right, result, flags=re.IGNORECASE)

    # Limpiar espacios dobles
    result = re.sub(r' {2,}', ' ', result).strip()
    return result


def fix_capitalization(text: str) -> str:
    """Asegura mayúsculas correctas en nombres propios detectados."""
    proper_nouns = [
        "Messi", "Di María", "De Paul", "Lautaro", "Álvarez", "Dybala",
        "Scaloni", "Mac Allister", "Enzo Fernández", "Molina", "Romero",
        "Argentina", "Mundial", "Copa", "Champions", "Premier",
        "River", "Boca", "Barcelona", "Madrid",
    ]
    for noun in proper_nouns:
        result = re.sub(re.escape(noun), noun, text, flags=re.IGNORECASE)
        text = result
    return text


def correct_segments(segments: list) -> list:
    """Corrige una lista de segmentos de Whisper."""
    corrected = []
    for seg in segments:
        text = seg.get("text", "")
        text = apply_corrections(text)
        text = fix_capitalization(text)
        # Eliminar espacios extra al inicio/fin
        text = text.strip()
        corrected.append({**seg, "text": text})
    return corrected


def correct_transcript(transcript: str) -> str:
    """Corrige el texto completo de la transcripción."""
    text = apply_corrections(transcript)
    text = fix_capitalization(text)
    return text


if __name__ == "__main__":
    # Test
    tests = [
        "hoy hablamos de lionel andres mesi y de rodrigo de pol",
        "julian alvares convirtió un gol de off side",
        "scalone armó una táctica de presing intenso",
        "mac alister y enzo fernandes fueron los mejores",
        "argentina juega la copa del mundo en el mundial 2026",
    ]
    for t in tests:
        print(f"ORIGINAL:  {t}")
        print(f"CORREGIDO: {correct_transcript(t)}")
        print()
