from unittest import result

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, Questionnaire, Biomarker, Result
from app.schemas import DatosFormulario, DatosEntrada
from app.auth import require_role
from app.services.scoring import calcular_score
from app.rag.recommender import buscar_fuentes_por_tags, recomendar_links, recomendar_sources, tags_para_recomendacion
from app.services.ia_recomendations import generar_recomendaciones_con_ia


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
    
    if biomarker.il6_value == 0:
        biomarker.il6_value="-"

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

    if not q:
        raise HTTPException(400, "Galdetegia falta da")
    
    existing = (
        db.query(Result)
        .filter(
            Result.questionnaire_id == q.id,
            Result.biomarker_id == b.id
        )
        .first()
    )

    if existing:
        ia_data = {"summary": "", "recommendations": []}

        if existing.ia_texto:
            try:
                ia_data = json.loads(existing.ia_texto)
            except json.JSONDecodeError:
                ia_data = {"summary": existing.ia_texto, "recommendations": []}

        return {
            "score": existing.score,
            "nivel": existing.nivel,
            "factores": existing.factores,
            "mensaje_general": existing.mensaje_general,
            "recomendacion_personalizada": {
                "summary": ia_data.get("summary", ""),
                "recommendations": ia_data.get("recommendations", []),
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
        ia_texto=json.dumps({
        "summary": ia.get("summary", ""),
        "recommendations": ia.get("recommendations", [])
        }, ensure_ascii=False),
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