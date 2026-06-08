// Stock page: shows current balance per supplier/area/unit with a client filter.
let stockCache = [];

function esc(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function logout() {
  localStorage.removeItem("token");
  location.href = "/";
}

function renderStock(query) {
  const q = query.toLowerCase();
  const rows = stockCache.filter(
    (r) =>
      !q ||
      `${r.supplier_name} ${r.area_name} ${r.unit_name}`.toLowerCase().includes(q)
  );

  document.getElementById("stock-body").innerHTML =
    rows
      .map(
        (r) =>
          `<tr><td>${esc(r.supplier_name)}</td><td>${esc(r.area_name)}</td><td>${esc(r.unit_name)}</td><td>${r.quantity}</td></tr>`
      )
      .join("") || `<tr class="empty"><td colspan="4">Brak danych</td></tr>`;
}

async function boot() {
  if (!token()) {
    location.href = "/";
    return;
  }
  try {
    await api("/auth/me");
    document.getElementById("logout-btn").onclick = logout;

    stockCache = await api("/pallets");
    const filter = document.getElementById("stock-filter");
    filter.oninput = () => renderStock(filter.value.trim());
    renderStock("");
  } catch (e) {
    logout();
  }
}

boot();
