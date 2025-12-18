# app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.schemas import DatosEntrada
from app.services.scoring import calcular_score

app = FastAPI(title="Bihotza Taupadak")

# Archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Plantillas HTML
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------- API ----------

@app.post("/api/calcular")
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
