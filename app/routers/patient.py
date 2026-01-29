from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, Questionnaire, Biomarker
from app.schemas import DatosFormulario, DatosEntrada
from app.auth import require_role
from app.services.scoring import calcular_score


import hashlib

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

    datos = DatosEntrada(
        formulario1=q.answers["formulario1"],
        formulario2=q.answers["formulario2"],
        il6_value=b.il6_value,
        dental_plaque=b.dental_plaque
    )

    score, factores = calcular_score(datos)

    if score < 25:
        nivel = "Berdea"
    elif 25 < score < 50:
        nivel = "Horia"
    elif 50 < score < 75:
        nivel = "Laranja"
    else:
        nivel = "Gorria"

    ia = recomendacion_personalizada_ia(
        score=score,
        nivel_code=nivel,
        factores=factores,
        answers=q.answers,            # contiene formulario1 y 2
        il6=b.il6_value,
        placa=b.dental_plaque
    )

    return {
        "score": score,
        "nivel": nivel,
        "factores": factores,
        "recomendaciones_generales": recomendaciones_generales(nivel),
        "recomendacion_personalizada": ia
    }

def recomendaciones_generales(nivel):
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


def recomendacion_personalizada(factores):
    if "Inflamazioaren presentzia altua" in factores:
        return "Inflamazio markatzaileak jarraipen berezia behar du."
    return "Ez da arrisku faktore nabarmenik hauteman."

def recomendacion_personalizada_ia(
    score: float,
    nivel_code: str,
    factores: list[str],
    answers: dict,
    il6: float,
    placa: float
):
    #fallback por si no hay IA aún o falla
    fallback = {
        "texto": recomendacion_personalizada(factores),
        "links": [],
        "sources": [],
        "modo": "fallback"
    }

    # Aquí, cuando implementes RAG, llamas a tu función:
    # advice = generar_consejos_rag(...)
    # return advice

    # (provisional)
    texto = []
    links = []

    f1 = answers.get("formulario1", {})
    if f1.get("cepillado") in ("behin", "gutxi"):
        texto.append("Intenta cepillarte al menos 2 veces al día (mañana y noche).\n")
        links.append({"title": "Técnica de cepillado (video)", "url": "https://www.youtube.com/results?search_query=t%C3%A9cnica+cepillado+dental"})

    if f1.get("osagarria") == "ez":
        texto.append("Añade higiene interdental (hilo/cepillos interproximales) 1 vez al día.\n")
        links.append({"title": "Higiene interdental (guía)", "url": "https://www.youtube.com/results?search_query=hilo+dental+uso"})

    if placa >= 2:
        texto.append("Con índice de placa elevado, refuerza rutina y considera una limpieza profesional.\n")
    if il6 > 10:
        texto.append("Si hay inflamación alta, sigue las indicaciones del profesional y mantén hábitos constantes.\n")

    if not texto:
        return fallback

    return {
        "texto": " ".join(texto),
        "links": links[:3],
        "sources": [],      
        "modo": "provisional"
    }