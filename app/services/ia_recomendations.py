import os
from ollama import Client

OLLAMA_MODEL = "qwen3-next:80b"

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