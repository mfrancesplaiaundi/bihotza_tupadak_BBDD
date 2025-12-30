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
from app.schemas import DatosClinicos, BiomarkerCreate
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

        resultado.append({
            "patient_code": p.patient_code,
            "created_at": p.created_at,
            "il6_value": clinico.il6_value if clinico else None,
            "dental_plaque": clinico.dental_plaque if clinico else None,
            "observations": clinico.observations if clinico else None,
            "measured_at": clinico.measured_at if clinico else None
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
        observations=data.observations
    )

    db.add(biomarker)
    db.commit()
    return {"status": "ok"}
