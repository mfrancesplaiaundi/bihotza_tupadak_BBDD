# app/services/scoring.py

def calcular_scores_parciales(datos):
    """
    Recibe un objeto DatosEntrada (schemas.py)
    Devuelve:
      - scores parciales
    """

    score_f1 = 0
    score_f2 = 0
    score_f2_q8 = 0
   

    # ---------- FORMULARIO 1: AHO HIGIENEA ----------
    # ---------- 1.Galdera ----------
    cepillado = datos.formulario1.cepillado

    if cepillado == "bitan":
        score_f1 += 0

    elif cepillado == "behin":
        score_f1 += 0.5
    
    elif cepillado == "gutxi":
        score_f1 += 1

# ---------- 2.Galdera ----------
    tiempo = datos.formulario1.tiempo

    if tiempo == "ondo":
        score_f1 += 0

    elif tiempo == "gutxi":
        score_f1 += 1
    
# ---------- 3.Galdera ----------
    eskuila = datos.formulario1.eskuila

    if eskuila == "elektrikoa":
        score_f1 += 0

    elif eskuila == "eskukoa":
        score_f1 += 0.5
    
# ---------- 4.Galdera ----------
    osagarria = datos.formulario1.osagarria

    if osagarria == "bai":
        score_f1 += 0

    elif osagarria == "ez":
        score_f1 += 1
    
# ---------- 5.Galdera ----------
    klinika = datos.formulario1.klinika

    if klinika == "seihilero":
        score_f1 += 0

    elif klinika == "urteanbat":
        score_f1 += 0.5
    
    elif klinika == "tartean":
        score_f1 += 1
    
    elif klinika == "bosturte":
        score_f1 += 1.5


    # ---------- FORMULARIO 2 (cuando lo tengas) ----------


 # ---------- 2.Galdera ----------
    zianosia = datos.formulario2.zianosia

    if zianosia == "ez":
        score_f2 += 0

    elif zianosia == "bai":
        score_f2 += 5

# ---------- 3.Galdera ----------
    ebakuntza = datos.formulario2.ebakuntza

    if ebakuntza == "ez":
        score_f2 += 0
    elif ebakuntza == "bat":
        score_f2 += 1
    elif ebakuntza == "bi":
        score_f2 += 3
    elif ebakuntza == "hiru":
        score_f2 += 5

 # ---------- 4.Galdera ----------
    protesia = datos.formulario2.protesia

    if protesia == "ez":
        score_f2 += 0

    elif protesia == "bai":
        score_f2 += 5

 # ---------- 5.Galdera ----------
    endokarditis = datos.formulario2.endokarditis

    if endokarditis == "ez":
        score_f2 += 0

    elif endokarditis == "bai":
        score_f2 += 5




# ---------- 8.Galdera ----------
    menpekotasuna = datos.formulario2.menpekotasuna

    if menpekotasuna == "ez":
        score_f2_q8 += 0
    elif menpekotasuna == "bat":
        score_f2_q8 += 5
    elif menpekotasuna == "bi":
        score_f2_q8 += 10
    elif menpekotasuna == "hiru":
        score_f2_q8 += 20


    return score_f1, score_f2, score_f2_q8
