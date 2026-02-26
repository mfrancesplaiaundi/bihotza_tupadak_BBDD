# app/routers/researcher.py
import os
import hmac
import secrets, hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.auth import create_access_token
from app.schemas import BiomarkerCreate
from app.models import Patient, Biomarker, Questionnaire
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


@router.post("/patients")
def crear_paciente(
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    # Código y PIN aleatorios
    patient_code = "P-" + secrets.token_hex(3).upper()
    pin = secrets.token_hex(2)

    pin_hash = hashlib.sha256(pin.encode()).hexdigest()

    paciente = Patient(
        patient_code=patient_code,
        pin_hash=pin_hash
    )

    db.add(paciente)
    db.commit()

    return {
        "patient_code": patient_code,
        "pin": pin
    }

@router.get("/patients")
def listar_pacientes_con_datos(
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    pacientes = db.query(Patient).all()
    resultado = []

    for p in pacientes:
        clinico = (
            db.query(Biomarker)
            .filter(Biomarker.patient_id == p.id)
            .order_by(Biomarker.measured_at.desc())
            .first()
        )

        q = (
        db.query(Questionnaire)
        .filter(Questionnaire.patient_id == p.id)
        .order_by(Questionnaire.created_at.desc())
        .first()
        )

        resultado.append({
            "patient_code": p.patient_code,
            "patient_id": p.id,
            "created_at": p.created_at,
            "il6_value": clinico.il6_value if clinico else None,
            "dental_plaque": clinico.dental_plaque if clinico else None,
            "tooth_count": clinico.tooth_count if clinico else None,
            "ph_value": clinico.ph_value if clinico else None,
            "observations": clinico.observations if clinico else None,
            "measured_at": clinico.measured_at if clinico else None,
            "has_questionnaire": q is not None,
            "last_questionnaire_at": q.created_at if q else None

        })

    return resultado

@router.get("/patients/select")
def pacientes_para_select(
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    pacientes = db.query(Patient).order_by(Patient.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "patient_code": p.patient_code
        }
        for p in pacientes
    ]

@router.post("/biomarkers")
def guardar_biomarcador(
    data: BiomarkerCreate,  
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    biomarker = Biomarker(
        patient_id=data.patient_id,
        il6_value=data.il6_value,
        dental_plaque=data.dental_plaque,
        tooth_count=data.tooth_count,
        ph_value=data.ph_value,
        observations=data.observations
    )

    db.add(biomarker)
    db.commit()
    return {"status": "ok"}


@router.post("/patients/{patient_id}/reset-pin")
def reset_pin_paciente(
    patient_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    nuevo_pin = secrets.token_hex(2)
    patient.pin_hash = hashlib.sha256(nuevo_pin.encode()).hexdigest()

    db.commit()

    return {
        "patient_code": patient.patient_code,
        "new_pin": nuevo_pin,
        "message": "PIN berria sortu da. Erabiltzaileari eman."
    }