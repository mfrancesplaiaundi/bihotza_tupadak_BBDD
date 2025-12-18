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


class DatosEntrada(BaseModel):
    formulario1: Formulario1
    formulario2: Formulario2
    il6: float
    indice_placa: float
