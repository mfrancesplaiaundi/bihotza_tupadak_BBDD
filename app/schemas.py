# app/schemas.py
from pydantic import BaseModel

class Formulario1(BaseModel):
    cepillado: str
    tiempo: str
    eskuila: str
    osagarria: str
    klinika: str

class Formulario2(BaseModel):
    kardiopatia: str
    zianosia: str
    ebakuntza: str
    protesia: str
    endokarditis: str
    diabetes: str
    erretzailea: str
    menpekotasuna: str


class DatosFormulario(BaseModel):
    formulario1: Formulario1
    formulario2: Formulario2

class DatosClinicos(BaseModel):
    il6: float
    indice_placa: float
    observaciones: str | None = None

class DatosEntrada(BaseModel):
    formulario1: Formulario1
    formulario2: Formulario2
    il6: float
    indice_placa: float

class LoginPaciente(BaseModel):
    patient_code: str
    pin: str

class LoginRequest(BaseModel):
    username: str
    password: str

class BiomarkerCreate(BaseModel):
    patient_id: str
    il6_value: float
    dental_plaque: float
    observations: str | None = None
