// Dashboard page logic: data loading, permission gating, actions.
const state = { user: null };

const TX_PREFIXES = ["rc", "rl", "co"];

// Searchable comboboxes (server-side search) — both for the transaction form
// fields and the masterdata management lists.
const COMBO_LIMIT = 8;
const FIELD_KINDS = { area: "areas", supplier: "suppliers", unit: "units" };
const MD = [
  ["areas", "Obszary"],
  ["suppliers", "Dostawcy"],
  ["units", "Jednostki"],
];

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

// ---------- Masterdata management combos ----------
function renderMasterdataCombos() {
  document.getElementById("md-lists").innerHTML = `
    <div class="md-grid">
      ${MD.map(
        ([kind, title]) => `
        <div class="combo" data-kind="${kind}">
          <div class="md-panel-head">
            <strong>${title}</strong>
            <span class="badge" id="count-${kind}">0</span>
          </div>
          <input class="combo-input" id="combo-${kind}" placeholder="Szukaj / wybierz…" autocomplete="off" />
          <div class="combo-menu hidden" id="menu-${kind}"></div>
          <div class="combo-selected hidden" id="sel-${kind}"></div>
        </div>`
      ).join("")}
    </div>`;

  MD.forEach(([kind]) => setupMasterdataCombo(kind));
}

function setupMasterdataCombo(kind) {
  const input = document.getElementById(`combo-${kind}`);
  const menu = document.getElementById(`menu-${kind}`);

  const search = debounce(async () => {
    const { items, total } = await fetchMd(kind, input.value.trim());
    document.getElementById(`count-${kind}`).textContent = total;
    renderOptions(menu, items, (uuid, name) => selectMasterdataItem(kind, uuid, name));
  }, 200);

  input.addEventListener("focus", search);
  input.addEventListener("input", search);
  input.addEventListener("blur", () => setTimeout(() => menu.classList.add("hidden"), 150));

  refreshComboCount(kind);
}

function selectMasterdataItem(kind, uuid, name) {
  const editable = can("masterdata");
  const sel = document.getElementById(`sel-${kind}`);

  sel.innerHTML = `<span>${esc(name)}</span>${
    editable ? `<button class="danger" data-uuid="${uuid}">Usuń</button>` : ""
  }`;
  sel.classList.remove("hidden");

  document.getElementById(`menu-${kind}`).classList.add("hidden");
  document.getElementById(`combo-${kind}`).value = name;

  const btn = sel.querySelector("button[data-uuid]");
  if (btn) btn.onclick = () => deleteMasterdata(kind, uuid);
}

function clearComboSelection(kind) {
  const sel = document.getElementById(`sel-${kind}`);
  sel.classList.add("hidden");
  sel.innerHTML = "";
  document.getElementById(`combo-${kind}`).value = "";
}

async function refreshComboCount(kind) {
  const { total } = await fetchMd(kind, "");
  document.getElementById(`count-${kind}`).textContent = total;
}

// ---------- Stock ----------
async function loadStock() {
  const rows = await api("/pallets");
  document.getElementById("stock-body").innerHTML = rows
    .map(
      (r) =>
        `<tr><td>${esc(r.supplier_name)}</td><td>${esc(r.area_name)}</td><td>${esc(r.unit_name)}</td><td>${r.quantity}</td></tr>`
    )
    .join("");
}

// ---------- Actions ----------
async function submitTx(prefix, type) {
  const msg = document.getElementById(prefix + "-msg");
  msg.className = "msg";
  msg.textContent = "";

  const area = document.getElementById(prefix + "-area").value;
  const supplier = document.getElementById(prefix + "-supplier").value;
  const unit = document.getElementById(prefix + "-unit").value;

  if (!area || !supplier || !unit) {
    msg.classList.add("error");
    msg.textContent = "Wybierz obszar, dostawcę i jednostkę";
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
        quantity: parseInt(document.getElementById(prefix + "-qty").value, 10),
        comment: document.getElementById(prefix + "-comment").value || null,
      },
    });
    msg.classList.add("ok");
    msg.textContent = "Zapisano";
    document.getElementById(prefix + "-qty").value = "";
    document.getElementById(prefix + "-comment").value = "";
    loadStock();
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

async function addMasterdata(kind, inputId) {
  const msg = document.getElementById("md-msg");
  msg.className = "msg";
  msg.textContent = "";
  const input = document.getElementById(inputId);
  const name = input.value.trim();
  if (!name) return;
  try {
    await api("/" + kind, { method: "POST", body: { name } });
    input.value = "";
    msg.classList.add("ok");
    msg.textContent = "Dodano";
    refreshComboCount(kind);
  } catch (e) {
    msg.classList.add("error");
    msg.textContent = e.message;
  }
}

async function deleteMasterdata(kind, uuid) {
  try {
    await api(`/${kind}/${uuid}`, { method: "DELETE" });
    clearComboSelection(kind);
    refreshComboCount(kind);
    loadStock();
  } catch (e) {
    document.getElementById("md-msg").textContent = e.message;
  }
}

function wireEvents() {
  document.getElementById("logout-btn").onclick = logout;
  document.querySelectorAll("button[data-tx]").forEach((b) => {
    b.onclick = () => submitTx(b.dataset.prefix, b.dataset.tx);
  });
  document.querySelectorAll("button[data-md]").forEach((b) => {
    b.onclick = () => addMasterdata(b.dataset.md, b.dataset.input);
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
    document.getElementById("user-info").textContent =
      `${state.user.username} (${state.user.role})`;
    setupFieldCombos();
    renderMasterdataCombos();
    await loadStock();
    wireEvents();
    applyPermissions();
  } catch (e) {
    logout();
  }
}

boot();
