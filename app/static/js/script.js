
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
    document.getElementById("logoutBtn").style.display = "inline-block";
    mostrar("investigador");
  } else if (data.role === "patient") {
    document.getElementById("logoutBtn").style.display = "inline-block";
    mostrar("menuPaciente");
  }
  
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");

  // opcional: limpiar selects / formularios
  document.querySelectorAll("input, textarea").forEach(el => el.value = "");

  // ocultar todo y volver al login
  mostrar("login");

  // ocultar botón
  document.getElementById("logoutBtn").style.display = "none";
}


function mostrar(id) {

    const secciones = ["login","resultadosPaciente","menuPaciente","analiticasPaciente", "form1", "form2", "formAnalitica", "resultados", "registrar", "investigador","listaPacientes"];

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

document.addEventListener("DOMContentLoaded", () => {
  mostrar("login");
});

async function registrarPaciente() {
  const token = localStorage.getItem("token");

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
  const token = localStorage.getItem("token");

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
      <td>${p.observations ?? "-"}</td>
      <td>${p.measured_at ? new Date(p.measured_at).toLocaleDateString() : "-"}</td>
    `;

    tbody.appendChild(fila);
  });
}

async function cargarPacientesSelect() {
  const token = localStorage.getItem("token");

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
  const token = localStorage.getItem("token");

  const payload = {
    patient_id: document.getElementById("patientSelect").value,
    il6_value: parseFloat(document.getElementById("il6").value),
    dental_plaque: parseFloat(document.getElementById("indice_placa").value),
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
  const token = localStorage.getItem("token");
  if (!token) {
    mostrar("login");
  } else {
    // opcional: restaurar vista según rol
    const role = localStorage.getItem("role");
    document.getElementById("logoutBtn").style.display = "inline-block";

    if (role === "researcher") mostrar("investigador");
    if (role === "patient") mostrar("menuPaciente");
  }
});

async function mostrarAnaliticasPaciente() {
  const token = localStorage.getItem("token");

  const res = await fetch("/api/patient/biomarkers", {
    headers: { "Authorization": "Bearer " + token }
  });

  const data = await res.json();
  mostrar("analiticasPaciente");

  document.getElementById("il6Paciente").innerText = data.il6_value ?? "-";
  document.getElementById("placaPaciente").innerText = data.dental_plaque ?? "-";
  document.getElementById("fechaPaciente").innerText =
    data.measured_at ? new Date(data.measured_at).toLocaleString() : "-";
}

async function mostrarResultadosPaciente() {
  const token = localStorage.getItem("token");

  const res = await fetch("/api/patient/resultados", {
    headers: {
      "Authorization": "Bearer " + token
    }
  });

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

  // Pintar factores
  const ul = document.getElementById("factoresPaciente");
  ul.innerHTML = "";

  data.factores.forEach(f => {
    const li = document.createElement("li");
    li.textContent = f;
    ul.appendChild(li);
  });
}
