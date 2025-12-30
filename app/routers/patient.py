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
        patient_id=payload["sub"],  # UUID del token
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
        .filter(Questionnaire.patient_id == payload["sub"])
        .order_by(Questionnaire.created_at.desc())
        .first()
    )

    b = (
        db.query(Biomarker)
        .filter(Biomarker.patient_id == payload["sub"])
        .order_by(Biomarker.measured_at.desc())
        .first()
    )

    if not q or not b:
        raise HTTPException(400, "Datu guztiak ez daude eskuragarri")

    datos = DatosEntrada(
        formulario1=q.answers["formulario1"],
        formulario2=q.answers["formulario2"],
        il6=b.il6_value,
        indice_placa=b.dental_plaque
    )

    score, factores = calcular_score(datos)

    if score < 20:
        nivel = "Baxua"
    elif score < 40:
        nivel = "Ertaina"
    else:
        nivel = "Altua"

    return {
        "score": score,
        "nivel": nivel,
        "factores": factores,
        "recomendaciones_generales": recomendaciones_generales(nivel),
        "recomendacion_personalizada": factores
    }

def recomendaciones_generales(nivel):
    if nivel == "Baxua":
        return [
            "Egungo aho-higiene ohiturak mantendu"
        ]
    elif nivel == "Ertaina":
        return [
            "Hortzen garbiketa hobetu",
            "Aldizkako azterketa gomendatua"
        ]
    else:
        return [
            "Ebaluazio periodontala",
            "Jarraipen estua"
        ]


def recomendacion_personalizada(factores):
    if "Inflamazioaren presentzia altua" in factores:
        return "Inflamazio markatzaileak jarraipen berezia behar du."
    return "Ez da arrisku faktore nabarmenik hauteman."
