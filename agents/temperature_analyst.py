"""
Agente 2 — Analista de temperatura de redes
Detecta qué jugadores y temas están más calientes en Google/Reddit/YouTube ahora.
"""

import json
import time
from datetime import datetime
from googlesearch import search
import requests
from bs4 import BeautifulSoup


QUERIES = [
    "jugador argentino más buscado hoy 2026",
    "Argentina fútbol viral redes sociales",
    "Argentina Reddit football trending",
    "youtube Argentina fútbol más visto semana",
    "who is trending Argentina football player 2026",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Jugadores argentinos conocidos para detectar menciones
PLAYERS = [
    "Messi", "Di María", "De Paul", "Lautaro", "Álvarez", "Dybala",
    "Romero", "Molina", "Mac Allister", "Enzo Fernández", "Scaloni",
]


def fetch_snippet(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["p", "h1", "h2"]):
            text = tag.get_text(strip=True)
            if len(text) > 60:
                return text[:300]
    except Exception:
        pass
    return ""


def count_mentions(text: str) -> dict:
    text_lower = text.lower()
    return {p: text_lower.count(p.lower()) for p in PLAYERS if p.lower() in text_lower}


def run() -> dict:
    results = []
    player_heat = {p: 0 for p in PLAYERS}
    seen_urls = set()

    for query in QUERIES:
        try:
            urls = list(search(query, num_results=3, lang="es"))
            for url in urls:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                snippet = fetch_snippet(url)
                if snippet:
                    mentions = count_mentions(snippet)
                    for p, count in mentions.items():
                        player_heat[p] += count
                    results.append({"query": query, "url": url, "snippet": snippet, "players_mentioned": mentions})
            time.sleep(1.5)
        except Exception as e:
            results.append({"query": query, "error": str(e)})

    # Ranking de jugadores más mencionados
    ranking = sorted(
        [(p, c) for p, c in player_heat.items() if c > 0],
        key=lambda x: x[1], reverse=True
    )

    return {
        "agent": "Analista de temperatura",
        "timestamp": datetime.now().isoformat(),
        "player_ranking": ranking,
        "results": results,
    }


if __name__ == "__main__":
    data = run()
    print(json.dumps(data, ensure_ascii=False, indent=2))
