const API = "";
let TOKEN       = localStorage.getItem("dme_token") || "";
let currentRole = "";
let allPatients = [];
let chartMois, chartSexe, chartTop;

// ===== AUTH =====
async function login() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !password) {
    showAlert("loginAlert", "Remplis tous les champs", "danger");
    return;
  }

  try {
    const res  = await fetch("/auth/login", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({username, password})
    });
    const data = await res.json();

    if (res.ok && data.token) {
      TOKEN       = data.token;
      currentRole = data.role;
      localStorage.setItem("dme_token", TOKEN);

      document.getElementById("sidebarUsername").textContent = data.username || username;
      document.getElementById("sidebarRole").textContent     = data.role === "admin" ? "Administrateur" : "Médecin";

      if (data.role === "admin") {
        document.getElementById("btnAdmin").style.display   = "block";
        document.getElementById("adminLabel").style.display = "block";
      }

      document.getElementById("loginPage").style.display = "none";
      document.getElementById("app").style.display       = "block";
      loadDashboard();
    } else {
      showAlert("loginAlert", data.erreur || "Erreur de connexion", "danger");
    }
  } catch (err) {
    showAlert("loginAlert", "Erreur réseau", "danger");
  }
}

function logout() {
  TOKEN = ""; currentRole = "";
  localStorage.removeItem("dme_token");
  document.getElementById("loginPage").style.display = "flex";
  document.getElementById("app").style.display       = "none";
  document.getElementById("username").value = "";
  document.getElementById("password").value = "";
}

// ===== NAVIGATION =====
function showPage(name, btn) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".sidebar button").forEach(b => b.classList.remove("active"));
  document.getElementById(`page-${name}`).classList.add("active");
  if (btn) btn.classList.add("active");

  if (name === "dashboard")     loadDashboard();
  if (name === "patients")      loadPatients();
  if (name === "consultations") loadPatientsSelect();
  if (name === "stats")         loadStats();
  if (name === "users")         loadUsers();
}

// ===== HELPERS =====
function headers() {
  return {"Content-Type": "application/json", "Authorization": `Bearer ${TOKEN}`};
}

function showAlert(id, msg, type) {
  const el = document.getElementById(id);
  el.innerHTML = (type === "success" ? "✅ " : "❌ ") + msg;
  el.className = `alert alert-${type} show`;
  setTimeout(() => el.classList.remove("show"), 3500);
}

function openModal(id)  { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

function initials(nom, prenom) {
  return ((nom || "")[0] || "") + ((prenom || "")[0] || "");
}

// ===== DASHBOARD =====
async function loadDashboard() {
  const now = new Date();
  document.getElementById("dashboardDate").textContent =
    now.toLocaleDateString("fr-FR", {weekday:"long", year:"numeric", month:"long", day:"numeric"});

  const [resP, resS] = await Promise.all([
    fetch("/patients",  {headers: headers()}),
    fetch("/stats",     {headers: headers()})
  ]);

  const patients = await resP.json();
  const stats    = await resS.json();

  if (!Array.isArray(patients)) return;

  document.getElementById("stat-patients").textContent      = stats.total_patients      || 0;
  document.getElementById("stat-consultations").textContent = stats.total_consultations || 0;

  // Compte les médecins
  if (currentRole === "admin") {
    const resU = await fetch("/users", {headers: headers()});
    const users = await resU.json();
    if (Array.isArray(users)) {
      document.getElementById("stat-medecins").textContent =
        users.filter(u => u.role === "medecin").length;
    }
  }

  const tbody = document.getElementById("recent-patients");
  tbody.innerHTML = "";

  for (const p of patients.slice(0, 6)) {
    const r = await fetch(`/patients/${p.id}`, {headers: headers()});
    const d = await r.json();
    const nb = d.consultations ? d.consultations.length : 0;

    tbody.innerHTML += `<tr>
      <td>
        <div style="display:flex; align-items:center; gap:10px;">
          <div class="patient-avatar">${initials(p.nom, p.prenom)}</div>
          <div style="font-weight:500;">${p.nom} ${p.prenom}</div>
        </div>
      </td>
      <td>${p.age} ans</td>
      <td><span class="badge badge-blue">${p.sexe || "-"}</span></td>
      <td>${p.contact || "-"}</td>
      <td><span class="badge badge-green">${nb} consultation(s)</span></td>
    </tr>`;
  }
}

// ===== PATIENTS =====
async function loadPatients() {
  const res  = await fetch("/patients", {headers: headers()});
  const data = await res.json();
  if (!Array.isArray(data)) return;
  allPatients = data;
  renderPatients(data);
}

function renderPatients(list) {
  const tbody = document.getElementById("patientTable");
  tbody.innerHTML = "";

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#aaa;padding:2rem;">Aucun patient trouvé</td></tr>`;
    return;
  }

  for (const p of list) {
    tbody.innerHTML += `<tr>
      <td>
        <div style="display:flex; align-items:center; gap:10px;">
          <div class="patient-avatar">${initials(p.nom, p.prenom)}</div>
          <div>
            <div style="font-weight:500;">${p.nom} ${p.prenom}</div>
            <div style="font-size:12px;color:#888;">ID: ${p.id}</div>
          </div>
        </div>
      </td>
      <td>${p.age} ans</td>
      <td><span class="badge ${p.sexe === "M" ? "badge-blue" : "badge-green"}">${p.sexe || "-"}</span></td>
      <td>${p.contact || "-"}</td>
      <td>
        <div class="actions">
          <button class="btn btn-info" onclick='editPatient(${JSON.stringify(p)})'>✏️ Modifier</button>
          <button class="btn btn-danger" onclick="deletePatient(${p.id})">🗑️</button>
        </div>
      </td>
    </tr>`;
  }
}

function filterPatients() {
  const q = document.getElementById("searchPatient").value.toLowerCase();
  renderPatients(allPatients.filter(p =>
    p.nom.toLowerCase().includes(q) ||
    p.prenom.toLowerCase().includes(q) ||
    (p.contact && p.contact.includes(q))
  ));
}

function openAddPatient() {
  document.getElementById("modalPatientTitle").textContent = "Nouveau patient";
  ["patientId","pNom","pPrenom","pAge","pContact"].forEach(id =>
    document.getElementById(id).value = "");
  document.getElementById("pSexe").value = "";
  openModal("modalPatient");
}

function editPatient(p) {
  document.getElementById("modalPatientTitle").textContent = "Modifier le patient";
  document.getElementById("patientId").value = p.id;
  document.getElementById("pNom").value      = p.nom;
  document.getElementById("pPrenom").value   = p.prenom;
  document.getElementById("pAge").value      = p.age;
  document.getElementById("pSexe").value     = p.sexe || "";
  document.getElementById("pContact").value  = p.contact || "";
  openModal("modalPatient");
}

async function savePatient() {
  const id     = document.getElementById("patientId").value;
  const nom    = document.getElementById("pNom").value.trim();
  const prenom = document.getElementById("pPrenom").value.trim();
  const age    = document.getElementById("pAge").value;

  if (!nom || !prenom || !age) {
    showAlert("patientAlert", "Nom, prénom et âge sont obligatoires", "danger");
    return;
  }

  const body = {
    nom, prenom, age: parseInt(age),
    sexe:    document.getElementById("pSexe").value,
    contact: document.getElementById("pContact").value.trim()
  };

  const url    = id ? `/patients/${id}` : `/patients`;
  const method = id ? "PUT" : "POST";

  const res  = await fetch(url, {method, headers: headers(), body: JSON.stringify(body)});
  const data = await res.json();

  if (res.ok) {
    closeModal("modalPatient");
    loadPatients();
    showAlert("patientAlert", data.message, "success");
  } else {
    showAlert("patientAlert", data.erreur || "Erreur", "danger");
  }
}

async function deletePatient(id) {
  if (!confirm("Supprimer ce patient et toutes ses consultations ?")) return;
  const res  = await fetch(`/patients/${id}`, {method: "DELETE", headers: headers()});
  const data = await res.json();
  showAlert("patientAlert", data.message || data.erreur, res.ok ? "success" : "danger");
  loadPatients();
}

// ===== CONSULTATIONS =====
async function loadPatientsSelect() {
  const res  = await fetch("/patients", {headers: headers()});
  const data = await res.json();
  if (!Array.isArray(data)) return;
  const sel = document.getElementById("selectPatient");
  sel.innerHTML = `<option value="">-- Choisir un patient --</option>`;
  data.forEach(p => {
    sel.innerHTML += `<option value="${p.id}">${p.nom} ${p.prenom}</option>`;
  });
}

async function loadConsultations() {
  const id = document.getElementById("selectPatient").value;
  if (!id) { document.getElementById("consultSection").style.display = "none"; return; }

  const res  = await fetch(`/patients/${id}/consultations`, {headers: headers()});
  const data = await res.json();
  if (!Array.isArray(data)) return;

  document.getElementById("consultSection").style.display = "block";
  const sel  = document.getElementById("selectPatient");
  document.getElementById("consultTitle").textContent =
    `📋 ${sel.options[sel.selectedIndex].text}`;

  const tbody = document.getElementById("consultTable");
  tbody.innerHTML = "";

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#aaa;padding:2rem;">Aucune consultation</td></tr>`;
    return;
  }

  for (const c of data) {
    tbody.innerHTML += `<tr>
      <td>${c.date}</td>
      <td>${c.symptomes  || "-"}</td>
      <td>${c.diagnostic || "-"}</td>
      <td>${c.traitement || "-"}</td>
      <td>
        <div class="actions">
          <button class="btn btn-info"   onclick='editConsult(${JSON.stringify(c)})'>✏️</button>
          <button class="btn btn-danger" onclick="deleteConsult(${c.id})">🗑️</button>
        </div>
      </td>
    </tr>`;
  }
}

function editConsult(c) {
  document.getElementById("modalConsultTitle").textContent = "Modifier la consultation";
  document.getElementById("consultId").value   = c.id;
  document.getElementById("cSymptomes").value  = c.symptomes  || "";
  document.getElementById("cDiagnostic").value = c.diagnostic || "";
  document.getElementById("cTraitement").value = c.traitement || "";
  openModal("modalConsult");
}

async function saveConsultation() {
  const id        = document.getElementById("consultId").value;
  const patientId = document.getElementById("selectPatient").value;
  const body      = {
    symptomes:  document.getElementById("cSymptomes").value.trim(),
    diagnostic: document.getElementById("cDiagnostic").value.trim(),
    traitement: document.getElementById("cTraitement").value.trim()
  };

  const url    = id ? `/consultations/${id}` : `/patients/${patientId}/consultations`;
  const method = id ? "PUT" : "POST";

  const res  = await fetch(url, {method, headers: headers(), body: JSON.stringify(body)});
  const data = await res.json();

  if (res.ok) {
    closeModal("modalConsult");
    document.getElementById("consultId").value = "";
    document.getElementById("modalConsultTitle").textContent = "Nouvelle consultation";
    loadConsultations();
    showAlert("consultAlert", data.message, "success");
  } else {
    showAlert("consultAlert", data.erreur || "Erreur", "danger");
  }
}

async function deleteConsult(id) {
  if (!confirm("Supprimer cette consultation ?")) return;
  const res  = await fetch(`/consultations/${id}`, {method: "DELETE", headers: headers()});
  const data = await res.json();
  showAlert("consultAlert", data.message || data.erreur, res.ok ? "success" : "danger");
  loadConsultations();
}

// ===== PDF =====
async function printPatientPDF() {
  const id = document.getElementById("selectPatient").value;
  if (!id) return;

  const res  = await fetch(`/patients/${id}`, {headers: headers()});
  const p    = await res.json();

  const content = document.getElementById("pdfContent");
  content.innerHTML = `
    <div class="pdf-header">
      <h2>🏥 Fiche Patient — DME</h2>
      <p>Générée le ${new Date().toLocaleDateString("fr-FR")}</p>
    </div>
    <div class="pdf-section">
      <h3>Informations personnelles</h3>
      <div class="pdf-grid">
        <div class="pdf-field"><label>Nom complet</label><span>${p.nom} ${p.prenom}</span></div>
        <div class="pdf-field"><label>Âge</label><span>${p.age} ans</span></div>
        <div class="pdf-field"><label>Sexe</label><span>${p.sexe === "M" ? "Masculin" : p.sexe === "F" ? "Féminin" : "-"}</span></div>
        <div class="pdf-field"><label>Contact</label><span>${p.contact || "-"}</span></div>
      </div>
    </div>
    <div class="pdf-section">
      <h3>Historique des consultations (${p.consultations.length})</h3>
      ${p.consultations.length === 0
        ? `<p style="color:#aaa; font-size:13px;">Aucune consultation enregistrée</p>`
        : p.consultations.map(c => `
          <div class="pdf-consult">
            <div class="date">📅 ${c.date}</div>
            ${c.symptomes  ? `<div><strong>Symptômes :</strong> ${c.symptomes}</div>`  : ""}
            ${c.diagnostic ? `<div><strong>Diagnostic :</strong> ${c.diagnostic}</div>` : ""}
            ${c.traitement ? `<div><strong>Traitement :</strong> ${c.traitement}</div>` : ""}
          </div>`).join("")}
    </div>`;

  openModal("modalPDF");
}

// ===== STATISTIQUES =====
async function loadStats() {
  const res  = await fetch("/stats", {headers: headers()});
  const data = await res.json();

  document.getElementById("stats-total-patients").textContent = data.total_patients;
  document.getElementById("stats-total-consult").textContent  = data.total_consultations;

  // Détruit les anciens graphiques
  if (chartMois)  { chartMois.destroy();  chartMois  = null; }
  if (chartSexe)  { chartSexe.destroy();  chartSexe  = null; }
  if (chartTop)   { chartTop.destroy();   chartTop   = null; }

  // Graphique — consultations par mois
  chartMois = new Chart(document.getElementById("chartMois"), {
    type: "line",
    data: {
      labels: data.mois_labels,
      datasets: [{
        label: "Consultations",
        data: data.mois_data,
        borderColor: "#1565c0",
        backgroundColor: "rgba(21,101,192,0.1)",
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#1565c0"
      }]
    },
    options: {
      responsive: true,
      plugins: {legend: {display: false}},
      scales: {
        y: {beginAtZero: true, ticks: {stepSize: 1}},
        x: {grid: {display: false}}
      }
    }
  });

  // Graphique — répartition par sexe
  chartSexe = new Chart(document.getElementById("chartSexe"), {
    type: "doughnut",
    data: {
      labels: ["Hommes", "Femmes", "Non renseigné"],
      datasets: [{
        data: [data.sexe.hommes, data.sexe.femmes, data.sexe.autres],
        backgroundColor: ["#1565c0", "#e91e63", "#90a4ae"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {position: "bottom"},
      }
    }
  });

  // Graphique — top patients
  chartTop = new Chart(document.getElementById("chartTop"), {
    type: "bar",
    data: {
      labels: data.top_patients.map(p => p.nom),
      datasets: [{
        label: "Consultations",
        data: data.top_patients.map(p => p.nb),
        backgroundColor: "#1565c0",
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      plugins: {legend: {display: false}},
      scales: {
        y: {beginAtZero: true, ticks: {stepSize: 1}},
        x: {grid: {display: false}}
      }
    }
  });
}

// ===== UTILISATEURS =====
async function loadUsers() {
  const res  = await fetch("/users", {headers: headers()});
  const data = await res.json();

  if (!Array.isArray(data)) {
    showAlert("userAlert", "Accès refusé — admin uniquement", "danger");
    return;
  }

  document.getElementById("userCount").textContent = `${data.length} utilisateur(s)`;
  const tbody = document.getElementById("userTable");
  tbody.innerHTML = "";

  for (const u of data) {
    const isMain     = u.id === 1 && u.username === "admin";
    const badgeClass = u.role === "admin" ? "badge-admin" : "badge-medecin";
    const roleLabel  = u.role === "admin" ? "Administrateur" : "Médecin";

    tbody.innerHTML += `<tr>
      <td>${u.id}</td>
      <td>
        <div style="display:flex; align-items:center; gap:10px;">
          <div class="user-avatar">${u.username[0].toUpperCase()}</div>
          <span style="font-weight:500;">${u.username}</span>
        </div>
      </td>
      <td><span class="badge ${badgeClass}">${roleLabel}</span></td>
      <td>
        <div class="actions">
          ${!isMain ? `
            <select onchange="changeRole(${u.id}, this.value)"
              style="padding:6px 10px; border-radius:8px; border:1.5px solid #e0e0e0;
                     font-size:13px; cursor:pointer; background:#fafafa;">
              <option value="medecin" ${u.role === "medecin" ? "selected" : ""}>Médecin</option>
              <option value="admin"   ${u.role === "admin"   ? "selected" : ""}>Admin</option>
            </select>
            <button class="btn btn-danger" onclick="deleteUser(${u.id}, '${u.username}')">🗑️</button>
          ` : `<span style="font-size:12px; color:#aaa;">Compte principal</span>`}
        </div>
      </td>
    </tr>`;
  }
}

async function saveUser() {
  const username = document.getElementById("uUsername").value.trim();
  const password = document.getElementById("uPassword").value;
  const confirm  = document.getElementById("uPasswordConfirm").value;
  const role     = document.getElementById("uRole").value;

  if (!username || !password) {
    showAlert("userAlert", "Nom d'utilisateur et mot de passe obligatoires", "danger");
    return;
  }
  if (password !== confirm) {
    showAlert("userAlert", "Les mots de passe ne correspondent pas", "danger");
    return;
  }
  if (password.length < 6) {
    showAlert("userAlert", "Mot de passe trop court (min 6 caractères)", "danger");
    return;
  }

  const res  = await fetch("/auth/register", {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({username, password, role})
  });
  const data = await res.json();

  if (res.ok) {
    closeModal("modalUser");
    ["uUsername","uPassword","uPasswordConfirm"].forEach(id =>
      document.getElementById(id).value = "");
    document.getElementById("uRole").value = "medecin";
    loadUsers();
    showAlert("userAlert", data.message, "success");
  } else {
    showAlert("userAlert", data.erreur || "Erreur", "danger");
  }
}

async function changeRole(id, role) {
  const res  = await fetch(`/users/${id}/role`, {
    method: "PUT", headers: headers(),
    body: JSON.stringify({role})
  });
  const data = await res.json();
  showAlert("userAlert", data.message || data.erreur, res.ok ? "success" : "danger");
  if (res.ok) loadUsers();
}

async function deleteUser(id, username) {
  if (!confirm(`Supprimer l'utilisateur "${username}" ?`)) return;
  const res  = await fetch(`/users/${id}`, {method: "DELETE", headers: headers()});
  const data = await res.json();
  showAlert("userAlert", data.message || data.erreur, res.ok ? "success" : "danger");
  if (res.ok) loadUsers();
}

// ===== AUTO LOGIN =====
window.onload = () => {
  if (TOKEN) {
    try {
      const payload = JSON.parse(atob(TOKEN.split(".")[1]));
      currentRole   = payload.role || "";

      document.getElementById("sidebarUsername").textContent =
        payload.username || "Utilisateur";
      document.getElementById("sidebarRole").textContent =
        currentRole === "admin" ? "Administrateur" : "Médecin";

      if (currentRole === "admin") {
        document.getElementById("btnAdmin").style.display   = "block";
        document.getElementById("adminLabel").style.display = "block";
      }
    } catch (e) {}

    document.getElementById("loginPage").style.display = "none";
    document.getElementById("app").style.display       = "block";
    loadDashboard();
  }
};