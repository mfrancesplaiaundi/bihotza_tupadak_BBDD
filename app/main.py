# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from app.schemas import DatosEntrada, DatosFormulario, LoginRequest
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import hashlib, os
from app.routers import researcher, patient
from app.database import engine
from app.models import Base

from app.database import get_db
from app.models import Patient
from app.auth import create_access_token
from pydantic import BaseModel

from app.services.scoring import calcular_score

app = FastAPI(title="Bihotza Taupadak")


Base.metadata.create_all(bind=engine)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Plantillas HTML
templates = Jinja2Templates(directory="app/templates")

app.include_router(researcher.router)
app.include_router(patient.router)


@app.post("/api/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    #  ¿Es investigador?
    if data.username == "ikertzailea" and data.password == "bihotzataupaka2026!":
        token = create_access_token({"role": "researcher"})
        return {"access_token": token, "role": "researcher"}

    #  ¿Es paciente? (username = patient_code)
    patient = db.query(Patient)\
        .filter_by(patient_code=data.username)\
        .first()

    if patient:
        pin_hash = hashlib.sha256(data.password.encode()).hexdigest()
        if patient.pin_hash == pin_hash:
            token = create_access_token({
                "role": "patient",
                "patient_id": patient.id
            })
            return {"access_token": token, "role": "patient"}

    # 3️⃣ Nada válido
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------- API ----------

""" @app.post("/api/calcular")
def calcular(datos: DatosEntrada):

    score, factores = calcular_score(datos)

    # Clasificación
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
 """




