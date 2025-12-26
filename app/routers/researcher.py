# app/routers/researcher.py
import os
import hmac

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.auth import create_access_token
from app.schemas import DatosClinicos
from app.models import Patient, Biomarker
from app.database import get_db


router = APIRouter(prefix="/api/researcher", tags=["researcher"])

class ResearcherLogin(BaseModel):
    username: str
    password: str

""" @router.post("/login")
def researcher_login(data: ResearcherLogin):
    expected_user = os.getenv("RESEARCHER_USER", "investigador")
    expected_pass = os.getenv("RESEARCHER_PASS", "investigador")

    user_ok = hmac.compare_digest(data.username, expected_user)
    pass_ok = hmac.compare_digest(data.password, expected_pass)

    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token({"role": "researcher"})
    return {"access_token": token, "token_type": "bearer"} """

@router.post("/datos-clinicos/{patient_code}")
def guardar_datos_clinicos(
    patient_code: str,
    data: DatosClinicos,
    db: Session = Depends(get_db),
    _payload: dict = Depends(require_role("researcher")),
):
    patient = db.query(Patient).filter(Patient.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    existing = (
        db.query(Biomarker)
        .filter(Biomarker.patient_id == patient.id)
        .order_by(Biomarker.created_at.desc())
        .first()
    )

    if existing:
        existing.il6 = data.il6
        existing.indice_placa = data.indice_placa
        existing.observaciones = data.observaciones
    else:
        clinicos = Biomarker(
            patient_id=patient.id,
            il6=data.il6,
            indice_placa=data.indice_placa,
            observaciones=data.observaciones,
        )
        db.add(clinicos)

    db.commit()
    return {"status": "datos_clinicos_guardados"}

