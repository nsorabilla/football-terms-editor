"""
Agente 1 — Analista de tendencias
Busca tendencias actuales de fútbol / Mundial / jugadores argentinos.
"""

import json
import time
from datetime import datetime
from googlesearch import search
import requests
from bs4 import BeautifulSoup


QUERIES = [
    "Argentina fútbol tendencias 2026",
    "jugadores argentinos famosos 2026 Mundial",
    "selección argentina partido noticias hoy",
    "Messi Di María Scaloni 2026",
    "Argentina Copa del Mundo 2026",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_snippet(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        # Primer párrafo con texto
        for tag in soup.find_all(["p", "h1", "h2"]):
            text = tag.get_text(strip=True)
            if len(text) > 60:
                return text[:300]
    except Exception:
        pass
    return ""


def run() -> dict:
    results = []
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
                    results.append({"query": query, "url": url, "snippet": snippet})
            time.sleep(1.5)  # respetar rate limit
        except Exception as e:
            results.append({"query": query, "error": str(e)})

    return {
        "agent": "Analista de tendencias",
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }


if __name__ == "__main__":
    data = run()
    print(json.dumps(data, ensure_ascii=False, indent=2))
