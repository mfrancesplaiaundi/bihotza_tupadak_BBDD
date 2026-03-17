from app.rag.sources import SOURCES

def _tags_desde_formularios(perfil: dict) -> set[str]:
    tags: set[str] = set()

    f1 = perfil.get("formulario1", {}) or {}
    f2 = perfil.get("formulario2", {}) or {}

    score = float(perfil.get("score", 0) or 0)

    dientes = float(perfil.get("dientes", 0) or 0)

    ph = float(perfil.get("ph", 0) or 0)

    # --- Formulario 1 (hábitos) ---
    cepillado = f1.get("cepillado")
    if cepillado in ("behin", "gutxi"):
        tags.update(["cepillado", "habitos", "tecnica"])

    tiempo = f1.get("tiempo")
    if tiempo == "gutxi":
        tags.update(["cepillado", "habitos"])

    eskuila = f1.get("eskuila")
    if eskuila == "eskukoa":
        tags.update(["electrico", "cepillado"])

    osagarria = f1.get("osagarria")
    if osagarria == "ez":
        tags.update(["accesorio", "interdental", "hilo", "habitos"])

    klinika = f1.get("klinika")
    if klinika in ("bosturte", "tartean"):
        tags.update(["revision", "dentista", "prevencion"])

    # --- Formulario 2 (riesgos) ---
    # diabetes en tu form2: "ez" / "bat" / "bi"
    diabetes = f2.get("diabetes")
    if diabetes in ("bat", "bi"):
        tags.update(["diabetes", "salud_bucal", "encias"])

    erretzailea = f2.get("erretzailea")
    if erretzailea == "bai":
        tags.update(["tabaco", "encias", "periodontitis"])

    kardiopatia = f2.get("kardiopatia")
    if kardiopatia == "bai":
        tags.update(["corazon", "cardio", "prevencion"])

    # --- Score / nivel ---
    if score >= 50:
        tags.update(["periodontitis", "refuerzo", "habitos"])
    if score >= 75:
        tags.update(["tratamiento", "profundizacion"])

    # --- Dientes ---
    if dientes != 0:
        tags.update(["perdida dental", "periodontitis"])

    # --- pH ---
    if ph <= 6.5:
        tags.update(["ph", "saliva", "salud_oral"])

    return tags


def recomendar_links(perfil: dict, max_links: int = 8, lang: str = "es") -> list[dict]:
    tags = _tags_desde_formularios(perfil)

    # 1) candidatos por idioma y tags
    candidatos = []
    for s in SOURCES:
        if s.get("lang") != lang:
            continue
        if tags.intersection(set(s.get("tags", []))):
            candidatos.append(s)

    # 2) ordenar: preferimos video y web antes que pdf
    prioridad_tipo = {"video": 0, "web": 1, "pdf": 2}
    candidatos.sort(key=lambda x: prioridad_tipo.get(x.get("type", "web"), 9))

    # 3) deduplicar por URL y cortar
    seen = set()
    result = []
    for s in candidatos:
        url = s["url"]
        if url in seen:
            continue
        seen.add(url)
        result.append({"title": s.get("title", url), "url": url})
        if len(result) >= max_links:
            break

    # si no hay suficientes, meter 1–2 “general”
    if len(result) < max_links:
        for s in SOURCES:
            if s.get("lang") == lang and "general" in s.get("tags", []):
                if s["url"] not in seen:
                    result.append({"title": s.get("title", s["url"]), "url": s["url"]})
                    seen.add(s["url"])
                    if len(result) >= max_links:
                        break

    return result


def recomendar_sources(perfil: dict, max_sources: int = 3, lang: str = "es") -> list[dict]:
 
    tags = _tags_desde_formularios(perfil)

    candidatos = []
    for s in SOURCES:
        if s.get("lang") != lang:
            continue
        if s.get("type") != "pdf":
            continue
        if tags.intersection(set(s.get("tags", []))):
            candidatos.append(s)

    # dedupe
    seen = set()
    out = []
    for s in candidatos:
        if s["url"] in seen:
            continue
        seen.add(s["url"])
        out.append({"title": s.get("title", s["url"]), "url": s["url"]})
        if len(out) >= max_sources:
            break

    return out

def buscar_fuentes_por_tags(
    tags: set[str],
    max_items: int = 3,
    lang: str = "es",
    source_type: str | None = None
) -> list[dict]:
    candidatos = []

    for s in SOURCES:
        if s.get("lang") != lang:
            continue

        if source_type and s.get("type") != source_type:
            continue

        source_tags = set(s.get("tags", []))
        coincidencias = tags.intersection(source_tags)

        if coincidencias:
            candidatos.append((len(coincidencias), s))

    # ordenar por nº de coincidencias descendente
    candidatos.sort(key=lambda x: x[0], reverse=True)

    seen = set()
    out = []

    for _, s in candidatos:
        url = s["url"]
        if url in seen:
            continue
        seen.add(url)

        out.append({
            "id": s.get("id"),
            "title": s.get("title", url),
            "url": url,
            "lang": s.get("lang"),
            "type": s.get("type"),
            "tags": s.get("tags", [])
        })

        if len(out) >= max_items:
            break

    return out

def tags_para_recomendacion(rec: dict) -> set[str]:
    tag = rec.get("tag")
    tags = set()

    if tag:
        tags.add(tag)

    mapa_relaciones = {
        "ph": {"ph", "saliva", "salud_oral"},
        "cepillado": {"cepillado", "habitos", "tecnica"},
        "higiene_interdental": {"interdental", "hilo", "accesorio", "habitos"},
        "placa": {"placa", "higiene", "encias", "prevencion"},
        "inflamacion": {"inflamacion", "encias", "periodontitis", "salud_oral"},
        "diabetes": {"diabetes", "salud_bucal", "encias"},
        "tabaco": {"tabaco", "encias", "periodontitis"},
        "corazon": {"corazon", "cardio", "prevencion"}
    }

    tags.update(mapa_relaciones.get(tag, set()))
    return tags