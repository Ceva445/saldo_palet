// Dashboard page logic: data loading, permission gating, actions.
const state = { user: null };

const TX_PREFIXES = ["rc", "rl", "co"];

// Searchable comboboxes (server-side search) — both for the transaction form
// fields and the masterdata management lists.
const COMBO_LIMIT = 8;
const FIELD_KINDS = { area: "areas", supplier: "suppliers", unit: "units" };

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

function can(module) {
  return state.user && state.user.permissions.includes(module);
}

function logout() {
  localStorage.removeItem("token");
  location.href = "/";
}

function esc(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function applyPermissions() {
  document.querySelectorAll("fieldset[data-module]").forEach((fs) => {
    const locked = !can(fs.dataset.module);
    fs.classList.toggle("locked", locked);
    fs.querySelectorAll("input, select, textarea, button").forEach((el) => {
      el.disabled = locked;
    });
  });
}

// ---------- Generic combobox ----------
async function fetchMd(kind, search) {
  const url = `/${kind}?search=${encodeURIComponent(search)}&limit=${COMBO_LIMIT}&offset=0`;
  const headers = {};
  if (token()) headers["Authorization"] = "Bearer " + token();

  const res = await fetch(url, { headers });
  if (res.status === 401) {
    logout();
    throw new Error("401");
  }
  const items = await res.json();
  const total = parseInt(res.headers.get("X-Total-Count") || "0", 10);
  return { items, total };
}

function renderOptions(menu, items, onPick) {
  if (!items.length) {
    menu.innerHTML = `<div class="combo-empty">Brak wyników</div>`;
  } else {
    menu.innerHTML = items
      .map(
        (i) =>
          `<div class="combo-option" data-uuid="${i.uuid}" data-name="${esc(i.name)}">${esc(i.name)}</div>`
      )
      .join("");
    menu.querySelectorAll(".combo-option").forEach((opt) => {
      // mousedown fires before the input's blur hides the menu.
      opt.onmousedown = (e) => {
        e.preventDefault();
        onPick(opt.dataset.uuid, opt.dataset.name);
      };
    });
  }
  menu.classList.remove("hidden");
}

// ---------- Transaction form field combos ----------
function setupFieldCombos() {
  for (const prefix of TX_PREFIXES) {
    for (const field of Object.keys(FIELD_KINDS)) {
      setupFieldCombo(prefix, field);
    }
  }
}

function setupReportCombos() {
  for (const field of Object.keys(FIELD_KINDS)) {
    setupFieldCombo("rp", field);
  }
}

function setupFieldCombo(prefix, field) {
  const kind = FIELD_KINDS[field];
  const input = document.getElementById(`${prefix}-${field}-input`);
  const hidden = document.getElementById(`${prefix}-${field}`);
  const menu = document.getElementById(`${prefix}-${field}-menu`);

  const search = debounce(async () => {
    hidden.value = ""; // typing invalidates the previous selection
    const { items } = await fetchMd(kind, input.value.trim());
    renderOptions(menu, items, (uuid, name) => {
      hidden.value = uuid;
      input.value = name;
      menu.classList.add("hidden");
    });
  }, 200);

  input.addEventListener("focus", search);
  input.addEventListener("input", search);
  input.addEventListener("blur", () => setTimeout(() => menu.classList.add("hidden"), 150));
}

// ---------- Masterdata (Typ + searchable name + add/delete) ----------
function mdKind() {
  return document.getElementById("md-type").value;
}

function clearMdName() {
  document.getElementById("md-name").value = "";
  document.getElementById("md-name-input").value = "";
  document.getElementById("md-name-menu").classList.add("hidden");
}

function setupMasterdataCombo() {
  const input = document.getElementById("md-name-input");
  const hidden = document.getElementById("md-name");
  const menu = document.getElementById("md-name-menu");

  const search = debounce(async () => {
    hidden.value = "";
    const { items } = await fetchMd(mdKind(), input.value.trim());
    renderOptions(menu, items, (uuid, name) => {
      hidden.value = uuid;
      input.value = name;
      menu.classList.add("hidden");
    });
  }, 200);

  input.addEventListener("focus", search);
  input.addEventListener("input", search);
  input.addEventListener("blur", () => setTimeout(() => menu.classList.add("hidden"), 150));
  document.getElementById("md-type").addEventListener("change", clearMdName);
}

// ---------- Actions ----------
async function submitTx(prefix, type) {
  const msg = document.getElementById(prefix + "-msg");
  msg.className = "msg";
  msg.textContent = "";

  const date = document.getElementById(prefix + "-date").value;
  const area = document.getElementById(prefix + "-area").value;
  const supplier = document.getElementById(prefix + "-supplier").value;
  const unit = document.getElementById(prefix + "-unit").value;
  const qtyRaw = document.getElementById(prefix + "-qty").value;
  const comment = document.getElementById(prefix + "-comment").value.trim();
  const quantity = parseInt(qtyRaw, 10);

  const missing = [];
  if (!date) missing.push("Data");
  if (!area) missing.push("Obszar");
  if (!supplier) missing.push("Dostawca");
  if (!unit) missing.push("Jednostka");
  if (qtyRaw === "" || Number.isNaN(quantity)) missing.push("Liczba sztuk");
  if (type === "CORRECTION" && !comment) missing.push("Komentarz");

  if (missing.length) {
    msg.classList.add("error");
    msg.textContent = "Uzupełnij pola: " + missing.join(", ");
    return;
  }

  if (type !== "CORRECTION" && quantity <= 0) {
    msg.classList.add("error");
    msg.textContent = "Liczba sztuk musi być większa od 0";
    return;
  }

  try {
    await api("/transactions", {
      method: "POST",
      body: {
        type,
        area_uuid: area,
        supplier_uuid: supplier,
        unit_uuid: unit,
        quantity,
        comment: comment || null,
        date,
      },
    });
    msg.classList.add("ok");
    msg.textContent = "✓ Zapisano";
    resetTxForm(prefix);
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

function resetTxForm(prefix) {
  // Clear quantity, comment and the three search comboboxes (keep the date).
  document.getElementById(prefix + "-qty").value = "";
  document.getElementById(prefix + "-comment").value = "";
  for (const field of Object.keys(FIELD_KINDS)) {
    document.getElementById(`${prefix}-${field}`).value = "";        // hidden uuid
    document.getElementById(`${prefix}-${field}-input`).value = "";  // visible text
  }
}

async function downloadReport(type, useSupplier, useRange) {
  const msg = document.getElementById("rp-msg");
  msg.className = "msg";
  msg.textContent = "";

  const supplier = document.getElementById("rp-supplier").value;
  const unit = document.getElementById("rp-unit").value;
  const area = document.getElementById("rp-area").value;
  const start = document.getElementById("rp-start").value;
  const end = document.getElementById("rp-end").value;

  if (useSupplier && !supplier) {
    msg.classList.add("error");
    msg.textContent = "Wybierz dostawcę";
    return;
  }
  if (useRange && (!start || !end)) {
    msg.classList.add("error");
    msg.textContent = "Podaj zakres dat (Start i Koniec)";
    return;
  }

  const params = new URLSearchParams();
  if (useSupplier && supplier) params.set("supplier_uuid", supplier);
  if (unit) params.set("unit_uuid", unit);
  if (area) params.set("area_uuid", area);
  if (type === "ksiegowania" || useRange) {
    if (start) params.set("start", start);
    if (end) params.set("end", end);
  }

  const buttons = document.querySelectorAll("button[data-report]");
  buttons.forEach((b) => (b.disabled = true));
  msg.innerHTML = '<span class="spinner"></span> Generowanie raportu… (może potrwać do minuty)';

  try {
    const res = await fetch(`/reports/${type}?${params.toString()}`, {
      headers: { Authorization: "Bearer " + token() },
    });
    if (res.status === 401) return logout();
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      throw new Error((data && data.message) || "Błąd generowania raportu");
    }

    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `${type}.xlsx`;

    const objUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objUrl);

    msg.classList.add("ok");
    msg.textContent = "Raport pobrany";
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  } finally {
    buttons.forEach((b) => (b.disabled = false));
  }
}

async function addMasterdata() {
  const msg = document.getElementById("md-msg");
  msg.className = "msg";
  msg.textContent = "";
  const name = document.getElementById("md-name-input").value.trim();
  if (!name) {
    msg.classList.add("error");
    msg.textContent = "Podaj nazwę";
    return;
  }
  try {
    await api("/" + mdKind(), { method: "POST", body: { name } });
    clearMdName();
    msg.classList.add("ok");
    msg.textContent = "Dodano";
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

async function deleteMasterdata() {
  const msg = document.getElementById("md-msg");
  msg.className = "msg";
  msg.textContent = "";
  const uuid = document.getElementById("md-name").value;
  const name = document.getElementById("md-name-input").value.trim();
  if (!uuid) {
    msg.classList.add("error");
    msg.textContent = "Wybierz istniejącą pozycję z listy";
    return;
  }
  if (!confirm(`Usunąć "${name}"?`)) return;
  try {
    await api(`/${mdKind()}/${uuid}`, { method: "DELETE" });
    clearMdName();
    msg.classList.add("ok");
    msg.textContent = "Usunięto";
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

function wireEvents() {
  document.getElementById("logout-btn").onclick = logout;
  document.querySelectorAll("button[data-tx]").forEach((b) => {
    b.onclick = () => submitTx(b.dataset.prefix, b.dataset.tx);
  });
  document.getElementById("md-add-btn").onclick = addMasterdata;
  document.getElementById("md-del-btn").onclick = deleteMasterdata;
  document.querySelectorAll("button[data-report]").forEach((b) => {
    b.onclick = () =>
      downloadReport(b.dataset.report, b.dataset.supplier === "1", b.dataset.range === "1");
  });
}

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function fillTodayDates() {
  const today = todayISO();
  document.querySelectorAll(".tx-date").forEach((el) => {
    el.value = today;
  });
}

// ---------- Boot ----------
async function boot() {
  if (!token()) {
    location.href = "/";
    return;
  }
  try {
    state.user = await api("/auth/me");
    if (state.user.must_change_password) {
      location.href = "/change-password";
      return;
    }
    document.getElementById("user-info").textContent =
      `${state.user.username} (${state.user.role})`;
    if (can("users")) {
      document.getElementById("users-link").classList.remove("hidden");
    }
    fillTodayDates();
    setupFieldCombos();
    setupReportCombos();
    setupMasterdataCombo();
    wireEvents();
    applyPermissions();
  } catch (e) {
    logout();
  }
}

boot();
