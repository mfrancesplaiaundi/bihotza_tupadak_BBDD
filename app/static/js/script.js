
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


  const data = await res.json();


  sessionStorage.setItem("token", data.access_token);
  sessionStorage.setItem("role", data.role);

  if (data.role === "researcher") {
    document.getElementById("logoutBtn").style.display = "inline-block";
    mostrar("investigador");
  } else if (data.role === "patient") {
    document.getElementById("logoutBtn").style.display = "inline-block";
    mostrar("menuPaciente");
  }
  
}

function logout() {
  sessionStorage.removeItem("token");
  sessionStorage.removeItem("role");

  // opcional: limpiar selects / formularios
  document.querySelectorAll("input, textarea").forEach(el => el.value = "");

  // ocultar todo y volver al login
  mostrar("login");

  // ocultar botón
  document.getElementById("logoutBtn").style.display = "none";
}


function mostrar(id) {

    const secciones = ["login","resultadosPaciente","menuPaciente","analiticasPaciente", "form1", "form2", "formAnalitica", "resultados", "registrar", "investigador","listaPacientes","estadisticas"];

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

function atraslimpiar(){
document.getElementById("resultadoPaciente").innerText="";
mostrar('investigador');
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

document.addEventListener("DOMContentLoaded", () => {
  mostrar("login");
});

async function registrarPaciente() {
  const token = sessionStorage.getItem("token");

  const res = await fetch("/api/researcher/patients", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  if (!res.ok) {
    alert("Errorea pazientea sortzean");
    return;
  }

  const data = await res.json();

  document.getElementById("resultadoPaciente").innerText =
    `Kodea: ${data.patient_code}\nPIN-a: ${data.pin}`;
}

async function cargarPacientes() {
  const token = sessionStorage.getItem("token");

  const res = await fetch("/api/researcher/patients", {
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  if (!res.ok) {
    alert("Errorea pazienteak kargatzean");
    return;
  }

  const pacientes = await res.json();
  const tbody = document.getElementById("tablaPacientes");
  tbody.innerHTML = "";

  pacientes.forEach(p => {
    const fila = document.createElement("tr");

    fila.innerHTML = `
      <td>${p.patient_code}</td>
      <td>${new Date(p.created_at).toLocaleDateString()}</td>
      <td>${p.il6_value ?? "-"}</td>
      <td>${p.dental_plaque ?? "-"}</td>
      <td>${p.tooth_count ?? "-"}</td>
      <td>${p.ph_value ?? "-"}</td>
      <td>${p.observations ?? "-"}</td>
      <td>${p.measured_at ? new Date(p.measured_at).toLocaleDateString() : "-"}</td>
      <td>${p.has_questionnaire ? "✔" : "✖"}</td>
      <td>${p.last_questionnaire_at? new Date(p.last_questionnaire_at).toLocaleDateString()   : "-"}</td>
      <td><button onclick="resetPinPaciente('${p.patient_id}')">Reset PIN</button></td>
    `;

    tbody.appendChild(fila);
  });
}

async function cargarPacientesSelect() {
  const token = sessionStorage.getItem("token");

  const res = await fetch("/api/researcher/patients/select", {
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  if (!res.ok) {
    alert("Errorea pazienteak kargatzean");
    return;
  }

  const pacientes = await res.json();
  const select = document.getElementById("patientSelect");

  select.innerHTML = '<option value="">-- Hautatu pazientea --</option>';

  pacientes.forEach(p => {
    const option = document.createElement("option");
    option.value = p.id;           
    option.textContent = p.patient_code;
    select.appendChild(option);
  });
}

function mostrarDatosClinicos() {
  mostrar("formAnalitica");
  cargarPacientesSelect();
}

async function guardarDatosClinicos() {
  const token = sessionStorage.getItem("token");

  const payload = {
    patient_id: document.getElementById("patientSelect").value,
    il6_value: parseFloat(document.getElementById("il6").value),
    dental_plaque: parseFloat(document.getElementById("indice_placa").value),
    tooth_count: document.getElementById("dientes").value,
    ph_value: parseFloat(document.getElementById("ph").value),
    observations: document.getElementById("observaciones").value
  };

  if (!payload.patient_id) {
    alert("Hautatu paziente bat");
    return;
  }

  const res = await fetch("/api/researcher/biomarkers", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    alert("Errorea datuak gordetzean");
    return;
  }

  alert("Datu klinikoak gorde dira");

  document.getElementById("il6").value="";
  document.getElementById("indice_placa").value="";
  document.getElementById("observaciones").value="";

  mostrar("investigador");
}

document.addEventListener("DOMContentLoaded", () => {
  const token = sessionStorage.getItem("token");
  if (!token) {
    mostrar("login");
  } else {
    // opcional: restaurar vista según rol
    const role = sessionStorage.getItem("role");
    document.getElementById("logoutBtn").style.display = "inline-block";

    if (role === "researcher") mostrar("investigador");
    if (role === "patient") mostrar("menuPaciente");
  }
});

async function mostrarAnaliticasPaciente() {
  const token = sessionStorage.getItem("token");

  const res = await fetch("/api/patient/biomarkers", {
    headers: { "Authorization": "Bearer " + token }
  });

  const data = await res.json();
  mostrar("analiticasPaciente");

  document.getElementById("il6Paciente").innerText = data.il6_value ?? "-";
  document.getElementById("placaPaciente").innerText = data.dental_plaque ?? "-";
  document.getElementById("dientesPaciente").innerText = data.tooth_count ?? "-";
  document.getElementById("phPaciente").innerText = data.ph_value ?? "-";
  document.getElementById("fechaPaciente").innerText =
    data.measured_at ? new Date(data.measured_at).toLocaleString() : "-";
}

async function mostrarResultadosPaciente() {
  const token = sessionStorage.getItem("token");

  const res = await fetch("/api/patient/resultados", {
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  if (res.status === 401 || res.status === 403) {
    logout();
    alert("Sesión caducada. Vuelve a iniciar sesión.");
  return;
  }


  if (!res.ok) {
    alert("Ezin dira emaitzak kalkulatu. Datu guztiak ez daude eskuragarri.");
    return;
  }

  const data = await res.json();

  // Mostrar sección
  mostrar("resultadosPaciente");

  // Pintar score y nivel
  document.getElementById("scorePaciente").innerText = data.score;
  document.getElementById("nivelPaciente").innerText = data.nivel;
  document.getElementById("mensajeGeneral").innerText = data.mensaje_general;


  // Pintar factores
  const listaFactores = document.getElementById("factoresPaciente");
  listaFactores.innerHTML = "";

  data.factores.forEach(f => {
    if (f.includes("Endokarditis")) {
      const li = document.createElement("li");
      li.textContent = f;
      listaFactores.appendChild(li);
    }
    if (f.includes("pH azidoa")) {
      const li = document.createElement("li");
      li.textContent = "Listu-pH baxu batek hainbat kausa izan ditzake (medikazioa, dieta, desordena gastrikoak, etab.). Aldi berean, hortz-higadura, gaixotasun periodontala edo ahoko osasunaren beste desoreka batzuk eragin ditzake. Kontsulta ezazu zure odontologoarekin jatorria identifikatzeko, eta ahoko osasuna babesteko eta dagokion espezialistarekin bidera dezan";
      listaFactores.appendChild(li);
      li.textContent = "Zure ahoaren pH maila azidoa denez, gomendagarria izan daiteke azukredun janariak eta edariak murriztea eguneroko dietan. Elikadura ohitura osasungarriek ahoaren oreka berreskuratzen laguntzen dute";
      listaFactores.appendChild(li);
      const a = document.createElement("a");
      a.href = "https://sepa.es/download/recomendaciones-sobre-dieta-y-salud-bucal/?wpdmdl=51283&_wpdmkey=69b91cdf4e1fd&subscriber=O9p-ySRz1XKM40lC7Rr3nsx4_hld9vLPLr9Y6902V4bJS6Fnipa0NQKByKIB96UBCqOnm8cFj0NUidqnQp_oAfA";
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "SEPA - Recomendaciones sobre dieta y salud bucal";
      li.appendChild(a);
      listaFactores.appendChild(li);

    }
    else if (f.includes("Erretzailea")){
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "https://osasuneskola.osakidetza.eus/es/medialib/html/tabakismoa-prebenitzea";
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "Erretzailea zara, esteka hau kontsultatu";
      li.appendChild(a);
      listaFactores.appendChild(li);
    }
    else if (f.includes("Diabetesa")){
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "https://osasuneskola.osakidetza.eus/es/medialib/html/diabetesa";
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "Diabetesa detektatu da, esteka hau kontsultatu";
      li.appendChild(a);
      listaFactores.appendChild(li);
    }
    
  });

  const ia=data.recomendacion_personalizada;

  const iaTexto=document.getElementById("iaTexto");
  iaTexto.innerText=ia?.recommendations ? ia.recommendations : "-";

  const recomendacionesList = document.getElementById("iaTexto");
  recomendacionesList.innerHTML = '';

  console.log(ia.recommendations);

  ia.recommendations.forEach(recommendation => {

    const li = document.createElement("li");

    const texto = document.createElement("p");
    texto.innerHTML = `<strong>Gomendioa:</strong> ${recommendation.ai_text || recommendation.text}`;

    const motivo = document.createElement("p");
    motivo.innerHTML = `<strong>Arrazoia:</strong> ${recommendation.reason}`;

    li.appendChild(texto);
    li.appendChild(motivo);

   
    if (recommendation.sources && recommendation.sources.length > 0) {
        const sourcesList = document.createElement("ul");
        recommendation.sources.forEach(source => {
            const sourceItem = document.createElement("li");
            const sourceLink = document.createElement("a");
            sourceLink.href = source.url;
            sourceLink.innerText = source.title;
            sourceLink.target="_blank";
            sourceItem.appendChild(sourceLink);
            sourcesList.appendChild(sourceItem);
          });
        li.appendChild(sourcesList);
    }

        // Añadir la recomendación completa a la lista
    recomendacionesList.appendChild(li);
  });  



  const iaLinks = document.getElementById("iaLinks");
  iaLinks.innerHTML = "";
  (ia?.links || []).forEach(l => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = l.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = l.title || l.url;
    li.appendChild(a);
    iaLinks.appendChild(li);
  });

  const ulSources = document.getElementById("iaSources");
  ulSources.innerHTML = "";

  const sources = ia?.sources || [];

  if (sources.length === 0) {
    const li = document.createElement("li");
    li.textContent = "—";
    ulSources.appendChild(li);
  } else {
    sources.forEach(s => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = s.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = s.title || s.url;
      li.appendChild(a);
      ulSources.appendChild(li);
    });
  }


}
async function guardarFormulariosPaciente() {
  const token = sessionStorage.getItem("token");
  const payload = recogerDatos();

  const res = await fetch("/api/patient/questionnaires", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    alert("Errorea galdeketak gordetzean");
    return;
  }

  alert("Galdeketak ondo gorde dira");
  mostrar("menuPaciente");
}

async function resetPinPaciente(patientId) {
  if (!confirm("PIN berria sortuko da. Jarraitu?")) return;

  const token = sessionStorage.getItem("token");

  const res = await fetch(`/api/researcher/patients/${patientId}/reset-pin`, {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  if (!res.ok) {
    alert("Errorea PIN berria sortzean");
    return;
  }

  const data = await res.json();

  alert(
    "PIN berria sortua:\n\n" +
    "Paziente kodea: " + data.patient_code + "\n" +
    "PIN berria: " + data.new_pin + "\n\n" +
    "⚠️ PIN hau pazienteari eman eta ez da berriro erakutsiko."
  );
}

async function cargarEstadisticas() {
  const token = sessionStorage.getItem("token");

  const res = await fetch("/api/researcher/estadisticas", {
    headers: {
      "Authorization": "Bearer " + token
    }
  });

  if (!res.ok) {
    alert("Errorea estatistikak kargatzean");
    return;
  }

  const valores = await res.json();
  const tbody = document.getElementById("tablaEstadisticas");
  tbody.innerHTML = "";   
  
  const fila = document.createElement("tr");

  fila.innerHTML = `
      <td>M1K1</td>
      <td>${valores.plaka_m1k1_media ?? "-"}</td>
      <td>${valores.il6_m1k1_media ?? "-"}</td>
      <td>${valores.hig_m1k1_media ?? "-"}</td>
      <td>${valores.kar_m1k1_media ?? "-"}</td>
      <td>${valores.men_m1k1_media ?? "-"}</td>
    `;

  tbody.appendChild(fila);

  const fila2 = document.createElement("tr");

  fila2.innerHTML = `
      <td>M0K1</td>
      <td>${valores.plaka_m0k1_media ?? "-"}</td>
      <td>${valores.il6_m0k1_media ?? "-"}</td>
      <td>${valores.hig_m0k1_media ?? "-"}</td>
      <td>${valores.kar_m0k1_media ?? "-"}</td>
      <td>-</td>
    `;

  tbody.appendChild(fila2);

  const fila3 = document.createElement("tr");

  fila3.innerHTML = `
      <td>M1K0</td>
      <td>${valores.plaka_m1k0_media ?? "-"}</td>
      <td>${valores.il6_m1k0_media ?? "-"}</td>
      <td>${valores.hig_m1k0_media ?? "-"}</td>
      <td>${valores.kar_m1k0_media ?? "-"}</td>
      <td>${valores.men_m1k0_media ?? "-"}</td>
    `;

  tbody.appendChild(fila3);

  const fila4 = document.createElement("tr");

  fila4.innerHTML = `
      <td>M0K0</td>
      <td>${valores.plaka_m0k0_media ?? "-"}</td>
      <td>${valores.il6_m0k0_media ?? "-"}</td>
      <td>${valores.hig_m0k0_media ?? "-"}</td>
      <td>${valores.kar_m0k0_media ?? "-"}</td>
      <td>-</td>
    `;

  tbody.appendChild(fila4);
  
}

async function exportarDatos() {
  try {
    const token = sessionStorage.getItem("token");

    const res = await fetch("/api/researcher/exportar", {
      headers: {
        "Authorization": "Bearer " + token
      }
    });

    if (!res.ok) {
      alert("Errorea datuak esportatzen");
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "jamovi_export.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error(error);
    alert("Errorea esportazioan");
  }
}  