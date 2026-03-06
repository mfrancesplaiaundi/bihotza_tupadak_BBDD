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

class DatosEntrada(BaseModel):
    formulario1: Formulario1
    formulario2: Formulario2
    il6_value: float
    dental_plaque: float
    tooth_count: int
    ph_value: float
    

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
    ph_value: float
    tooth_count: int
    observations: str | None = None
