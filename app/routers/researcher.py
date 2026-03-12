# app/routers/researcher.py
import csv
from io import StringIO
import os
import hmac
import secrets, hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import require_role
from app.auth import create_access_token
from app.schemas import BiomarkerCreate, DatosEntrada
from app.models import Patient, Biomarker, Questionnaire
from app.database import get_db
from app.services.scoring_parcial import calcular_scores_parciales


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

@router.get("/estadisticas")
def estadisticas_pacientes(
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    pacientes = db.query(Patient).all()
    il6_m0k0 = []
    il6_m0k1 = []
    il6_m1k0 = []
    il6_m1k1 = []
    plaka_m0k0 = []
    plaka_m0k1 = []
    plaka_m1k0 = []
    plaka_m1k1 = []
    hig_m0k0 = []
    hig_m0k1 = []
    hig_m1k0 = []
    hig_m1k1 = []
    kar_m0k0 = []
    kar_m0k1 = []
    kar_m1k0 = []
    kar_m1k1 = []
    men_m1k0 = []
    men_m1k1 = []
    resultado = []


    for p in pacientes:
        b = (
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

        if not q or not b:
            raise HTTPException(400, "Datu guztiak ez daude eskuragarri")
        
        # Mirar en qué grupo meter cada paciente, para eso mirar respuestas de los formularios

        datos = DatosEntrada(
            formulario1=q.answers["formulario1"],
            formulario2=q.answers["formulario2"],
            il6_value=b.il6_value,
            dental_plaque=b.dental_plaque,
            tooth_count=b.tooth_count,
            ph_value=b.ph_value        
        )

        score_f1,  score_f2, score_f2_q8 = calcular_scores_parciales(datos)

        f2 = q.answers.get("formulario2", {})

        if f2.get("kardiopatia") == "bai":
            if f2.get("menpekotasuna") in ("bat", "bi", "hiru"):
                il6_m1k1.append(b.il6_value)
                plaka_m1k1.append(b.dental_plaque)
                hig_m1k1.append(float(score_f1))
                kar_m1k1.append(float(score_f2))
                men_m1k1.append(float(score_f2_q8))        
            else:
                il6_m0k1.append(b.il6_value)
                plaka_m0k1.append(b.dental_plaque)
                hig_m0k1.append(float(score_f1))
                kar_m0k1.append(float(score_f2))
        elif f2.get("kardiopatia") == "ez":
            if f2.get("menpekotasuna") in ("bat", "bi", "hiru"):
                il6_m1k0.append(b.il6_value)
                plaka_m1k0.append(b.dental_plaque)
                hig_m1k0.append(float(score_f1))
                kar_m1k0.append(float(score_f2))
                men_m1k0.append(float(score_f2_q8))        
            else:
                il6_m0k0.append(b.il6_value)
                plaka_m0k0.append(b.dental_plaque)
                hig_m0k0.append(float(score_f1))
                kar_m0k0.append(float(score_f2))

        
        # Medias de los arrays
        
    il6_m1k1_media= sum(il6_m1k1)/len(il6_m1k1)        
    plaka_m1k1_media= sum(plaka_m1k1)/len(plaka_m1k1)        
    hig_m1k1_media= sum(hig_m1k1)/len(hig_m1k1)        
    kar_m1k1_media= sum(kar_m1k1)/len(kar_m1k1)        
    men_m1k1_media= sum(men_m1k1)/len(men_m1k1)

    il6_m0k1_media= sum(il6_m0k1)/len(il6_m0k1)        
    plaka_m0k1_media= sum(plaka_m0k1)/len(plaka_m0k1)        
    hig_m0k1_media= sum(hig_m0k1)/len(hig_m0k1)        
    kar_m0k1_media= sum(kar_m0k1)/len(kar_m0k1)        

    il6_m1k0_media= sum(il6_m1k0)/len(il6_m1k0)        
    plaka_m1k0_media= sum(plaka_m1k0)/len(plaka_m1k0)        
    hig_m1k0_media= sum(hig_m1k0)/len(hig_m1k0)        
    kar_m1k0_media= sum(kar_m1k0)/len(kar_m1k0)        
    men_m1k0_media= sum(men_m1k0)/len(men_m1k0)

    il6_m0k0_media= sum(il6_m0k0)/len(il6_m0k0)        
    plaka_m0k0_media= sum(plaka_m0k0)/len(plaka_m0k0)        
    hig_m0k0_media= sum(hig_m0k0)/len(hig_m0k0)        
    kar_m0k0_media= sum(kar_m0k0)/len(kar_m0k0)  
    
    # Habría que devolver directamente los valores de las medias

    return {"il6_m1k1_media": il6_m1k1_media,
        "plaka_m1k1_media": plaka_m1k1_media,
        "hig_m1k1_media": hig_m1k1_media,
        "kar_m1k1_media": kar_m1k1_media,
        "men_m1k1_media": men_m1k1_media,

        "il6_m0k1_media": il6_m0k1_media,
        "plaka_m0k1_media": plaka_m0k1_media,
        "hig_m0k1_media": hig_m0k1_media,
        "kar_m0k1_media": kar_m0k1_media,

        "il6_m1k0_media": il6_m1k0_media,
        "plaka_m1k0_media": plaka_m1k0_media,
        "hig_m1k0_media": hig_m1k0_media,
        "kar_m1k0_media": kar_m1k0_media,
        "men_m1k0_media": men_m1k0_media,
        
        "il6_m0k0_media": il6_m0k0_media,
        "plaka_m0k0_media": plaka_m0k0_media,
        "hig_m0k0_media": hig_m0k0_media,
        "kar_m0k0_media": kar_m0k0_media,

    }

@router.get("/exportar")
def estadisticas_pacientes(
    db: Session = Depends(get_db),
    _=Depends(require_role("researcher"))
):
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "patient_id",
        "il6_value",
        "dental_plaque",
        "kardiopatia",
        "menpekotasuna",
        "score_f1_q1_q5",
        "score_f2_q2_q5",
        "score_f2_q8"
    ])
    
    pacientes = db.query(Patient).all()


    for p in pacientes:
        b = (
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

        if not q or not b:
            raise HTTPException(400, "Datu guztiak ez daude eskuragarri")
        
        # Mirar en qué grupo meter cada paciente, para eso mirar respuestas de los formularios

        datos = DatosEntrada(
            formulario1=q.answers["formulario1"],
            formulario2=q.answers["formulario2"],
            il6_value=b.il6_value,
            dental_plaque=b.dental_plaque,
            tooth_count=b.tooth_count,
            ph_value=b.ph_value        
        )

        score_f1,  score_f2, score_f2_q8 = calcular_scores_parciales(datos)

        f2 = q.answers.get("formulario2", {})

        if f2.get("menpekotasuna")in ("bat","bi","hiru"):
            menpekotasuna="bai"
        else:
            menpekotasuna="ez"

        writer.writerow([
            p.patient_code,
            b.il6_value,
            b.dental_plaque,
            f2.get("kardiopatia"),
            menpekotasuna,
            score_f1,
            score_f2,
            score_f2_q8
        ])
        
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jamovi_export.csv"}
    )
 
    