
 async function login() {

  const user = document.getElementById("user").value;
  const pass = document.getElementById("pass").value;

  const res = await fetch("/api/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      username: user,
      password: pass
    })
  });
  if (await !res.ok) {
    alert("Sarbide okerra");
    return;
  }
  console.log("Resultado:", res);

  const data = await res.json();
  console.log("Respuesta JSON:", data);

  localStorage.setItem("token", data.access_token);
  localStorage.setItem("role", data.role);

  if (data.role === "researcher") {
    mostrar("formAnalitica");
  } else if (data.role === "patient") {
    mostrar("form1");
  }
}

function mostrar(id) {

    const secciones = ["login", "form1", "form2", "formAnalitica", "resultados"];

    secciones.forEach(sec => {
        const elemento = document.getElementById(sec);
        if (elemento) {
            elemento.style.display = "none";
            elemento.classList.remove("visible");
        }
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
async function guardarDatosClinicos() {

  const token = localStorage.getItem("token");
  if (!token) {
    alert("Ez zaude identifikatuta");
    mostrar("login");
    return;
  }

  const patientCode = document.getElementById("patientCode").value;

  const res = await fetch(
    `/api/researcher/datos-clinicos/${patientCode}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({
        il6: parseFloat(document.getElementById("il6").value),
        indice_placa: parseFloat(document.getElementById("placa").value),
        observaciones: document.getElementById("observaciones").value
      })
    }
  );

  if (!res.ok) {
    alert("Errorea datu klinikoak gordetzean");
    return;
  }

  alert("Datu klinikoak behar bezala gordeta");

  // opcional: limpiar formulario
  document.getElementById("il6").value = "";
  document.getElementById("placa").value = "";
  document.getElementById("observaciones").value = "";
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

document.addEventListener("DOMContentLoaded", () => {
  mostrar("login");
});