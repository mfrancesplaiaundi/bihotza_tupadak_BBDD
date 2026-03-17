import os
from ollama import Client

from app.services.source_context import (
    resolver_fuentes_a_contexto,
    construir_contexto_fuentes,
)

OLLAMA_MODEL = "qwen3.5:397b"

client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + '05b78b69308143bcbfccc0c6e545bae7.1z0UAiUzDS8t9QMVeO_3-ipj'}
)

def enriquecer_recomendacion_con_ia_cloud(rec: dict, perfil: dict) -> str:
    fuentes_txt = "\n".join([
        f"- {s.get('title')} ({s.get('url')}) | tags: {', '.join(s.get('tags', []))}"
        for s in rec.get("sources", [])
    ])

    prompt = f"""
    Pazientearen datuak:
    - Score: {perfil.get('score')}
    - Maila: {perfil.get('nivel_code')}
    - Faktoreak: {', '.join(perfil.get('factores', []))}
    - IL6: {perfil.get('il6')}
    - Plaka: {perfil.get('placa')}
    - Hortzak: {perfil.get('dientes')}
    - pH: {perfil.get('ph')}

    Oinarrizko gomendioa:
    - Lehentasuna: {rec.get('priority')}
    - Testua: {rec.get('text')}
    - Arrazoia: {rec.get('reason')}

    Iturriak:
    {fuentes_txt if fuentes_txt else "- Ez dago iturri espezifikorik"}

    Idatzi gomendio hobetua:
    - gehienez 2 esaldi
    - euskaraz
    - argia eta zehatza
    - tonu mediko zuhurrarekin
    - ez diagnostikatu
    - ez asmatu daturik
    """

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a cautious clinical support assistant for oral health education. "
                    "Write brief, clear advice in Basque. "
                    "Do not diagnose, do not prescribe medication, and do not invent facts."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response["message"]["content"].strip()



def generar_recomendaciones_con_ia(perfil: dict, sources: list[dict]) -> dict:
    fuentes_resueltas = resolver_fuentes_a_contexto(sources, max_fuentes=3)
    contexto_fuentes = construir_contexto_fuentes(fuentes_resueltas)

    prompt = f"""
Pazientearen datuak:
- Score: {perfil.get('score')}
- Maila: {perfil.get('nivel_code')}
- Faktoreak: {', '.join(perfil.get('factores', []))}
- IL6: {perfil.get('il6')}
- Plaka: {perfil.get('placa')}
- Hortzak: {perfil.get('dientes')}
- pH: {perfil.get('ph')}

Iturriak:
{contexto_fuentes if contexto_fuentes else "Ez dago iturri erabilgarririk."}

Sortu gehienez 5 gomendio, lehentasunaren arabera ordenatuta. Desberdinak izan behar dira. Gomendio bakoitzetik esan ze iturriak erabili dituzun gomendioa egiteko, url-a. Iturriak eta gomendioak desberdinak izan behar dira.

Erantzun JSON hutsean formatu honetan:
{{
  "summary": "....",
  "recommendations": [
    {{
      "priority": "alta",
      "text": "...",
      "reason": "...",
      "sources": [
        {{
        "url": "...",
        "title": "..."
        }}
    ]
    }}
  ]
}}

Arauak:
- euskaraz, 
- Argia izan behar du, kontuan izan pazientea ondo ulertu behar duela. Bi esaldi edo horrela egin.
- saiatu gomendio desberdinak egiten eta iturri desberdinak erabili.
- ez diagnostikatu
- ez gomendatu botikarik
- ez asmatu daturik
- oinarritu emandako iturrietan bakarrik
- Erantzun euskaraz modu naturalean, osasun arloko paziente bati zuzendutako hizkera argi eta ulerterrazean.
- Ez egin itzulpen literala gaztelaniatik edo ingelesetik.
- hitzak ez asmatu, begiratu hiztegian
- gomendio moduan idatzi, pazienteari zuzenduta

Adibide ona:
- "Saiatu egunean bi aldiz hortzak garbitzen eta hortzarteko garbiketa ere egunero egiten."
- "Komeni da aho-osasuneko profesional batekin berrikuspena egitea."
- "Mantendu hidratazio egokia eta zaindu zure ahoaren oreka."


"""

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Erantzun euskaraz modu naturalean, osasun arloko paziente bati zuzendutako hizkera argi eta ulerterrazean. "
                    "Return only valid JSON. Write in Basque. "
                    "Ez egin itzulpen literala gaztelaniatik edo ingelesetik."
                    "Erabili euskaraz ohikoak diren egiturak eta esamolde naturalak."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response["message"]["content"].strip()