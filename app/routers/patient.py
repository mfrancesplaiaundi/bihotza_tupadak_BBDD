from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Patient, Questionnaire, Biomarker
from schemas import PatientLogin, QuestionnaireCreate
from auth import create_token, get_current_user
from services.scoring import calculate_score
import hashlib

router = APIRouter(prefix="/patient", tags=["patient"])

@router.post("/login")
def login(data: PatientLogin, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter_by(patient_code=data.patient_code).first()
    if not patient:
        raise HTTPException(401, "Credenciales incorrectas")

    if patient.pin_hash != hashlib.sha256(data.pin.encode()).hexdigest():
        raise HTTPException(401, "Credenciales incorrectas")

    token = create_token({"role": "patient", "patient_id": patient.id})
    return {"access_token": token}

@router.post("/questionnaire")
def save_questionnaire(
    data: QuestionnaireCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["role"] != "patient":
        raise HTTPException(403)

    q = Questionnaire(
        patient_id=user["patient_id"],
        answers=data.answers
    )
    db.add(q)
    db.commit()
    return {"status": "guardado"}
@router.post("/process")

def process(user=Depends(get_current_user), db: Session = Depends(get_db)):
    patient_id = user["patient_id"]

    q = db.query(Questionnaire).filter_by(patient_id=patient_id)\
        .order_by(Questionnaire.created_at.desc()).first()
    il6 = db.query(Biomarker).filter_by(patient_id=patient_id)\
        .order_by(Biomarker.measured_at.desc()).first()

    if not q or not il6:
        raise HTTPException(400, "Datos incompletos")

    score, recs = calculate_score(q.answers, il6.il6_value)
    return {"score": score, "recommendations": recs}
