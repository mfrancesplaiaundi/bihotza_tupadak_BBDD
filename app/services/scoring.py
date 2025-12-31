# app/services/scoring.py

def calcular_score(datos):
    """
    Recibe un objeto DatosEntrada (schemas.py)
    Devuelve:
      - score total
      - lista de factores que han influido
    """

    score = 0
    factores = []

    # ---------- FORMULARIO 1: AHO HIGIENEA ----------
    # ---------- 1.Galdera ----------
    cepillado = datos.formulario1.cepillado

    if cepillado == "bitan":
        score += 0
        factores.append("Hortzen garbiketa ona")

    elif cepillado == "behin":
        score += 0.5
        factores.append("Hortzen garbiketa hobetzekoa")
    
    elif cepillado == "gutxi":
        score += 1
        factores.append("Hortzen garbiketa oso eskasa, hobetzekoa")

# ---------- 2.Galdera ----------
    tiempo = datos.formulario1.tiempo

    if tiempo == "ondo":
        score += 0

    elif tiempo == "gutxi":
        score += 1
        factores.append("Denbora gehiago behar da hortzak garbitzen")
    
# ---------- 3.Galdera ----------
    eskuila = datos.formulario1.eskuila

    if eskuila == "elektrikoa":
        score += 0

    elif eskuila == "eskukoa":
        score += 0.5
        factores.append("Hobeto litzateke eskuil elektrikoa erabiltzea")
    
# ---------- 4.Galdera ----------
    osagarria = datos.formulario1.osagarria

    if osagarria == "bai":
        score += 0

    elif osagarria == "ez":
        score += 1
        factores.append("Hortz-tarteak garbitzeko metodo osagarriren bat (hortz-haria, eskuila interproximalak, silikonazko txotx edo “pick”-ak, irrigadorea, superfloss© moduko haria…) erabiltzea gomendatzen da")
    
# ---------- 5.Galdera ----------
    klinika = datos.formulario1.klinika

    if klinika == "seihilero":
        score += 0

    elif klinika == "urteanbat":
        score += 0.5
    
    elif klinika == "tartean":
        score += 1
    
    elif klinika == "bosturte":
        score += 1.5
        factores.append("Klinikara, gutzienez, urtean behin joatea gomendatzen da")


    # ---------- FORMULARIO 2 (cuando lo tengas) ----------

# ---------- 1.Galdera ----------
    kardiopatia = datos.formulario2.kardiopatia

    if kardiopatia == "ez":
        score += 0

    elif kardiopatia == "bai":
        score += 10
 # ---------- 2.Galdera ----------
    zianosia = datos.formulario2.zianosia

    if zianosia == "ez":
        score += 0

    elif zianosia == "bai":
        score += 5

# ---------- 3.Galdera ----------
    ebakuntza = datos.formulario2.ebakuntza

    if ebakuntza == "ez":
        score += 0
    elif ebakuntza == "bat":
        score += 1
    elif ebakuntza == "bi":
        score += 3
    elif ebakuntza == "hiru":
        score += 5

 # ---------- 4.Galdera ----------
    protesia = datos.formulario2.protesia

    if protesia == "ez":
        score += 0

    elif protesia == "bai":
        score += 5

 # ---------- 5.Galdera ----------
    endokarditis = datos.formulario2.endokarditis

    if endokarditis == "ez":
        score += 0

    elif endokarditis == "bai":
        score += 5

 # ---------- 6.Galdera ----------
    diabetes = datos.formulario2.diabetes

    if diabetes == "ez":
        score += 0
    elif diabetes == "bat":
        score += 3
    elif diabetes == "bi":
        score += 5

 # ---------- 7.Galdera ----------
    erretzailea = datos.formulario2.erretzailea

    if erretzailea == "ez":
        score += 0

    elif erretzailea == "bai":
        score += 5

# ---------- 8.Galdera ----------
    menpekotasuna = datos.formulario2.menpekotasuna

    if menpekotasuna == "ez":
        score += 0
    elif menpekotasuna == "bat":
        score += 5
    elif menpekotasuna == "bi":
        score += 10
    elif menpekotasuna == "hiru":
        score += 20
    # ---------- DATOS ANALÍTICOS ----------
     
    # ---------- IL-6 ----------
    if datos.il6_value <= 5:
        score += 0
        factores.append("Inflamazioaren presentzia baxua")
    elif 5 < datos.il6_value <= 10:
        score += 10
        factores.append("Inflamazioaren presentzia ertaina")
    elif datos.il6_value > 10:
        score += 20
        factores.append("Inflamazioaren presentzia altua")

    # ---------- Plaka Indizea ----------
    if datos.dental_plaque <= 1:
        score += 0
        factores.append("Higiene maila: Ona")
    elif 1 < datos.dental_plaque <= 2:
        score += 5
        factores.append("Higiene maila: Bitartekoa")
    elif 2 < datos.dental_plaque <= 3:
        score += 10
        factores.append("Odontologoa bisitatu, aho-hortz higiene inguruko neurri egokiak aktibatzeko")
    elif datos.dental_plaque > 3:
        score += 15
        factores.append("Odontologoa bisitatu, aho-hortz higiene inguruko neurri egokiak aktibatzeko")

    return score, factores
