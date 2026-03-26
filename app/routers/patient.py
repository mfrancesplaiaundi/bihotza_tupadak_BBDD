from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, Questionnaire, Biomarker, Result
from app.schemas import DatosFormulario, DatosEntrada
from app.auth import require_role
from app.services.scoring import calcular_score
from app.rag.recommender import buscar_fuentes_por_tags, recomendar_links, recomendar_sources, tags_para_recomendacion
from app.services.ia_recomendations import enriquecer_recomendacion_con_ia_cloud, generar_recomendaciones_con_ia


import hashlib
import json

router = APIRouter(prefix="/api/patient", tags=["patient"])

@router.post("/questionnaires")
def guardar_cuestionarios(
    data: DatosFormulario,
    db: Session = Depends(get_db),
    payload=Depends(require_role("patient"))
):
    q = Questionnaire(
        patient_id=payload["patient_id"],  # UUID del token
        answers=data.dict()
    )
    db.add(q)
    db.commit()
  
    return {"status": "ok"}

@router.get("/biomarkers")
def ver_biomarcadores_paciente(
    db: Session = Depends(get_db),
    payload=Depends(require_role("patient"))
):
    biomarker = (
        db.query(Biomarker)
        .filter(Biomarker.patient_id == payload["patient_id"])
        .order_by(Biomarker.measured_at.desc())
        .first()
    )

    if not biomarker:
        return {"message": "Oraindik ez dago analitikarik"}

    return {
        "il6_value": biomarker.il6_value,
        "dental_plaque": biomarker.dental_plaque,
        "tooth_count": biomarker.tooth_count,
        "ph_value": biomarker.ph_value,
        "measured_at": biomarker.measured_at
    }


@router.get("/resultados")
def resultados_paciente(
    db: Session = Depends(get_db),
    payload=Depends(require_role("patient"))
):
    q = (
        db.query(Questionnaire)
        .filter(Questionnaire.patient_id == payload["patient_id"])
        .order_by(Questionnaire.created_at.desc())
        .first()
    )

    b = (
        db.query(Biomarker)
        .filter(Biomarker.patient_id == payload["patient_id"])
        .order_by(Biomarker.measured_at.desc())
        .first()
    )

    if not q or not b:
        raise HTTPException(400, "Datu guztiak ez daude eskuragarri")
    
    existing = (
        db.query(Result)
        .filter(
            Result.questionnaire_id == q.id,
            Result.biomarker_id == b.id
        )
        .first()
    )

    if existing:
        return {
            "score": existing.score,
            "nivel": existing.nivel,
            "factores": existing.factores,
            "mensaje_general": existing.mensaje_general,
            "recomendacion_personalizada": {
                "texto": existing.ia_texto,
                "links": existing.ia_links or [],
                "sources": existing.ia_sources or [],
                "modo": existing.ia_mode
            }
        }

    datos = DatosEntrada(
        formulario1=q.answers["formulario1"],
        formulario2=q.answers["formulario2"],
        il6_value=b.il6_value,
        dental_plaque=b.dental_plaque,
        tooth_count=b.tooth_count,
        ph_value=b.ph_value        
    )

    score, factores = calcular_score(datos)

    if score <= 25:
        nivel = "Berdea"
    elif 25 < score <= 50:
        nivel = "Horia"
    elif 50 < score < 75:
        nivel = "Laranja"
    else:
        nivel = "Gorria"

    ia = recomendacion_personalizada_ia(
        score=score,
        nivel_code=nivel,
        factores=factores,
        answers=q.answers,            
        il6=b.il6_value,
        placa=b.dental_plaque,
        dientes=b.tooth_count,
        ph=b.ph_value
    )

    result = Result(
        patient_id=payload["patient_id"],
        questionnaire_id=q.id,
        biomarker_id=b.id,
        score=score,
        nivel=nivel,
        factores=factores,
        mensaje_general=mensaje_general(nivel),
        ia_texto=ia.get("texto"),
        ia_links=ia.get("links", []),
        ia_sources=ia.get("sources", []),
        ia_mode=ia.get("modo")
    )

    db.add(result)
    db.commit()

    return {
        "score": score,
        "nivel": nivel,
        "factores": factores,
        "mensaje_general": mensaje_general(nivel),
        "recomendacion_personalizada": ia
    }

def mensaje_general(nivel):
    if nivel == "Berdea":
        return [
            "🟢 Eutsi horri! segi zure ahoko eta bihotzeko osasuna zaintzen!"
        ]
    elif nivel == "Horia":
        return [
            "🟡 Aldaketa txiki batek bide handia ireki dezake. Egin pausotxo bat eta zure ahoak eta bihotzak ederki nabarituko dute."
        ]
    elif nivel == "Laranja":
        return [
            "🟠 Gelditu une batez eta entzun zure gorputza. Zaintza txiki batzuk orain ahoko eta bihotzeko osasunari, eta ongizate handiagoa gero."
        ]
    else:
        return [
            "🔴 Hau da zure unea: hartu norabidea berriro. Zure ahoko eta bihotzeko osasuna lehentasun bihurtzen duzunean, bidea argituko zaizu berriz."
        ]

""" def recomendacion_personalizada_ia(
    score: float,
    nivel_code: str,
    factores: list[str],
    answers: dict,
    il6: float,
    placa: float,
    dientes: int,
    ph: float
):

    recomendaciones = []
    texto = []
    links = []
    sources = []

    f1 = answers.get("formulario1", {})

    perfil = {
        "score": score,
        "nivel_code": nivel_code,
        "factores": factores,
        "formulario1": answers.get("formulario1", {}),
        "formulario2": answers.get("formulario2", {}),
        "il6": il6,
        "placa": placa,
        "dientes": dientes,
        "ph": ph
    }

    if f1.get("cepillado") in ("behin", "gutxi"):
        recomendaciones.append({
            "priority": "alta",
            "text": "Saia zaitez egunean gutxienez 2 aldiz eskuilatzen (goizez eta gauez).",
            "reason": "Eskuilatze maiztasun txikiak aho-higiene txarragoarekin lotura izan dezake.",
            "tag": "cepillado"
        })

    if f1.get("osagarria") == "ez":
        recomendaciones.append({
            "priority": "alta",
            "text": "Gehitu hortzarteko higienea (hari edo eskuila interproximalak) egunean behin.",
            "reason": "Hortzen arteko higieneak plaka pilaketa murrizten lagun dezake.",
            "tag": "higiene_interdental"
        })

    if placa >= 2:
        recomendaciones.append({
            "priority": "alta",
            "text": "Plaka-indize altua duzunez, komeni da aho-garbiketa ohiturak indartzea eta garbiketa profesionala baloratzea.",
            "reason": "Plaka altuak hantura eta aho-arazoen arriskua handitu dezake.",
            "tag": "placa"
        })

    if il6 > 10:
        recomendaciones.append({
            "priority": "alta",
            "text": "Inflamazio-markatzaile altua dagoenez, jarraitu profesional sanitarioaren aholkuak eta mantendu zaintza-ohitura egonkorrak.",
            "reason": "Inflamazio maila altuak arreta handiagoa eskatzen du.",
            "tag": "inflamacion"
        })

    if ph < 6.5:
        recomendaciones.append({
            "priority": "media",
            "text": "Saiatu hidratazio egokia mantentzen eta zure aho-ingurunearen oreka zaintzen.",
            "reason": "pH baxuak aho-ingurunean desoreka adieraz dezake.",
            "tag": "ph"
        })
    
    for rec in recomendaciones:
        rec_tags = tags_para_recomendacion(rec)
        rec["sources"] = buscar_fuentes_por_tags(
            tags=rec_tags,
            max_items=3,
            lang="es"
        )

        try:
            rec["ai_text"] = "[OLLAMA] " + enriquecer_recomendacion_con_ia_cloud(rec, perfil)
        except Exception as e:
            rec["ai_text"] = rec["text"]
            rec["ai_error"] = str(e)

    links = recomendar_links(perfil)
    sources = recomendar_sources(perfil)

    summary = "Zure datuen arabera, aho-osasunarekin lotutako gomendio pertsonalizatu batzuk prestatu dira."

    return {
        "summary": summary,
        "recommendations": recomendaciones[:4],
        "links": links,
        "sources": sources,
        "modo": "heuristica"
    }
 """

def recomendacion_personalizada_ia(
    score: float,
    nivel_code: str,
    factores: list[str],
    answers: dict,
    il6: float,
    placa: float,
    dientes: float,
    ph: float
):
    perfil = {
        "score": score,
        "nivel_code": nivel_code,
        "factores": factores,
        "formulario1": answers.get("formulario1", {}),
        "formulario2": answers.get("formulario2", {}),
        "il6": il6,
        "placa": placa,
        "dientes": dientes,
        "ph": ph
    }

    links = recomendar_links(perfil)
    sources = recomendar_sources(perfil)

    try:
        respuesta_ia = generar_recomendaciones_con_ia(perfil, sources)
        data_ia = parsear_json_ia(respuesta_ia)

        return {
            "summary": data_ia.get("summary", ""),
            "recommendations": data_ia.get("recommendations", []),
            "links": links,
            "sources": sources,
            "modo": "ia"
        }

    except Exception as e:
        return {
            "summary": "Ezin izan dira gomendio aurreratuak sortu.",
            "recommendations": [],
            "links": links,
            "sources": sources,
            "modo": "fallback",
            "error": str(e)
        }


def parsear_json_ia(texto: str) -> dict:
    texto = texto.strip()

    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio == -1 or fin == -1:
        raise ValueError("La IA no devolvió un JSON válido")

    json_str = texto[inicio:fin + 1]
    return json.loads(json_str)