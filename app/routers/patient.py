from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Patient, Questionnaire, Biomarker
from app.schemas import DatosFormulario, DatosEntrada
from app.auth import require_role
from app.services.scoring import calcular_score
from app.rag.recommender import recomendar_links, recomendar_sources


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
        answers=q.answers,            # contiene formulario1 y 2
        il6=b.il6_value,
        placa=b.dental_plaque
    )

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
    placa: float
):
    #fallback por si no hay IA aún o falla


    # Aquí, cuando implementes RAG, llamas a tu función:
    # advice = generar_consejos_rag(...)
    # return advice

    # (provisional)
    texto = []
    links = []
    sources = []

    f1 = answers.get("formulario1", {})
    if f1.get("cepillado") in ("behin", "gutxi"):
        texto.append("Saia zaitez egunean gutxienez 2 aldiz eskuilatzen (goizez eta gauez).\n")
    

    if f1.get("osagarria") == "ez":
        texto.append("Gehitu hortzarteko higienea (hari/eskuila interproximalak) egunean behin \n")
    

    if placa >= 2:
        texto.append("Plaka-indizea altuarekin, errutina indartu behar duzu eta garbiketa profesionaltzat hartu behar duzu.\n")
    if il6 > 10:
        texto.append("Inflamazio altua duzu, jarraitu profesionalaren jarraibideei eta mantendu ohiturak etengabe\n")

    perfil = {
        "score": score,
        "nivel_code": nivel_code,
        "factores": factores,
        "formulario1": answers.get("formulario1", {}),
        "formulario2": answers.get("formulario2", {}),
        "il6": il6,
        "placa": placa,
    }

    links = recomendar_links(perfil)
    sources = recomendar_sources(perfil)

    return {
        "texto": " ".join(texto),
        "links": links,
        "sources": sources,      
        "modo": "heuristica"
    }