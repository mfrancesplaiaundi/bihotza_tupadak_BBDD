function mostrarFormularioInicial() {

    document.querySelector(".imagen").classList.add("oculto");
    document.querySelector(".hero").classList.add("oculto");

    mostrar("form1");
}

function mostrar(id) {
    
    const secciones = ["form1", "form2", "formAnalitica", "resultados"];

    secciones.forEach(sec => {
        const elemento = document.getElementById(sec);
        elemento.style.display = "none";
        elemento.classList.remove("visible");
    });

    const seleccionado = document.getElementById(id);
    seleccionado.style.display = "block";

    setTimeout(() => {
        seleccionado.classList.add("visible");
    }, 20);
}

function recogerDatos() {
    return {
        formulario1: {
            cepillado: document.getElementById("cepillado").value,
            tiempo: document.getElementById("tiempo").value,
            eskuila: document.getElementById("eskuila").value,
            osagarria: document.getElementById("osagarria").value,
            klinika: document.getElementById("klinika").value
        },
        formulario2: {
            kardiopatia: document.getElementById("kardiopatia").value,
            zianosia: document.getElementById("zianosia").value,
            ebakuntza: document.getElementById("ebakuntza").value,
            protesia: document.getElementById("protesia").value,
            endokarditis: document.getElementById("endokarditis").value,
            diabetes: document.getElementById("diabetes").value,
            erretzailea: document.getElementById("erretzailea").value,
            menpekotasuna: document.getElementById("menpekotasuna").value,
        },
        il6: parseFloat(document.getElementById("il6").value),
        indice_placa: parseFloat(document.getElementById("indice_placa").value)
    };
}

function enviarDatos() {
    const datos = recogerDatos();

    fetch("/api/calcular", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos)
    })
    .then(res => res.json())
    .then(respuesta => {
        mostrar("resultados");
        document.querySelector(".score-ejemplo").innerHTML =
            `<strong>${respuesta.score} puntu</strong>`;

        document.querySelectorAll(".indicacion")[0].innerText =
            respuesta.recomendaciones_generales.join(". ");

        document.querySelectorAll(".indicacion")[1].innerText =
            respuesta.recomendacion_personalizada.join("\n ");;
    });
}

