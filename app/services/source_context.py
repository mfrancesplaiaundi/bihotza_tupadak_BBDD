from __future__ import annotations

import io
from typing import List, Dict
import requests
import fitz 
from bs4 import BeautifulSoup


TIMEOUT = 20
MAX_CHARS_PER_SOURCE = 3000
MAX_SOURCES_DEFAULT = 3


def limpiar_texto(txt: str) -> str:
    return " ".join(txt.split())


def recortar_texto(txt: str, max_chars: int = MAX_CHARS_PER_SOURCE) -> str:
    return limpiar_texto(txt)[:max_chars]


def extraer_texto_web(url: str) -> str:
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    texto = soup.get_text(separator=" ", strip=True)
    return recortar_texto(texto)


def extraer_texto_pdf(url: str) -> str:
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    doc = fitz.open(stream=pdf_bytes.read(), filetype="pdf")

    partes = []
    for page in doc:
        partes.append(page.get_text())

    texto = "\n".join(partes)
    return recortar_texto(texto)


def resolver_fuente(source: Dict) -> Dict:
    url = source.get("url", "")
    source_type = source.get("type", "web")

    try:
        if source_type == "pdf" or url.lower().endswith(".pdf"):
            contenido = extraer_texto_pdf(url)
        else:
            contenido = extraer_texto_web(url)

        return {
            "id": source.get("id"),
            "title": source.get("title", url),
            "url": url,
            "lang": source.get("lang"),
            "type": source_type,
            "tags": source.get("tags", []),
            "content": contenido,
            "ok": True,
        }

    except Exception as e:
        return {
            "id": source.get("id"),
            "title": source.get("title", url),
            "url": url,
            "lang": source.get("lang"),
            "type": source_type,
            "tags": source.get("tags", []),
            "content": "",
            "ok": False,
            "error": str(e),
        }


def resolver_fuentes_a_contexto(
    sources: List[Dict],
    max_fuentes: int = MAX_SOURCES_DEFAULT
) -> List[Dict]:
    out = []

    for source in sources[:max_fuentes]:
        out.append(resolver_fuente(source))

    return out


def construir_contexto_fuentes(fuentes_resueltas: List[Dict]) -> str:
    bloques = []

    for i, f in enumerate(fuentes_resueltas, start=1):
        if not f.get("ok") or not f.get("content"):
            continue

        bloques.append(
            f"""Fuente {i}:
Título: {f.get("title")}
URL: {f.get("url")}
Tipo: {f.get("type")}
Tags: {", ".join(f.get("tags", []))}
Contenido:
{f.get("content")}
"""
        )

    return "\n\n".join(bloques)